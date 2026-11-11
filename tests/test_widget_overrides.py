"""No widget reuses one of navkit's ``Widget`` method names with another signature.

Such a method is called by navkit with navkit's arguments, and fails only when
that path runs: ``FindFileDialog.refusal()`` -- its reason for refusing OK --
shadowed ``Widget.refusal(command)``, so Tab in Find File raised a ``TypeError``
from ``enables()``.  This walks every widget class the two libraries define.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from navkit.widget import Widget


def _load_every_widget() -> None:
    for package in ("navml.widgets", "navigator.widgets"):
        module = importlib.import_module(package)
        for info in pkgutil.walk_packages(module.__path__, package + "."):
            importlib.import_module(info.name)


def _subclasses(cls: type) -> set[type]:
    found = set()
    for sub in cls.__subclasses__():
        found.add(sub)
        found |= _subclasses(sub)
    return found


def _positional(function) -> tuple[int, int] | None:
    """How many positional arguments past ``self`` it needs and takes; None for ``*args``."""
    parameters = list(inspect.signature(function).parameters.values())[1:]
    if any(p.kind is p.VAR_POSITIONAL for p in parameters):
        return None
    positional = [p for p in parameters if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    return sum(p.default is p.empty for p in positional), len(positional)


def test_no_widget_method_shadows_navkit_s_with_another_signature():
    _load_every_widget()
    navkit = {name: f for name, f in vars(Widget).items()
              if inspect.isfunction(f) and not name.startswith("__")}
    clashes = []
    for cls in _subclasses(Widget):
        for name, function in vars(cls).items():
            if name not in navkit or not inspect.isfunction(function):
                continue
            base, override = _positional(navkit[name]), _positional(function)
            if base is None or override is None:
                continue
            # The override must accept every call navkit makes: no more required
            # arguments than navkit passes, room for as many as it may pass.
            if override[0] > base[1] or override[1] < base[0]:
                clashes.append(f"{cls.__module__}.{cls.__qualname__}.{name}{inspect.signature(function)}"
                               f" vs Widget.{name}{inspect.signature(navkit[name])}")
    assert clashes == []
