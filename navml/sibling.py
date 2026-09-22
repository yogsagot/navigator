"""Reading the hand-written half without importing it.

Four of the generator's checks are about the ``.py`` beside a document -- that a
composed ``on_<id>_<event>`` names an id the markup still declares, that a
markup handler does not land on a method the class already implements, that a
handler body awaits what is actually ``async def``, and that an event is not
declared in both halves.  All four are answered here, by :func:`ast.parse`, and
**none of them by importing the file**.

That is not thrift.  The generated half has to stay a pure function of the
markup: if it were built from what the ``.py`` happens to contain, deleting a
method would rewrite ``dialog_nml.py`` and ``navml build --check`` would report
drift for an edit made somewhere else entirely.  Parsing lets the *checks* see
that file while the *emitter* never does.  Importing it would also be a cycle --
``dialog.py`` is the module whose class the generated one is about to become the
base of.

What is read is deliberately shallow: module-level classes, their methods and
whether each is ``async def``, the class-body ``name: T = reactive(...)`` lines,
and the ``emits`` tuple.  A name is a name here, never a resolved object, so
everything this module answers is a question about *spelling* -- which is all
the checks that use it ask.
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Method:
    """One ``def`` in a class body, as a stub would write it.

    *signature* is the parameter list with every default already replaced by
    ``...``, which is what a ``.pyi`` spells, and *returns* the return
    annotation as written.  Both are text: this module resolves nothing.
    """

    name: str
    line: int
    is_async: bool
    signature: str = "self"
    returns: str | None = None


@dataclass(frozen=True, slots=True)
class SiblingClass:
    """One module-level class, as far as spelling goes."""

    name: str
    line: int
    #: Each base exactly as written -- ``Widget``, ``navkit.widget.Widget``.
    bases: tuple[str, ...] = ()
    methods: dict[str, Method] = field(default_factory=dict)
    #: ``name: T = reactive(...)`` in the class body, mapped to its line.
    reactive: dict[str, int] = field(default_factory=dict)
    #: Every annotated class-body name, mapped to the annotation as written.
    annotations: dict[str, str] = field(default_factory=dict)
    #: Every class-body name assigned without an annotation.
    assigned: tuple[str, ...] = ()
    #: The names in ``emits = (ClickEvent,)``, as written.
    emits: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Sibling:
    """The hand-written half of a component, read rather than imported."""

    path: Path
    #: Every name the module's import block binds, mapped to its line.
    imports: dict[str, int] = field(default_factory=dict)
    #: The import lines themselves, for a stub that has to resolve what the
    #: hand-written signatures were annotated with.
    import_lines: list[str] = field(default_factory=list)
    classes: dict[str, SiblingClass] = field(default_factory=dict)

    @property
    def filename(self) -> str:
        return self.path.name

    def component(self, name: str) -> SiblingClass | None:
        """The class the generated half will become the base of."""
        return self.classes.get(name)

    @classmethod
    def read(cls, path: str | Path) -> Sibling | None:
        """Read *path*, or ``None`` where there is no hand-written half.

        A component is markup alone, Python alone, or both, so the absence of
        this file is one of the three shapes rather than a failure.  A
        :class:`SyntaxError` is left to propagate naming the ``.py``: it is
        Python's complaint about a Python file, and dressing it as a markup
        error would point at the wrong document.
        """
        path = Path(path)
        if not path.exists():
            return None
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        sibling = cls(path=path)
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    bound = alias.asname or alias.name.split(".")[0]
                    sibling.imports.setdefault(bound, node.lineno)
                if not (
                    isinstance(node, ast.ImportFrom)
                    and node.module == "__future__"
                ):
                    sibling.import_lines.append(ast.unparse(node))
            elif isinstance(node, ast.ClassDef):
                sibling.classes[node.name] = _read_class(node)
        return sibling


def _read_class(node: ast.ClassDef) -> SiblingClass:
    methods: dict[str, Method] = {}
    reactives: dict[str, int] = {}
    annotations: dict[str, str] = {}
    assigned: list[str] = []
    emits: tuple[str, ...] = ()
    for statement in node.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[statement.name] = Method(
                name=statement.name,
                line=statement.lineno,
                is_async=isinstance(statement, ast.AsyncFunctionDef),
                signature=_signature(statement.args),
                returns=(
                    ast.unparse(statement.returns) if statement.returns else None
                ),
            )
            continue
        if isinstance(statement, ast.AnnAssign):
            targets = (
                [statement.target]
                if isinstance(statement.target, ast.Name)
                else []
            )
            for target in targets:
                annotations[target.id] = ast.unparse(statement.annotation)
        elif isinstance(statement, ast.Assign):
            targets = [t for t in statement.targets if isinstance(t, ast.Name)]
            assigned.extend(t.id for t in targets)
        else:
            continue
        emits = _read_emits(targets, statement.value) or emits
        _read_reactive(reactives, targets, statement.value)
    return SiblingClass(
        name=node.name,
        line=node.lineno,
        bases=tuple(ast.unparse(base) for base in node.bases),
        methods=methods,
        reactive=reactives,
        annotations=annotations,
        assigned=tuple(assigned),
        emits=emits,
    )


def _signature(arguments: ast.arguments) -> str:
    """The parameter list as a stub spells it: every default is ``...``.

    A ``.pyi`` records that a parameter *has* a default, never what it is, so
    the values are replaced rather than copied -- which also keeps a default
    that calls something out of a file nothing executes.
    """
    args = copy.deepcopy(arguments)
    args.defaults = [ast.Constant(value=...) for _ in args.defaults]
    args.kw_defaults = [
        None if default is None else ast.Constant(value=...)
        for default in args.kw_defaults
    ]
    # Every default is now ``...``, so the one spelling ``ast.unparse`` gets
    # wrong -- ``text: str=...`` -- can be corrected without touching a value.
    return ast.unparse(ast.fix_missing_locations(args)).replace("=...", " = ...")


def _read_reactive(
    found: dict[str, int], targets: list[ast.Name], value: ast.expr | None
) -> None:
    """Record ``name: T = reactive(...)``, by the spelling of the call."""
    if not isinstance(value, ast.Call):
        return
    called = value.func
    name = called.attr if isinstance(called, ast.Attribute) else getattr(called, "id", "")
    if name != "reactive":
        return
    for target in targets:
        found.setdefault(target.id, value.lineno)


def _read_emits(targets: list[ast.Name], value: ast.expr | None) -> tuple[str, ...]:
    """The names in ``emits = (ClickEvent,)``, or an empty tuple."""
    if not any(target.id == "emits" for target in targets):
        return ()
    if not isinstance(value, (ast.Tuple, ast.List)):
        return ()
    return tuple(ast.unparse(element) for element in value.elts)
