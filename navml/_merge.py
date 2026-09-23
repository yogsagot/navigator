"""Joining the two halves of a component at import time.

A component is made of a markup half and a hand-written half, and **either may
be absent**.  All three shapes reach the same public module name, so nothing
importing a component can tell which it is looking at:

======================  ==================================  ==================
shape                   files in ``button/``                backs ``button``
======================  ==================================  ==================
Python only             ``button.py``                       nothing here --
                                                            the stock
                                                            ``PathFinder``
markup only             ``button_nml.py`` (+ ``.nml``,      the generated
                        ``.pyi``)                           module, re-homed
both                    ``button.py`` and ``button_nml.py``  ``button.py``,
                                                            with the generated
                                                            class spliced in
======================  ==================================  ==================

**A component is a directory**, and the files above sit in it beside an
``__init__.py`` that re-exports the class -- so ``navml.widgets.button`` is a
package and the component itself is ``navml.widgets.button.button``.  That is
this repository's convention rather than a rule of the language: a flat package
whose modules sit directly in it still works, and the tests build them.

The merge itself is one line -- ``cls.__bases__ = (generated,)`` -- and
everything in this module exists to reach it safely.  See *The two halves of a
component* in ``navml/DESIGN.md`` for why it is a rebase rather than a
namespace merge, and for the measurements behind each check below.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys
from types import ModuleType
from typing import Any, Sequence

#: What a generated module's name ends with.  ``button.nml`` compiles to
#: ``button_nml.py``, and the finder keys on *that* file rather than on the
#: markup: both halves of a component are then ordinary ``.py`` files, which
#: reach a wheel automatically inside a declared package, so the import path
#: never depends on a file a packaging mistake can drop.  The markup ships too,
#: but as source to read and rebuild from rather than as a runtime asset.
GENERATED_SUFFIX = "_nml"

#: The attribute a generated module uses to name the class it declares.  The
#: loader looks this up in the hand-written half rather than deriving a class
#: name from a file name, so there is no ``snake_case``/``CamelCase``
#: convention to get wrong and a handler module may define helpers freely.
COMPONENT_ATTR = "__navml_component__"

#: Packages that may contain components, filled in by :func:`register`.  A
#: *library* is what registers -- ``navml.widgets`` -- and everything below it
#: is covered, because a component is a directory and so lives one package
#: deeper than the library that holds it.
_REGISTERED: set[str] = set()


class ComponentError(ImportError):
    """One half of a component disagrees with the other."""


def register(package: str) -> None:
    """Say that *package* may contain components.

    Called from the package's own ``__init__.py``, which importing anything
    inside it is guaranteed to run first -- so there is no window in which a
    component is importable and the finder is not yet installed.  A ``.pth``
    file would not do: those are executed only by :func:`site.addsitedir`, and
    the ``.deb``/``.rpm`` tree is mounted on ``PYTHONPATH`` rather than being a
    site directory, so it would work for pip and pipx and silently not for the
    native packages.

    **It is the widget library that registers, not each component.**
    ``navml.register("navml.widgets")`` covers ``navml.widgets.button`` and
    everything below it, which is what lets a component directory's
    ``__init__.py`` be a re-export and nothing else -- a component has no
    reason to know it is one, which is the same argument that keeps navml's
    mark off the class.
    """
    _REGISTERED.add(package)
    install()


def _registered(package: str) -> bool:
    """Whether *package* is registered, or sits inside one that is.

    The walk up the dotted name is what a component directory costs: the
    package a component module lives in is the component's own, and the one
    somebody registered is the library above it.  The finder is consulted for
    *every* import in the process, so the loop has to stay cheap -- ``json``
    fails on one set lookup, ``os.path`` on two.
    """
    while package:
        if package in _REGISTERED:
            return True
        package = package.rpartition(".")[0]
    return False


def install() -> None:
    """Put the finder on ``sys.meta_path``, once."""
    if not any(isinstance(finder, ComponentFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, ComponentFinder())


# -- the finder -------------------------------------------------------------


class ComponentFinder(importlib.abc.MetaPathFinder):
    """Claims ``<pkg>.<name>`` when ``<name>_nml.py`` sits beside it."""

    def find_spec(
        self, fullname: str, path: Sequence[str] | None = None, target: Any = None
    ) -> importlib.machinery.ModuleSpec | None:
        package, _, name = fullname.rpartition(".")
        # `path is None' is the cheaper of the two and fails for every
        # top-level import, so it goes first: this runs for every import in
        # the process.
        if path is None or not _registered(package):
            return None
        if name.endswith(GENERATED_SUFFIX):
            # The generated half is an ordinary module and loads as one.
            return None

        generated_file = _beside(path, name + GENERATED_SUFFIX + ".py")
        if generated_file is None:
            # No markup half: this is either an ordinary Python-only component
            # or not a component at all.  Either way it is PathFinder's.
            return None

        generated_name = f"{package}.{name}{GENERATED_SUFFIX}"
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if spec is not None and spec.submodule_search_locations is not None:
            # **A component is a module, never a package.**  Without this, a
            # stale flat `button_nml.py' left beside a `button/' directory --
            # an untracked copy, or a native package upgrade that adds files
            # without removing them -- would make this finder rebase whatever
            # `button/__init__.py' re-exported onto a generated class from
            # before the move.  Declining hands the import back to PathFinder,
            # which turns a silent wrong MRO into an ordinary one.
            return None
        if spec is not None and spec.loader is not None:
            # Both halves.  Delegate to the real source loader and add one
            # line afterwards, so __file__, __spec__, get_source and get_code
            # all keep naming the file a human actually wrote.
            spec.loader = RebaseLoader(spec.loader, generated_name)
            return spec

        # Markup only.  The generated module is the whole component.
        loader = GeneratedLoader(generated_name)
        spec = importlib.util.spec_from_file_location(
            fullname, generated_file, loader=loader
        )
        if spec is not None:
            # The generated module owns that bytecode cache; this one is a
            # view onto it and compiles nothing of its own.
            spec.cached = None
        return spec

    def invalidate_caches(self) -> None:  # pragma: no cover - nothing cached
        pass

    def __repr__(self) -> str:
        return f"<navml component finder for {len(_REGISTERED)} package(s)>"


def _beside(path: Sequence[str], filename: str) -> str | None:
    for entry in path:
        candidate = os.path.join(entry, filename)
        if os.path.isfile(candidate):
            return candidate
    return None


# -- both halves ------------------------------------------------------------


class RebaseLoader(importlib.abc.Loader):
    """The real source loader, plus ``cls.__bases__ = (generated,)``.

    Delegating rather than executing two sources into one namespace is the
    whole point: the module has exactly one source file, so ``__file__``,
    ``__spec__.origin``, ``get_source`` and ``get_code`` are each about one
    file and each true, and :mod:`inspect`, :mod:`runpy`, :mod:`pydoc`,
    :mod:`linecache`, :mod:`pdb` and coverage all keep working.
    """

    def __init__(self, inner: Any, generated_name: str):
        self._inner = inner
        self._generated_name = generated_name

    def __getattr__(self, name: str) -> Any:
        # get_code, get_source, get_filename, is_package, path, ...
        return getattr(self._inner, name)

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType | None:
        return self._inner.create_module(spec)

    def exec_module(self, module: ModuleType) -> None:
        self._inner.exec_module(module)
        generated = importlib.import_module(self._generated_name)
        name = _component_name(generated)
        markup = getattr(generated, name)
        handwritten = getattr(module, name, None)

        where = f"{getattr(module, '__file__', module.__name__)!r} and {generated.__file__!r}"
        if handwritten is None:
            raise ComponentError(
                f"{module.__name__} does not define {name!r}, which its markup "
                f"half declares as the component: {where}"
            )
        if not isinstance(handwritten, type):
            raise ComponentError(
                f"{module.__name__}.{name} is not a class, but its markup half "
                f"declares {name!r} as the component: {where}"
            )
        if handwritten.__bases__ == (markup,):
            return  # already spliced; a reload got here first
        _check_bases(handwritten, markup, where)
        try:
            handwritten.__bases__ = (markup,)
        except TypeError as exc:  # pragma: no cover - the object-base case
            raise ComponentError(
                f"{module.__name__}.{name} cannot be joined to its markup half "
                f"({exc}): a component's hand-written half has to name a widget "
                f"base -- `class {name}({markup.__bases__[0].__name__})' -- and "
                f"not `class {name}:'.  {where}"
            ) from exc

    def __repr__(self) -> str:
        return f"<navml rebase loader onto {self._generated_name}>"


def _check_bases(handwritten: type, markup: type, where: str) -> None:
    """Refuse a hand-written base the markup half does not descend from.

    CPython will not do this for us: assigning ``__bases__`` over an unrelated
    base succeeds and drops it from the MRO without a word, which is the worst
    shape this failure can take.  A loose ancestor is allowed -- ``Widget``
    where the markup says ``Window`` -- because the resulting MRO is identical;
    what is refused is a base that would silently disappear.
    """
    declared = handwritten.__bases__
    name = handwritten.__name__
    if declared == (object,):
        raise ComponentError(
            f"{name} has no widget base, so its markup half cannot be joined "
            f"to it: write `class {name}({markup.__bases__[0].__name__})', the "
            f"same base the markup declares.  {where}"
        )
    if len(declared) != 1:
        raise ComponentError(
            f"{name} declares {len(declared)} bases "
            f"({', '.join(base.__name__ for base in declared)}); a component's "
            f"hand-written half declares exactly one, the same one its markup "
            f"half declares.  {where}"
        )
    if not issubclass(markup, declared[0]):
        raise ComponentError(
            f"{name} declares base {declared[0].__name__!r} but its markup half "
            f"declares {markup.__bases__[0].__name__!r}, which does not descend "
            f"from it -- joining the two would drop {declared[0].__name__!r} "
            f"from the class silently.  {where}"
        )


# -- markup only ------------------------------------------------------------


class GeneratedLoader(importlib.abc.Loader):
    """Publishes a generated module under the component's own name.

    The component exists in one file, so rather than re-executing anything this
    copies the generated module's public names across and re-homes the class
    with ``__module__``.  ``__file__`` points at the generated source, which is
    what keeps :func:`inspect.getsource` working: it resolves a class through
    ``sys.modules[cls.__module__].__file__``, and that now names the file the
    class really lives in.
    """

    def __init__(self, generated_name: str):
        self._generated_name = generated_name

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType | None:
        return None

    def exec_module(self, module: ModuleType) -> None:
        generated = importlib.import_module(self._generated_name)
        name = _component_name(generated)
        exported = getattr(generated, "__all__", None)
        if exported is None:
            exported = [n for n in vars(generated) if not n.startswith("_")]
        for attribute in exported:
            setattr(module, attribute, getattr(generated, attribute))
        setattr(module, "__all__", list(exported))
        module.__doc__ = generated.__doc__
        _rehome(getattr(generated, name), module.__name__)

    def get_source(self, fullname: str) -> str | None:
        """Hand back the generated half's source, for :mod:`linecache`.

        ``__file__`` already names a real path, so this is belt and braces --
        but a loader that can answer is what stops a traceback through a
        markup-only component printing frames with no source line.
        """
        generated = importlib.import_module(self._generated_name)
        loader = getattr(generated, "__loader__", None)
        reader = getattr(loader, "get_source", None)
        return None if reader is None else reader(self._generated_name)

    def __repr__(self) -> str:
        return f"<navml generated loader for {self._generated_name}>"


def _rehome(component: type, module_name: str) -> None:
    """Publish *component* under *module_name*, keeping it sourceable.

    Python 3.13 gave every class a ``__firstlineno__``, and ``inspect`` now
    reads the class body's line from it rather than by scanning the file --
    but ``type.__setattr__`` *deletes* it when ``__module__`` is assigned, on
    the assumption that a re-homed class no longer lives where it was compiled
    (CPython gh-118465).  Here that assumption is wrong: only the name the
    class is published under changes, and ``__file__`` still names the file it
    was compiled from.  So put the line number back, or ``inspect.getsource``
    on a markup-only component raises ``OSError`` on 3.13 and works on 3.12.
    """
    first_line = vars(component).get("__firstlineno__")
    component.__module__ = module_name
    if first_line is not None and "__firstlineno__" not in vars(component):
        component.__firstlineno__ = first_line  # type: ignore[attr-defined]


def _component_name(generated: ModuleType) -> str:
    name = getattr(generated, COMPONENT_ATTR, None)
    if not isinstance(name, str) or not hasattr(generated, name):
        raise ComponentError(
            f"{generated.__name__} declares no {COMPONENT_ATTR}, so nothing "
            f"says which class it generated: {generated.__file__!r}"
        )
    return name
