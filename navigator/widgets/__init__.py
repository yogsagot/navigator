"""The file manager's own widgets.

The screens `python -m navigator` paints, one directory each, moved out of the
entry point so that they can be imported by name.  **That is the point of the
package rather than a side effect of it**: `navigator/__main__.py` is what the
command runs, so it is already in `sys.modules` as `__main__`, and
`from navigator.__main__ import Panel` would import a *second* copy of it --
a second `Panel` class, a second stylesheet, and two of everything the two
copies then disagree about.  A widget a document names has to be importable by
its own name, which is what `navml/DESIGN.md`'s worked example needs before
`manager.nml` can compile.

It is a component package in navml's sense, registered below, though every
widget in it is still Python alone.  Registering now costs nothing -- the
finder looks for a `*_nml.py` beside a module and declines when there is none
-- and it means the first document dropped in here works without anybody
remembering this line.

The re-exports are lazy for the reason `navml/widgets/__init__.py` explains at
length: generating a component imports the classes its document names, so a
package that re-exported eagerly would make importing any one widget import
every widget, and a cold build could generate nothing.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

import navml

navml.register(__name__)

#: Name -> the package in here that publishes it.  Written out rather than
#: discovered, so a typo is an `AttributeError' naming the widget.  Two names
#: map to `panel': its module carries `DirEntry' beside `Panel'.
_WIDGETS = {
    "Console": "console",
    "DirEntry": "panel",
    "KeyBar": "keybar",
    "Manager": "manager",
    "MenuBar": "menubar",
    "Panel": "panel",
}

__all__ = sorted(_WIDGETS)


def __getattr__(name: str) -> Any:
    """Import a widget the first time somebody asks for it (:pep:`562`)."""
    module = _WIDGETS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    widget = getattr(importlib.import_module(f"{__name__}.{module}"), name)
    globals()[name] = widget
    return widget


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


if TYPE_CHECKING:
    # A module `__getattr__' answers `Any' to a type checker, which would make
    # every widget untyped at every call site.  These are the real types.
    from navigator.widgets.console import Console
    from navigator.widgets.keybar import KeyBar
    from navigator.widgets.manager import Manager
    from navigator.widgets.menubar import MenuBar
    from navigator.widgets.panel import DirEntry, Panel
