"""View > *Filter lines* (Ctrl+G): only the lines of a file that match a
pattern, each under its own number -- ``grep`` inside the viewer.

A departure, asked for: DN's viewer had F6's filters, which hide characters,
and nothing that hid lines.  The name says *lines* so the two are not taken
for one another.

**Nothing in the viewer counts lines**, which is what lets a gigabyte open at
once; this does, once, on a thread (:class:`LineScan`), reading the file in
``WINDOW`` pieces on its own descriptor as search does.  Every line is decoded
in the viewer's encoding and matched as text -- the encodings the viewer
offers are UTF-8 and one-byte code pages, so a line always ends at a ``\\n``
byte.  What is kept of a hit is its number, where it is, and its text up to
``TEXT_LIMIT`` characters: what the rows are painted from without going back to
the file.

**A scan can go on from where it stopped** (``scanned_to``), which is how
*Follow end* keeps a filtered log filtered: only what was written since is
read.  A last line with no ending yet is matched but not passed -- it is read
again, whole or longer, by the next scan.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from typing import Callable

from navigator.lib.viewer.layout import decode

#: How much of the file one read takes.
WINDOW = 1024 * 1024

#: How many matching lines are kept: past it the scan stops, and says so.
HIT_LIMIT = 200_000

#: How much of a matching line's text is kept for its row.
TEXT_LIMIT = 4096

#: The longest a line is let grow while no ending is found: past it, what is
#: read so far is taken as a line of its own, as the viewer cuts a line at
#: ``LINE_LIMIT`` -- a minified gigabyte is not held in memory to be matched.
LONG_LINE = 4 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class LinePattern:
    """What *Filter lines* looks for: *text*, literal or a regular
    expression, in either case or this one, and the lines matching it or --
    *invert* -- the lines that do not."""

    text: str
    regex: bool = False
    case: bool = False
    invert: bool = False

    def compile(self) -> re.Pattern[str]:
        """The pattern lines are matched against.  Raises ``re.error`` for a
        regular expression that is not one."""
        source = self.text if self.regex else re.escape(self.text)
        return re.compile(source, 0 if self.case else re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Hit:
    """A line shown: its number from 1, its first byte, where its text ends
    (before the ``\\r\\n`` or ``\\n``), and that text, decoded."""

    number: int
    start: int
    end: int
    text: str


@dataclass(eq=False)
class LineScan:
    """The lines matching *pattern* in a file, as far as it has been read.

    The thread doing a scan writes ``position`` and the lists; the loop reads
    them once :meth:`scan` has returned, and sets the stop flag.  Nothing
    reactive crosses.
    """

    pattern: LinePattern
    codec: str = "utf-8"
    hits: list[Hit] = field(default_factory=list)
    #: Lines passed, ended ones only.
    lines: int = 0
    #: Where the next scan starts: just after the last ended line.
    scanned_to: int = 0
    #: The last line, not ended yet, when it matched: shown, never counted.
    tail: Hit | None = None
    #: Whether ``HIT_LIMIT`` was reached and the rest not looked at.
    truncated: bool = False
    #: How far the scan running now has got, for its progress box.
    position: int = 0

    def __post_init__(self) -> None:
        self._compiled = self.pattern.compile()
        self._stop = threading.Event()

    # -- the job contract SearchProgress reads ---------------------------------

    def stop(self) -> None:
        self._stop.set()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    # -- what is shown ----------------------------------------------------------

    @property
    def shown(self) -> list[Hit]:
        """The rows: every hit, and the unfinished last line when it matched."""
        return self.hits if self.tail is None else [*self.hits, self.tail]

    def matches(self, text: str) -> bool:
        return (self._compiled.search(text) is not None) != self.pattern.invert

    def spans(self, text: str) -> list[tuple[int, int]]:
        """Where *text* -- a row as painted -- matches, to mark: none for an
        inverted pattern, whose lines are the ones that do not."""
        if self.pattern.invert:
            return []
        return [(m.start(), m.end()) for m in self._compiled.finditer(text) if m.end() > m.start()]

    # -- reading ---------------------------------------------------------------

    def scan(self, read: Callable[[int, int], bytes], size: int) -> None:
        """Read on from ``scanned_to`` to *size* through *read(offset,
        count)*, keeping the lines that match.  On a thread; it stops early
        when stopped, or once ``HIT_LIMIT`` lines are kept."""
        if self.truncated:
            return
        self.tail = None
        pos = self.scanned_to
        carry = b""
        while pos < size and not self.stopped:
            self.position = pos
            data = read(pos, min(WINDOW, size - pos))
            if not data:
                break
            block = carry + data
            base = pos - len(carry)
            pos += len(data)
            start = 0
            while True:
                eol = block.find(b"\n", start)
                if eol < 0:
                    break
                self._line(block, base, start, eol)
                if self.truncated:
                    return
                start = eol + 1
                self.scanned_to = base + start
            if len(block) - start > LONG_LINE:
                self._line(block, base, start, len(block))
                if self.truncated:
                    return
                start = len(block)
                self.scanned_to = base + start
            carry = block[start:]
        self.position = pos
        if carry and not self.stopped and pos >= size:
            # The last line, not ended (yet): matched, not passed.
            text = self._text(carry)
            if self.matches(text):
                self.tail = Hit(self.lines + 1, self.scanned_to, self.scanned_to + len(carry.rstrip(b"\r")),
                                text[:TEXT_LIMIT])

    def _line(self, block: bytes, base: int, start: int, eol: int) -> None:
        self.lines += 1
        end = eol - 1 if eol > start and block[eol - 1] == 0x0D else eol
        text = self._text(block[start:end])
        if self.matches(text):
            self.hits.append(Hit(self.lines, base + start, base + end, text[:TEXT_LIMIT]))
            if len(self.hits) >= HIT_LIMIT:
                self.truncated = True

    def _text(self, data: bytes) -> str:
        return decode(data.rstrip(b"\r"), self.codec)


#: The last pattern asked for, which the box opens on in every viewer -- as
#: F7's ``last_search``.
last_pattern: LinePattern | None = None


class Reader:
    """A viewer source read on a thread: its own descriptor for a file on the
    disk (the loop paints through the shared one meanwhile), the bytes held
    for one read whole, the drive, waiting, for one across a network.
    Closed when done with."""

    def __init__(self, source: object) -> None:
        self._fd: int | None = None
        data = getattr(source, "_data", None)
        if getattr(source, "remote", False):
            self.read = source.read_blocking  # type: ignore[attr-defined]
        elif data is not None:
            self.read = lambda offset, count: data[offset:offset + count]
        else:
            import os

            fd = self._fd = os.open(source.path, os.O_RDONLY)  # type: ignore[attr-defined]
            self.read = lambda offset, count: os.pread(fd, count, offset)

    def close(self) -> None:
        if self._fd is not None:
            import os

            os.close(self._fd)
            self._fd = None


def scan(line_scan: LineScan, source: object, size: int) -> LineScan:
    """*line_scan* read on to *size* through a :class:`Reader` of *source*:
    the thread's whole errand."""
    reader = Reader(source)
    try:
        line_scan.scan(reader.read, size)
    finally:
        reader.close()
    return line_scan
