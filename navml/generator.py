"""Emitting the Python a document becomes.

The second half of the toolchain.  Everything a document can get wrong has been
said by the time this module runs -- :mod:`navml.parser` refused what a document
could fail on its own and :mod:`navml.checks` refused the rest -- so nothing
here validates anything.  It writes.

**The file is written through** :class:`navml.coder.Coder` **rather than built
as a syntax tree and unparsed.**  A tree carries no comments, and comments are
load-bearing here: every emitted line ends in a trailing ``# button.nml:12``,
which is the whole of the source map, and a ``#:`` run above a declaration in
the markup is re-emitted above the declaration in the Python.  ``ast.unparse``
is still what turns a document's expressions into source, one fragment at a
time, through :mod:`navml.expression`; the frame around them is lines.

**The tree is built inline in ``__init__``, and every widget is constructed
before any property is installed.**  Inline because a shared ``_build()`` would
be overridden by a derived component's, so the base's children would never be
built and the derived one's would be built twice.  Construct-first because
:meth:`navkit.widget.Widget.add` lays out and mounts a child the moment it joins
a tree that is already mounted, so a widget can be asked for a value before a
sibling named further down the document exists.

The one thing the emitter decides for itself is the source map, and *Source
mapping* in ``navml/DESIGN.md`` records why it is a comment rather than a
``linecache`` entry under a ``.nml`` filename: ``button_nml.py`` is a real
tracked file, so a traceback names it for free and every tool that reads Python
follows.
"""

from __future__ import annotations

import builtins
from dataclasses import dataclass, field
from typing import Any

from navkit.events import emitted
from navkit.reactive import UNKNOWN

from navml.coder import Coder
from navml.expression import (
    ARGUMENT,
    BIND,
    compile_expression,
    compile_handler,
)
from navml.parser import (
    AliasDecl,
    Block,
    EventDecl,
    PropertyDecl,
    StylePropertyDecl,
)
from navml.resolve import Resolved

#: The first line of every file this module writes, and what ``navml build``
#: looks for before it is willing to overwrite one.
MARKER = "# navml: generated"

#: Where an emitted statement wraps.  The *code* is held to it; the trailing
#: source-map comment is allowed to overhang, because wrapping a line to make
#: room for a comment about it would be the tail wagging the dog.
_WIDTH = 79

#: The indent every statement in the generated ``__init__`` carries, counted in
#: characters, so that the wrap above measures the line as it will be written.
_BODY = 8

_PROSE = """\
#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md."""

_STUBS_PROSE = """\
# One stub per (id, emitted event), each wired in ``__init__``
# below.  They return False, so a component that overrides none
# of them is exactly a component that never mentioned them: the
# event carries on up to whatever the document's own handler
# does with it.  The hand-written half is the *derived* class,
# so its override wins over the stub without either half naming
# the other."""

#: What the generated module imports for itself, by the reason it needs it.
_IMPORTS = {
    "_Any": ("typing", "Any"),
    "_dataclass": ("dataclasses", "dataclass"),
    "_Event": ("navkit.events", "Event"),
    "_StyleProperty": ("navkit.stylesheet", "StyleProperty"),
    "_bind": ("navkit.reactive", "bind"),
    "_reactive": ("navkit.reactive", "reactive"),
    "_Alias": ("navml._alias", "_Alias"),
    "_Component": ("navml.component", "Component"),
}

_BUILTIN_TYPES = (bool, int, float, str, bytes)


@dataclass
class _Line:
    """One emitted statement, the markup line it came from, and its indent.

    *indent* is an offset from whatever block the line is written into, which
    is how a handler body sits inside its own ``async def`` and how a binding
    too long for one line wraps.
    """

    code: str
    line: int | None = None
    indent: int = 0


@dataclass
class _Build:
    """What the walk collects, before anything is written."""

    resolved: Resolved
    needs: set[str] = field(default_factory=lambda: {"_Any", "_Component"})
    events: list[tuple[EventDecl, str]] = field(default_factory=list)
    declarations: list[_Line] = field(default_factory=list)
    ids: list[_Line] = field(default_factory=list)
    stubs: list[tuple[str, str, str, int]] = field(default_factory=list)
    construct: list[_Line] = field(default_factory=list)
    install: list[list[_Line]] = field(default_factory=list)
    counter: int = 0
    locals: dict[int, str] = field(default_factory=dict)

    def needing(self, name: str) -> str:
        self.needs.add(name)
        return name


def generate(resolved: Resolved) -> str:
    """The whole of ``<stem>_nml.py``, as text."""
    build = _Build(resolved)
    _collect(build)
    return _write(build)


# -- the walk ----------------------------------------------------------------


def _collect(build: _Build) -> None:
    resolved = build.resolved
    root = resolved.document.root
    root_install: list[_Line] = []

    for declaration in root.declarations:
        _collect_declaration(build, declaration, root_install)

    _collect_lines(build, root, "self", root_install)
    build.install.append(root_install)

    for block in root.walk():
        if block is root:
            continue
        _collect_child(build, block)


def _collect_child(build: _Build, block: Block) -> None:
    resolved = build.resolved
    owner = _owner(build, block)
    parent = _owner(build, _parent_of(resolved, block))
    cls = resolved.class_of(block)
    build.construct.append(
        _Line(f"{owner} = {block.type}(parent={parent})", block.line)
    )
    if block.id is not None:
        build.ids.append(_Line(f"{block.id}: {block.type}", block.id_line))

    lines: list[_Line] = []
    _collect_lines(build, block, owner, lines)
    if block.id is not None:
        _collect_stubs(build, block, cls, owner, lines)
    build.install.append(lines)


def _collect_lines(
    build: _Build, block: Block, owner: str, lines: list[_Line]
) -> None:
    """The property, style and handler lines of one block."""
    resolved = build.resolved
    for prop in block.properties:
        compiled = compile_expression(
            prop.expression,
            own=resolved.own(block),
            ids=resolved.ids,
            line=prop.line,
            filename=resolved.filename,
        )
        if compiled.rewritten:
            build.needing("_bind")
        lines.extend(
            _assignment(f"{owner}.{prop.name}", compiled, prop.line)
        )
    if block.style is not None:
        lines.append(
            _Line(
                f"{owner}.inline_style = {block.style.text()!r}",
                block.style.line,
            )
        )
    for handler in block.handlers:
        _collect_handler(build, block, owner, handler, lines)


def _assignment(target: str, compiled, line: int) -> list[_Line]:
    """``target = value``, wrapped at the binding's bracket when it is long.

    Wrapping has to be decided here rather than left to a formatter, because
    ``navml build --check`` compares the text: a rule nobody applies twice the
    same way would report drift on every run.
    """
    statement = f"{target} = {compiled.value}"
    if len(statement) + _BODY <= _WIDTH or not compiled.rewritten:
        return [_Line(statement, line)]
    return [
        _Line(f"{target} = {BIND}(", line),
        _Line(f"lambda {ARGUMENT}: {compiled.expression}", indent=1),
        _Line(")"),
    ]


def _collect_handler(
    build: _Build, block: Block, owner: str, handler, lines: list[_Line]
) -> None:
    """A handler is a one-statement ``async def`` closing over its widget.

    Not a lambda, because the commonest body is an assignment and a lambda
    cannot hold one; not a method, because a derived component's would shadow
    its base's by the same naming rule.  The ``return True`` is the generator's:
    a markup handler always consumes.
    """
    resolved = build.resolved
    body = compile_handler(
        handler.body,
        own=resolved.own(block),
        ids=resolved.ids,
        owner=owner,
        line=handler.line,
        filename=resolved.filename,
    )
    name = f"_{handler.name}"
    if lines:
        lines.append(_Line(""))
    lines.append(_Line(f"async def {name}(event):", handler.line))
    lines.append(_Line(body, indent=1))
    lines.append(_Line("return True", indent=1))
    lines.append(_Line(f"{owner}.{handler.name} = {name}"))


def _collect_stubs(
    build: _Build, block: Block, cls: type, owner: str, lines: list[_Line]
) -> None:
    """One handler per event this child declares it emits.

    Bubbling says *a click happened*; it cannot say *which child*.  The
    component never asks -- the name it is called by is the answer, composed
    from the ``id:`` line and the handler navkit derives from the event class.
    An explicit markup line for the same event suppresses the convention,
    because both would assign to the same attribute.
    """
    explicit = {handler.name for handler in block.handlers}
    for event in sorted(emitted(cls), key=lambda e: e.handler):
        if event.handler in explicit:
            continue
        composed = f"on_{block.id}_{event.handler.removeprefix('on_')}"
        build.needing("_Event")
        build.stubs.append(
            (composed, block.id or "", event.handler, block.id_line or block.line)
        )
        lines.append(
            _Line(
                f"{owner}.{event.handler} = self.{composed}",
                block.id_line or block.line,
            )
        )


def _collect_declaration(
    build: _Build, declaration, install: list[_Line]
) -> None:
    """One root-block directive, and where each kind of it lands.

    An ``event`` is the one that does not land in the class body at all: the
    class it declares goes above the component, and only its ``emits`` entry
    joins the body.
    """
    if isinstance(declaration, EventDecl):
        build.needing("_dataclass")
        build.needing("_Event")
        build.events.append((declaration, declaration.name))
        return

    # A ``#:`` run above a declaration in the markup is re-emitted above the
    # declaration in the Python, so the reason a property exists survives.
    build.declarations.extend(_Line(f"#: {line}") for line in declaration.doc)

    if isinstance(declaration, StylePropertyDecl):
        build.needing("_StyleProperty")
        values = (
            ""
            if declaration.values is None
            else f", values={_tuple(declaration.values)}"
        )
        build.declarations.append(
            _Line(
                f"{declaration.name} = _StyleProperty"
                f"({declaration.default!r}{values})",
                declaration.line,
            )
        )
        return

    if isinstance(declaration, AliasDecl):
        build.needing("_Alias")
        annotation = _alias_annotation(build, declaration)
        build.declarations.append(
            _Line(
                f"{declaration.name}{annotation} = "
                f'_Alias("{declaration.target}", "{declaration.attribute}")',
                declaration.line,
            )
        )
        return

    assert isinstance(declaration, PropertyDecl)
    _collect_property(build, declaration, install)


def _collect_property(
    build: _Build, declaration: PropertyDecl, install: list[_Line]
) -> None:
    """Where a ``property`` line lands, which is one of three places.

    A literal is a default.  An expression that reads nothing reactive is a
    ``factory``, so that two instances do not share one mutable value.  An
    expression that reads something is a binding, and a binding belongs to an
    instance -- so the class body gets an empty declaration and ``__init__``
    gets the expression.
    """
    resolved = build.resolved
    root = resolved.document.root
    build.needing("_reactive")
    compiled = compile_expression(
        declaration.expression,
        own=resolved.own(root),
        ids=resolved.ids,
        line=declaration.line,
        filename=resolved.filename,
    )
    if compiled.rewritten:
        build.needing("_bind")
        build.declarations.append(
            _Line(f"{declaration.name} = _reactive()", declaration.line)
        )
        install.append(
            _Line(
                f"self.{declaration.name} = {compiled.binding}",
                declaration.line,
            )
        )
        return
    if compiled.constant:
        annotation = _literal_annotation(declaration.expression)
        build.declarations.append(
            _Line(
                f"{declaration.name}{annotation} = "
                f"_reactive({compiled.expression})",
                declaration.line,
            )
        )
        return
    build.declarations.append(
        _Line(
            f"{declaration.name} = _reactive("
            f"factory=lambda: {compiled.expression})",
            declaration.line,
        )
    )


# -- writing it out ----------------------------------------------------------


def _write(build: _Build) -> str:
    resolved = build.resolved
    document = resolved.document
    root = document.root
    coder = Coder("python")

    coder.add(0, MARKER)
    coder.add(0, f'"""Generated from ``{document.filename}``.')
    coder.new_line()
    coder.add(0, "Do not edit: edit the markup and rerun "
                 "``python -m navml build``.")
    coder.add(0, '"""')
    coder.new_line()
    coder.add(0, "from __future__ import annotations")
    coder.new_line()
    coder.add_formatted(0, _PROSE)
    _write_imports(coder, build)
    coder.new_line()
    coder.add(0, f'__navml_component__ = "{root.type}"')
    coder.new_line()
    coder.add(0, f"__all__ = {_names(build)}")

    for declaration, name in build.events:
        _write_gap(coder)
        coder.add(0, "@_dataclass(frozen=True, slots=True)")
        coder.add(0, f"class {name}(_Event):")
        coder.comment(-1, f"{document.filename}:{declaration.line}", True)
        _write_docstring(
            coder, 1, declaration.doc, f"{name}, raised by this component."
        )

    _write_gap(coder)
    coder.add(0, f"class {root.type}({_bases(resolved)}):")
    if root.doc:
        _write_docstring(coder, 1, root.doc)
        coder.new_line()
    coder.add(1, "#: The document this class was generated from.")
    coder.add(1, f'__navml_source__ = "{document.filename}"')
    if build.events:
        coder.new_line()
        coder.add(1, "#: What this component emits, read through emitted().")
        names = ", ".join(name for _, name in build.events)
        coder.add(1, f"emits = ({names},)")

    if build.declarations:
        coder.new_line()
        _write_lines(coder, build, 1, build.declarations)
    if build.ids:
        coder.new_line()
        coder.add(1, "#: Ids, annotated so the hand-written half completes them.")
        _write_lines(coder, build, 1, build.ids)
    if build.stubs:
        coder.new_line()
        coder.add_formatted(1, _STUBS_PROSE)
        for composed, target, handler, line in build.stubs:
            coder.new_line()
            coder.add(1, f"async def {composed}(self, event: _Event) -> bool:")
            coder.comment(-1, f"{document.filename}:{line}", True)
            coder.add(
                2,
                f'"""``{target}`` raised an event whose handler '
                f'is ``{handler}``."""',
            )
            coder.add(2, "return False")

    coder.new_line()
    coder.add(1, "def __init__(self, **kwargs: _Any) -> None:")
    coder.add(2, "super().__init__(**kwargs)")
    if build.construct:
        _write_lines(coder, build, 2, build.construct)
    for group in build.install:
        if group:
            coder.new_line()
            _write_lines(coder, build, 2, group)
    return coder.render()


def _write_gap(coder: Coder) -> None:
    """Two blank lines, which is what separates two top-level definitions."""
    coder.new_line()
    coder.new_line()


def _write_imports(coder: Coder, build: _Build) -> None:
    """The generator's own imports, then the document's, verbatim."""
    groups: dict[str, list[str]] = {}
    for alias in sorted(build.needs):
        module, name = _IMPORTS[alias]
        groups.setdefault(module, []).append(f"from {module} import {name} as {alias}")
    previous = None
    for module in sorted(groups, key=_import_order):
        group = _import_order(module)[0]
        if previous is not None and group != previous:
            coder.new_line()
        previous = group
        for line in groups[module]:
            coder.add(0, line)
    for line in build.resolved.document.imports:
        coder.add(0, line.source)
        coder.comment(-1, f"{build.resolved.filename}:{line.line}", True)


def _import_order(module: str) -> tuple[int, str]:
    """stdlib, then navkit, then navml -- the order the repository writes."""
    if module.startswith("navml"):
        return (2, module)
    if module.startswith("navkit"):
        return (1, module)
    return (0, module)


def _write_lines(
    coder: Coder, build: _Build, indent: int, lines: list[_Line]
) -> None:
    for entry in lines:
        if not entry.code:
            coder.new_line()
            continue
        coder.add(indent + entry.indent, entry.code)
        if entry.line is not None:
            coder.comment(-1, f"{build.resolved.filename}:{entry.line}", True)


def _write_docstring(
    coder: Coder, indent: int, doc: tuple[str, ...], fallback: str = ""
) -> None:
    """A ``#:`` run above a head, re-emitted as the class's docstring.

    One line stays one line; a run becomes a summary, a blank line and the
    rest, which is the shape every docstring in this repository already has.
    """
    lines = list(doc) or ([fallback] if fallback else [])
    if not lines:
        return
    if len(lines) == 1:
        coder.add(indent, f'"""{lines[0]}"""')
        return
    coder.add(indent, f'"""{lines[0]}')
    if lines[1]:
        coder.new_line()
    for line in lines[1:]:
        if line:
            coder.add(indent, line)
        else:
            coder.new_line()
    coder.add(indent, '"""')


# -- small answers -----------------------------------------------------------


def _bases(resolved: Resolved) -> str:
    """``_Component`` is appended to whatever the document declared.

    Unconditionally, so that a component derived from a *Python-only* widget
    still stops ``Widget.layout`` cascading into the children the markup placed.
    """
    base = resolved.document.root.base
    return "_Component" if base is None else f"{base}, _Component"


def _names(build: _Build) -> str:
    names = [build.resolved.document.root.type]
    names.extend(name for _, name in build.events)
    return "[" + ", ".join(f'"{name}"' for name in names) + "]"


def _tuple(values: tuple[Any, ...]) -> str:
    inner = ", ".join(repr(value) for value in values)
    return f"({inner},)" if len(values) == 1 else f"({inner})"


def _owner(build: _Build, block: Block) -> str:
    """The expression naming *block*'s widget inside the generated ``__init__``.

    An id becomes an attribute of the component; anything else becomes a local
    that dies when the constructor returns, which is all the anonymity rule is.
    """
    if block is build.resolved.document.root:
        return "self"
    if block.id is not None:
        return f"self.{block.id}"
    key = id(block)
    if key not in build.locals:
        build.counter += 1
        build.locals[key] = f"_w{build.counter}"
    return build.locals[key]


def _parent_of(resolved: Resolved, block: Block) -> Block:
    for candidate in resolved.document.root.walk():
        if block in candidate.children:
            return candidate
    raise AssertionError("every block but the root has a parent")


def _literal_annotation(source: str) -> str:
    """``text: str = _reactive("")`` -- the type the literal already is.

    Only for a literal, and only for the handful of builtins whose name is
    always in scope.  A declaration with no annotation is unchecked, which is
    the right default rather than a gap.
    """
    try:
        value = eval(source, {"__builtins__": {}})  # noqa: S307 - a literal
    except Exception:  # pragma: no cover - the parser vetted it
        return ""
    for kind in _BUILTIN_TYPES:
        if type(value) is kind:
            return f": {kind.__name__}"
    return ""


def _alias_annotation(build: _Build, declaration: AliasDecl) -> str:
    """The target's declared type, where the generated module can name it."""
    from navkit.reactive import declarations

    target = build.resolved.ids[declaration.target]
    found = declarations(target).get(declaration.attribute)
    kind = None if found is None else found.type
    if kind is UNKNOWN or kind is None:
        return f": {build.needing('_Any')}"
    name = getattr(kind, "__name__", None)
    if name and getattr(builtins, name, None) is kind:
        return f": {name}"
    if name and build.resolved.namespace.get(name) is kind:
        return f": {name}"
    return f": {build.needing('_Any')}"
