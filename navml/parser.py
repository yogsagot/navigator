"""Reading a ``.nml`` document into a node graph.

The first half of the markup toolchain.  This module answers *what does this
document say*; the code generator answers *what Python does it become*, and the
two are kept apart by one rule: **the parser imports nothing the document
names**.  It never resolves a type, never touches a live class and never reads
``navkit.reactive.declarations()``.  So every check here is one a document can
fail on its own -- a malformed line, a reserved word, two ids of one name -- and
every check needing a class object belongs to the generator, which *The cold
build* in ``navml/DESIGN.md`` already requires to import.

That split is what makes this module testable with no widget tree, and it is
also what makes ``imports_of()`` below cheap enough for ``navml build`` to order
a whole directory of documents by their import graph without executing any of
them.

The shape of the language, and the three lexical rules it rests on:

* **Blocks are made by indentation**, with spaces -- a tab is an error rather
  than a width nobody can agree on.  A line ending in ``:`` with nothing after
  it opens a block; everything else is a line of the block it sits in.
* **A logical line continues while a bracket is open**, which is Python's own
  implicit continuation and nothing more.  An indented line under a property or
  a handler is an error, so an indent keeps meaning exactly one thing.
* **``#`` starts a comment when followed by a space, an end of line, or a
  second ``#:``-forming colon.**  Not otherwise, because ``bg: #1e1e2e`` is a
  colour: a ``style:`` block is written in the ``.nss`` value grammar, where
  ``#rrggbb`` is a literal.  A ``#:`` run directly above a declaration is
  captured and handed to the generator, which is how the doc comments
  ``navigator/__main__.py`` writes beside its reactive attributes survive the
  move into markup.

Nothing here holds a class object or a compiled expression: everything to the
right of a ``:`` is kept as source text with the line it came from, because
compiling it is a pass that needs the document's types to be live.
"""

from __future__ import annotations

import ast
import keyword
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

from navkit.stylesheet import PropertySpec, parse_value
from navkit.stylesheet import StylesheetError

from navml.errors import MarkupError

#: Names a document may not declare.  Each already means something in the
#: resolution table the generator compiles expressions against -- ``event`` is
#: every handler's one argument -- so a document allowed to declare one would
#: have it mean two things a few lines apart.  See *Naming rules* in
#: ``navml/DESIGN.md`` for what both ancestors got wrong here.
RESERVED = frozenset({"self", "root", "parent", "event"})

#: Directive keywords with a two-token head: ``property text: ""``.  ``event``
#: is the fourth directive and is not here, because it is the one line in the
#: language that carries no colon at all.
DIRECTIVES = frozenset({"property", "style_property", "alias"})

#: The one block in a document that is not a widget.  Its body is a stylesheet
#: fragment rather than Python, so it is read by different rules.
STYLE = "style"

_HEAD = re.compile(r"(\w+)\s*(?:\(\s*([\w.]+)\s*\))?\s*:\Z")
_NAMES = re.compile(r"[A-Za-z_]\w*\Z")


# -- the node graph ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Import:
    """One line of the import block, and what it binds.

    ``source`` is the line exactly as written, because the generator copies it
    into the generated module verbatim -- navml invents no grammar here, it
    reuses Python's.  ``modules`` is what ``navml build`` orders documents by;
    a relative import keeps its leading dots, so ``from ..widgets.label import
    Label`` is ``"..widgets.label"``.
    """

    source: str
    line: int
    module: str
    names: tuple[str, ...]
    modules: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Property:
    """An ordinary ``name: expression`` line.  The expression is source text."""

    name: str
    expression: str
    line: int
    doc: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Handler:
    """An ``on_*:`` line.  One statement, whose one argument is ``event``."""

    name: str
    body: str
    line: int
    doc: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PropertyDecl:
    """``property console_visible: False`` -- a reactive attribute of its own."""

    name: str
    expression: str
    line: int
    doc: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StylePropertyDecl:
    """``style_property icons: auto | none`` -- what a *sheet* may say.

    The right-hand side is a ``.nss`` value rather than a Python expression, so
    it is kept as the decoded literals: ``default`` is the first alternative
    and ``values`` the whole vocabulary, or ``None`` where only a default was
    given and the type alone narrows it.
    """

    name: str
    default: object
    values: tuple[object, ...] | None
    line: int
    doc: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AliasDecl:
    """``alias title: header.text`` -- exactly one property deep."""

    name: str
    target: str
    attribute: str
    line: int
    doc: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EventDecl:
    """``event ClickEvent`` -- the class, not the handler name."""

    name: str
    line: int
    doc: tuple[str, ...] = ()


#: Everything a root block may declare about the component itself.
Declaration = PropertyDecl | StylePropertyDecl | AliasDecl | EventDecl


@dataclass(frozen=True, slots=True)
class StyleDeclaration:
    """One line of a ``style:`` block, in the ``.nss`` value grammar."""

    name: str
    value: str
    line: int


@dataclass(frozen=True, slots=True)
class StyleBlock:
    """A ``style:`` block, which becomes one ``inline_style`` string."""

    declarations: tuple[StyleDeclaration, ...]
    line: int

    def text(self) -> str:
        """The declarations as the one string ``inline_style`` takes."""
        return "; ".join(f"{d.name}: {d.value}" for d in self.declarations)


@dataclass(frozen=True, slots=True)
class Block:
    """A widget: the root block declares one, every other constructs one.

    ``base`` and ``declarations`` are only ever filled on the root -- a child
    block is an instance of a class that already exists, so it has nothing to
    extend and nowhere to put a descriptor.
    """

    type: str
    line: int
    base: str | None = None
    id: str | None = None
    id_line: int | None = None
    declarations: tuple[Declaration, ...] = ()
    properties: tuple[Property, ...] = ()
    handlers: tuple[Handler, ...] = ()
    style: StyleBlock | None = None
    children: tuple[Block, ...] = ()
    doc: tuple[str, ...] = ()

    def walk(self) -> Iterator[Block]:
        """This block and every block under it, in document order."""
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass(frozen=True, slots=True)
class Document:
    """One ``.nml`` file: an import block and the component it declares."""

    filename: str
    imports: tuple[Import, ...]
    root: Block

    @property
    def bound(self) -> dict[str, str]:
        """Every name the import block binds, mapped to where it came from."""
        return {
            name: line.module for line in self.imports for name in line.names
        }

    def ids(self) -> dict[str, Block]:
        """Every id the document declares, mapped to the block carrying it."""
        return {b.id: b for b in self.root.walk() if b.id is not None}


# -- the scanner ------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Line:
    """One logical line: its text, its indent, and where it started."""

    text: str
    indent: int
    line: int
    doc: tuple[str, ...]


def _code(text: str, depth: int, quote: str | None) -> tuple[str, int, str | None]:
    """*text* with its comment removed, and the bracket/string state after it.

    Walks the line rather than matching it, because the right-hand side of a
    ``:`` is Python and a ``#`` inside a string is not a comment -- neither in
    ``text: "# 1"`` nor in ``f"{d['#']}"``, which this handles by never leaving
    a string until its own quote closes.
    """
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if quote is not None:
            if ch == "\\":
                out.append(text[i : i + 2])
                i += 2
                continue
            if text.startswith(quote, i):
                out.append(quote)
                i += len(quote)
                quote = None
                continue
            out.append(ch)
            i += 1
            continue
        if ch == "#" and (i + 1 == n or text[i + 1] in " \t" or text.startswith("#:", i)):
            break
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch in "\"'":
            quote = ch * 3 if text.startswith(ch * 3, i) else ch
            out.append(quote)
            i += len(quote)
            continue
        out.append(ch)
        i += 1
    return "".join(out), depth, quote


def _logical_lines(text: str, filename: str) -> list[_Line]:
    """Every line worth reading: comments gone, continuations joined."""
    physical = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines: list[_Line] = []
    doc: list[str] = []
    index = 0
    while index < len(physical):
        raw = physical[index]
        start = index + 1
        stripped = raw.strip()
        if not stripped:
            doc.clear()
            index += 1
            continue
        if stripped.startswith("#:"):
            doc.append(stripped[2:].strip())
            index += 1
            continue
        indent = len(raw) - len(raw.lstrip(" \t"))
        if "\t" in raw[:indent]:
            raise MarkupError(
                "a tab in the indentation; blocks are made of spaces, because "
                "a tab is a width nobody agrees on",
                start,
                filename,
            )
        code, depth, quote = _code(raw, 0, None)
        while depth > 0 or (quote is not None and len(quote) == 3):
            index += 1
            if index >= len(physical):
                raise MarkupError(
                    "the line never ends: a bracket or a string is still open "
                    "at the end of the file",
                    start,
                    filename,
                )
            more, depth, quote = _code(physical[index], depth, quote)
            code += " " + more.strip()
        if depth < 0:
            raise MarkupError("a closing bracket with nothing open", start, filename)
        if quote is not None:
            raise MarkupError("a string that never closes", start, filename)
        body = code.strip()
        if not body:
            index += 1
            continue
        lines.append(_Line(body, indent, start, tuple(doc)))
        doc.clear()
        index += 1
    return lines


# -- reading the document ---------------------------------------------------


def _identifier(name: str, what: str, line: int, filename: str) -> str:
    """*name* as a name a generated module can carry, or an error saying why."""
    if not _NAMES.match(name):
        raise MarkupError(
            f"{name!r} cannot be {what}: it is emitted into generated source "
            f"as an attribute name, so it has to be a Python identifier",
            line,
            filename,
        )
    if keyword.iskeyword(name):
        raise MarkupError(f"{name!r} is a Python keyword, so it cannot be {what}",
                          line, filename)
    return name


def _declared(name: str, what: str, line: int, filename: str) -> str:
    """The same, for a name that also has to stay out of the reserved list."""
    _identifier(name, what, line, filename)
    if name in RESERVED:
        raise MarkupError(
            f"{name!r} is reserved and cannot be {what}: it already names "
            f"something in every expression in this document",
            line,
            filename,
        )
    return name


def _expression(source: str, what: str, line: int, filename: str) -> str:
    """*source* as an expression, or an error at the markup line it sits on.

    Syntax is something a document can be wrong about on its own, so it is
    asked here rather than left to the generator: a binding's failure is lazy
    and cached, so a malformed expression left to run time surfaces at the
    first read of the value, arbitrarily far from the line that caused it.
    Nothing is kept -- the tree is thrown away and the text stored, because
    compiling it needs the document's types to be live.
    """
    try:
        ast.parse(source, mode="eval")
    except SyntaxError as error:
        raise MarkupError(
            f"cannot read {what}: {error.msg}", line, filename
        ) from None
    return source


def _statement(source: str, line: int, filename: str) -> str:
    """The same for a handler body, which is one statement and may ``await``.

    Parsed inside an ``async def`` because that is the context it compiles
    into -- and because the count is what "one line" actually means: a body
    joined by semicolons is two statements wearing one line.
    """
    try:
        tree = ast.parse("async def _handler(event):\n " + source)
    except SyntaxError as error:
        raise MarkupError(
            f"cannot read the handler: {error.msg}", line, filename
        ) from None
    if len(tree.body[0].body) != 1:  # type: ignore[attr-defined]
        raise MarkupError(
            "a handler written in markup is one statement: anything longer is "
            "a method in the component's .py half that this line calls",
            line,
            filename,
        )
    return source


def _is_head(text: str) -> bool:
    """Does this line open a block?  It ends with a ``:`` and says no more."""
    return text.endswith(":") and not text[:-1].rstrip().endswith(":")


def _is_import(text: str) -> bool:
    head = text.split(maxsplit=1)[0] if text.split() else ""
    return head in ("import", "from")


def _head(line: _Line, filename: str, *, root: bool) -> tuple[str, str | None]:
    """The type a block head names, and the base if the root declares one."""
    match = _HEAD.match(line.text)
    if match is None:
        raise MarkupError(
            f"cannot read {line.text!r} as a block: a block head is a type "
            f"name, optionally with the base it extends -- 'Panel:' or "
            f"'FramedButton(Button):'",
            line.line,
            filename,
        )
    name, base = match.group(1), match.group(2)
    _identifier(name, "a type name", line.line, filename)
    if base is not None:
        if not root:
            raise MarkupError(
                f"{line.text!r} names a base, and only the root block declares "
                f"one: a child block constructs a type that already exists",
                line.line,
                filename,
            )
        if "." in base:
            raise MarkupError(
                f"a base is a single name, not {base!r}: say where it comes "
                f"from with 'from ... import ...' at the top of the document",
                line.line,
                filename,
            )
        _identifier(base, "a base", line.line, filename)
    return name, base


def _import(line: _Line, filename: str) -> Import:
    """One import line, read with Python's own grammar."""
    try:
        tree = ast.parse(line.text)
    except SyntaxError as error:
        raise MarkupError(
            f"cannot read the import: {error.msg}", line.line, filename
        ) from None
    if len(tree.body) != 1 or not isinstance(
        tree.body[0], (ast.Import, ast.ImportFrom)
    ):
        raise MarkupError(
            "only imports come before the root block", line.line, filename
        )
    node = tree.body[0]
    if isinstance(node, ast.ImportFrom):
        if node.module == "__future__":
            raise MarkupError(
                "a __future__ import is refused: it has to be the first "
                "statement of a module and the generated module writes its own",
                line.line,
                filename,
            )
        if any(alias.name == "*" for alias in node.names):
            raise MarkupError(
                "'import *' is refused: it makes the names this document binds "
                "unknowable, so a block head could no longer be checked",
                line.line,
                filename,
            )
        module = "." * node.level + (node.module or "")
        modules: tuple[str, ...] = (module,)
    else:
        module = ""
        modules = tuple(alias.name for alias in node.names)
    names = tuple(
        alias.asname or alias.name.split(".")[0] for alias in node.names
    )
    for name in names:
        if name in RESERVED:
            raise MarkupError(
                f"{name!r} is reserved and cannot be imported: it would be "
                f"shadowed inside every handler body and nowhere else",
                line.line,
                filename,
            )
    return Import(line.text, line.line, module, names, modules)


def _style_property(
    name: str, source: str, line: int, filename: str
) -> tuple[object, tuple[object, ...] | None]:
    """The right-hand side of ``style_property``: the default, and the rest.

    A ``.nss`` value rather than a Python expression, and the default's own
    form is the type -- which is what :class:`navkit.stylesheet.StyleProperty`
    does with the default it is handed, so this decodes through navkit's own
    reader rather than inventing a second one.  No ``$variable`` is meaningful
    here: there is no sheet loaded when a class body runs.
    """
    alternatives: list[object] = []
    for piece in source.split("|"):
        text = piece.strip()
        if not text:
            raise MarkupError(
                f"an empty alternative in {source!r}", line, filename
            )
        if text.startswith("$"):
            raise MarkupError(
                f"a variable is not meaningful in a style_property: {text} "
                f"could not be resolved until a sheet was loaded, and a class "
                f"body runs before any sheet is",
                line,
                filename,
            )
        try:
            alternatives.append(parse_value(name, text, {}, line, filename))
        except StylesheetError as error:
            raise MarkupError(error.message, line, filename) from None
    default = alternatives[0]
    if len({type(value) for value in alternatives}) > 1:
        raise MarkupError(
            f"the alternatives of {name!r} are not all the same kind of value; "
            f"the default's form is the type and '|' only narrows it",
            line,
            filename,
        )
    values = tuple(alternatives) if len(alternatives) > 1 else None
    try:
        PropertySpec.of(default, values)
    except ValueError as error:
        raise MarkupError(str(error), line, filename) from None
    return default, values


def _leaf(
    line: _Line, filename: str, *, root: bool
) -> tuple[str, object]:
    """One non-block line, as a ``(kind, node)`` pair."""
    text = line.text
    if _is_import(text):
        raise MarkupError(
            "an import comes before the root block, at the left margin",
            line.line,
            filename,
        )
    head, colon, rest = text.partition(":")
    head, rest = head.strip(), rest.strip()
    words = head.split()

    if not colon:
        if words and words[0] == "event":
            if len(words) != 2:
                raise MarkupError(
                    "an event declaration names one class: 'event ClickEvent'",
                    line.line,
                    filename,
                )
            if not root:
                raise _root_only("event", line, filename)
            name = _declared(words[1], "an event", line.line, filename)
            return "declaration", EventDecl(name, line.line, line.doc)
        if words and words[0] in DIRECTIVES:
            raise MarkupError(
                f"a value is required: '{words[0]} {' '.join(words[1:]) or 'name'}"
                f": <value>'",
                line.line,
                filename,
            )
        raise MarkupError(
            f"cannot read {text!r}: a line is 'name: value', a directive, or a "
            f"block head ending in ':'",
            line.line,
            filename,
        )

    if len(words) == 2 and words[0] in DIRECTIVES:
        keyword_, name = words
        if not root:
            raise _root_only(keyword_, line, filename)
        _declared(name, f"a {keyword_.replace('_', ' ')}", line.line, filename)
        if not rest:
            raise MarkupError(
                f"a value is required: '{keyword_} {name}: <value>'",
                line.line,
                filename,
            )
        if keyword_ == "property":
            _expression(rest, f"the value of {name!r}", line.line, filename)
            return "declaration", PropertyDecl(name, rest, line.line, line.doc)
        if keyword_ == "style_property":
            default, values = _style_property(name, rest, line.line, filename)
            return "declaration", StylePropertyDecl(
                name, default, values, line.line, line.doc
            )
        target, dot, attribute = rest.partition(".")
        if not dot or "." in attribute:
            raise MarkupError(
                f"an alias is one property deep: 'alias {name}: <id>.<attribute>'"
                f", never a chain",
                line.line,
                filename,
            )
        _identifier(target.strip(), "an alias target", line.line, filename)
        _identifier(attribute.strip(), "an alias target", line.line, filename)
        if target.strip() in RESERVED:
            raise MarkupError(
                f"an alias names an id declared in this document, not "
                f"{target.strip()!r}: it has no stable meaning from the other "
                f"side of the boundary",
                line.line,
                filename,
            )
        return "declaration", AliasDecl(
            name, target.strip(), attribute.strip(), line.line, line.doc
        )

    if len(words) != 1:
        if words and words[0] == "event":
            raise MarkupError(
                "an event declaration carries no value: markup says what a "
                "component emits, Python says what it emits about",
                line.line,
                filename,
            )
        raise MarkupError(
            f"cannot read {head!r} as a name: a directive is two words and a "
            f"property is one",
            line.line,
            filename,
        )

    name = words[0]
    if not rest:
        raise MarkupError(f"a value is required: '{name}: <value>'",
                          line.line, filename)
    if name == "id":
        if root:
            raise MarkupError(
                "the root block is named 'root' in every expression in this "
                "document, so it takes no id",
                line.line,
                filename,
            )
        return "id", _declared(rest, "an id", line.line, filename)
    _identifier(name, "a property", line.line, filename)
    if name.startswith("on_"):
        _statement(rest, line.line, filename)
        return "handler", Handler(name, rest, line.line, line.doc)
    _expression(rest, f"the value of {name!r}", line.line, filename)
    return "property", Property(name, rest, line.line, line.doc)


def _root_only(directive: str, line: _Line, filename: str) -> MarkupError:
    return MarkupError(
        f"'{directive}' is declared in the root block only: it becomes a "
        f"descriptor on the class this document declares, and every other "
        f"block is an instance of a class that already exists -- give this "
        f"child a document of its own, or declare it in the .py half",
        line.line,
        filename,
    )


def _read_style(lines: Sequence[_Line], index: int, filename: str
                ) -> tuple[StyleBlock, int]:
    """A ``style:`` block: declarations in the ``.nss`` grammar, not Python."""
    head = lines[index]
    index += 1
    declarations: list[StyleDeclaration] = []
    if index < len(lines) and lines[index].indent > head.indent:
        indent = lines[index].indent
        while index < len(lines) and lines[index].indent >= indent:
            line = lines[index]
            if line.indent > indent:
                raise MarkupError(
                    "unexpected indent inside a style block", line.line, filename
                )
            name, colon, value = line.text.partition(":")
            name, value = name.strip(), value.strip()
            if not colon or not value:
                raise MarkupError(
                    f"{line.text!r} is not a declaration; expected "
                    f"'property: value'",
                    line.line,
                    filename,
                )
            if not re.match(r"[A-Za-z_][\w-]*\Z", name):
                raise MarkupError(
                    f"cannot read {name!r} as a property name", line.line, filename
                )
            declarations.append(StyleDeclaration(name, value, line.line))
            index += 1
    if not declarations:
        raise MarkupError("a style block says nothing", head.line, filename)
    return StyleBlock(tuple(declarations), head.line), index


def _read_block(
    lines: Sequence[_Line], index: int, filename: str, *, root: bool
) -> tuple[Block, int]:
    """One block and everything indented under it."""
    head = lines[index]
    type_name, base = _head(head, filename, root=root)
    index += 1
    identifier: str | None = None
    identifier_line: int | None = None
    declarations: list[Declaration] = []
    properties: list[Property] = []
    handlers: list[Handler] = []
    children: list[Block] = []
    style: StyleBlock | None = None
    if index < len(lines) and lines[index].indent > head.indent:
        indent = lines[index].indent
        while index < len(lines) and lines[index].indent >= indent:
            line = lines[index]
            if line.indent > indent:
                raise MarkupError(
                    f"unexpected indent under {head.text!r}", line.line, filename
                )
            if _is_head(line.text):
                if line.text.rstrip(":").strip() == STYLE:
                    if style is not None:
                        raise MarkupError(
                            "a second style block; one widget has one style",
                            line.line,
                            filename,
                        )
                    style, index = _read_style(lines, index, filename)
                else:
                    child, index = _read_block(lines, index, filename, root=False)
                    children.append(child)
                continue
            kind, node = _leaf(line, filename, root=root)
            if index + 1 < len(lines) and lines[index + 1].indent > indent:
                raise _too_long(kind, lines[index + 1], filename)
            if kind == "id":
                if identifier is not None:
                    raise MarkupError(
                        "a second id on one widget; the first would be lost",
                        line.line,
                        filename,
                    )
                identifier = node  # type: ignore[assignment]
                identifier_line = line.line
            elif kind == "declaration":
                declarations.append(node)  # type: ignore[arg-type]
            elif kind == "handler":
                if any(h.name == node.name for h in handlers):  # type: ignore
                    raise MarkupError(
                        f"a second {node.name!r} on one widget; the first "  # type: ignore
                        f"would be lost",
                        line.line,
                        filename,
                    )
                handlers.append(node)  # type: ignore[arg-type]
            else:
                if any(p.name == node.name for p in properties):  # type: ignore
                    raise MarkupError(
                        f"a second {node.name!r} on one widget; the first "  # type: ignore
                        f"would be lost",
                        line.line,
                        filename,
                    )
                properties.append(node)  # type: ignore[arg-type]
            index += 1
    return (
        Block(
            type=type_name,
            line=head.line,
            base=base,
            id=identifier,
            id_line=identifier_line,
            declarations=tuple(declarations),
            properties=tuple(properties),
            handlers=tuple(handlers),
            style=style,
            children=tuple(children),
            doc=head.doc,
        ),
        index,
    )


def _too_long(kind: str, line: _Line, filename: str) -> MarkupError:
    """What an indented line under a leaf means, which is always a mistake."""
    if kind == "handler":
        return MarkupError(
            "a handler written in markup is one line: anything longer is a "
            "method in the component's .py half that this line calls",
            line.line,
            filename,
        )
    return MarkupError(
        "an expression continues only inside brackets, the way Python's does; "
        "an indented line under a property opens nothing",
        line.line,
        filename,
    )


# -- what a whole document has to agree about -------------------------------


def _check_document(document: Document) -> None:
    """The collisions a document can have with itself, and nothing further."""
    filename = document.filename
    root = document.root
    taken: dict[str, int] = {}

    def claim(name: str, line: int, what: str) -> None:
        if name in taken:
            raise MarkupError(
                f"{name!r} is already {'declared' if taken[name] != line else 'used'} "
                f"on line {taken[name]}; {what} and it would both be "
                f"'self.{name}' and one would silently win",
                line,
                filename,
            )
        taken[name] = line

    for declaration in root.declarations:
        if isinstance(declaration, EventDecl):
            continue
        claim(declaration.name, declaration.line, "a declaration")
    for block in root.walk():
        if block.id is not None:
            claim(block.id, block.line, "an id")

    bound = document.bound
    for declaration in root.declarations:
        if isinstance(declaration, EventDecl) and declaration.name in bound:
            raise MarkupError(
                f"{declaration.name!r} is already imported, and a declared "
                f"event becomes a name of the generated module too",
                declaration.line,
                filename,
            )

    ids = document.ids()
    for declaration in root.declarations:
        if isinstance(declaration, AliasDecl) and declaration.target not in ids:
            raise MarkupError(
                f"an alias names an id declared in this document, and "
                f"{declaration.target!r} is not one",
                declaration.line,
                filename,
            )


# -- the way in -------------------------------------------------------------


def parse(text: str, *, filename: str = "<markup>") -> Document:
    """Read one document.  Raises :class:`~navml.errors.MarkupError`."""
    lines = _logical_lines(text, filename)
    index = 0
    imports: list[Import] = []
    while index < len(lines) and lines[index].indent == 0 and _is_import(
        lines[index].text
    ):
        imports.append(_import(lines[index], filename))
        index += 1
    if index >= len(lines):
        raise MarkupError(
            "a document declares one component, and this one declares none",
            lines[-1].line if lines else 1,
            filename,
        )
    if lines[index].indent:
        raise MarkupError(
            "the root block sits at the left margin", lines[index].line, filename
        )
    if not _is_head(lines[index].text):
        raise MarkupError(
            f"cannot read {lines[index].text!r}: a document opens with its "
            f"imports and then the component it declares",
            lines[index].line,
            filename,
        )
    root, index = _read_block(lines, index, filename, root=True)
    if index < len(lines):
        line = lines[index]
        if _is_import(line.text):
            raise MarkupError(
                "an import comes before the root block", line.line, filename
            )
        if line.indent:
            raise MarkupError(
                f"unexpected indent: {line.indent} spaces match no block that "
                f"is open here",
                line.line,
                filename,
            )
        raise MarkupError(
            "a document declares one component, and this is a second",
            line.line,
            filename,
        )
    document = Document(filename, tuple(imports), root)
    _check_document(document)
    return document


def parse_file(path: str | Path) -> Document:
    """Read the document at *path*, named by its file name in every error."""
    path = Path(path)
    return parse(path.read_text(encoding="utf-8"), filename=path.name)


def imports_of(path: str | Path) -> tuple[Import, ...]:
    """The import block of the document at *path*, and nothing else.

    What ``navml build`` orders a directory of documents by: the edges of the
    import graph are readable without executing anything, so a cold build --
    where no component has been generated yet -- can still work out which
    document to compile first.  Reading stops at the root block, so a document
    that does not parse still answers this.
    """
    path = Path(path)
    lines = _logical_lines(path.read_text(encoding="utf-8"), path.name)
    imports: list[Import] = []
    for line in lines:
        if line.indent or not _is_import(line.text):
            break
        imports.append(_import(line, path.name))
    return tuple(imports)
