"""The viewer's *reStructuredText* reading of a file: a departure, DN's viewer had none.

``render`` parses a whole document with docutils -- the reference parser,
whose tree is what Sphinx and PyPI render -- and walks its nodes into a
:class:`~navigator.lib.viewer.layout.Builder`: sections as headings, paragraphs
joined and wrapped, bullet and enumerated lists, block quotes, literal and
``code-block`` blocks coloured by :mod:`navigator.lib.highlight`, grid and
simple tables in box characters, transitions as rules, admonitions as a quoted
block under their name, definition and field lists indented under their term.

**Nothing outside the file is read or run**: ``include`` and ``raw`` are
switched off, and every warning docutils has is kept quiet -- a document with
errors still renders what it can.
"""

from __future__ import annotations

import io
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

#: Admonitions, each shown as a quoted block under its name.
ADMONITIONS = {
    "attention": "Attention", "caution": "Caution", "danger": "Danger", "error": "Error",
    "hint": "Hint", "important": "Important", "note": "Note", "tip": "Tip", "warning": "Warning",
}

#: Nodes that show nothing.
SILENT = frozenset({
    "comment", "target", "substitution_definition", "system_message", "pending", "raw",
    "decoration", "meta", "problematic_message",
})


def _roman(number: int) -> str:
    out = ""
    for value, letters in ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
                           (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while number >= value:
            out, number = out + letters, number - value
    return out


def _enumerator(kind: str, number: int) -> str:
    if kind == "loweralpha":
        return chr(ord("a") + (number - 1) % 26)
    if kind == "upperalpha":
        return chr(ord("A") + (number - 1) % 26)
    if kind == "lowerroman":
        return _roman(number)
    if kind == "upperroman":
        return _roman(number).upper()
    return str(number)


class _Renderer(Builder):
    """docutils' document tree walked into a :class:`Builder`."""

    def __init__(self, line_starts: list[int], width: int, glyphs: Any, lines: list[str]) -> None:
        super().__init__(line_starts, width, glyphs)
        #: The source's lines, to find a code block's first line in.
        self.lines = lines
        #: How deep in sections the walk is: a title's heading level.
        self.depth = 0
        #: How many list items the walk is inside.
        self.items = 0

    # -- where ----------------------------------------------------------------

    def src(self, node: Any, back: int = 0) -> int:
        """The offset of *node*'s line (docutils counts from 1), or of the
        first line found beneath it; the last offset if none is."""
        line = getattr(node, "line", None)
        if line is None:
            for child in node.findall(include_self=False):
                line = getattr(child, "line", None)
                if line is not None:
                    break
        if line is None:
            return self.last_src
        return self.line_src(line - 1 - back)

    # -- inline ---------------------------------------------------------------

    def inline(self, node: Any, styles: tuple[str, ...] = (), link: str | None = None) -> list[Cell]:
        """*node*'s text as cells, its emphasis, literals and references classed."""
        cells: list[Cell] = []
        for child in node.children:
            name = child.tagname
            if name == "#text":
                cells.extend(_cells(child.astext().replace("\n", " ").replace("\t", " "),
                                    self.classes(*styles), link))
            elif name in SILENT:
                continue
            elif name in ("emphasis", "title_reference"):
                cells.extend(self.inline(child, styles + ("emph",), link))
            elif name == "strong":
                cells.extend(self.inline(child, styles + ("strong",), link))
            elif name in ("literal", "math"):
                cells.extend(self.inline(child, styles + ("code",), link))
            elif name == "reference":
                cells.extend(self.inline(child, styles + ("link",), child.get("refuri") or link))
            elif name in ("footnote_reference", "citation_reference"):
                cells.extend(_cells(f"[{child.astext()}]", self.classes(*styles, "link"), link))
            elif name == "image":
                alt = child.get("alt") or ""
                cells.extend(_cells(f"[{alt}]" if alt else "[image]", self.classes(*styles, "image"),
                                    child.get("uri") or link))
            else:
                cells.extend(self.inline(child, styles, link))
        return cells

    # -- blocks ---------------------------------------------------------------

    def walk(self, node: Any, *, tight: bool = False) -> None:
        """Every block under *node*, in order.  *tight*: the first paragraph of
        a list item, set straight after its bullet."""
        for index, child in enumerate(node.children):
            self.block_of(child, tight=tight and index == 0)

    def block_of(self, node: Any, *, tight: bool = False) -> None:
        name = node.tagname
        if name in SILENT or name == "#text":
            return
        if name == "section":
            self.depth += 1
            self.walk(node)
            self.depth -= 1
        elif name == "title":
            level = max(1, min(self.depth, 6))
            # A title's line is its underline's: the text is the line above.
            self.heading(level, self.inline(node, ("heading", f"h{level}")), self.src(node, back=1))
        elif name in ("subtitle", "rubric"):
            self.heading(6, self.inline(node, ("heading", "h6")), self.src(node))
        elif name == "paragraph":
            self.paragraph(self.inline(node), self.src(node), tight=tight)
        elif name in ("bullet_list", "enumerated_list"):
            self.a_list(node)
        elif name == "block_quote":
            self.quote()
            self.walk(node)
            self.pop()
            self.gap = True
        elif name in ("literal_block", "doctest_block"):
            classes = node.get("classes") or []
            language = "pycon" if name == "doctest_block" else next(
                (c for c in classes if c != "code"), "") if "code" in classes else ""
            lines = node.astext().split("\n")
            number = self.code_line(node, lines)
            self.code(lines, language, [self.line_src(number + n) for n in range(len(lines))])
        elif name == "transition":
            self.rule(self.src(node))
        elif name in ADMONITIONS or name == "admonition":
            self.admonition(node)
        elif name == "definition_list":
            for item in node.children:
                self.definition(item)
        elif name == "field_list":
            for field in node.children:
                self.definition(field)
        elif name == "table":
            self.a_table(node)
        elif name == "image":
            alt = node.get("alt") or ""
            self.paragraph(_cells(f"[{alt}]" if alt else "[image]", self.classes("image"), node.get("uri")),
                           self.src(node))
        elif name == "line_block":
            cells: list[Cell] = []
            for line in node.findall(lambda n: n.tagname == "line"):
                if cells:
                    cells.append(("\n", (), None))
                cells.extend(self.inline(line))
            self.paragraph(cells, self.src(node))
        elif name in ("footnote", "citation"):
            label = next((c.astext() for c in node.children if c.tagname == "label"), "")
            self.push(_cells(f"[{label}] ", self.classes("link")))
            self.walk(node, tight=True)
            self.pop()
            self.gap = True
        elif name == "label":
            return
        elif name in ("topic", "sidebar"):
            self.walk(node)
        else:
            # A container docutils knows and this does not (compound,
            # container, figure, legend...): what is inside it.
            self.walk(node)

    def code_line(self, node: Any, lines: list[str]) -> int:
        """The source line (from 0) a literal block's text begins on.  docutils
        gives a ``::`` block its first line but a ``code-block`` the line after
        it, so the first line's text is looked for around the one given."""
        given = (getattr(node, "line", None) or 1) - 1
        first = lines[0].strip() if lines else ""
        if not first:
            return given
        for distance in range(len(lines) + 4):
            for number in (given - distance, given + distance):
                if 0 <= number < len(self.lines) and self.lines[number].strip() == first:
                    return number
        return given

    def a_list(self, node: Any) -> None:
        if self.items:
            self.gap = False  # a list under an item's text: no blank row between
        enumerated = node.tagname == "enumerated_list"
        number = int(node.get("start", 1) or 1)
        kind = node.get("enumtype", "arabic")
        prefix, suffix = node.get("prefix", ""), node.get("suffix", ".")
        for index, item in enumerate(node.children):
            if index:
                self.gap = False
            if enumerated:
                mark = f"{prefix}{_enumerator(kind, number + index)}{suffix} "
            else:
                mark = self.glyphs.bullet + " "
            self.push(_cells(mark, self.classes("bullet")))
            self.items += 1
            self.walk(item, tight=True)
            self.items -= 1
            self.pop()
        self.gap = True

    def admonition(self, node: Any) -> None:
        """Its name, strong, over its body in a quote's gutter."""
        title = next((c for c in node.children if c.tagname == "title"), None)
        label = self.inline(title) if title is not None else _cells(
            ADMONITIONS.get(node.tagname, node.tagname.title()))
        self.quote()
        self.paragraph([(char, classes + ("strong",), link) for char, classes, link in label],
                       self.src(node), tight=True)
        self.gap = False  # the body straight under its name
        for child in node.children:
            if child is not title:
                self.block_of(child)
        self.pop()
        self.gap = True

    def definition(self, item: Any) -> None:
        """A definition list's item or a field: the term, strong; the rest two
        columns in under it."""
        heads = [c for c in item.children if c.tagname in ("term", "field_name", "classifier")]
        bodies = [c for c in item.children if c.tagname in ("definition", "field_body")]
        cells: list[Cell] = []
        for head in heads:
            if cells:
                cells.extend(_cells(" : "))
            cells.extend(self.inline(head, ("strong",)))
        self.paragraph(cells, self.src(item))
        self.push([BLANK, BLANK], [BLANK, BLANK])
        self.gap = False
        for body in bodies:
            self.walk(body, tight=True)
        self.pop()
        self.gap = True

    def a_table(self, node: Any) -> None:
        rows: list[tuple[int, bool, list[list[Cell]]]] = []
        for part in node.findall(lambda n: n.tagname in ("thead", "tbody")):
            head = part.tagname == "thead"
            for row in part.children:
                if row.tagname != "row":
                    continue
                cells: list[list[Cell]] = []
                for entry in row.children:
                    cell: list[Cell] = []
                    for paragraph in entry.children:
                        if cell:
                            cell.append((" ", (), None))
                        if paragraph.tagname == "paragraph":
                            cell.extend(self.inline(paragraph, ("th",) if head else ()))
                        else:
                            cell.extend(_cells(paragraph.astext().replace("\n", " ")))
                    cells.append(cell)
                rows.append((self.src(row), head, cells))
        if rows:
            self.table(rows, [])


def render(data: bytes, width: int, *, codec: str = "utf-8", unicode: bool = True) -> Layout:
    """*data*, a reStructuredText document in *codec*, laid out *width*
    columns wide; *unicode* draws with box characters and bullets, else with ASCII."""
    from docutils.core import publish_doctree

    text = decode(data, codec).replace("\r\n", "\n").replace("\r", "\n")
    document = publish_doctree(text, settings_overrides={
        # Quiet, and never fatal: a document with errors renders what it can.
        "report_level": 5, "halt_level": 5, "warning_stream": io.StringIO(),
        # Nothing outside the file: no include, no raw, no file reads.
        "file_insertion_enabled": False, "raw_enabled": False,
        # Keep the first title a section's, so it is a heading like the rest.
        "doctitle_xform": False, "sectsubtitle_xform": False,
        # Code blocks are coloured here, by Navigator's own highlighting.
        "syntax_highlight": "none",
    })
    renderer = _Renderer(line_starts(data), width, UNICODE if unicode else ASCII, text.split("\n"))
    renderer.walk(document)
    return renderer.finish()
