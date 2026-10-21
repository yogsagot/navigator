"""The rows a rendered document is painted from: what the viewer's Markdown
and HTML readings (:mod:`.markdown`, :mod:`.html`) have in common.

A reader walks its document and calls a :class:`Builder`'s block methods --
a heading, a paragraph, a code block, a table, a rule -- and pushes and pops
the containers rows are inside (a quote's gutter, a list item's bullet).  The
builder wraps, prefixes and draws, and hands back a :class:`Layout`.

**Rows are not byte ranges**, which text mode's are: a row carries ``src``,
the byte offset of the source line its block starts on (a code or table row,
of its own line), and ``block``, which block it belongs to.  That is what the
viewer keeps ``top`` at, so the scroll bar, the view history and switching back
to the source still have an offset to go by.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from typing import Any

from navkit.screen import char_width

from navigator.lib import highlight

#: The most a file may hold to be rendered: it is read and parsed whole,
#: where text mode reads only the rows it shows.
RENDER_LIMIT = 4 * 1024 * 1024

#: Columns a code block is indented by, and a tab's stops inside one.
CODE_INDENT = 2
TAB_SIZE = 8

#: A cell: its character ("" for the second column of a wide one), its
#: classes, and the URL it links to.
Cell = tuple[str, tuple[str, ...], "str | None"]

#: A blank, of no class.
BLANK: Cell = (" ", (), None)


@dataclass(frozen=True, slots=True)
class Glyphs:
    """What rules, bullets, quotes and tables are drawn with."""

    bullet: str
    rule: str
    h1: str
    h2: str
    quote: str
    todo: str
    done: str
    #: A table's frame: across, down, the four corners, the four tees and the cross.
    box: str


UNICODE = Glyphs("•", "─", "═", "─", "│", "☐", "☒", "─│┌┐└┘├┤┬┴┼")
ASCII = Glyphs("*", "-", "=", "-", "|", "[ ]", "[x]", "-|+++++++++")


@dataclass(slots=True)
class Row:
    cells: list[Cell]
    #: The byte offset of the source line the row's block (or line) starts on.
    src: int
    #: Which block the row belongs to: a search hit is looked for among one
    #: block's rows.
    block: int

    @property
    def text(self) -> str:
        return "".join(char for char, _, _ in self.cells)


@dataclass(slots=True, eq=False)
class Layout:
    rows: list[Row] = field(default_factory=list)
    width: int = 0
    #: Each row's ``src``, for ``bisect``; made on the first look.
    _srcs: list[int] = field(default_factory=list, repr=False)

    def row_for(self, offset: int) -> int:
        """The first row of the block holding byte *offset*: the last row whose
        ``src`` is at or before it, taken back to its block's first."""
        if len(self._srcs) != len(self.rows):
            self._srcs = [row.src for row in self.rows]
        index = max(0, bisect.bisect_right(self._srcs, offset) - 1)
        while index > 0 and self.rows[index - 1].block == self.rows[index].block \
                and self.rows[index - 1].src == self.rows[index].src:
            index -= 1
        return index

    def block_rows(self, index: int) -> range:
        """The rows of the block row *index* is in."""
        if not self.rows:
            return range(0)
        block = self.rows[index].block
        start = index
        while start > 0 and self.rows[start - 1].block == block:
            start -= 1
        end = index + 1
        while end < len(self.rows) and self.rows[end].block == block:
            end += 1
        return range(start, end)


def _cells(text: str, classes: tuple[str, ...] = (), link: str | None = None) -> list[Cell]:
    """*text* as cells, a wide character taking two, a control none."""
    cells: list[Cell] = []
    for char in text:
        width = char_width(char)
        if width == 0:
            if cells and ord(char) >= 0x20 and cells[-1][0]:
                # A combining mark joins the character before it.
                base, look, url = cells[-1]
                cells[-1] = (base + char, look, url)
            continue
        cells.append((char, classes, link))
        if width == 2:
            cells.append(("", classes, link))
    return cells


def _wrap(cells: list[Cell], width: int) -> list[list[Cell]]:
    """*cells* broken into lines of at most *width* columns: at blanks, at a
    ``"\\n"`` cell (a hard break), and through a word longer than a line."""
    width = max(1, width)
    lines: list[list[Cell]] = []
    line: list[Cell] = []
    space: Cell | None = None
    word: list[Cell] = []

    def put_word() -> None:
        nonlocal line, space, word
        if not word:
            return
        gap = 1 if line and space is not None else 0
        if line and len(line) + gap + len(word) > width:
            lines.append(line)
            line, gap = [], 0
        if gap:
            line.append(space)
        while len(line) + len(word) > width:
            # Longer than a line: cut, never through a wide character.
            room = width - len(line)
            if room < len(word) and room > 0 and word[room][0] == "":
                room -= 1
            if room <= 0:
                lines.append(line)
                line = []
                continue
            line.extend(word[:room])
            word = word[room:]
            lines.append(line)
            line = []
        line.extend(word)
        word, space = [], None

    for cell in cells:
        char = cell[0]
        if char == "\n":
            put_word()
            lines.append(line)
            line, space = [], None
        elif char == " ":
            put_word()
            if line and space is None:
                space = cell
        else:
            word.append(cell)
    put_word()
    if line or not lines:
        lines.append(line)
    return lines


class Builder:
    """Rows made block by block, inside the containers pushed."""

    def __init__(self, line_starts: list[int], width: int, glyphs: Glyphs) -> None:
        self.line_starts = line_starts
        self.width = max(1, width)
        self.glyphs = glyphs
        self.layout = Layout(width=self.width)
        #: The containers the next row is inside: each a quote's gutter or a
        #: list item's bullet, ``[first, rest, used]``.
        self.prefixes: list[list[Any]] = []
        #: Classes every cell inside the current containers carries (a quote's).
        self.inside: list[tuple[str, ...]] = []
        self.block = 0
        #: Whether the next block is set off by a blank row.
        self.gap = False
        self.last_src = 0

    # -- offsets --------------------------------------------------------------

    def line_src(self, number: int) -> int:
        """The byte offset of source line *number*, from 0."""
        return self.line_starts[max(0, min(number, len(self.line_starts) - 1))]

    # -- emitting -------------------------------------------------------------

    def room(self) -> int:
        return max(1, self.width - sum(len(entry[1]) for entry in self.prefixes))

    def emit(self, cells: list[Cell], src: int) -> None:
        prefix: list[Cell] = []
        for entry in self.prefixes:
            prefix.extend(entry[1] if entry[2] else entry[0])
            entry[2] = True
        self.layout.rows.append(Row(prefix + cells, src, self.block))
        self.last_src = src

    def open_block(self) -> None:
        """A blank row before a block, unless it is the first or ``gap`` is off."""
        if self.gap and self.layout.rows:
            prefix: list[Cell] = []
            for entry in self.prefixes:
                prefix.extend(entry[1] if entry[2] else [BLANK] * len(entry[1]))
            while prefix and prefix[-1][0] == " ":
                prefix.pop()
            self.layout.rows.append(Row(prefix, self.last_src, self.block))
        self.gap = True
        self.block += 1

    def classes(self, *own: str) -> tuple[str, ...]:
        outer = tuple(name for group in self.inside for name in group)
        return outer + own

    def push(self, first: list[Cell], rest: list[Cell] | None = None,
             inside: tuple[str, ...] = ()) -> None:
        """A container: *first* before its first row, *rest* (blanks as wide,
        by default) before every other, *inside* on every cell within."""
        if rest is None:
            rest = [BLANK] * len(first)
        self.prefixes.append([first, rest, False])
        self.inside.append(inside)

    def pop(self) -> None:
        if self.prefixes:
            self.prefixes.pop()
            self.inside.pop()

    def quote(self) -> None:
        """A quote's gutter pushed: every row inside starts ``│ ``."""
        self.open_block()
        self.gap = False
        gutter = _cells(self.glyphs.quote + " ", ("quote",))
        self.push(gutter, gutter, ("quote",))

    def finish(self) -> Layout:
        while self.layout.rows and not self.layout.rows[-1].cells:
            self.layout.rows.pop()
        return self.layout

    # -- blocks ---------------------------------------------------------------

    def heading(self, level: int, cells: list[Cell], src: int) -> None:
        """*cells* (classed ``heading h<level>`` by the caller), wrapped; the
        first two levels underlined."""
        self.open_block()
        lines = _wrap(cells, self.room())
        for line in lines:
            self.emit(line, src)
        under = {1: self.glyphs.h1, 2: self.glyphs.h2}.get(level)
        if under:
            span = max((len(line) for line in lines), default=0)
            self.emit(_cells(under * span, self.classes("heading", f"h{level}", "underline")), src)

    def paragraph(self, cells: list[Cell], src: int, *, tight: bool = False) -> None:
        """*cells* wrapped to the room there is.  *tight*, a tight list item's
        text: no blank row before it when the item has just begun."""
        if tight and not self.gap:
            self.block += 1
            self.gap = True
        else:
            self.open_block()
        for line in _wrap(cells, self.room()):
            self.emit(line, src)

    def rule(self, src: int) -> None:
        self.open_block()
        self.emit(_cells(self.glyphs.rule * self.room(), self.classes("rule")), src)

    def code(self, lines: list[str], language: str, srcs: list[int]) -> None:
        """A code block: indented, never wrapped, coloured as *language* (a
        Pygments name, "" for none), each line at its own source offset."""
        self.open_block()
        lines = [line.expandtabs(TAB_SIZE) for line in lines]
        spans = highlight.lex_text(language, lines) if language else [[] for _ in lines]
        base = self.classes("code", "block")
        room = self.room()
        indent = [(" ", base, None)] * CODE_INDENT
        for number, line in enumerate(lines):
            cells: list[Cell] = []
            for position, char in enumerate(line):
                classes = base
                for start, end, token_classes in spans[number] if number < len(spans) else ():
                    if start <= position < end:
                        classes = base + ("token",) + token_classes
                        break
                cells.extend(_cells(char, classes))
            row = indent + cells
            row.extend([(" ", base, None)] * max(0, room - len(row)))
            self.emit(row, srcs[number] if number < len(srcs) else self.last_src)

    def table(self, rows: list[tuple[int, bool, list[list[Cell]]]], aligns: list[str]) -> None:
        """*rows* -- each ``(src, is_head, cells)`` -- drawn in box characters
        at the widths that fit, the widest column shrunk first."""
        columns = max((len(cells) for _, _, cells in rows), default=0)
        if columns == 0:
            return
        self.open_block()
        aligns = list(aligns) + ["left"] * (columns - len(aligns))
        widths = [1] * columns
        for _, _, cells in rows:
            for column, cell in enumerate(cells):
                widths[column] = max(widths[column], len(cell))
        # Each column is a blank either side and a line after: shrink the
        # widest until the table fits.
        fit = self.room() - 1 - 3 * columns
        while sum(widths) > max(fit, columns) and max(widths) > 1:
            widest = widths.index(max(widths))
            widths[widest] -= 1
        box = self.glyphs.box
        across, down = box[0], box[1]
        frame = self.classes("table")

        def line(left: str, middle: str, right: str) -> list[Cell]:
            text = left + middle.join(across * (width + 2) for width in widths) + right
            return _cells(text, frame)

        self.emit(line(box[2], box[8], box[3]), rows[0][0])
        for number, (src, is_head, cells) in enumerate(rows):
            cells = cells + [[] for _ in range(columns - len(cells))]
            wrapped = [_wrap(cell, widths[column]) for column, cell in enumerate(cells)]
            height = max(len(pieces) for pieces in wrapped)
            for y in range(height):
                out = _cells(down, frame)
                for column, pieces in enumerate(wrapped):
                    piece = pieces[y] if y < len(pieces) else []
                    spare = widths[column] - len(piece)
                    fill = (" ", frame + (("th",) if is_head else ()), None)
                    left = {"right": spare, "center": spare // 2}.get(aligns[column], 0)
                    out.append(fill)
                    out.extend([fill] * left + piece + [fill] * (spare - left))
                    out.append(fill)
                    out.extend(_cells(down, frame))
                self.emit(out, src)
            if is_head and (number + 1 < len(rows) and not rows[number + 1][1]):
                self.emit(line(box[6], box[10], box[7]), rows[number + 1][0])
        self.emit(line(box[4], box[9], box[5]), rows[-1][0])


def line_starts(data: bytes) -> list[int]:
    """The byte offset of every line of *data*."""
    starts = [0]
    find = data.find
    at = find(b"\n")
    while at >= 0:
        starts.append(at + 1)
        at = find(b"\n", at + 1)
    return starts


def decode(data: bytes, codec: str = "utf-8") -> str:
    """*data* as text, as the viewer reads it: an undecodable byte in UTF-8
    replaced, a one-byte code page's every byte a character."""
    return data.decode(codec, errors="replace")
