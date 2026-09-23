"""Building a directory of documents, and checking one that was built.

``python -m navml build`` regenerates ``<stem>_nml.py`` and ``<stem>.pyi`` beside
every ``<stem>.nml`` it is pointed at -- *beside* meaning inside the component's
own directory, since a component is one; ``--check`` reports the ones that no
longer match their markup and writes nothing.  It is a user-facing command
rather than only a maintainer's: the markup ships, so somebody who installed
Navigator can edit a component's ``.nml`` in place and rebuild it.

**Documents are compiled in the order their import blocks describe.**  That is
not tidiness either: generation needs live classes, so compiling ``button.nml``
really imports ``Label``, and a cold build -- one where no generated module
exists yet -- can only work from the leaves inward.  The order is readable
without executing anything, because :func:`navml.parser.imports_of` stops at the
root block, and **a cycle between two documents is an error rather than
something to resolve**.

Two things this module refuses to do.  It will not overwrite a file whose first
line is not :data:`navml.generator.MARKER`, because everything it writes it also
owns.  And it never writes a half-built file: each artefact is written beside
its target and moved into place, so an interrupted build leaves the previous one
intact.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from navml.checks import check
from navml.errors import MarkupError
from navml.generator import MARKER, generate
from navml.parser import imports_of, parse_file
from navml.resolve import resolve
from navml.sibling import Sibling
from navml.stubs import stub


@dataclass
class Artefact:
    """One generated file, and what building it would do to it."""

    path: Path
    content: str
    #: The first line at which the file on disk differs, 1-based, or ``None``
    #: when it is already what would be written.
    differs: int | None = None

    @property
    def stale(self) -> bool:
        return self.differs is not None


@dataclass
class BuildReport:
    """What one run did, or would have done."""

    documents: list[Path] = field(default_factory=list)
    written: list[Path] = field(default_factory=list)
    unchanged: list[Path] = field(default_factory=list)
    stale: list[Artefact] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.stale


def build(
    paths: list[str | Path] | None = None, *, check_only: bool = False
) -> BuildReport:
    """Generate (or check) every document under *paths*."""
    documents = order(discover(paths))
    report = BuildReport(documents=list(documents))
    for path in documents:
        for artefact in compile_document(path):
            _apply(artefact, report, check_only)
    return report


def compile_document(path: Path) -> list[Artefact]:
    """The two files *path* becomes, each with its difference from disk."""
    path = Path(path)
    stem = path.stem
    document = parse_file(path)
    sibling = Sibling.read(path.with_suffix(".py"))
    resolved = resolve(document, package=package_of(path), sibling=sibling)
    check(resolved)
    return [
        _artefact(path.with_name(f"{stem}_nml.py"), generate(resolved)),
        _artefact(path.with_name(f"{stem}.pyi"), stub(resolved)),
    ]


# -- finding the documents ---------------------------------------------------


def discover(paths: list[str | Path] | None = None) -> list[Path]:
    """Every ``.nml`` under *paths*, or under the installed package.

    Defaulting to :mod:`navml` itself is what makes the installed-copy workflow
    work: with no argument at all, the command rebuilds the library it is part
    of, wherever that happens to have been installed.
    """
    if not paths:
        paths = [Path(__file__).parent]
    found: list[Path] = []
    for entry in paths:
        entry = Path(entry)
        if entry.is_dir():
            found.extend(sorted(entry.rglob("*.nml")))
        elif entry.suffix == ".nml":
            found.append(entry)
        else:
            raise MarkupError("not a document", 0, str(entry))
    return found


def package_of(path: Path) -> str | None:
    """The dotted package a document's generated module will live in.

    Read off the directories rather than configured, by walking up while an
    ``__init__.py`` is there -- which is the same question the import system
    asks, and the one a relative import in the document is resolved against.
    """
    parts: list[str] = []
    directory = Path(path).resolve().parent
    while (directory / "__init__.py").exists():
        parts.append(directory.name)
        directory = directory.parent
    return ".".join(reversed(parts)) or None


def order(documents: list[Path]) -> list[Path]:
    """*documents*, each after the ones it imports.

    The edges come from the import block alone, which is why
    :func:`~navml.parser.imports_of` exists: reading them costs a parse that
    stops at the root block, and no import at all.
    """
    modules = {name: path for path in documents for name in _names_of(path)}
    edges: dict[Path, set[Path]] = {path: set() for path in documents}
    for path in documents:
        for line in imports_of(path):
            for module in line.modules:
                needed = modules.get(_absolute(module, package_of(path)))
                if needed is not None and needed != path:
                    edges[path].add(needed)

    ordered: list[Path] = []
    remaining = dict(edges)
    while remaining:
        ready = sorted(
            path for path, needs in remaining.items() if not (needs & set(remaining))
        )
        if not ready:
            first = sorted(remaining)[0]
            raise MarkupError(
                "these documents import each other: "
                + ", ".join(sorted(p.name for p in remaining)),
                1,
                first.name,
            )
        for path in ready:
            ordered.append(path)
            del remaining[path]
    return ordered


def _own_directory(package: str | None, stem: str) -> str | None:
    """*package*, when *stem* is the module it publishes under its own name.

    A component is a directory and the files in it repeat its name, so
    ``navml/widgets/button/button.nml`` compiles to
    ``navml.widgets.button.button`` -- while every document that wants it
    writes ``from navml.widgets.button import Button``, because the directory
    is the public name and the module inside it is where the class happens to
    sit.  A flat package answers ``None`` here, which is the whole of why the
    flat layout keeps working.
    """
    if package and package.rpartition(".")[2] == stem:
        return package
    return None


def _names_of(path: Path) -> tuple[str, ...]:
    """Every dotted name another document may import this one by.

    Two of them when a component is a directory, and they are not
    interchangeable: the inner name is where the module really is, the public
    one is what gets written.  Keying on only the first is what made this
    function plural -- the lookup in :func:`order` missed, every edge
    disappeared, and a cold build silently fell back on alphabetical order.
    """
    package = package_of(path)
    inner = f"{package}.{path.stem}" if package else path.stem
    public = _own_directory(package, path.stem)
    return (inner, public) if public else (inner,)


def _absolute(module: str, package: str | None) -> str:
    """A relative import spelled the way the importing document would see it."""
    if not module.startswith("."):
        return module
    depth = len(module) - len(module.lstrip("."))
    parts = (package or "").split(".")
    base = ".".join(parts[: len(parts) - depth + 1])
    tail = module[depth:]
    return f"{base}.{tail}" if tail else base


# -- writing, or not ---------------------------------------------------------


def _artefact(path: Path, content: str) -> Artefact:
    return Artefact(path=path, content=content, differs=_difference(path, content))


def _difference(path: Path, content: str) -> int | None:
    """The first line at which *path* differs from *content*, if it does."""
    if not path.exists():
        return 1
    current = path.read_text(encoding="utf-8")
    if current == content:
        return None
    for number, (was, now) in enumerate(
        zip(current.splitlines(), content.splitlines()), start=1
    ):
        if was != now:
            return number
    return min(len(current.splitlines()), len(content.splitlines())) + 1


def _apply(artefact: Artefact, report: BuildReport, check_only: bool) -> None:
    if not artefact.stale:
        report.unchanged.append(artefact.path)
        return
    if check_only:
        report.stale.append(artefact)
        return
    _write(artefact)
    report.written.append(artefact.path)


def _write(artefact: Artefact) -> None:
    """Replace the file, having first made sure it is ours to replace."""
    path = artefact.path
    if path.exists():
        first = path.read_text(encoding="utf-8").split("\n", 1)[0]
        if first != MARKER:
            raise MarkupError(
                f"{path.name} was not written by navml; it will not be "
                f"overwritten",
                1,
                path.name,
            )
    temporary = path.with_name(path.name + ".navml-new")
    temporary.write_text(artefact.content, encoding="utf-8")
    os.replace(temporary, path)
    _forget(path)


def _forget(path: Path) -> None:
    """Drop a rewritten module, so a later document compiles against it.

    A build runs in one process and a document may import one generated a
    moment ago; without this the second would resolve against whatever was
    imported before the build started.

    **The component's own package goes too.**  A component is a directory
    whose ``__init__`` re-exports the class, so that package holds a binding
    to the very class this write just replaced -- and a later
    ``from navml.widgets.label import Label`` would find the package in
    ``sys.modules``, never re-import, and resolve against the class from
    before the write.  :func:`order` keeps that from reaching a cold build,
    where nothing has been imported yet; what it bites is a second build in
    the same process, which is what a test session does.

    The *library* above it -- ``navml.widgets`` -- is deliberately left alone.
    Its :pep:`562` ``__getattr__`` caches into its own globals and so goes
    stale too, but no build path reads a component through it: every document
    and every generated module names the component's own module.
    """
    importlib.invalidate_caches()
    package = package_of(path)
    stem = path.stem
    base = stem.removesuffix("_nml")
    names = {f"{package}.{stem}", f"{package}.{base}"}
    if (public := _own_directory(package, base)) is not None:
        names.add(public)
    for name in names:
        sys.modules.pop(name, None)
