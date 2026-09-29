"""What F3 shows, before anything paints it: DOS Navigator's ``TFileViewer`` model.

``FVIEWER.PAS`` kept a 32K window onto the file and walked it with
``Seek``, ``MakeLines``, ``CountUp`` and ``CountDown``; this module is those
four and ``SearchFileStr``, with no widget in it, so every rule about where a
line starts can be tested without a screen.

**Positions are byte offsets**, as they were in DN: a view's top is the offset
of the first line it shows, never a line number, so opening a gigabyte costs
nothing and the scroll bar's value is simply how far into the file the view is.
A line number would need the whole file counted first.

**The file is read with ``os.pread``, not mapped.**  ``mmap`` would give
``rfind`` and ``re`` the whole file for free, and a log truncated while it is
mapped then kills Navigator with ``SIGBUS`` on the next repaint.  A cache of
fixed chunks costs a copy and cannot crash.

**Text is UTF-8 and an undecodable byte is CP437.**  That is to say, a byte
that is not part of a valid sequence is drawn as the glyph DOS Navigator would
have drawn for it -- and so is a control character, which DN drew from the
same font -- so a binary looks the way it did in 1995 and a UTF-8 file looks
the way it does in a terminal.
"""

from __future__ import annotations

import os
import re
import stat
import threading
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from navkit.screen import char_width

#: How much the cache reads at once, and how many such chunks it keeps.
CHUNK = 64 * 1024
CACHED_CHUNKS = 32

#: The longest line the viewer will look for the end of.  DN's ``Lines[].Len``
#: was a byte, so an unwrapped line was cut into 255-byte pieces; this is the
#: same cut made for a modern screen, and what stops a minified megabyte on
#: one line from being scanned whole for every row painted.
LINE_LIMIT = 64 * 1024

#: How far back a line start is looked for before giving up and cutting.
#: Past this a line longer than ``LINE_LIMIT`` is still cut into pieces, but
#: the pieces going up need not line up with the ones coming down.
BACK_LIMIT = 16 * LINE_LIMIT

#: How much a search reads between two looks at whether it should stop.
SEARCH_WINDOW = 1024 * 1024

#: What a regular file reporting size 0 -- ``/proc``, ``/sys`` -- is read up to.
UNSIZED_LIMIT = 16 * 1024 * 1024

#: Tabs stop every eight columns, as ``MoveStr``'s ``and dx,7`` had them.
TAB = 8

#: What DN's filter puts in place of a byte it hides.
FILTERED = "·"

#: The three filters F6 cycles, by the tag the info line gives each.
FILTER_TAGS = ("", "{ASCII}", "{32-255}")

#: The glyphs code page 437 puts at 0x00 to 0x1F, which Python's ``cp437``
#: codec decodes as control characters instead.  0x00 is a blank on a VGA.
_CP437_LOW = (
    " ☺☻♥♦♣♠•◘○◙♂♀♪♫☼"
    "►◄↕‼¶§▬↨↑↓→←∟↔▲▼"
)

_EOL = re.compile(rb"[\r\n]")


def cp437(byte: int) -> str:
    """The glyph a VGA in code page 437 shows for *byte*."""
    if byte < 0x20:
        return _CP437_LOW[byte]
    if byte == 0x7F:
        return "⌂"
    return bytes((byte,)).decode("cp437")


@dataclass(frozen=True, slots=True)
class Line:
    """One screen row of text: its cells, the bytes it covers, and what follows.

    ``cells`` is one entry per *column*: a character and the offset of the
    byte it came from.  A wide character is followed by ``("", offset)``, the
    column it covers, and a tab by as many blanks as it expands to -- so
    scrolling sideways is a slice, and a search hit is found by offset.
    """

    cells: tuple[tuple[str, int], ...]
    start: int
    next: int


class ViewSource:
    """A file, read in cached chunks, and walked in lines."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._fd: int | None = None
        self._chunks: OrderedDict[int, bytes] = OrderedDict()
        self._data: bytes | None = None
        self._eol_cache: tuple[int, int, int] | None = None
        info = os.stat(self.path)
        if not stat.S_ISREG(info.st_mode):
            # A fifo would block the loop on the first read, a device might
            # never end: DN refused anything that was not a file as well.
            raise OSError(21 if stat.S_ISDIR(info.st_mode) else 22,
                          "Not a regular file", str(self.path))
        self._open()
        self.size = info.st_size
        if self.size == 0:
            # /proc and /sys report nothing and produce plenty.
            self._data = self._read_all()
            self.size = len(self._data)

    # -- reading ---------------------------------------------------------------

    def _open(self) -> int:
        if self._fd is None:
            self._fd = os.open(self.path, os.O_RDONLY)
        return self._fd

    def close(self) -> None:
        """Let the file go.  A later read opens it again."""
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        self._chunks.clear()

    def _read_all(self) -> bytes:
        parts, total = [], 0
        fd = self._open()
        while total < UNSIZED_LIMIT:
            part = os.read(fd, min(CHUNK, UNSIZED_LIMIT - total))
            if not part:
                break
            parts.append(part)
            total += len(part)
        return b"".join(parts)

    def _chunk(self, index: int) -> bytes:
        chunk = self._chunks.get(index)
        if chunk is not None:
            self._chunks.move_to_end(index)
            return chunk
        chunk = os.pread(self._open(), CHUNK, index * CHUNK)
        self._chunks[index] = chunk
        if len(self._chunks) > CACHED_CHUNKS:
            self._chunks.popitem(last=False)
        return chunk

    def read(self, offset: int, count: int) -> bytes:
        """Up to *count* bytes at *offset*, never past the size taken at open.

        Short if the file shrank since: a truncated log shows what is left
        rather than failing, which is the other half of not mapping it.
        """
        offset = max(0, offset)
        count = min(count, self.size - offset)
        if count <= 0:
            return b""
        if self._data is not None:
            return self._data[offset:offset + count]
        first, last = offset // CHUNK, (offset + count - 1) // CHUNK
        if first == last:
            base = first * CHUNK
            return self._chunk(first)[offset - base:offset - base + count]
        data = b"".join(self._chunk(i) for i in range(first, last + 1))
        start = offset - first * CHUNK
        return data[start:start + count]

    # -- lines ---------------------------------------------------------------

    def _eol(self, offset: int) -> tuple[int, int]:
        """Where the line holding *offset* ends, and where the next one starts.

        The end is the terminator's offset, or ``LINE_LIMIT`` past the line's
        start, or the end of the file.  Remembered for the last line asked
        about, because a wrapped line asks once per row.
        """
        cached = self._eol_cache
        # At the end itself only when a terminator is there: at a cut, the
        # end of one piece is the start of the next, which has its own end.
        if cached is not None and cached[0] <= offset and (
            offset < cached[1] or (offset == cached[1] and cached[2] > cached[1])
        ):
            return cached[1], cached[2]
        limit = min(self.size, offset + LINE_LIMIT)
        pos = offset
        while pos < limit:
            block = self.read(pos, min(4096, limit - pos))
            if not block:
                break
            match = _EOL.search(block)
            if match is not None:
                eol = pos + match.start()
                follow = self.read(eol, 2)
                nxt = eol + (2 if follow == b"\r\n" else 1)
                self._eol_cache = (offset, eol, nxt)
                return eol, nxt
            pos += len(block)
        self._eol_cache = (offset, limit, limit)
        return limit, limit

    def line(self, offset: int, width: int | None = None, *,
             filter: int = 0, max_cols: int | None = None) -> Line | None:
        """The row that starts at *offset*, or ``None`` past the end.

        With *width* the row is wrapped at that many columns; without, it runs
        to the end of its line, and *max_cols* stops the decoding once that
        many columns are known -- what a screen needs, when the rest would only
        be clipped.
        """
        if offset >= self.size:
            return None
        eol, nxt = self._eol(offset)
        data = self.read(offset, eol - offset)
        cells: list[tuple[str, int]] = []
        stop = decode_cells(data, offset, cells, filter=filter, width=width,
                            max_cols=None if width else max_cols)
        if width and stop < eol:
            # A character wider than the whole row still has to be passed,
            # or the viewer would stand on it forever.
            return Line(tuple(cells), offset, max(stop, offset + 1))
        return Line(tuple(cells), offset, max(nxt, offset + 1))

    def prev_line_start(self, offset: int, width: int | None = None) -> int:
        """Where the row before the one starting at *offset* starts.

        DN's ``ScrollUp``: back past the terminator ending the previous line,
        back again to the one before *that*, and then -- when wrapping -- walk
        forward row by row from the hard line start and keep the last row
        that starts before *offset*.
        """
        if offset <= 0:
            return 0
        offset = min(offset, self.size)
        end = offset
        tail = self.read(end - 2, 2) if end >= 2 else self.read(0, end)
        if tail.endswith(b"\r\n"):
            end -= 2
        elif tail.endswith((b"\n", b"\r")):
            end -= 1
        hard = self._hard_start(end)
        if end > hard:
            # Line up with the pieces a line longer than LINE_LIMIT was cut
            # into coming down.
            hard += (end - 1 - hard) // LINE_LIMIT * LINE_LIMIT
        start = hard
        while True:
            row = self.line(start, width, max_cols=1)
            if row is None or row.next >= offset or row.next <= start:
                return start
            start = row.next

    def _hard_start(self, end: int) -> int:
        """The offset just after the last line break before *end*."""
        lo = max(0, end - BACK_LIMIT)
        pos = end
        while pos > lo:
            begin = max(lo, pos - 4096)
            block = self.read(begin, pos - begin)
            at = max(block.rfind(b"\n"), block.rfind(b"\r"))
            if at >= 0:
                return begin + at + 1
            pos = begin
        return lo

    def line_start(self, offset: int, width: int | None = None) -> int:
        """The start of the row holding the byte at *offset*."""
        offset = max(0, min(offset, self.size))
        if offset == 0:
            return 0
        return self.prev_line_start(offset + 1, width)

    def last_page_top(self, rows: int, width: int | None = None) -> int:
        """The top that puts the last row of the file on the last screen row."""
        top = self.size
        for _ in range(max(1, rows)):
            if top <= 0:
                return 0
            top = self.prev_line_start(top, width)
        return top

    # -- searching -----------------------------------------------------------

    def find(self, pattern: re.Pattern[bytes], start: int, *, backward: bool = False,
             span: int = 64, job: SearchJob | None = None) -> tuple[int, int] | None:
        """The first match at or after *start*, or the last one before it.

        *span* is the longest a match can be, which is how far consecutive
        windows overlap so that none is missed across a boundary.  A byte
        before each window is read too, for a whole-word lookbehind to see.

        *job*, when given, is told where the search has got to after every
        window and asked whether to stop -- ``SearchFileStr``'s gauge and
        its ``CancelSearch``.  A stopped search answers ``None``, and the job
        says it was stopped.
        """
        # Its own descriptor and no cache: this runs on a thread while the
        # loop goes on painting through the shared one.
        if self._data is not None:
            data_all = self._data

            def read(offset: int, count: int) -> bytes:
                offset = max(0, offset)
                return data_all[offset:offset + count]
        else:
            fd = os.open(self.path, os.O_RDONLY)

            def read(offset: int, count: int) -> bytes:
                offset = max(0, offset)
                return os.pread(fd, max(0, min(count, self.size - offset)), offset)
        try:
            return self._find(read, pattern, start, backward, span, job or SearchJob())
        finally:
            if self._data is None:
                os.close(fd)

    def _find(self, read, pattern, start, backward, span, job):
        window = SEARCH_WINDOW
        if not backward:
            pos = max(0, start)
            while pos < self.size:
                job.position = pos
                if job.stopped:
                    return None
                lead = 1 if pos > 0 else 0
                data = read(pos - lead, window + span + lead)
                match = pattern.search(data, lead)
                if match is not None and match.start() - lead < window:
                    return pos - lead + match.start(), match.end() - match.start()
                pos += window
            return None
        pos = min(start, self.size)
        while pos > 0:
            job.position = pos
            if job.stopped:
                return None
            lo = max(0, pos - window)
            lead = 1 if lo > 0 else 0
            data = read(lo - lead, pos - lo + span + lead)
            found = None
            for match in pattern.finditer(data, lead):
                if lo - lead + match.start() >= pos:
                    break
                found = match
            if found is not None:
                return lo - lead + found.start(), found.end() - found.start()
            pos = lo
        return None


class SearchJob:
    """A running search, as the loop and the thread doing it both see it.

    The thread writes ``position`` and reads ``stopped``; the loop does the
    reverse.  An int assignment and an ``Event`` are all that cross, so there
    is nothing to lock -- and nothing reactive, which is the loop's alone.
    """

    def __init__(self) -> None:
        self.position = 0
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()


def decode_cells(data: bytes, base: int, cells: list[tuple[str, int]], *,
                 filter: int = 0, width: int | None = None,
                 max_cols: int | None = None) -> int:
    """Append the columns *data* paints to *cells*; return the offset reached.

    *base* is the offset of ``data[0]`` in the file.  Decoding stops early --
    and the offset returned says where -- when the next character would not
    fit in *width* columns, or once *max_cols* columns are known.
    """
    i, n = 0, len(data)
    while i < n:
        col = len(cells)
        if max_cols is not None and col >= max_cols:
            break
        byte = data[i]
        if byte < 0x80:
            if byte == 0x09:
                count = TAB - col % TAB
                if width is not None:
                    count = min(count, max(1, width - col))
                    if col >= width:
                        break
                cells.extend((" ", base + i) for _ in range(count))
            else:
                char = cp437(byte) if byte < 0x20 or byte == 0x7F else chr(byte)
                if filter and (byte < 0x20 or byte == 0x7F):
                    char = FILTERED
                if width is not None and col + 1 > width:
                    break
                cells.append((char, base + i))
            i += 1
            continue
        length = 2 if byte >= 0xC0 else 1
        if byte >= 0xE0:
            length = 3
        if byte >= 0xF0:
            length = 4
        char = None
        if length > 1:
            try:
                char = data[i:i + length].decode("utf-8")
            except UnicodeDecodeError:
                char = None
        if char is None:
            # Not UTF-8: the byte on its own, as DN's font drew it.
            length = 1
            char = FILTERED if filter == 1 else cp437(byte)
            cols = 1
        else:
            cols = char_width(char)
            if filter == 1:
                char, cols = FILTERED, 1
            elif cols == 0:
                if _is_combining(char):
                    # No column of its own, and navkit paints one
                    # character per cell: the accent is dropped rather than
                    # given a column it never had.
                    i += length
                    continue
                char, cols = FILTERED, 1
        if width is not None and col + cols > width:
            break
        cells.append((char, base + i))
        if cols == 2:
            cells.append(("", base + i))
        i += length
    return base + i


def _is_combining(char: str) -> bool:
    return unicodedata.combining(char) != 0 or unicodedata.category(char) in ("Mn", "Me", "Cf")


# -- hex and dump ------------------------------------------------------------


def hex_row_bytes(width: int) -> int:
    """Bytes per row in hex mode: DN's ``HexPos := (Size.X-12) div 4``."""
    return max(1, (width - 12) // 4)


def dump_row_bytes(width: int) -> int:
    """Bytes per row in dump mode: ``((Size.X-9) div 16)*16``, and 16 at least."""
    return max(16, (width - 9) // 16 * 16)


def hex_char(byte: int, filter: int) -> str:
    """The character column of a hex row: ``DumpStr``'s rules."""
    if byte == 0:
        return "."
    if filter and (byte < 0x20 or (filter == 1 and byte >= 0x80)):
        return FILTERED
    return cp437(byte)


def dump_char(byte: int, filter: int) -> str:
    """A dump row's character: ``XDumpStr``, which leaves 0 to the font."""
    if filter and (byte < 0x20 or (filter == 1 and byte >= 0x80)):
        return FILTERED
    return cp437(byte)


def hex_row(data: bytes, address: int, per_row: int, filter: int) -> str:
    """``AAAAAAAA: 4F 5A ... │ OZ...`` -- ``DumpStr``, padded to a full row."""
    pairs = "".join(f"{b:02X} " for b in data).ljust(per_row * 3)
    chars = "".join(hex_char(b, filter) for b in data)
    return f"{address & 0xFFFFFFFF:08X}: {pairs}│ {chars}"


def dump_row(data: bytes, address: int, filter: int) -> str:
    """``AAAAAAAA text...`` -- ``XDumpStr``."""
    return f"{address & 0xFFFFFFFF:08X} " + "".join(dump_char(b, filter) for b in data)


#: Where the hex pairs of a row begin, and where its characters begin.
HEX_PAIRS_AT = 10


def hex_chars_at(per_row: int) -> int:
    return HEX_PAIRS_AT + per_row * 3 + 2


DUMP_CHARS_AT = 9


# -- the search pattern --------------------------------------------------------

#: What is not part of a word, for *Whole words*: every byte that is not an
#: ASCII letter, digit or underscore, and not part of a UTF-8 sequence.
_WORD = rb"0-9A-Za-z_\x80-\xff"


def compile_search(text: str, *, case: bool = False, words: bool = False
                   ) -> tuple[re.Pattern[bytes], int]:
    """A bytes pattern finding *text* in UTF-8, and the longest match it can make.

    Each character becomes the alternation of its case variants' encodings, so
    *Case sensitive* off finds ``Ä`` for ``ä`` too -- which ``re.IGNORECASE``
    on bytes would not, knowing only ASCII.
    """
    parts: list[bytes] = []
    span = 0
    for char in text:
        variants = {char}
        if not case:
            variants |= {v for v in (char.lower(), char.upper(), char.casefold()) if len(v) == 1}
        encoded = sorted({v.encode("utf-8") for v in variants})
        span += max(len(e) for e in encoded)
        if len(encoded) == 1:
            parts.append(re.escape(encoded[0]))
        else:
            parts.append(b"(?:" + b"|".join(re.escape(e) for e in encoded) + b")")
    body = b"".join(parts)
    if words:
        body = rb"(?<![" + _WORD + rb"])" + body + rb"(?![" + _WORD + rb"])"
    return re.compile(body, re.DOTALL), max(1, span)


def group_digits(number: int) -> str:
    """``12,345``: DN's ``FStr``."""
    return f"{number:,}"


# -- the last search -----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ViewSearch:
    """What the *Find* dialog asked for: DN's ``TViewSearch`` record."""

    what: str
    case: bool = False
    words: bool = False
    backward: bool = False

    def compile(self) -> tuple[re.Pattern[bytes], int]:
        return compile_search(self.what, case=self.case, words=self.words)


#: The last search, shared by every viewer as DN's ``SearchString`` was, so
#: Shift+F7 in a new viewer finds what F7 asked for in the last one.
last_search: ViewSearch | None = None
