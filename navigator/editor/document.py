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

import os
import re
import stat
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from navigator.job import Stopped
from navigator.memory import NotEnoughMemory

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
    call -- a CR or LF byte is never part of a UTF-8 sequence, so a run of
    whole lines decodes as its lines would one by one -- and what follows the
    break waits for the next chunk.  **A CR at a chunk's very end waits too**,
    since the LF that would make it one CRLF may be the next chunk's first
    byte: DN's ``ReadBlock`` stepped its file back one byte for the same CR.
    """

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.endings: list[str] = []
        self.counts: Counter[str] = Counter()
        #: Bytes after the last break taken, not yet decoded.
        self._pending: list[bytes] = []
        self._pending_size = 0
        #: What the decoded characters take, as CPython stores them.
        self._chars = 0

    def feed(self, chunk: bytes) -> None:
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
        text = decode(head)
        lines, endings = _split(text)
        lines.pop()  # the "" after the break the head ends with
        self._take(text, lines, endings)

    def finish(self) -> Document:
        """The document, with whatever followed the last break as its last line."""
        text = decode(b"".join(self._pending))
        self._pending, self._pending_size = [], 0
        lines, endings = _split(text)
        self._take(text, lines, endings)
        self.endings.append("")
        return Document(self.lines, self.endings, _newline(self.counts))

    def _take(self, text: str, lines: list[str], endings: list[str]) -> None:
        self.lines.extend(lines)
        self.endings.extend(endings)
        self.counts.update(endings)
        # Latin-1 text is a byte a character in CPython; anything else two or
        # more -- and an undecodable byte, kept as a surrogate, is two.
        self._chars += len(text) * (1 if text.isascii() else 2)

    @property
    def estimate(self) -> int:
        """Roughly what the text read so far takes in memory, in bytes."""
        return (self._chars + self._pending_size + _LINE_COST * len(self.lines)
                + _CRLF_COST * self.counts.get("\r\n", 0))


def encode_lines(lines: list[str], endings: list[str], job: Any = None, *,
                 step: int = 65536):
    """*lines* and their *endings* as bytes, *step* lines to a chunk: a save's.

    A *job* sees ``position`` as the lines done so far.  Each chunk is joined
    and encoded in one call, so a thread writing it hardly holds the loop up.
    """
    for start in range(0, len(lines), step):
        stop = start + step
        parts = [part for pair in zip(lines[start:stop], endings[start:stop]) for part in pair]
        yield encode("".join(parts))
        if job is not None:
            job.position = min(stop, len(lines))


def read_text(path: Path | str, job: Any = None, *, chunk: int = READ_CHUNK,
              budget: int | None = None) -> str:
    """*path*'s text as one string, line breaks and all: ^K R's block.

    Read as :func:`read_document` reads, a chunk at a time.
    """
    document = read_document(path, job, chunk=chunk, budget=budget)
    return "".join(line + ending for line, ending in zip(document.lines, document.endings))


def read_document(path: Path | str, job: Any = None, *, chunk: int = READ_CHUNK,
                  budget: int | None = None) -> Document:
    """Read *path* a chunk at a time, for a thread to do while the loop paints.

    Raises ``OSError`` for anything that is not a regular file -- looked at
    before it is opened, so a FIFO cannot hang the reader on ``open``.  A
    *job* sees ``total`` and ``position`` as bytes and stops the read by
    ``stop()``, which raises :class:`~navigator.job.Stopped`.

    With a *budget* in bytes, raises :class:`~navigator.memory.NotEnoughMemory`
    rather than go past it, as DN's ``ReadBlock`` checked ``MemAvail``: at
    once, for a file larger than the budget; after each chunk, for a text
    whose lines so far say the whole will not fit; and for what was read, for
    a file whose size said nothing (``/proc``) or whose tail is denser.
    """
    info = os.stat(path)
    if not stat.S_ISREG(info.st_mode):
        raise OSError(21 if stat.S_ISDIR(info.st_mode) else 22,
                      "Not a regular file", str(path))
    size = info.st_size
    if budget is not None and size > budget:
        raise NotEnoughMemory(str(path))
    if job is not None:
        job.total = size
        job.position = 0
    reader = LineReader()
    done = 0
    with open(path, "rb", buffering=0) as file:
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
    """Lines of text, their terminators, and the terminator new lines take."""

    lines: list[str] = field(default_factory=lambda: [""])
    endings: list[str] = field(default_factory=lambda: [""])
    newline: str = DEFAULT_NEWLINE

    @classmethod
    def from_bytes(cls, data: bytes) -> Document:
        lines, endings = _split(decode(data))
        counts = Counter(endings)
        endings.append("")
        return cls(lines, endings, _newline(counts))

    @classmethod
    def load(cls, path: Path | str) -> Document:
        """Read *path*.  Raises ``OSError`` for anything that is not a regular file.

        A file that does not exist is not an error here: the caller decides
        whether an editor may start one.
        """
        return read_document(path)

    def encode(self) -> bytes:
        """The bytes this document is: exactly what it was read from, if unedited."""
        return b"".join(encode(line) + ending.encode("ascii")
                        for line, ending in zip(self.lines, self.endings))

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
        self.lines[start.line:end.line + 1] = [joined]
        self.endings[start.line:end.line + 1] = [ending]
        return removed
