"""The viewer's *Markdown* reading of a file: a departure, DN's viewer had none.

``render`` parses a whole document with markdown-it-py (CommonMark, with GFM's
tables and strikethrough) and lays it out for a width through
:class:`~navigator.lib.viewer.layout.Builder`: headings, paragraphs joined and
wrapped, lists, quotes, tables drawn in box characters, rules, and code blocks
coloured by :mod:`navigator.lib.highlight`.  The markup itself is not shown.

Nothing here knows of widgets or threads: the viewer reads the file and calls
:func:`render` on its own thread.  markdown-it-py is the optional
``navigator-fm[markdown]`` extra; :func:`available` says whether it is there.
"""

from __future__ import annotations

import functools
import importlib.util
import re
from typing import Any

from navigator.lib.viewer.layout import (
    ASCII,
    RENDER_LIMIT,
    UNICODE,
    Builder,
    Cell,
    Layout,
    _cells,
    _wrap,
    decode,
    line_starts,
)

__all__ = ["EXTRA", "MARKDOWN_LIMIT", "Layout", "available", "decode", "render"]

#: The extra that brings markdown-it-py.
EXTRA = "navigator-fm[markdown]"

#: The most a Markdown file may hold to be rendered: the layout's limit.
MARKDOWN_LIMIT = RENDER_LIMIT

_TASK = re.compile(r"\[([ xX])\] ")


@functools.cache
def available() -> bool:
    """Whether markdown-it-py can be imported."""
    return importlib.util.find_spec("markdown_it") is not None


class _Renderer(Builder):
    """markdown-it's tokens walked into a :class:`Builder`."""

    def __init__(self, tokens: list[Any], line_starts: list[int], width: int, glyphs: Any) -> None:
        super().__init__(line_starts, width, glyphs)
        self.tokens = tokens
        #: Each list open: whether it is tight, an ordered one's next number,
        #: its delimiter, and whether no item has been seen yet.
        self.lists: list[list[Any]] = []

    def src(self, token: Any, line: int = 0) -> int:
        if token.map is None:
            return self.last_src
        return self.line_src(token.map[0] + line)

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
        return self.finish()

    def step(self, index: int) -> int:
        token = self.tokens[index]
        kind = token.type
        if kind == "heading_open":
            level = int(token.tag[1:])
            cells = self.inline(self.tokens[index + 1], ("heading", token.tag))
            self.heading(level, cells, self.src(token))
            return index + 3
        if kind == "paragraph_open":
            self.paragraph(self.inline(self.tokens[index + 1]), self.src(token), tight=token.hidden)
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
            self.pop()
            return index + 1
        if kind == "blockquote_open":
            self.quote()
            return index + 1
        if kind == "blockquote_close":
            self.pop()
            self.gap = True
            return index + 1
        if kind in ("fence", "code_block"):
            content = token.content
            if content.endswith("\n"):
                content = content[:-1]
            lines = content.split("\n")
            language = (token.info or "").strip().split(maxsplit=1)[0].lower() if token.info else ""
            # Inside the fence: a fenced block's first line is the one after it.
            skip = 1 if kind == "fence" else 0
            self.code(lines, language, [self.src(token, number + skip) for number in range(len(lines))])
            return index + 1
        if kind == "hr":
            self.rule(self.src(token))
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
            return self.gfm_table(index)
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

    def list_item(self, index: int) -> None:
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
        self.push(_cells(mark, self.classes("bullet")))

    def gfm_table(self, index: int) -> int:
        """A GFM table: its cells gathered, then drawn by :meth:`Builder.table`."""
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
        self.table(rows, aligns)
        return index + 1


def render(data: bytes, width: int, *, codec: str = "utf-8", unicode: bool = True) -> Layout:
    """*data*, a Markdown document in *codec*, laid out *width* columns wide;
    *unicode* draws with box characters and bullets, else with ASCII."""
    from markdown_it import MarkdownIt

    parser = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    text = decode(data, codec).replace("\r\n", "\n").replace("\r", "\n")
    tokens = parser.parse(text)
    return _Renderer(tokens, line_starts(data), width, UNICODE if unicode else ASCII).run()
