"""Joining the two halves of a component at import time.

A component is made of a markup half and a hand-written half, and **either may
be absent**.  All three shapes reach the same public module name, so nothing
importing a component can tell which it is looking at:

======================  ==================================  ==================
shape                   files                               backs ``button``
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

#: Packages that may contain components, filled in by :func:`register`.  The
#: finder sits on ``sys.meta_path`` and is therefore consulted for *every*
#: import in the process, so its first act is a set lookup that fails.
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
    """
    _REGISTERED.add(package)
    install()


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
        if package not in _REGISTERED or path is None:
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
        getattr(generated, name).__module__ = module.__name__

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


def _component_name(generated: ModuleType) -> str:
    name = getattr(generated, COMPONENT_ATTR, None)
    if not isinstance(name, str) or not hasattr(generated, name):
        raise ComponentError(
            f"{generated.__name__} declares no {COMPONENT_ATTR}, so nothing "
            f"says which class it generated: {generated.__file__!r}"
        )
    return name
