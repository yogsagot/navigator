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

#: A line break, longest first so CRLF is one break and not two.
BREAK = re.compile(r"\r\n|\r|\n")
_BREAK_BYTES = re.compile(rb"\r\n|\r|\n")

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


@dataclass
class Document:
    """Lines of text, their terminators, and the terminator new lines take."""

    lines: list[str] = field(default_factory=lambda: [""])
    endings: list[str] = field(default_factory=lambda: [""])
    newline: str = DEFAULT_NEWLINE

    @classmethod
    def from_bytes(cls, data: bytes) -> Document:
        lines, endings, start = [], [], 0
        for match in _BREAK_BYTES.finditer(data):
            lines.append(decode(data[start:match.start()]))
            endings.append(match.group().decode("ascii"))
            start = match.end()
        lines.append(decode(data[start:]))
        endings.append("")
        counts = Counter(e for e in endings if e)
        newline = counts.most_common(1)[0][0] if counts else DEFAULT_NEWLINE
        return cls(lines, endings, newline)

    @classmethod
    def load(cls, path: Path | str) -> Document:
        """Read *path*.  Raises ``OSError`` for anything that is not a regular file.

        A file that does not exist is not an error here: the caller decides
        whether an editor may start one.
        """
        info = os.stat(path)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(21 if stat.S_ISDIR(info.st_mode) else 22,
                          "Not a regular file", str(path))
        with open(path, "rb") as file:
            return cls.from_bytes(file.read())

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
