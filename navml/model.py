"""Model documents: a ``.nml`` whose root is a table rather than a widget.

A document whose root block declares ``field`` lines is a *model*.  Its root
extends :class:`navkit.database.Model`, and instead of children it says what
one row of a table holds::

    from navkit.database import Model

    #: One remembered input-line string.
    HistoryEntry(Model):
        table: "history"
        field list_id: str
        field text: str
        field pinned: bool = False
        unique entry: list_id, text

This module is the whole toolchain for one, beside the widget one rather than
woven through it, because almost nothing carries over: there is no tree to
construct, no expression to bind and no handler to wire.  What does carry over
is everything around the class -- the import block executed by
:func:`navml.resolve._namespace`, the hand-written half read by
:mod:`navml.sibling` and joined by :mod:`navml._merge`, the ``# file.nml:12``
source map, and ``navml build --check``.

**The build computes the schema; the run time only compares it.**  The
generated class carries its fields, the statements that make its table
(:func:`navkit.database.ddl_for`) and their fingerprint
(:func:`navkit.database.fingerprint`), so opening a database never derives
anything -- and a field changed in markup shows up in ``--check`` as a stale
``__schema__``.
"""

from __future__ import annotations

import ast
import builtins
from dataclasses import dataclass
from typing import Any

from navkit.database import (
    CODECS,
    DatabaseError,
    Field,
    Index,
    Model,
    ddl_for,
    fingerprint,
    zero_of,
)

from navml.coder import Coder
from navml.errors import MarkupError
from navml.parser import Document, FieldDecl, IndexDecl
from navml.resolve import _namespace
from navml.sibling import Sibling

#: The root-block properties a model document may set, and nothing else.
_PROPERTIES = frozenset({"table", "dropped"})

_ELLIPSIS = "..."


def is_model(document: Document) -> bool:
    """Whether *document* declares a table: its root has a ``field`` line."""
    return any(isinstance(d, FieldDecl) for d in document.root.declarations)


@dataclass(frozen=True)
class ResolvedModel:
    """A model document, its names made live and everything checked."""

    document: Document
    package: str | None
    namespace: dict[str, Any]
    sibling: Sibling | None
    table: str
    fields: tuple[Field, ...]
    indexes: tuple[Index, ...]
    dropped: tuple[str, ...]
    ddl: tuple[str, ...]
    schema: str

    @property
    def filename(self) -> str:
        return self.document.filename


def resolve_model(
    document: Document,
    *,
    package: str | None = None,
    sibling: Sibling | None = None,
) -> ResolvedModel:
    """Import what *document* names, refuse what it gets wrong, compute its DDL."""
    filename = document.filename
    root = document.root
    namespace = _namespace(document, package)

    def refuse(line: int, message: str) -> Any:
        raise MarkupError(message, line, filename)

    if root.base is None:
        refuse(root.line, f"a model extends Model: write '{root.type}(Model):'")
    base = namespace.get(root.base)
    if base is None:
        refuse(root.line, f"{root.base} is not imported")
    if not (isinstance(base, type) and issubclass(base, Model)):
        refuse(
            root.line,
            f"{root.base} is not a navkit.database.Model, and a document that "
            f"declares fields declares a table",
        )
    if base is not Model and base.__fields__:
        refuse(root.line, f"{root.base} already has a table; a model has one")
    for block in root.children:
        refuse(block.line, "a model has fields, not children")
    for handler in root.handlers:
        refuse(handler.line, "a model has no handlers; methods go in its .py half")
    if root.style is not None:
        refuse(root.style.line, "a model paints nothing, so it has no style")
    if root.keys is not None:
        refuse(root.keys.line, "a model binds no keys")
    for declaration in root.declarations:
        if not isinstance(declaration, (FieldDecl, IndexDecl)):
            refuse(
                declaration.line,
                "a model declares fields and indexes; anything else belongs "
                "to a widget",
            )

    properties = {prop.name: prop for prop in root.properties}
    for prop in root.properties:
        if prop.name not in _PROPERTIES:
            refuse(
                prop.line,
                f"a model says {', '.join(sorted(_PROPERTIES))}, not {prop.name!r}",
            )
    table = _snake(root.type)
    if "table" in properties:
        prop = properties["table"]
        table = _literal(prop.expression, prop.line, filename)
        if not isinstance(table, str) or not table.isidentifier():
            refuse(prop.line, "table is a string naming the table: table: \"history\"")
        if table.startswith("_navml"):
            refuse(prop.line, "a table named _navml... is navml's own")
    dropped: tuple[str, ...] = ()
    if "dropped" in properties:
        prop = properties["dropped"]
        value = _literal(prop.expression, prop.line, filename)
        value = (value,) if isinstance(value, str) else value
        if not (isinstance(value, tuple) and all(isinstance(v, str) for v in value)):
            refuse(prop.line, 'dropped names columns as strings: dropped: "old", "older"')
        dropped = value

    fields: list[Field] = []
    for declaration in root.declarations:
        if isinstance(declaration, FieldDecl):
            fields.append(_field(declaration, namespace, filename))
    names = {field.name for field in fields}
    if "id" in names:
        refuse(
            next(d.line for d in root.declarations if d.name == "id"),
            "every table has an 'id' key already; a model does not declare it",
        )
    for name in dropped:
        if name in names:
            refuse(properties["dropped"].line, f"{name!r} is dropped and declared")

    indexes: list[Index] = []
    for declaration in root.declarations:
        if isinstance(declaration, IndexDecl):
            for column in declaration.columns:
                if column not in names and column != "id":
                    refuse(
                        declaration.line,
                        f"{declaration.name} covers {column!r}, which is not a field",
                    )
            indexes.append(
                Index(declaration.name, declaration.columns, declaration.unique)
            )

    ddl = ddl_for(table, fields, indexes)
    return ResolvedModel(
        document=document,
        package=package,
        namespace=namespace,
        sibling=sibling,
        table=table,
        fields=tuple(fields),
        indexes=tuple(indexes),
        dropped=dropped,
        ddl=ddl,
        schema=fingerprint(ddl, dropped),
    )


def _field(declaration: FieldDecl, namespace: dict[str, Any], filename: str) -> Field:
    """A ``field`` line as the :class:`~navkit.database.Field` it declares."""
    line = declaration.line
    kind = namespace.get(declaration.type, getattr(builtins, declaration.type, None))
    if kind is None:
        raise MarkupError(f"{declaration.type} is not imported", line, filename)
    if kind not in CODECS:
        known = ", ".join(sorted(k.__name__ for k in CODECS))
        raise MarkupError(
            f"a field holds one of {known}, not {declaration.type}", line, filename
        )
    if declaration.default is None:
        if declaration.null:
            default = None
        else:
            try:
                default = zero_of(kind)
            except DatabaseError:
                raise MarkupError(
                    f"{declaration.name} needs a default: a {kind.__name__} has "
                    f"no empty value, so write '{declaration.type} | None'",
                    line,
                    filename,
                ) from None
    else:
        default = _literal(declaration.default, line, filename)
        if default is None and not declaration.null:
            raise MarkupError(
                f"{declaration.name} defaults to None, so its type is "
                f"'{declaration.type} | None'",
                line,
                filename,
            )
        if default is not None and not _holds(kind, default):
            raise MarkupError(
                f"{declaration.default} is not a {kind.__name__}", line, filename
            )
    return Field(declaration.name, kind, default, declaration.null)


def _holds(kind: type, value: Any) -> bool:
    if kind is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, kind)


def _literal(source: str, line: int, filename: str) -> Any:
    try:
        return ast.literal_eval(source)
    except (ValueError, SyntaxError):
        raise MarkupError(f"{source!r} is not a literal", line, filename) from None


def _snake(name: str) -> str:
    """``HistoryEntry`` -> ``history_entry``: the table a model is named for."""
    out: list[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index and not name[index - 1].isupper():
            out.append("_")
        out.append(char.lower())
    return "".join(out)


# -- what it becomes ------------------------------------------------------------


def generate_model(resolved: ResolvedModel) -> str:
    """The whole of ``<stem>_nml.py`` for a model document."""
    from navml.generator import MARKER, _import_order, _write_docstring

    document = resolved.document
    root = document.root
    filename = resolved.filename
    coder = Coder("python")

    coder.add(0, MARKER)
    coder.add(0, f'"""Generated from ``{filename}``.')
    coder.new_line()
    coder.add(0, "Do not edit: edit the markup and rerun ``python -m navml build``.")
    coder.add(0, '"""')
    coder.new_line()
    coder.add(0, "from __future__ import annotations")
    coder.new_line()
    coder.add(0, "from navkit.database import Field as _Field")
    if resolved.indexes:
        coder.add(0, "from navkit.database import Index as _Index")
    for line in sorted(document.imports, key=lambda i: _import_order(i.module)):
        coder.add(0, line.source)
        coder.comment(-1, f"{filename}:{line.line}", True)
    coder.new_line()
    coder.add(0, f'__navml_component__ = "{root.type}"')
    coder.new_line()
    coder.add(0, f'__all__ = ["{root.type}"]')
    coder.new_line()
    coder.new_line()
    coder.add(0, f"class {root.type}({root.base}):")
    coder.comment(-1, f"{filename}:{root.line}", True)
    if root.doc:
        _write_docstring(coder, 1, root.doc)
        coder.new_line()
    coder.add(1, "#: The document this class was generated from.")
    coder.add(1, f'__navml_source__ = "{filename}"')
    coder.add(1, f'__table__ = "{resolved.table}"')

    declarations = [
        d for d in root.declarations if isinstance(d, (FieldDecl, IndexDecl))
    ]
    coder.add(1, "__fields__ = (")
    for field, declaration in zip(
        resolved.fields, [d for d in declarations if isinstance(d, FieldDecl)]
    ):
        null = ", null=True" if field.null else ""
        coder.add(
            2, f'_Field("{field.name}", {declaration.type}, {field.default!r}{null}),'
        )
        coder.comment(-1, f"{filename}:{declaration.line}", True)
    coder.add(1, ")")
    if resolved.indexes:
        coder.add(1, "__indexes__ = (")
        for index, declaration in zip(
            resolved.indexes, [d for d in declarations if isinstance(d, IndexDecl)]
        ):
            unique = ", unique=True" if index.unique else ""
            coder.add(2, f'_Index("{index.name}", {index.columns!r}{unique}),')
            coder.comment(-1, f"{filename}:{declaration.line}", True)
        coder.add(1, ")")
    if resolved.dropped:
        coder.add(1, f"__dropped__ = {resolved.dropped!r}")
    coder.new_line()
    coder.add(1, "#: What the table is made from, and the fingerprint _navml_schema")
    coder.add(1, "#: keeps of it: a database whose row matches is never examined.")
    coder.add(1, "__ddl__ = (")
    for statement in resolved.ddl:
        coder.add(2, f"{statement!r},")
    coder.add(1, ")")
    coder.add(1, f'__schema__ = "{resolved.schema}"')

    coder.new_line()
    coder.add(1, "id: int | None")
    for field, declaration in zip(
        resolved.fields, [d for d in declarations if isinstance(d, FieldDecl)]
    ):
        if declaration.doc:
            coder.new_line()
            for line in declaration.doc:
                coder.add(1, f"#: {line}")
        coder.add(1, f"{field.name}: {_annotation(declaration)}")
        coder.comment(-1, f"{filename}:{declaration.line}", True)
    return coder.render()


def stub_model(resolved: ResolvedModel) -> str:
    """The ``.pyi`` for a model: its fields, the class API typed, the ``.py`` half."""
    from navml.generator import MARKER

    document = resolved.document
    root = document.root
    name = root.type
    sibling = resolved.sibling
    component = sibling.component(name) if sibling is not None else None
    coder = Coder("python")

    coder.add(0, MARKER)
    module = document.filename.removesuffix(".nml")
    if resolved.package:
        module = f"{resolved.package}.{module}"
    coder.add(0, f'"""The merged surface of ``{module}``."""')
    coder.new_line()
    coder.add(0, "from typing import Any as _Any")
    coder.new_line()
    coder.add(0, "from navkit.database import Query as _Query")
    for line in document.imports:
        coder.add(0, line.source)
    if sibling is not None:
        already = set(document.bound)
        extra = [
            line for line in sibling.import_lines
            if not any(line.endswith(f" {bound}") for bound in already)
        ]
        if extra:
            coder.new_line()
            for line in extra:
                coder.add(0, line)
        for other, declared in sibling.classes.items():
            if other == name:
                continue
            coder.new_line()
            coder.new_line()
            bases = ", ".join(declared.bases) or "object"
            coder.add(0, f"class {other}({bases}): {_ELLIPSIS}")

    fields = [d for d in root.declarations if isinstance(d, FieldDecl)]
    coder.new_line()
    coder.new_line()
    coder.add(0, f"class {name}({root.base}):")
    coder.add(1, "id: int | None")
    for declaration in fields:
        coder.add(1, f"{declaration.name}: {_annotation(declaration)}")
    if component is not None:
        for attribute, annotation in component.annotations.items():
            coder.add(1, f"{attribute}: {annotation}")
        for attribute in component.assigned:
            coder.add(1, f"{attribute}: _Any")

    keywords = ", ".join(
        f"{d.name}: {_annotation(d)} = {_ELLIPSIS}" for d in fields
    )
    methods = {} if component is None else dict(component.methods)
    generated = {
        "__init__": f"def __init__(self, *, id: int | None = {_ELLIPSIS}, "
                    f"{keywords}) -> None: {_ELLIPSIS}",
        "where": f"def where(cls, **conditions: _Any) -> _Query[{name}]: {_ELLIPSIS}",
        "query": f"def query(cls) -> _Query[{name}]: {_ELLIPSIS}",
        "all": f"def all(cls) -> list[{name}]: {_ELLIPSIS}",
        "get": f"def get(cls, **conditions: _Any) -> {name} | None: {_ELLIPSIS}",
        "count": f"def count(cls, **conditions: _Any) -> int: {_ELLIPSIS}",
        "delete_where": f"def delete_where(cls, **conditions: _Any) -> int: {_ELLIPSIS}",
        "create": f"def create(cls, *, {keywords}) -> {name}: {_ELLIPSIS}",
        "upsert": f"def upsert(cls, *, {keywords}) -> {name}: {_ELLIPSIS}",
    }
    for method, text in generated.items():
        if method in methods:
            _write_method(coder, methods.pop(method))
            continue
        if method != "__init__":
            coder.add(1, "@classmethod")
        coder.add(1, text)
    for method in methods.values():
        _write_method(coder, method)
    return coder.render()


def _write_method(coder: Coder, method) -> None:
    """A hand-written method, keeping ``classmethod`` and ``staticmethod``."""
    from navml.stubs import _write_method as write

    for decorator in method.decorators:
        if decorator.rsplit(".", 1)[-1] in ("classmethod", "staticmethod"):
            coder.add(1, f"@{decorator}")
    write(coder, method)


def _annotation(declaration: FieldDecl) -> str:
    return f"{declaration.type} | None" if declaration.null else declaration.type
