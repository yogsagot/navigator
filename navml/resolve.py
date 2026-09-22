"""Turning a document's names into live objects.

The parser imports nothing a document names; this is the module that does, and
it is the only one.  Everything downstream -- the checks, the expression
compiler's ``own`` sets, the emitter -- asks a :class:`Resolved` rather than
reaching for an import of its own, so *generation imports a component's
dependencies exactly once*, and a test can build a :class:`Resolved` by hand and
exercise the emitter with no imports at all.

**Generation is not a static pass over text.**  Compiling ``button.nml`` really
does import ``Label``, because deciding what ``text`` means in
``text: parent.text`` needs ``declarations(Label)``.  Two things follow, and
both are ``navml build``'s to arrange: documents are compiled in the order their
import blocks describe, and a component package must not re-export eagerly.

The import block is executed as written rather than reassembled from its parts.
It is Python, `ast.unparse` round-trips every form of it, and a document that
says ``from ..widgets.label import Label`` means what Python means by that -- so
the lines are compiled and run in a namespace carrying the generated module's
own ``__name__`` and ``__package__``, and a relative import resolves against the
package the document will be generated into.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from navkit.reactive import Declaration, declarations
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

from navml.component import Component
from navml.errors import MarkupError
from navml.parser import Block, Directive, Document
from navml.sibling import Sibling


@dataclass(frozen=True)
class Resolved:
    """A document, and everything about it that needed a live class."""

    document: Document
    #: The package the generated module will live in, or ``None`` when the
    #: document only imports absolute paths.
    package: str | None
    #: Every name the import block bound, plus the builtins Python supplies.
    namespace: dict[str, Any]
    #: What the root block extends: the declared base, or :class:`Component`
    #: when the head is bare.  ``Component`` is appended to it either way.
    base: type
    #: The hand-written half, read but never imported.
    sibling: Sibling | None
    ids: dict[str, type] = field(default_factory=dict)
    #: Root-block declarations, by the name each introduces.
    declared: dict[str, Directive] = field(default_factory=dict)
    _classes: dict[int, type] = field(default_factory=dict)
    _own: dict[int, frozenset[str]] = field(default_factory=dict)

    @property
    def filename(self) -> str:
        return self.document.filename

    def class_of(self, block: Block) -> type:
        """The class *block* constructs, or declares when it is the root."""
        return self._classes[id(block)]

    def own(self, block: Block) -> frozenset[str]:
        """Every attribute an expression inside *block* may name bare.

        For a child block that is what its class declares; for the root it is
        what the base declares plus what the document itself does, since the
        class the document declares does not exist yet.
        """
        return self._own[id(block)]


def resolve(
    document: Document,
    *,
    package: str | None = None,
    sibling: Sibling | None = None,
) -> Resolved:
    """Import what *document* names and answer for it.

    Raises :class:`MarkupError`, naming the ``.nml`` line, for the two failures
    that stop a document being resolved at all: an import that does not import,
    and a type the document names that its imports do not bind.  Everything
    else a document can get wrong is :mod:`navml.checks`'s to say.
    """
    namespace = _namespace(document, package)
    root = document.root
    base = _base(document, namespace)

    resolved = Resolved(
        document=document,
        package=package,
        namespace=namespace,
        base=base,
        sibling=sibling,
        declared={d.name: d for d in root.declarations},
    )
    resolved._classes[id(root)] = base
    resolved._own[id(root)] = frozenset(
        set(attributes(base)) | {d.name for d in root.declarations}
    )
    for block in root.walk():
        if block is root:
            continue
        cls = _type(document, namespace, block)
        resolved._classes[id(block)] = cls
        resolved._own[id(block)] = attributes(cls)
        if block.id is not None:
            resolved.ids[block.id] = cls
    return resolved


def attributes(cls: type) -> frozenset[str]:
    """Every name an expression inside a widget of *cls* may name bare.

    The reactive declarations, and the *style properties* beside them.  A
    :class:`~navkit.stylesheet.StyleProperty` is not a
    :class:`~navkit.reactive.Declaration` -- it is authored in a sheet rather
    than assigned -- so ``declarations()`` never reports ``border`` or
    ``icons``, and a bare ``icons`` in an expression would compile to a module
    global and raise ``NameError`` at the first read.
    """
    found = set(declarations(cls))
    for klass in cls.__mro__:
        found.update(
            name
            for name, value in vars(klass).items()
            if isinstance(value, StyleProperty)
        )
    return frozenset(found)


def declared(cls: type, name: str) -> Declaration | None:
    """The declaration *cls* holds for *name*, if it holds one."""
    return declarations(cls).get(name)


def style_property(cls: type, name: str) -> StyleProperty | None:
    """The style property *cls* declares under *name*, if it declares one."""
    for klass in cls.__mro__:
        value = vars(klass).get(name)
        if isinstance(value, StyleProperty):
            return value
    return None


# -- the two failures that stop resolution -----------------------------------


def _namespace(document: Document, package: str | None) -> dict[str, Any]:
    """Run the import block, in the generated module's own terms."""
    stem = document.filename.removesuffix(".nml")
    namespace: dict[str, Any] = {
        "__name__": f"{package}.{stem}_nml" if package else f"{stem}_nml",
        "__package__": package,
    }
    for line in document.imports:
        try:
            exec(  # noqa: S102 - the line is Python, and says so
                compile(line.source, document.filename, "exec"), namespace
            )
        except Exception as error:
            raise MarkupError(
                f"{line.source}: {error}", line.line, document.filename
            ) from error
    return namespace


def _base(document: Document, namespace: Mapping[str, Any]) -> type:
    """What the root block extends.

    A bare head asks for :class:`~navml.component.Component`, which the
    generator appends to every class it writes in any case -- so a document that
    names ``Component`` as its base is refused rather than compiled into
    ``class X(Component, _Component)``, which is a duplicate base.
    """
    root = document.root
    if root.base is None:
        return Component
    base = _lookup(document, namespace, root.base, root.line)
    if base is Component:
        return _refuse(
            document,
            root.line,
            f"{root.base} is the base every generated class already has; "
            f"write a bare {root.type}: instead",
        )
    return base


def _type(
    document: Document, namespace: Mapping[str, Any], block: Block
) -> type:
    return _lookup(document, namespace, block.type, block.line)


def _lookup(
    document: Document, namespace: Mapping[str, Any], name: str, line: int
) -> type:
    """*name* as a widget class, or a failure naming the markup line.

    Checked here rather than left to run time because the alternative is a
    ``NameError`` raised out of a lazy, failure-caching binding, arbitrarily far
    from the line that caused it.
    """
    if name not in namespace:
        known = ", ".join(sorted(document.bound)) or "nothing"
        return _refuse(
            document,
            line,
            f"{name} is not imported; this document imports {known}",
        )
    found = namespace[name]
    if not isinstance(found, type) or not issubclass(found, Widget):
        return _refuse(document, line, f"{name} is not a widget class")
    return found


def _refuse(document: Document, line: int, message: str) -> Any:
    raise MarkupError(message, line, document.filename)
