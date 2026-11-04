"""F3's structured view: a JSON, YAML, TOML, XML or property-list file's data
as a tree -- keys and indices as branches, scalars shown at their key.

A departure, asked for: DOS Navigator's viewer showed bytes and lines only.
Shift+F4 switches to it from the text, as it switches a CSV to the
spreadsheet (``FileWindow.as_tree``); the window is
``navigator/widgets/viewer/struct_window``.

**The file is parsed whole, on a thread**, by the standard library's
``json``, ``tomllib``, ``xml.etree`` and ``plistlib``, and PyYAML's composer
-- never ``yaml.load``: the composer builds nodes and runs no constructor, so a
document's tags (``!Ref``, ``!!python/object``) are shown, never acted on.
``STRUCT_LIMIT`` bounds what is read.

**A** :class:`Node` **is made only when its branch is opened**: each wraps
what the parser made (a dict, a list, a YAML node, an element) and makes its
children the first time they are asked for, so a large document costs its
parse and the branches looked at, not a second tree.  A YAML alias is the
node it names, shared -- a branch that holds itself is shown as deep as it is
opened, and every walk over the whole tree (:func:`walk`) passes a node once.

**Where a node is in the file** is known for YAML (its composer marks every
node), so going back to the text lands on its line; the other parsers keep no
places, and the text opens where it was.  A parse error's place is known for
all of them (:class:`ParseFailed`).
"""

from __future__ import annotations

import datetime
import fnmatch
import json
import re
import threading
from pathlib import Path
from typing import Any, Iterator

#: The most a file may hold to be shown as a tree: it is parsed whole.
STRUCT_LIMIT = 32 * 1024 * 1024

#: The formats, and what reads each.
KINDS = ("json", "jsonl", "yaml", "toml", "xml", "plist", "html")

#: How many characters of a value a row or a search looks at.
VALUE_LIMIT = 4096

#: Held while a node's children are made (:meth:`Node.children`).
_MAKING = threading.Lock()

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*\Z")


class ParseFailed(Exception):
    """The file is not what its name says: the parser's *message*, and where
    -- *line* and *column* from 1, *offset* the byte its line starts at --
    when it said."""

    def __init__(self, message: str, line: int = 0, column: int = 0, offset: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.offset = offset

    def __str__(self) -> str:
        if self.line:
            return f"Line {self.line}, column {self.column}: {self.message}"
        return self.message


def kind_by_name(name: str | Path | None, masks: str | None = None) -> str | None:
    """The format *name* is read in, when ``[viewer] structured_masks`` (or
    *masks*) names it: by its extension -- ``.yml`` YAML, ``.toml`` TOML,
    ``.jsonl``/``.ndjson`` JSON lines, ``.plist`` a property list, anything
    else the masks name that ends ``ml`` (``.xml``, ``.svg``, ``.xhtml``) XML
    -- and JSON otherwise."""
    if name is None:
        return None
    if masks is None:
        from navigator.settings import SETTINGS

        masks = SETTINGS.viewer.structured_masks
    lower = Path(name).name.lower()
    if not any(fnmatch.fnmatchcase(lower, mask.strip().lower()) for mask in masks.split(";") if mask.strip()):
        return None
    suffix = Path(lower).suffix
    if suffix in (".yml", ".yaml"):
        return "yaml"
    if suffix == ".toml":
        return "toml"
    if suffix in (".jsonl", ".ndjson"):
        return "jsonl"
    if suffix == ".plist":
        return "plist"
    if suffix.endswith("ml") or suffix == ".svg":
        return "xml"
    return "json"


#: What View > *Data tree* reads a file as when the masks do not name it:
#: by its extension first.
_BY_SUFFIX = {".json": "json", ".geojson": "json", ".ipynb": "json", ".jsonl": "jsonl", ".ndjson": "jsonl",
              ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".xml": "xml", ".svg": "xml",
              ".xhtml": "html", ".html": "html", ".htm": "html", ".plist": "plist"}


def kind_for(name: str | Path, head: bytes = b"") -> str:
    """What View > *Data tree* reads *name* as: what the masks say, else
    its extension (``.html`` HTML among them, which Shift+F4 leaves to the
    Markup view), else its first bytes -- ``{`` or ``[`` JSON, ``<`` XML
    (HTML when it says ``<!doctype html`` or ``<html``), anything else YAML,
    which reads most plain text as something."""
    kind = kind_by_name(name)
    if kind is not None:
        return kind
    kind = _BY_SUFFIX.get(Path(name).suffix.lower())
    if kind is not None:
        return kind
    start = head.lstrip(b"\xef\xbb\xbf \t\r\n")[:64].lower()
    if start[:1] in (b"{", b"["):
        return "json"
    if start.startswith((b"<!doctype html", b"<html")):
        return "html"
    if start[:1] == b"<":
        return "xml"
    return "yaml"


# -- the tree ------------------------------------------------------------------------


class Node:
    """A branch or a leaf of the tree.

    *key* is a mapping's key, a list's index, an element's or attribute's
    name, or None for the root; *kind* one of ``object``, ``array``,
    ``string``, ``number``, ``bool``, ``null``, ``date``, ``element``,
    ``attribute``, ``text``, ``tagged``; *text* a scalar's value as shown.
    """

    __slots__ = ("key", "kind", "text", "parent", "offset", "format", "_data", "_children", "_count")

    def __init__(self, key: Any, kind: str, text: str = "", *, parent: Node | None = None,
                 offset: int | None = None, format: str = "json", data: Any = None,
                 count: int = 0) -> None:
        self.key = key
        self.kind = kind
        self.text = text
        self.parent = parent
        self.offset = offset
        self.format = format
        self._data = data
        self._children: list[Node] | None = None
        self._count = count

    def __repr__(self) -> str:
        return f"Node({self.key!r}, {self.kind!r}, {self.text!r})"

    @property
    def container(self) -> bool:
        return self.kind in ("object", "array", "element")

    @property
    def count(self) -> int:
        """How many children it has, known without making them."""
        return self._count

    def children(self) -> list[Node]:
        """Its children, made the first time they are asked for -- once, by
        whichever asks first: a search on a thread and the tree on the loop
        get the same nodes, so the one found is the one shown."""
        if self._children is None:
            with _MAKING:
                if self._children is None:
                    self._children = list(_CHILDREN[self.format](self)) if self._count else []
        return self._children

    def value(self) -> str:
        """What *Copy value* copies: a scalar as it is, a branch in its own
        format's text -- JSON, YAML or the element."""
        if not self.container:
            return self.text
        return _DUMPERS[self.format](self)


def walk(root: Node) -> Iterator[Node]:
    """Every node under *root*, depth first in the order shown -- *root*
    first.  A branch reached again (a YAML alias) is passed, not opened
    again, so a branch holding itself ends."""
    seen: set[int] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        if not node.container:
            continue
        held = identity(node)
        if held in seen:
            continue
        seen.add(held)
        stack.extend(reversed(node.children()))


def identity(node: Node) -> int:
    """What a branch holds, as a number: the same for every alias of one YAML
    node, so a walk can tell it has been there."""
    return id(node._data[0]) if node.format == "yaml" else id(node._data)


def path(node: Node) -> str:
    """Where *node* is, as a path: jq's for JSON, YAML, TOML and property
    lists (``.servers[2]."odd key".host``), XPath's for XML
    (``/config/server[2]/@port``)."""
    chain = []
    while node is not None:
        chain.append(node)
        node = node.parent
    chain.reverse()
    if chain[0].format == "xml":
        parts = []
        for item in chain:
            if item.kind == "attribute":
                parts.append(f"@{item.key}")
            elif item.kind == "text":
                parts.append("text()")
            else:
                parts.append(_xml_step(item))
        return "/" + "/".join(parts)
    out = ""
    for item in chain[1:]:
        if isinstance(item.key, int):
            out += f"[{item.key}]"
        elif _IDENTIFIER.match(str(item.key)):
            out += f".{item.key}"
        else:
            out += "." + json.dumps(str(item.key), ensure_ascii=False)
    return out or "."


def _xml_step(item: Node) -> str:
    """An element's step: its name, and its place among its parent's
    elements of that name when it is not the only one."""
    parent = item.parent
    if parent is None:
        return str(item.key)
    same = [child for child in parent.children() if child.kind == "element" and child.key == item.key]
    if len(same) < 2:
        return str(item.key)
    return f"{item.key}[{next(i for i, child in enumerate(same, 1) if child is item)}]"


def matches(node: Node, needle: str, *, case: bool = False) -> bool:
    """Whether *needle* is in *node*'s key or value -- in either case
    unless *case*."""
    def has(text: str) -> bool:
        return needle in text if case else needle.casefold() in text.casefold()

    return (node.key is not None and has(str(node.key))) or (
        not node.container and has(node.text[:VALUE_LIMIT]))


def find(root: Node, after: Node | None, needle: str, *, case: bool = False,
         backward: bool = False, stopped: Any = None) -> Node | None:
    """The first node past *after* -- in the order rows are shown, every
    branch open -- whose key or value holds *needle*; before it, *backward*.
    From the top (or the end) when *after* is None.  Every branch is opened in
    the model to look, so on a thread; *stopped()* ends it early."""
    order = list(walk(root))
    if backward:
        order.reverse()
    start = 0
    if after is not None:
        start = next((index + 1 for index, node in enumerate(order) if node is after), 0)
    for index in range(start, len(order)):
        if stopped is not None and index % 4096 == 0 and stopped():
            return None
        if matches(order[index], needle, case=case):
            return order[index]
    return None


# -- reading -----------------------------------------------------------------------


def parse(data: bytes, kind: str) -> Node:
    """*data*, read as *kind*, as the tree's root.  Raises :class:`ParseFailed`."""
    if kind not in KINDS:
        raise ValueError(f"{kind!r} is not one of {', '.join(KINDS)}")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return _READERS[kind](data)


def _line_offset(data: bytes, line: int) -> int | None:
    """The byte line *line* (from 1) starts at."""
    if line < 1:
        return None
    at = 0
    for _ in range(line - 1):
        at = data.find(b"\n", at)
        if at < 0:
            return None
        at += 1
    return at


def _text(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        line = data.count(b"\n", 0, error.start) + 1
        raise ParseFailed("not UTF-8 text", line, 0, _line_offset(data, line)) from None


# JSON, TOML and property lists: Python's own values.


class _Pairs(list):
    """A JSON object, as its pairs: their order kept, and a key given twice
    kept twice -- a dict would keep the last one alone."""


def _read_json(data: bytes) -> Node:
    try:
        value = json.loads(_text(data), object_pairs_hook=_Pairs)
    except json.JSONDecodeError as error:
        raise ParseFailed(error.msg, error.lineno, error.colno, _line_offset(data, error.lineno)) from None
    return _python(None, value, None, "json")


def _read_jsonl(data: bytes) -> Node:
    """One document a line: the root an array of them."""
    values = []
    for number, line in enumerate(_text(data).splitlines(), 1):
        if not line.strip():
            continue
        try:
            values.append(json.loads(line, object_pairs_hook=_Pairs))
        except json.JSONDecodeError as error:
            raise ParseFailed(error.msg, number, error.colno, _line_offset(data, number)) from None
    return _python(None, values, None, "json")


_TOML_PLACE = re.compile(r"\(at line (\d+), column (\d+)\)")


def _read_toml(data: bytes) -> Node:
    import tomllib

    try:
        value = tomllib.loads(_text(data))
    except tomllib.TOMLDecodeError as error:
        message = str(error)
        place = _TOML_PLACE.search(message)
        if place is None:
            raise ParseFailed(message) from None
        line, column = int(place.group(1)), int(place.group(2))
        raise ParseFailed(message[:place.start()].strip(), line, column, _line_offset(data, line)) from None
    return _python(None, value, None, "toml")


def _read_plist(data: bytes) -> Node:
    import plistlib

    try:
        value = plistlib.loads(data)
    except Exception as error:  # plistlib raises what its readers do
        raise ParseFailed(str(error) or type(error).__name__) from None
    return _python(None, value, None, "plist")


def _python(key: Any, value: Any, parent: Node | None, format: str) -> Node:
    """A node for a Python value a parser made."""
    if isinstance(value, _Pairs):
        return Node(key, "object", parent=parent, format=format, data=value, count=len(value))
    if isinstance(value, dict):
        return Node(key, "object", parent=parent, format=format, data=_Pairs(value.items()), count=len(value))
    if isinstance(value, (list, tuple)):
        return Node(key, "array", parent=parent, format=format, data=value, count=len(value))
    if isinstance(value, bool):
        return Node(key, "bool", "true" if value else "false", parent=parent, format=format)
    if value is None:
        return Node(key, "null", "null", parent=parent, format=format)
    if isinstance(value, (int, float)):
        return Node(key, "number", repr(value) if isinstance(value, float) else str(value),
                    parent=parent, format=format)
    if isinstance(value, (datetime.date, datetime.time)):
        return Node(key, "date", value.isoformat(), parent=parent, format=format)
    if isinstance(value, bytes):
        return Node(key, "string", value.hex(" "), parent=parent, format=format)
    return Node(key, "string", str(value), parent=parent, format=format)


def _python_children(node: Node) -> Iterator[Node]:
    data = node._data
    if node.kind == "object":
        for key, value in data:
            yield _python(key, value, node, node.format)
    else:
        for index, value in enumerate(data):
            yield _python(index, value, node, node.format)


def _python_dump(node: Node) -> str:
    return json.dumps(_plain(node._data), indent=2, ensure_ascii=False, default=str)


def _plain(value: Any) -> Any:
    if isinstance(value, _Pairs):
        return {str(key): _plain(item) for key, item in value}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, bytes):
        return value.hex()
    return value


# YAML: the composer's nodes, which keep their places and their tags.

_YAML_KINDS = {
    "tag:yaml.org,2002:str": "string",
    "tag:yaml.org,2002:int": "number",
    "tag:yaml.org,2002:float": "number",
    "tag:yaml.org,2002:bool": "bool",
    "tag:yaml.org,2002:null": "null",
    "tag:yaml.org,2002:timestamp": "date",
    "tag:yaml.org,2002:binary": "string",
}


class _Documents:
    """Several YAML documents in one file: shown as a list of them."""

    def __init__(self, nodes: list[Any]) -> None:
        self.value = nodes


def _read_yaml(data: bytes) -> Node:
    import yaml

    loader = getattr(yaml, "CSafeLoader", None) or yaml.SafeLoader
    try:
        documents = [document for document in yaml.compose_all(data, Loader=loader) if document is not None]
    except yaml.MarkedYAMLError as error:
        mark = error.problem_mark or error.context_mark
        message = error.problem or error.context or str(error)
        if mark is None:
            raise ParseFailed(message) from None
        raise ParseFailed(message, mark.line + 1, mark.column + 1, _line_offset(data, mark.line + 1)) from None
    except yaml.YAMLError as error:
        raise ParseFailed(str(error)) from None
    starts = _starts(data)
    if len(documents) == 1:
        return _yaml(None, documents[0], None, starts)
    if not documents:
        return Node(None, "null", "null", format="yaml")
    return Node(None, "array", parent=None, offset=0, format="yaml", data=(_Documents(documents), starts),
                count=len(documents))


def _starts(data: bytes) -> list[int]:
    starts = [0]
    at = data.find(b"\n")
    while at >= 0:
        starts.append(at + 1)
        at = data.find(b"\n", at + 1)
    return starts


def _yaml(key: Any, node: Any, parent: Node | None, starts: list[int]) -> Node:
    import yaml

    line = node.start_mark.line if node.start_mark is not None else None
    offset = starts[line] if line is not None and line < len(starts) else None
    if isinstance(node, yaml.MappingNode):
        return Node(key, "object", parent=parent, offset=offset, format="yaml", data=(node, starts),
                    count=len(node.value))
    if isinstance(node, yaml.SequenceNode):
        return Node(key, "array", parent=parent, offset=offset, format="yaml", data=(node, starts),
                    count=len(node.value))
    kind = _YAML_KINDS.get(node.tag, "tagged")
    text = node.value if kind != "tagged" else f"{node.tag} {node.value}"
    return Node(key, kind, text, parent=parent, offset=offset, format="yaml")


def _yaml_key(node: Any) -> str:
    """A mapping's key as shown: a scalar's text, else the key's own YAML."""
    import yaml

    if isinstance(node, yaml.ScalarNode):
        return node.value
    return yaml.serialize(node).strip()


def _yaml_children(node: Node) -> Iterator[Node]:
    held, starts = node._data
    if isinstance(held, _Documents):
        for index, document in enumerate(held.value):
            yield _yaml(index, document, node, starts)
    elif node.kind == "object":
        for key, value in held.value:
            yield _yaml(_yaml_key(key), value, node, starts)
    else:
        for index, value in enumerate(held.value):
            yield _yaml(index, value, node, starts)


def _yaml_dump(node: Node) -> str:
    import yaml

    held, _ = node._data
    if isinstance(held, _Documents):
        return yaml.serialize_all(held.value)
    return yaml.serialize(held)


# XML: elements, their attributes and their text.


def _read_xml(data: bytes) -> Node:
    import xml.etree.ElementTree as ElementTree

    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        line, column = getattr(error, "position", (0, 0))
        message = str(error).split(": line ")[0]
        raise ParseFailed(message, line, column + 1, _line_offset(data, line)) from None
    return _element(root, None)


#: HTML's elements that hold nothing and have no end tag.
_VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
                   "source", "track", "wbr"})

#: The elements a start tag closes while they are the one open, as many as
#: there are: a new ``<li>`` ends the last, a ``<tr>`` the cell and the row
#: before it, a block a paragraph -- what makes unclosed lists, tables and
#: paragraphs come out as a browser builds them.
_BLOCKS = ("address", "article", "aside", "blockquote", "div", "dl", "fieldset", "footer", "form", "h1", "h2",
           "h3", "h4", "h5", "h6", "header", "hr", "main", "nav", "ol", "pre", "section", "table", "ul")
_CLOSED_BY = {"li": {"li"}, "p": {"p"}, "dt": {"dt", "dd"}, "dd": {"dt", "dd"}, "tr": {"tr", "td", "th"},
              "td": {"td", "th"}, "th": {"td", "th"}, "option": {"option"},
              **{block: {"p"} for block in _BLOCKS}}


def _read_html(data: bytes) -> Node:
    """HTML as a browser forgives it, through the standard library's
    ``html.parser``: unclosed ``<li>`` and ``<p>`` closed by the next, empty
    elements (``<br>``) holding nothing, an end tag closing its element
    wherever it is open and ignored where it is not -- the Markup view's
    reading of HTML (:mod:`navigator.lib.viewer.html`), built into elements
    the XML tree shows.  Comments and the doctype are left out.  It never
    refuses a file."""
    import xml.etree.ElementTree as ElementTree
    from html.parser import HTMLParser

    document = ElementTree.Element("#document")
    stack = [document]

    def add_text(text: str) -> None:
        parent = stack[-1]
        if len(parent):
            last = parent[-1]
            last.tail = (last.tail or "") + text
        else:
            parent.text = (parent.text or "") + text

    class Builder(HTMLParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            closes = _CLOSED_BY.get(tag, ())
            while len(stack) > 1 and stack[-1].tag in closes:
                stack.pop()
            element = ElementTree.SubElement(stack[-1], tag, {name: value or "" for name, value in attrs})
            if tag not in _VOID:
                stack.append(element)

        def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            ElementTree.SubElement(stack[-1], tag, {name: value or "" for name, value in attrs})

        def handle_endtag(self, tag: str) -> None:
            for depth in range(len(stack) - 1, 0, -1):
                if stack[depth].tag == tag:
                    del stack[depth:]
                    return

        def handle_data(self, data: str) -> None:
            add_text(data)

    builder = Builder(convert_charrefs=True)
    builder.feed(data.decode("utf-8", errors="replace"))
    builder.close()
    elements = list(document)
    if len(elements) == 1 and not (document.text or "").strip() and not (elements[0].tail or "").strip():
        return _element(elements[0], None)
    return _element(document, None)


def _local(name: str) -> str:
    """A name without its ``{namespace}``: what the file's reader sees."""
    return name.rsplit("}", 1)[-1] if name.startswith("{") else name


def _element(element: Any, parent: Node | None) -> Node:
    count = (len(element.attrib) + (1 if (element.text or "").strip() else 0)
             + sum(1 + (1 if (child.tail or "").strip() else 0) for child in element if isinstance(child.tag, str)))
    return Node(_local(element.tag) if isinstance(element.tag, str) else "?", "element",
                parent=parent, format="xml", data=element, count=count)


def _xml_children(node: Node) -> Iterator[Node]:
    element = node._data
    for name, value in element.attrib.items():
        yield Node(_local(name), "attribute", value, parent=node, format="xml")
    text = (element.text or "").strip()
    if text:
        yield Node("#text", "text", text, parent=node, format="xml")
    for child in element:
        if isinstance(child.tag, str):
            yield _element(child, node)
            tail = (child.tail or "").strip()
            if tail:
                # Mixed content: the text after a child, where it is.
                yield Node("#text", "text", tail, parent=node, format="xml")


def _xml_dump(node: Node) -> str:
    import xml.etree.ElementTree as ElementTree

    return ElementTree.tostring(node._data, encoding="unicode")


_READERS = {"html": _read_html, "json": _read_json, "jsonl": _read_jsonl, "toml": _read_toml, "plist": _read_plist,
            "yaml": _read_yaml, "xml": _read_xml}
_CHILDREN = {"json": _python_children, "toml": _python_children, "plist": _python_children,
             "yaml": _yaml_children, "xml": _xml_children}
_DUMPERS = {"json": _python_dump, "toml": _python_dump, "plist": _python_dump,
            "yaml": _yaml_dump, "xml": _xml_dump}
