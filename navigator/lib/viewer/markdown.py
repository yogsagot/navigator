"""The viewer's *Markdown* reading of a file: a departure, DN's viewer had none.

``render`` parses a whole document with markdown-it-py (CommonMark, with GFM's
tables and strikethrough) and lays it out for a width: headings, paragraphs
joined and wrapped, lists, quotes, tables drawn in box characters, rules, and
code blocks coloured by :mod:`navigator.lib.highlight`.  The markup itself is
not shown.

**Rows are not byte ranges**, which text mode's are: a row carries ``src``,
the byte offset of the source line its block starts on (a code or table row,
of its own line), and ``block``, which block it belongs to.  That is what the
viewer keeps ``top`` at, so the scroll bar, the view history and switching back
to the source still have an offset to go by.

Nothing here knows of widgets or threads: the viewer reads the file and calls
:func:`render` on its own thread.  markdown-it-py is the optional
``navigator-fm[markdown]`` extra; :func:`available` says whether it is there.
"""

from __future__ import annotations

import bisect
import functools
import importlib.util
import re
from dataclasses import dataclass, field
from typing import Any

from navkit.screen import char_width

from navigator.lib import highlight

#: The extra that brings markdown-it-py.
EXTRA = "navigator-fm[markdown]"

#: The most a file may hold to be rendered: it is read and parsed whole,
#: where text mode reads only the rows it shows.
MARKDOWN_LIMIT = 4 * 1024 * 1024

#: Columns a code block is indented by, and a tab's stops inside one.
CODE_INDENT = 2
TAB_SIZE = 8

#: A cell: its character ("" for the second column of a wide one), its
#: classes, and the URL it links to.
Cell = tuple[str, tuple[str, ...], "str | None"]

_TASK = re.compile(r"\[([ xX])\] ")


@functools.cache
def available() -> bool:
    """Whether markdown-it-py can be imported."""
    return importlib.util.find_spec("markdown_it") is not None


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


def _width(cells: list[Cell]) -> int:
    return len(cells)


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


class _Renderer:
    def __init__(self, tokens: list[Any], line_starts: list[int], width: int, glyphs: Glyphs) -> None:
        self.tokens = tokens
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
        self.gap = False
        #: Each list open: whether it is tight, an ordered one's next number,
        #: its delimiter, and whether no item has been seen yet.
        self.lists: list[list[Any]] = []

    # -- offsets --------------------------------------------------------------

    def src(self, token: Any, line: int = 0) -> int:
        if token.map is None:
            return self.last_src
        number = min(token.map[0] + line, len(self.line_starts) - 1)
        return self.line_starts[number]

    last_src = 0

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
        """A blank row before a block, unless it is the first, or follows a
        tight list item's start."""
        if self.gap and self.layout.rows:
            prefix: list[Cell] = []
            for entry in self.prefixes:
                prefix.extend(entry[1] if entry[2] else [(" ", (), None)] * len(entry[1]))
            while prefix and prefix[-1][0] == " ":
                prefix.pop()
            self.layout.rows.append(Row(prefix, self.last_src, self.block))
        self.gap = True
        self.block += 1

    def classes(self, *own: str) -> tuple[str, ...]:
        outer = tuple(name for group in self.inside for name in group)
        return outer + own

    # -- inline ---------------------------------------------------------------

    def inline(self, token: Any, base: tuple[str, ...] = ()) -> list[Cell]:
        cells: list[Cell] = []
        styles: list[str] = []
        links: list[str | None] = []
        for child in token.children or ():
            kind = child.type
            classes = self.classes(*base, *styles)
            link = links[-1] if links else None
            if kind == "text":
                cells.extend(_cells(child.content.replace("\t", " "), classes, link))
            elif kind == "softbreak":
                cells.append((" ", classes, link))
            elif kind == "hardbreak":
                cells.append(("\n", classes, link))
            elif kind == "code_inline":
                cells.extend(_cells(child.content, classes + ("code",), link))
            elif kind in ("strong_open", "em_open", "s_open"):
                styles.append({"strong_open": "strong", "em_open": "emph", "s_open": "strike"}[kind])
            elif kind in ("strong_close", "em_close", "s_close"):
                if styles:
                    styles.pop()
            elif kind == "link_open":
                links.append(child.attrs.get("href") or None)
                styles.append("link")
            elif kind == "link_close":
                if links:
                    links.pop()
                if styles:
                    styles.pop()
            elif kind == "image":
                alt = child.content or "".join(c.content for c in child.children or ())
                cells.extend(_cells(f"[{alt}]" if alt else "[image]", classes + ("image",),
                                    child.attrs.get("src") or link))
            elif kind == "html_inline":
                cells.extend(_cells(child.content, classes + ("html",), link))
            else:
                cells.extend(_cells(child.content, classes, link))
        return cells

    # -- blocks ---------------------------------------------------------------

    def run(self) -> Layout:
        index = 0
        tokens = self.tokens
        while index < len(tokens):
            index = self.step(index)
        while self.layout.rows and not self.layout.rows[-1].cells:
            self.layout.rows.pop()
        return self.layout

    def step(self, index: int) -> int:
        token = self.tokens[index]
        kind = token.type
        if kind == "heading_open":
            self.heading(token, self.tokens[index + 1])
            return index + 3
        if kind == "paragraph_open":
            self.paragraph(token, self.tokens[index + 1])
            return index + 3
        if kind in ("bullet_list_open", "ordered_list_open"):
            start = int(token.attrs.get("start", 1) or 1) if kind == "ordered_list_open" else None
            if self.lists and self.lists[-1][0]:
                # Straight under a tight item's text: no blank row between.
                self.gap = False
            self.lists.append([self._tight(index), start, token.markup, True])
            return index + 1
        if kind in ("bullet_list_close", "ordered_list_close"):
            self.lists.pop()
            self.gap = True
            return index + 1
        if kind == "list_item_open":
            self.list_item(index)
            return index + 1
        if kind == "list_item_close":
            self.prefixes.pop()
            self.inside.pop()
            return index + 1
        if kind == "blockquote_open":
            self.open_block()
            self.gap = False
            gutter = _cells(self.glyphs.quote + " ", ("quote",))
            self.prefixes.append([gutter, gutter, False])
            self.inside.append(("quote",))
            return index + 1
        if kind == "blockquote_close":
            self.prefixes.pop()
            self.inside.pop()
            self.gap = True
            return index + 1
        if kind in ("fence", "code_block"):
            self.code(token)
            return index + 1
        if kind == "hr":
            self.open_block()
            self.emit(_cells(self.glyphs.rule * self.room(), self.classes("rule")), self.src(token))
            return index + 1
        if kind == "html_block":
            content = token.content.strip()
            if content.startswith("<!--") and content.endswith("-->"):
                return index + 1  # a comment, which no renderer shows
            self.open_block()
            lines = token.content.rstrip("\n").split("\n")
            for number, line in enumerate(lines):
                for piece in _wrap(_cells(line.replace("\t", " "), self.classes("html")), self.room()):
                    self.emit(piece, self.src(token, number))
            return index + 1
        if kind == "table_open":
            return self.table(index)
        return index + 1

    def _tight(self, index: int) -> bool:
        """Whether the list opening at *index* is tight: its paragraphs hidden."""
        depth = 0
        for token in self.tokens[index:]:
            depth += token.nesting
            if token.type == "paragraph_open" and depth == 3:
                return token.hidden
            if depth == 0:
                break
        return True

    def heading(self, token: Any, inline: Any) -> None:
        self.open_block()
        level = token.tag
        cells = self.inline(inline, ("heading", level))
        src = self.src(token)
        lines = _wrap(cells, self.room())
        for line in lines:
            self.emit(line, src)
        under = {"h1": self.glyphs.h1, "h2": self.glyphs.h2}.get(level)
        if under:
            span = max((len(line) for line in lines), default=0)
            self.emit(_cells(under * span, self.classes("heading", level, "underline")), src)

    def paragraph(self, token: Any, inline: Any) -> None:
        if token.hidden and not self.gap:
            # A tight list item's, straight after the item before.
            self.block += 1
            self.gap = True
        else:
            self.open_block()
        cells = self.inline(inline)
        src = self.src(token)
        for line in _wrap(cells, self.room()):
            self.emit(line, src)

    def list_item(self, index: int) -> None:
        token = self.tokens[index]
        tight, number, markup, first_item = self.lists[-1]
        self.lists[-1][3] = False
        if number is not None:
            mark = f"{number}{markup or '.'} "
            self.lists[-1][1] = number + 1
        else:
            mark = self.glyphs.bullet + " "
            inline = self.tokens[index + 2] if index + 2 < len(self.tokens) else None
            if inline is not None and inline.type == "inline" and inline.children:
                first = inline.children[0]
                found = _TASK.match(first.content) if first.type == "text" else None
                if found:
                    first.content = first.content[found.end():]
                    mark = (self.glyphs.todo if found.group(1) == " " else self.glyphs.done) + " "
        if not first_item:
            # Between items: a blank row in a loose list, none in a tight one.
            self.gap = not tight
        first = _cells(mark, self.classes("bullet"))
        self.prefixes.append([first, [(" ", (), None)] * len(first), False])
        self.inside.append(())

    def code(self, token: Any) -> None:
        self.open_block()
        content = token.content
        if content.endswith("\n"):
            content = content[:-1]
        lines = [line.expandtabs(TAB_SIZE) for line in content.split("\n")]
        language = (token.info or "").strip().split(maxsplit=1)[0].lower() if token.info else ""
        spans = highlight.lex_text(language, lines) if language else [[] for _ in lines]
        base = self.classes("code", "block")
        room = self.room()
        # Inside the fence: a fenced block's first line is the one after it.
        skip = 1 if token.type == "fence" else 0
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
            self.emit(row, self.src(token, number + skip))

    def table(self, index: int) -> int:
        """A GFM table: its cells gathered, then drawn at the widths that fit."""
        self.open_block()
        rows: list[tuple[int, bool, list[list[Cell]]]] = []
        aligns: list[str] = []
        head = False
        tokens = self.tokens
        while index < len(tokens) and tokens[index].type != "table_close":
            token = tokens[index]
            if token.type == "thead_open":
                head = True
            elif token.type == "thead_close":
                head = False
            elif token.type == "tr_open":
                rows.append((self.src(token), head, []))
            elif token.type in ("th_open", "td_open"):
                style = token.attrs.get("style") or ""
                align = style.split(":", 1)[1] if ":" in style else "left"
                if len(rows[-1][2]) >= len(aligns):
                    aligns.append(align)
            elif token.type == "inline" and rows:
                rows[-1][2].append(self.inline(token, ("th",) if rows[-1][1] else ()))
            index += 1
        columns = max((len(cells) for _, _, cells in rows), default=0)
        if columns == 0:
            return index + 1
        aligns += ["left"] * (columns - len(aligns))
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

        top_src = rows[0][0]
        self.emit(line(box[2], box[8], box[3]), top_src)
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
        return index + 1


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


def render(data: bytes, width: int, *, codec: str = "utf-8", unicode: bool = True) -> Layout:
    """*data*, a Markdown document in *codec*, laid out *width* columns wide;
    *unicode* draws with box characters and bullets, else with ASCII."""
    from markdown_it import MarkdownIt

    parser = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    text = decode(data, codec).replace("\r\n", "\n").replace("\r", "\n")
    tokens = parser.parse(text)
    return _Renderer(tokens, line_starts(data), width, UNICODE if unicode else ASCII).run()
