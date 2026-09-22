"""Emitting the ``.pyi`` that stands for both halves of a component.

A stub *replaces* its module for a type checker, so it cannot carry only the
half this toolchain writes: for a markup-only component it is the only thing a
checker ever sees, and for a component with both halves it has to describe the
hand-written members too or they vanish.  So this module writes the union --
the generated surface from the document, and the hand-written surface read out
of the sibling ``.py`` by :mod:`navml.sibling`, which parses it rather than
importing it.

Two consequences are worth knowing rather than discovering.  The first is that
this is why the stub is regenerated whenever the module beside it is: a
component can gain a hand-written half without the ``.nml`` changing at all.
The second is the open question *Still open* in ``navml/DESIGN.md`` records --
because a stub replaces its module, an error planted in ``button.py`` is not
reported even when a checker is pointed straight at it.  That is measured, not
predicted, and it is waiting for the day lint tooling is configured.
"""

from __future__ import annotations

from navkit.reactive import UNKNOWN

from navml.coder import Coder
from navml.generator import MARKER
from navml.parser import AliasDecl, EventDecl, PropertyDecl, StylePropertyDecl
from navml.resolve import Resolved
from navml.sibling import SiblingClass

_ELLIPSIS = "..."


def stub(resolved: Resolved) -> str:
    """The whole of ``<stem>.pyi``, as text."""
    from navml.generator import _Build

    document = resolved.document
    root = document.root
    component = _component(resolved)
    build = _Build(resolved)
    stubs = list(_composed(resolved))
    coder = Coder("python")

    coder.add(0, MARKER)
    coder.add(0, f'"""The merged surface of ``{_module(resolved)}``."""')
    coder.new_line()
    coder.add(0, "from typing import Any as _Any")
    coder.new_line()
    if stubs:
        coder.add(0, "from navkit.events import Event as _Event")
        coder.new_line()
    coder.add(0, "from navml.component import Component as _Component")
    for line in document.imports:
        coder.add(0, line.source)
    if (sibling_imports := _sibling_imports(resolved)):
        coder.new_line()
        for line in sibling_imports:
            coder.add(0, line)

    for name, declared in _sibling_classes(resolved).items():
        coder.new_line()
        coder.new_line()
        bases = ", ".join(declared.bases) or "object"
        coder.add(0, f"class {name}({bases}): {_ELLIPSIS}")

    coder.new_line()
    coder.new_line()
    coder.add(0, f"class {root.type}({_bases(resolved)}):")

    for declaration in root.declarations:
        if isinstance(declaration, EventDecl):
            continue
        coder.add(1, f"{declaration.name}{_annotation(build, declaration)}")
    for block in root.walk():
        if block is not root and block.id is not None:
            coder.add(1, f"{block.id}: {block.type}")
    if component is not None:
        for name, annotation in component.annotations.items():
            coder.add(1, f"{name}: {annotation}")
        for name in component.assigned:
            coder.add(1, f"{name}: _Any")

    written = _write_init(coder, component)
    methods = {} if component is None else component.methods
    for composed in stubs:
        # The hand-written half's override, where there is one: its signature
        # is the truer of the two, and one name may be written only once.
        if composed in methods:
            continue
        written.add(composed)
        coder.add(
            1,
            f"async def {composed}(self, event: _Event) -> bool: {_ELLIPSIS}",
        )
    for name, method in methods.items():
        if name in written:
            continue
        _write_method(coder, method)
    return coder.render()


# -- the pieces --------------------------------------------------------------


def _write_init(coder: Coder, component) -> set[str]:
    """The constructor, which is the hand-written one where there is one."""
    method = component.methods.get("__init__") if component else None
    if method is None:
        coder.add(1, f"def __init__(self, **kwargs: _Any) -> None: {_ELLIPSIS}")
    else:
        _write_method(coder, method)
    return {"__init__"}


def _composed(resolved: Resolved):
    """Every ``on_<id>_<event>`` name the generated half declares.

    They are part of what the module offers whether or not the hand-written
    half overrides them, so a reader can see that the component answers for its
    children by name.
    """
    from navkit.events import emitted

    root = resolved.document.root
    for block in root.walk():
        if block is root or block.id is None:
            continue
        explicit = {handler.name for handler in block.handlers}
        for event in sorted(
            emitted(resolved.class_of(block)), key=lambda e: e.handler
        ):
            if event.handler not in explicit:
                yield f"on_{block.id}_{event.handler.removeprefix('on_')}"


#: Decorators that turn a ``def`` into an attribute.  ``computed`` is navkit's
#: and ``property`` and ``cached_property`` are Python's; all three are read
#: rather than called, so a stub that declared a method would be wrong at every
#: call site.
_ATTRIBUTE_DECORATORS = {"computed", "property", "cached_property"}


def _write_method(coder: Coder, method) -> None:
    for decorator in method.decorators:
        if decorator.rsplit(".", 1)[-1] in _ATTRIBUTE_DECORATORS:
            coder.add(1, f"{method.name}: {method.returns or '_Any'}")
            return
    prefix = "async def" if method.is_async else "def"
    returns = f" -> {method.returns}" if method.returns else ""
    coder.add(
        1, f"{prefix} {method.name}({method.signature}){returns}: {_ELLIPSIS}"
    )


def _annotation(build, declaration) -> str:
    """What a declared name is annotated with in the stub.

    A literal default names its own type; anything else is ``_Any``, which is
    what the generated module leaves unannotated too -- an attribute with no
    declared type is unchecked, and saying so in the stub keeps the two halves
    telling one story.
    """
    from navml.generator import _alias_annotation, _literal_annotation

    if isinstance(declaration, AliasDecl):
        return _alias_annotation(build, declaration)
    if isinstance(declaration, StylePropertyDecl):
        name = type(declaration.default).__name__
        return f": {name}" if name in {"str", "int", "bool", "float"} else ": _Any"
    assert isinstance(declaration, PropertyDecl)
    return _literal_annotation(declaration.expression) or ": _Any"


def _bases(resolved: Resolved) -> str:
    base = resolved.document.root.base
    return "_Component" if base is None else f"{base}, _Component"


def _component(resolved: Resolved) -> SiblingClass | None:
    sibling = resolved.sibling
    if sibling is None:
        return None
    return sibling.component(resolved.document.root.type)


def _sibling_classes(resolved: Resolved) -> dict[str, SiblingClass]:
    """Everything else the hand-written half defines -- its event classes.

    Part of what the public module name offers, so part of what the stub says.
    """
    sibling = resolved.sibling
    if sibling is None:
        return {}
    component = resolved.document.root.type
    return {
        name: declared
        for name, declared in sibling.classes.items()
        if name != component
    }


def _sibling_imports(resolved: Resolved) -> list[str]:
    """The hand-written half's imports, so its annotations resolve.

    Ones the document already made are dropped, since a stub that imported a
    name twice would still be right and would read as though nobody noticed.
    """
    sibling = resolved.sibling
    if sibling is None:
        return []
    already = set(resolved.document.bound)
    lines = []
    for line in sibling.import_lines:
        bound = {
            name
            for name, _ in sibling.imports.items()
            if f" {name}" in line or line.endswith(name)
        }
        if bound and bound <= already:
            continue
        lines.append(line)
    return lines


def _module(resolved: Resolved) -> str:
    stem = resolved.document.filename.removesuffix(".nml")
    return f"{resolved.package}.{stem}" if resolved.package else stem
