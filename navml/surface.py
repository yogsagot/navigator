"""The surface of a Python-only class split into mixins, as a stub.

A component with markup has its ``.pyi`` (:mod:`navml.stubs`), which flattens
its mixins' methods into the class and declares only the markup base -- so a
mixin can be typed against it, ``if TYPE_CHECKING: from ... import Manager as
_Base``, with no cycle.  A class written in Python alone (``FileEditor``,
``FileViewer``, navkit's ``Application``) has no stub, and a mixin typed
against the class itself is a cycle to a type checker: the class derives from
the mixin, which derives from the class.

So such a class gets ``<stem>_surface.pyi`` beside its module: the class with
its own bases only -- its mixins left out -- and every method and class-level
name of the class and its mixins, read as :mod:`navml.sibling` reads them,
with the attributes their methods assign -- less what a real base declares,
the one thing asked of the imported class.  It is a stub with no module of its own, which a
type checker resolves and nothing imports at run time; its mixins say
``from <module>_surface import <Class> as _Base`` under ``TYPE_CHECKING``.

``python -m navml build`` writes these with the markup's artefacts, and
``--check`` reports one that no longer matches.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from navml.coder import Coder
from navml.generator import MARKER
from navml.sibling import Sibling, SiblingClass
from navml.stubs import _write_method, inherited, write_instance

SUFFIX = "_surface.pyi"


def discover(paths: list[Path]) -> list[tuple[Path, str]]:
    """Every ``(module, class)`` under *paths* that is Python alone and split
    into mixins -- the classes a surface is written for."""
    found: list[tuple[Path, str]] = []
    for entry in paths:
        entry = Path(entry)
        modules = sorted(entry.rglob("*.py")) if entry.is_dir() else [entry]
        for path in modules:
            if (path.name.endswith("_nml.py") or path.with_suffix(".nml").exists()
                    or "__pycache__" in path.parts or not _mentions_mixins(path)):
                continue
            sibling = Sibling.read(path)
            if sibling is None or not sibling.mixins:
                continue
            for name, declared in sibling.classes.items():
                if any(base in sibling.mixins for base in declared.bases):
                    found.append((path, name))
    return found


def _mentions_mixins(path: Path) -> bool:
    """A cheap look before parsing: only a module importing a mixin can be one."""
    text = path.read_text(encoding="utf-8")
    return "class " in text and "import" in text


def surface_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}{SUFFIX}")


def surface(path: Path, name: str, module: str) -> str:
    """The whole of *path*'s ``<stem>_surface.pyi`` for its class *name*;
    *module* is *path*'s dotted name, for what the class's own module defines."""
    sibling = Sibling.read(path)
    assert sibling is not None
    declared = sibling.component(name)
    assert declared is not None
    bases = [base for base in declared.bases if base not in sibling.mixins]

    body = Coder("python")
    for attribute, annotation in declared.annotations.items():
        body.add(1, f"{attribute}: {annotation}")
    for attribute in declared.assigned:
        if attribute not in declared.annotations:
            body.add(1, f"{attribute}: _Any")
    for method in declared.methods.values():
        _write_method(body, method)
    taken = set(declared.methods) | set(declared.annotations) | set(declared.assigned)
    write_instance(body, declared.instance, taken, _inherited(module, name, sibling))
    if not body.render().strip():
        body.add(1, "...")
    # The class's own name in an annotation means the real class, as it does
    # in the source: the surface is only a base to its mixins.
    text = re.sub(rf"\b{name}\b", f"_{name}", body.render())

    coder = Coder("python")
    coder.add(0, MARKER)
    coder.add(0, f'"""The surface of ``{module}.{name}``, its mixins folded in, for them to be typed against."""')
    coder.new_line()
    coder.add(0, "from typing import Any as _Any")
    lines = _imports(sibling, text + " ".join(bases))
    if lines:
        coder.new_line()
        for line in lines:
            coder.add(0, line)
    own = sorted(_defined_in(path, sibling) & _words(text + " " + " ".join(bases)) - {name})
    if own:
        coder.add(0, f"from {module} import {', '.join(own)}")
    if f"_{name}" in _words(text):
        coder.add(0, f"from {module} import {name} as _{name}")
    coder.new_line()
    coder.new_line()
    coder.add(0, f"class {name}({', '.join(bases)}):" if bases else f"class {name}:")
    return coder.render() + text


def _inherited(module: str, name: str, sibling: Sibling) -> set[str]:
    """What the class's real bases define, read off the live class: imported
    here, as the markup's stub resolves what a document names."""
    import importlib

    cls = getattr(importlib.import_module(module), name)
    bases = [base for base in cls.__bases__ if base.__name__ not in sibling.mixins]
    return inherited(*bases)


def _imports(sibling: Sibling, used_in: str) -> list[str]:
    """The import lines binding a name the surface spells -- its own and its
    mixins' (:meth:`Sibling._take_imports` folded them), the mixins left out."""
    used = _words(used_in)
    kept = []
    for line in sibling.import_lines:
        node = ast.parse(line).body[0]
        assert isinstance(node, (ast.Import, ast.ImportFrom))
        node.names = [
            alias for alias in node.names
            if (alias.asname or alias.name.split(".")[0]) in used
            and (alias.asname or alias.name) not in sibling.mixins
        ]
        if node.names:
            kept.append(ast.unparse(node))
    return kept


def _defined_in(path: Path, sibling: Sibling) -> set[str]:
    """What *path* itself defines at module level -- importable from it."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names - set(sibling.sources)


def _words(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", text))
