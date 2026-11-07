"""The text an editor holds: lines, and the terminator each one ended with.

**Every line keeps its own terminator**, so a file with CRLF in one half and LF
in the other is written back exactly as it was read.  ``endings[i]`` is what
follows ``lines[i]`` -- ``"\\r\\n"``, ``"\\n"``, ``"\\r"``, or ``""`` for the last
line, which a file ending in a newline leaves empty.  A line break the user
types takes :attr:`Document.newline`, the ending the file uses most.

Text crossing the model's boundary -- what an edit inserts, what a delete
returns -- is a plain string whose line breaks are the terminators themselves.
Deleting a range and inserting what came back therefore restores the endings
too, which is all undo needs.
"""

from __future__ import annotations

import codecs
import os
import re
import stat
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from navkit.i18n import tr
from navigator.lib.editor import encodings
from navigator.lib.system.job import Stopped
from navigator.lib.system.memory import NotEnoughMemory

#: A line break, longest first so CRLF is one break and not two.
BREAK = re.compile(r"\r\n|\r|\n")
#: The same, captured, so ``split`` hands back the breaks between the lines.
_BREAK_SPLIT = re.compile(r"(\r\n|\r|\n)")

#: How much of a file is read at a time: large, so the work per read is a
#: handful of calls into C and the thread holds the interpreter only briefly
#: between them -- the loop keeps painting while a file is read.
READ_CHUNK = 4 << 20

#: What a line costs in memory beyond its characters: the string's header
#: and its slot in ``lines`` and in ``endings``.  A CRLF ending is a string of
#: its own besides; a lone CR or LF is one CPython shares.
_LINE_COST = 64
_CRLF_COST = 56

#: What a new file's line breaks are, unless the editor is told otherwise.
DEFAULT_NEWLINE = "\n"

#: The Editor setup's *Line divisor* choices, as the terminators they name.
NEWLINES = {"lf": "\n", "crlf": "\r\n", "cr": "\r"}

#: What the bottom frame calls each terminator.
ENDING_NAMES = {"\n": "LF", "\r\n": "CRLF", "\r": "CR"}


@dataclass(frozen=True, slots=True, order=True)
class Pos:
    """A place in the text: a line, and a string index into it."""

    line: int
    index: int


def shifted(pos: Pos, kind: str, start: Pos, end: Pos, *, stay: bool = False) -> Pos:
    """Where *pos* is after an edit: ``"insert"`` put text from *start* to
    *end*, or ``"delete"`` took out what lay between them.

    A place inside what was deleted closes up to *start*.  Text inserted
    right at *pos* goes before it, unless *stay* -- a block's end, which
    should not swallow what is typed after it.
    """
    if kind == "insert":
        if pos < start or (stay and pos == start):
            return pos
        if pos.line == start.line:
            return Pos(end.line, end.index + pos.index - start.index)
        return Pos(pos.line + end.line - start.line, pos.index)
    if pos <= start:
        return pos
    if pos <= end:
        return start
    if pos.line == end.line:
        return Pos(start.line, start.index + pos.index - end.index)
    return Pos(pos.line - (end.line - start.line), pos.index)


def split_text(text: str) -> tuple[list[str], list[str]]:
    """*text* as lines and the terminators between them; the last has ``""``."""
    lines, endings, start = [], [], 0
    for match in BREAK.finditer(text):
        lines.append(text[start:match.start()])
        endings.append(match.group())
        start = match.end()
    lines.append(text[start:])
    endings.append("")
    return lines, endings


def decode(data: bytes) -> str:
    """UTF-8, with every byte that is not kept as a lone surrogate."""
    return data.decode("utf-8", "surrogateescape")


def encode(text: str) -> bytes:
    """The inverse of :func:`decode`, exactly."""
    return text.encode("utf-8", "surrogateescape")


def _split(text: str) -> tuple[list[str], list[str]]:
    """:func:`split_text` without the final ``""``, done in C.

    Not ``str.splitlines``, which breaks at form feeds and ``\\u2028`` too.
    """
    if "\r" not in text:
        lines = text.split("\n")
        return lines, ["\n"] * (len(lines) - 1)
    parts = _BREAK_SPLIT.split(text)
    return parts[0::2], parts[1::2]


def _newline(counts: Counter[str]) -> str:
    """The terminator used most; a tie goes to the one met first."""
    return counts.most_common(1)[0][0] if counts else DEFAULT_NEWLINE


class LineReader:
    """A text read a chunk at a time into lines and their terminators.

    Gives exactly what :meth:`Document.from_bytes` gives for the whole, however
    the bytes are cut.  Each chunk is decoded up to its last line break in one
    call -- a CR or LF byte is never part of a UTF-8 sequence, nor of a
    legacy code page's (``navigator.lib.codepages`` admits none that is), so a run of whole lines decodes as its lines would
    one by one -- and what follows the break waits for the next chunk.  **A CR
    at a chunk's very end waits too**, since the LF that would make it one
    CRLF may be the next chunk's first byte: DN's ``ReadBlock`` stepped its
    file back one byte for the same CR.

    The encoding is *encoding*, or what the first bytes' byte order mark says
    (:func:`~navigator.lib.editor.encodings.sniff`), the mark taken off.
    UTF-16 and UTF-32, whose CR and LF are more than a byte, go through an
    incremental decoder first and are cut the same way as text.  *fallback*,
    a legacy code page, is what a sniffed UTF-8 text that turned out not to be is read
    as instead (``[editor] fallback_encoding``).
    """

    def __init__(self, encoding: str | None = None, fallback: str = "") -> None:
        self.lines: list[str] = []
        self.endings: list[str] = []
        self.counts: Counter[str] = Counter()
        self.encoding = encoding
        self.fallback = fallback
        #: Whether a byte did not decode, kept as a lone surrogate.
        self.escaped = False
        #: The first bytes, held until there are enough to tell a mark by.
        self._head = b"" if encoding is None else None
        self._strip = encoding is not None
        #: With *encoding* given: the first bytes, held until its mark can be told.
        self._held = b""
        #: Bytes after the last break taken, not yet decoded.
        self._pending: list[bytes] = []
        self._pending_size = 0
        #: UTF-16 or UTF-32 decoder, and the text it gave after the last break.
        self._decoder: codecs.IncrementalDecoder | None = None
        self._text = ""
        #: What the decoded characters take, as CPython stores them.
        self._chars = 0

    def feed(self, chunk: bytes) -> None:
        if self._head is not None:
            chunk = self._head + chunk
            if len(chunk) < 4 and chunk and any(
                    mark.startswith(chunk) for mark in (codecs.BOM_UTF8, codecs.BOM_UTF16_LE,
                                                        codecs.BOM_UTF16_BE, codecs.BOM_UTF32_LE,
                                                        codecs.BOM_UTF32_BE)):
                self._head = chunk
                return
            self._head = None
            self.encoding, skip = encodings.sniff(chunk)
            chunk = chunk[skip:]
        elif self._strip:
            # The encoding's own mark, if the text starts with it -- held
            # until there are as many bytes as the mark has.
            mark = encodings.bom(self.encoding or "")
            chunk = self._held + chunk
            if mark and len(chunk) < len(mark) and mark.startswith(chunk):
                self._held = chunk
                return
            self._strip, self._held = False, b""
            if mark and chunk.startswith(mark):
                chunk = chunk[len(mark):]
        if not encodings.ascii_compatible(self.encoding or encodings.UTF8):
            if self._decoder is None:
                self._decoder = codecs.getincrementaldecoder(
                    encodings.python_codec(self.encoding or ""))("strict")
            self._feed_text(self._decoder.decode(chunk))
            return
        end = len(chunk) - chunk.endswith(b"\r")
        cut = max(chunk.rfind(b"\n", 0, end), chunk.rfind(b"\r", 0, end))
        if cut < 0:
            if chunk:
                self._pending.append(chunk)
                self._pending_size += len(chunk)
            return
        head = chunk[:cut + 1]
        if self._pending:
            head = b"".join([*self._pending, head])
        rest = chunk[cut + 1:]
        self._pending = [rest] if rest else []
        self._pending_size = len(rest)
        text = self._decode(head)
        lines, endings = _split(text)
        lines.pop()  # the "" after the break the head ends with
        self._take(text, lines, endings)

    def _feed_text(self, text: str) -> None:
        """UTF-16 and UTF-32 :meth:`feed`: the same cut, on what the decoder gave."""
        text = self._text + text
        end = len(text) - text.endswith("\r")
        cut = max(text.rfind("\n", 0, end), text.rfind("\r", 0, end))
        if cut < 0:
            self._text = text
            return
        head, self._text = text[:cut + 1], text[cut + 1:]
        lines, endings = _split(head)
        lines.pop()
        self._take(head, lines, endings)

    def _decode(self, data: bytes) -> str:
        return encodings.decode(data, self.encoding or encodings.UTF8)

    def finish(self) -> Document:
        """The document, with whatever followed the last break as its last line.

        Raises ``UnicodeDecodeError`` for UTF-16 or UTF-32 that does not decode."""
        if self._held:
            # Fewer bytes than the encoding's mark: they are text.
            held, self._held, self._strip = self._held, b"", False
            self.feed(held)
        if self._head is not None:
            # Fewer bytes than a mark: sniff what there is.
            head, self._head = self._head, None
            self.encoding, skip = encodings.sniff(head)
            if head[skip:]:
                self._pending, self._pending_size = [head[skip:]], len(head) - skip
        encoding = self.encoding or encodings.UTF8
        if self._decoder is not None or not encodings.ascii_compatible(encoding):
            decoder = self._decoder or codecs.getincrementaldecoder(
                encodings.python_codec(encoding))("strict")
            text = self._text + decoder.decode(b"".join(self._pending), final=True)
            self._text = ""
        else:
            text = self._decode(b"".join(self._pending))
        self._pending, self._pending_size = [], 0
        lines, endings = _split(text)
        self._take(text, lines, endings)
        self.endings.append("")
        document = Document(self.lines, self.endings, _newline(self.counts), encoding,
                            counts=self.counts)
        if self.escaped and encoding == encodings.UTF8 and self.fallback not in ("", encodings.UTF8):
            return document.reinterpreted(self.fallback)
        return document

    def _take(self, text: str, lines: list[str], endings: list[str]) -> None:
        self.lines.extend(lines)
        self.endings.extend(endings)
        self.counts.update(endings)
        ascii_ = text.isascii()
        if not ascii_ and not self.escaped:
            self.escaped = encodings.has_escaped(text)
        # Latin-1 text is a byte a character in CPython; anything else two or
        # more -- and an undecodable byte, kept as a surrogate, is two.
        self._chars += len(text) * (1 if ascii_ else 2)

    @property
    def estimate(self) -> int:
        """Roughly what the text read so far takes in memory, in bytes."""
        return (self._chars + self._pending_size + _LINE_COST * len(self.lines)
                + _CRLF_COST * self.counts.get("\r\n", 0))


def encode_lines(lines: list[str], endings: list[str], job: Any = None, *,
                 step: int = 65536, encoding: str = encodings.UTF8):
    """*lines* and their *endings* as bytes, *step* lines to a chunk: a save's.

    A *job* sees ``position`` as the lines done so far.  Each chunk is joined
    and encoded in one call, so a thread writing it hardly holds the loop up.
    The bytes are in *encoding*, its byte order mark first.  A character it
    cannot write raises ``UnicodeEncodeError`` -- check first with
    :func:`~navigator.lib.editor.encodings.first_unencodable` to say where.
    """
    mark = encodings.bom(encoding)
    if mark:
        yield mark
    for start in range(0, len(lines), step):
        stop = start + step
        parts = [part for pair in zip(lines[start:stop], endings[start:stop]) for part in pair]
        yield encodings.encode("".join(parts), encoding)
        if job is not None:
            job.position = min(stop, len(lines))


def read_text(path: Path | str, job: Any = None, *, chunk: int = READ_CHUNK,
              budget: int | None = None, as_root: bool = False, fallback: str = "") -> str:
    """*path*'s text as one string, line breaks and all: ^K R's block.

    Read as :func:`read_document` reads, a chunk at a time.
    """
    document = read_document(path, job, chunk=chunk, budget=budget, as_root=as_root,
                             fallback=fallback)
    return "".join(line + ending for line, ending in zip(document.lines, document.endings))


def read_document(path: Path | str, job: Any = None, *, chunk: int = READ_CHUNK,
                  budget: int | None = None, as_root: bool = False,
                  encoding: str | None = None, fallback: str = "") -> Document:
    """Read *path* a chunk at a time, for a thread to do while the loop paints.

    Raises ``OSError`` for anything that is not a regular file -- looked at
    before it is opened, so a FIFO cannot hang the reader on ``open``.  A
    *job* sees ``total`` and ``position`` as bytes and stops the read by
    ``stop()``, which raises :class:`~navigator.lib.system.job.Stopped`.

    With a *budget* in bytes, raises :class:`~navigator.lib.system.memory.NotEnoughMemory`
    rather than go past it, as DN's ``ReadBlock`` checked ``MemAvail``: at
    once, for a file larger than the budget; after each chunk, for a text
    whose lines so far say the whole will not fit; and for what was read, for
    a file whose size said nothing (``/proc``) or whose tail is denser.

    *as_root* reads it through the root helper
    (:data:`~navigator.lib.drives.root.ROOT_DRIVE`).

    The text is in *encoding*, else in what its byte order mark says, else
    UTF-8 -- or the legacy *fallback* when it is not.  A text that claims
    UTF-16 or UTF-32 by its mark and does not decode is read again as UTF-8.
    """
    try:
        return _read_document(path, job, chunk, budget, as_root, encoding, fallback)
    except UnicodeDecodeError:
        return _read_document(path, job, chunk, budget, as_root, encodings.UTF8, fallback)


def _read_document(path: Path | str, job: Any, chunk: int, budget: int | None, as_root: bool,
                   encoding: str | None, fallback: str) -> Document:
    if as_root:
        from navigator.lib.drives.location import Location
        from navigator.lib.drives.root import ROOT_DRIVE

        where = Location.of(Path(path))
        info = ROOT_DRIVE.stat(where)
    else:
        info = os.stat(path)
    if not stat.S_ISREG(info.st_mode):
        raise OSError(21 if stat.S_ISDIR(info.st_mode) else 22,
                      tr("Not a regular file"), str(path))
    size = info.st_size
    if budget is not None and size > budget:
        raise NotEnoughMemory(str(path))
    if job is not None:
        job.total = size
        job.position = 0
    reader = LineReader(encoding, fallback)
    done = 0
    with (ROOT_DRIVE.open_read(where) if as_root else open(path, "rb", buffering=0)) as file:
        while True:
            if job is not None and job.stopped:
                raise Stopped
            data = file.read(chunk)
            if not data:
                break
            reader.feed(data)
            done += len(data)
            if job is not None:
                job.position = done
            if budget is not None:
                estimate = reader.estimate
                if estimate > budget or (done < size and estimate * size // done > budget):
                    raise NotEnoughMemory(str(path))
    return reader.finish()


@dataclass
class Document:
    """Lines of text, their terminators, the terminator new lines take, and the
    encoding the bytes are in (:mod:`navigator.lib.editor.encodings`).

    ``counts`` tallies the terminators, kept by :meth:`insert` and
    :meth:`delete`, so the bottom frame can say LF, CRLF, CR or Mixed without
    walking the text.
    """

    lines: list[str] = field(default_factory=lambda: [""])
    endings: list[str] = field(default_factory=lambda: [""])
    newline: str = DEFAULT_NEWLINE
    encoding: str = encodings.UTF8
    counts: Counter[str] = field(default=None, repr=False, compare=False)  # type: ignore[assignment]
    #: What ``highlight.ini``'s masks say for this file, read with it on the
    #: reading thread (``navigator.widgets.editor.loading``); the editor
    #: applies it when it takes the text up.  Not part of the text.
    defaults: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.counts is None:
            self.counts = Counter(self.endings[:-1])
            self.counts.pop("", None)

    @classmethod
    def from_bytes(cls, data: bytes, encoding: str | None = None, fallback: str = "") -> Document:
        """*data* as a text, read as :func:`read_document` reads a file."""
        reader = LineReader(encoding, fallback)
        reader.feed(data)
        try:
            return reader.finish()
        except UnicodeDecodeError:
            if encoding == encodings.UTF8:
                raise
            return cls.from_bytes(data, encodings.UTF8, fallback)

    @classmethod
    def load(cls, path: Path | str, fallback: str = "") -> Document:
        """Read *path*.  Raises ``OSError`` for anything that is not a regular file.

        A file that does not exist is not an error here: the caller decides
        whether an editor may start one.
        """
        return read_document(path, fallback=fallback)

    def encode(self, *, mark: bool = True) -> bytes:
        """The bytes this document is: exactly what it was read from, if unedited.

        In :attr:`encoding`, its byte order mark first unless *mark* is False.
        Raises ``UnicodeEncodeError`` for a character the encoding has not."""
        return b"".join(encode_lines(self.lines, self.endings, encoding=self.encoding)) if mark \
            else encodings.encode("".join(part for pair in zip(self.lines, self.endings)
                                          for part in pair), self.encoding)

    def reinterpreted(self, encoding: str) -> Document:
        """The same bytes read as *encoding*: *Reopen with encoding*, done on the
        text in memory, so a changed text keeps its changes.  A byte order mark
        is not part of it: the new text gets *encoding*'s, if any.

        Raises ``UnicodeDecodeError`` when the bytes are not *encoding*, or
        ``UnicodeEncodeError`` when the text has characters its own encoding
        cannot write."""
        data = self.encode(mark=False)
        reader = LineReader(encoding)
        reader._strip = False
        reader.feed(data)
        document = reader.finish()
        if not document.counts:
            document.newline = self.newline
        return document

    # -- line endings ------------------------------------------------------------

    @property
    def line_ending(self) -> str:
        """``LF``, ``CRLF`` or ``CR`` for the one terminator the text uses,
        ``Mixed`` for more than one, and the one new lines take for none."""
        used = [ending for ending, count in self.counts.items() if count > 0]
        if len(used) > 1:
            return "Mixed"
        return ENDING_NAMES.get(used[0] if used else self.newline, "LF")

    def _count(self, removed: list[str], added: list[str]) -> None:
        counts = self.counts
        for ending in removed:
            if ending:
                counts[ending] -= 1
                if counts[ending] <= 0:
                    del counts[ending]
        for ending in added:
            if ending:
                counts[ending] += 1

    # -- reading ---------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.lines)

    @property
    def end(self) -> Pos:
        return Pos(len(self.lines) - 1, len(self.lines[-1]))

    def clamp(self, pos: Pos) -> Pos:
        line = max(0, min(pos.line, len(self.lines) - 1))
        return Pos(line, max(0, min(pos.index, len(self.lines[line]))))

    def text(self, start: Pos, end: Pos) -> str:
        """What lies between *start* and *end*, terminators included."""
        if start.line == end.line:
            return self.lines[start.line][start.index:end.index]
        parts = [self.lines[start.line][start.index:], self.endings[start.line]]
        for line in range(start.line + 1, end.line):
            parts += [self.lines[line], self.endings[line]]
        parts.append(self.lines[end.line][:end.index])
        return "".join(parts)

    # -- the two edits everything else is made of ------------------------------

    def insert(self, at: Pos, text: str) -> Pos:
        """Put *text* at *at* and return where it ends."""
        new, breaks = split_text(text)
        line = self.lines[at.line]
        head, tail = line[:at.index], line[at.index:]
        if len(new) == 1:
            self.lines[at.line] = head + new[0] + tail
            return Pos(at.line, at.index + len(new[0]))
        last_ending = self.endings[at.line]
        new[0] = head + new[0]
        end = Pos(at.line + len(new) - 1, len(new[-1]))
        new[-1] = new[-1] + tail
        breaks[-1] = last_ending
        self._count((), breaks[:-1])
        self.lines[at.line:at.line + 1] = new
        self.endings[at.line:at.line + 1] = breaks
        return end

    def delete(self, start: Pos, end: Pos) -> str:
        """Take out what lies between *start* and *end*, and return it."""
        removed = self.text(start, end)
        if start.line == end.line:
            line = self.lines[start.line]
            self.lines[start.line] = line[:start.index] + line[end.index:]
            return removed
        joined = self.lines[start.line][:start.index] + self.lines[end.line][end.index:]
        ending = self.endings[end.line]
        self._count(self.endings[start.line:end.line], ())
        self.lines[start.line:end.line + 1] = [joined]
        self.endings[start.line:end.line + 1] = [ending]
        return removed
