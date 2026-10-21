"""The viewer's *HTML* reading of a file: a departure, DN's viewer had none.

What a text browser's dump gives (``lynx -dump``): the page's ``<title>`` as
its first heading, then headings, paragraphs with their blanks run together,
lists, quotes, tables drawn in box characters, rules, and ``<pre>`` as a code
block coloured by its ``language-*`` class.  Links keep their URL (an OSC 8
hyperlink once painted), images are their ``[alt]``; scripts, styles and the
rest of ``<head>`` are not shown, and CSS is not read.

The stdlib's :class:`html.parser.HTMLParser` reads the page, so nothing needs
installing.  It is forgiving and so is this: an end tag closes its own element
wherever it is open, an unclosed ``<p>`` or ``<li>`` ends where the next block
begins, and an unknown tag is passed through.  Every row's ``src`` is the
source line of the tag its block began at.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

from navigator.lib.viewer.layout import (
    ASCII,
    BLANK,
    UNICODE,
    Builder,
    Cell,
    Layout,
    _cells,
    decode,
    line_starts,
)

#: Elements whose text is never shown.
HIDDEN = frozenset({"script", "style", "template", "noscript"})

#: What may stand in ``<head>``: anything else ends it, ``</head>`` or not.
HEAD_ONLY = frozenset({"title", "meta", "link", "base", "script", "style", "noscript", "template"})

#: Elements that end the paragraph before them and begin one of their own.
BLOCKS = frozenset({
    "p", "div", "section", "article", "header", "footer", "main", "nav", "aside", "figure",
    "figcaption", "address", "details", "summary", "form", "fieldset", "center", "body", "html",
    "dl", "legend", "caption", "hgroup", "search", "menu",
})

#: Inline elements and the class their text carries.
INLINE = {
    "b": "strong", "strong": "strong",
    "i": "emph", "em": "emph", "cite": "emph", "var": "emph", "dfn": "emph",
    "s": "strike", "del": "strike", "strike": "strike",
    "code": "code", "kbd": "code", "samp": "code", "tt": "code",
}

_BLANKS = re.compile(r"\s+")
_LANGUAGE = re.compile(r"\b(?:language|lang)-([\w+#.-]+)")


def _language(attrs: dict[str, str | None]) -> str:
    found = _LANGUAGE.search(attrs.get("class") or "")
    return found.group(1).lower() if found else ""


def _align(attrs: dict[str, str | None]) -> str:
    align = (attrs.get("align") or "").lower()
    style = attrs.get("style") or ""
    found = re.search(r"text-align\s*:\s*(left|right|center)", style, re.I)
    if found:
        align = found.group(1).lower()
    return align if align in ("left", "right", "center") else "left"


class _Renderer(Builder, HTMLParser):
    """A page's tags walked into a :class:`Builder`."""

    def __init__(self, line_starts: list[int], width: int, glyphs: Any) -> None:
        Builder.__init__(self, line_starts, width, glyphs)
        HTMLParser.__init__(self, convert_charrefs=True)
        #: The paragraph being gathered, and the source offset it began at.
        self.run: list[Cell] = []
        self.run_src = 0
        #: Inline classes open, with the tag that opened each.
        self.styles: list[tuple[str, str]] = []
        self.links: list[str | None] = []
        #: How deep inside elements that hide their text.
        self.hidden = 0
        #: Inside ``<head>``, whose text is not shown but for the title.
        self.in_head = False
        #: The page's title as it is read, else None.
        self.title: list[str] | None = None
        self.title_src = 0
        #: The heading open, its level, else None.
        self.level: int | None = None
        #: A ``<pre>``'s text as it is read, with its language and first line.
        self.pre: list[str] | None = None
        self.pre_language = ""
        self.pre_line = 0
        #: Each list open: ordered, its next number, whether an item is open.
        self.lists: list[list[Any]] = []
        #: The table being gathered: its rows (``src``, in a head, cells, all
        #: ``th``), the alignment per column, and the cell open.
        self.rows: list[list[Any]] | None = None
        self.aligns: list[str] = []
        self.cell: list[Cell] | None = None
        self.in_head_rows = False
        self.tables = 0

    # -- where ----------------------------------------------------------------

    def here(self) -> int:
        """The byte offset of the line the parser is at."""
        return self.line_src(self.getpos()[0] - 1)

    def text_classes(self) -> tuple[str, ...]:
        own = tuple(name for _, name in self.styles)
        if self.level is not None:
            own = ("heading", f"h{self.level}") + own
        return self.classes(*own)

    # -- paragraphs -------------------------------------------------------------

    def add(self, cells: list[Cell]) -> None:
        """Cells to the open table cell, else to the paragraph."""
        if self.cell is not None:
            self.cell.extend(cells)
            return
        if not self.run:
            self.run_src = self.here()
        self.run.extend(cells)

    def flush(self) -> None:
        """The paragraph gathered, as a heading or a paragraph; nothing if blank."""
        run, self.run = self.run, []
        while run and run[-1][0] in (" ", "\n"):
            run.pop()
        while run and run[0][0] == " ":
            run.pop(0)
        if not run:
            return
        if self.level is not None:
            self.heading(self.level, run, self.run_src)
        else:
            self.paragraph(run, self.run_src, tight=bool(self.lists))

    # -- the parser's calls ---------------------------------------------------

    def handle_starttag(self, tag: str, attr_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attr_list)
        if tag == "head":
            self.in_head = True
            return
        if self.in_head and tag not in HEAD_ONLY:
            self.in_head = False
        if tag in HIDDEN:
            self.hidden += 1
            return
        if tag == "title":
            self.title, self.title_src = [], self.here()
            return
        if self.hidden or self.in_head:
            return
        if self.pre is not None:
            if tag == "code" and not "".join(self.pre).strip() and not self.pre_language:
                self.pre_language = _language(attrs)
            return
        if tag == "table":
            self.tables += 1
            if self.tables == 1:
                self.flush()
                self.rows, self.aligns, self.cell, self.in_head_rows = [], [], None, False
            return
        if self.rows is not None and self.tables == 1:
            if self.table_tag(tag, attrs):
                return
        if tag in BLOCKS or tag == "body":
            if self.cell is not None:
                self.cell.append((" ", (), None))
            else:
                self.flush()
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush()
            self.level = int(tag[1])
            return
        if tag in INLINE:
            self.styles.append((tag, INLINE[tag]))
            return
        if tag == "a":
            self.links.append(attrs.get("href") or None)
            self.styles.append((tag, "link"))
            return
        if tag == "br":
            self.add([("\n" if self.cell is None else " ", self.text_classes(), self.link())])
            return
        if tag == "img":
            alt = (attrs.get("alt") or "").strip()
            self.add(_cells(f"[{alt}]" if alt else "[image]", self.text_classes() + ("image",),
                            attrs.get("src") or self.link()))
            return
        if self.cell is not None:
            return  # other blocks inside a table cell: its text runs on
        if tag == "hr":
            self.flush()
            self.rule(self.here())
        elif tag in ("ul", "ol", "menu"):
            self.flush()
            if self.lists:
                self.gap = False  # a list under an item's text: no blank row between
            start = attrs.get("start")
            number = int(start) if start and start.lstrip("-").isdigit() else 1
            self.lists.append([tag == "ol", number, False])
        elif tag == "li":
            self.flush()
            if not self.lists:
                self.lists.append([False, 1, False])
            current = self.lists[-1]
            if current[2]:
                self.pop()
                self.gap = False
            ordered, number, _ = current
            value = attrs.get("value")
            if ordered and value and value.lstrip("-").isdigit():
                number = int(value)
            mark = f"{number}. " if ordered else self.glyphs.bullet + " "
            current[1], current[2] = number + 1, True
            self.push(_cells(mark, self.classes("bullet")))
        elif tag == "blockquote":
            self.flush()
            self.quote()
        elif tag == "dt":
            self.flush()
            self.styles.append((tag, "strong"))
        elif tag == "dd":
            self.flush()
            self.push([BLANK, BLANK], [BLANK, BLANK])
            self.gap = False
        elif tag == "pre":
            self.flush()
            self.pre, self.pre_language, self.pre_line = [], _language(attrs), self.getpos()[0] - 1

    def table_tag(self, tag: str, attrs: dict[str, str | None]) -> bool:
        """A table's own tags, while one is gathered; True when *tag* was one."""
        rows = self.rows
        if tag == "thead":
            self.in_head_rows = True
        elif tag in ("tbody", "tfoot"):
            self.in_head_rows = False
        elif tag == "tr":
            self.end_cell()
            rows.append([self.here(), self.in_head_rows, [], True])
        elif tag in ("td", "th"):
            self.end_cell()
            if not rows:
                rows.append([self.here(), self.in_head_rows, [], True])
            row = rows[-1]
            if tag == "td":
                row[3] = False
            if len(row[2]) >= len(self.aligns):
                self.aligns.append(_align(attrs))
            self.cell = []
            if tag == "th":
                self.styles.append(("th", "th"))
        else:
            return False
        return True

    def end_cell(self) -> None:
        if self.cell is None or not self.rows:
            return
        cell, self.cell = self.cell, None
        while cell and cell[-1][0] == " ":
            cell.pop()
        while cell and cell[0][0] == " ":
            cell.pop(0)
        self.rows[-1][2].append(cell)
        self.close_style("th")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in ("br", "img", "hr"):
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self.in_head = False
            return
        if tag in HIDDEN:
            self.hidden = max(0, self.hidden - 1)
            return
        if tag == "title":
            if self.title is not None:
                text = _BLANKS.sub(" ", "".join(self.title)).strip()
                self.title = None
                if text:
                    self.heading(1, _cells(text, self.classes("heading", "h1")), self.title_src)
            return
        if self.hidden or self.in_head:
            return
        if self.pre is not None:
            if tag == "pre":
                self.end_pre()
            return
        if tag == "table":
            self.tables = max(0, self.tables - 1)
            if self.tables == 0 and self.rows is not None:
                self.end_cell()
                rows = [(src, head or all_th, cells) for src, head, cells, all_th in self.rows if cells]
                self.rows = None
                self.table(rows, self.aligns)
            return
        if self.rows is not None and self.tables == 1:
            if tag in ("td", "th"):
                self.end_cell()
                return
            if tag == "thead":
                self.in_head_rows = False
                return
            if tag in ("tr", "tbody", "tfoot"):
                self.end_cell()
                return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush()
            self.level = None
            return
        if tag in INLINE or tag == "dt":
            if tag == "dt":
                self.flush()
            self.close_style(tag)
            return
        if tag == "a":
            if self.close_style("a") and self.links:
                self.links.pop()
            return
        if self.cell is not None:
            return
        if tag in BLOCKS:
            self.flush()
        elif tag in ("ul", "ol", "menu"):
            self.flush()
            if self.lists:
                if self.lists[-1][2]:
                    self.pop()
                self.lists.pop()
            self.gap = True
        elif tag == "li":
            self.flush()
            if self.lists and self.lists[-1][2]:
                self.pop()
                self.lists[-1][2] = False
                self.gap = False
        elif tag == "blockquote":
            self.flush()
            self.pop()
            self.gap = True
        elif tag == "dd":
            self.flush()
            self.pop()

    def close_style(self, tag: str) -> bool:
        """The innermost inline class *tag* opened, closed; False if none is."""
        for index in range(len(self.styles) - 1, -1, -1):
            if self.styles[index][0] == tag:
                del self.styles[index]
                return True
        return False

    def link(self) -> str | None:
        return self.links[-1] if self.links else None

    def handle_data(self, data: str) -> None:
        if self.title is not None:
            self.title.append(data)
            return
        if self.hidden or self.in_head:
            return
        if self.pre is not None:
            self.pre.append(data)
            return
        if self.rows is not None and self.cell is None:
            return  # between a table's cells
        text = _BLANKS.sub(" ", data)
        if not text:
            return
        target = self.cell if self.cell is not None else self.run
        if text == " " and (not target or target[-1][0] in (" ", "\n")):
            return
        if target and target[-1][0] in (" ", "\n") and text.startswith(" "):
            text = text[1:]
        self.add(_cells(text, self.text_classes(), self.link()))

    def end_pre(self) -> None:
        text = "".join(self.pre or [])
        self.pre = None
        first = self.pre_line
        if text.startswith("\n"):
            # The break straight after <pre> is not content, as browsers have it.
            text, first = text[1:], first + 1
        if text.endswith("\n"):
            text = text[:-1]
        lines = text.split("\n")
        self.code(lines, self.pre_language, [self.line_src(first + number) for number in range(len(lines))])

    def done(self) -> Layout:
        self.close()
        if self.pre is not None:
            self.end_pre()
        self.flush()
        if self.rows is not None:
            self.tables = 1
            self.handle_endtag("table")
        return self.finish()


def render(data: bytes, width: int, *, codec: str = "utf-8", unicode: bool = True) -> Layout:
    """*data*, an HTML page in *codec*, laid out *width* columns wide;
    *unicode* draws with box characters and bullets, else with ASCII."""
    renderer = _Renderer(line_starts(data), width, UNICODE if unicode else ASCII)
    renderer.feed(decode(data, codec).replace("\r\n", "\n").replace("\r", "\n"))
    return renderer.done()
