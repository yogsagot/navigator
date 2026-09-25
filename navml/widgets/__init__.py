"""The widget library.

Every directory in here is a component, in one of the three shapes
:mod:`navml._merge` describes -- its files sit inside it and its ``__init__``
re-exports the class.  ``from navml.widgets import Button`` is the ordinary way
in, and it also means the shape a component happens to be written in never
reaches the call site.

**The re-exports are lazy, and that is load-bearing rather than tidy.** The
code generator needs live class objects -- it reads ``declarations(cls)`` off
the classes a document names -- so generating ``button_nml.py`` really does
import ``Label``.  Re-exporting eagerly would mean importing any one component
imported every component, and a cold build could then import nothing until
everything had already been generated.  Doing it through :pep:`562`'s module
``__getattr__`` breaks that, and takes the rest of the library out of the
import path of anything that wanted one widget.

So: **a component package registers itself eagerly and re-exports lazily.**
"""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING, Any

import navml

navml.register(__name__)

#: Component name -> the package in here that publishes it.  Written out
#: rather than discovered, so that a typo is an `AttributeError' naming the
#: component and not a silent miss, and so that the listing survives being
#: read from a zip or a wheel.
_COMPONENTS = {
    "Button": "button",
    "CheckBoxes": "check_boxes",
    "Cluster": "cluster",
    "Control": "control",
    "Desktop": "desktop",
    "Dialog": "dialog",
    "Field": "field",
    "InputLine": "input_line",
    "Label": "label",
    "ListViewer": "list_viewer",
    "Modal": "modal",
    "RadioButtons": "radio_buttons",
    "ScrollBar": "scroll_bar",
    "Spacer": "spacer",
    "StaticText": "static_text",
    "Timer": "timer",
    "Window": "window",
}

__all__ = sorted(_COMPONENTS)


def __getattr__(name: str) -> Any:
    """Import a component the first time somebody asks for it (:pep:`562`).

    The result is cached in this module's globals, so the second access does
    not reach here at all.
    """
    module = _COMPONENTS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    component = getattr(importlib.import_module(f"{__name__}.{module}"), name)
    globals()[name] = component
    return component


def import_all() -> None:
    """Import every component in this package.

    **What a stylesheet needs before it can be parsed.**  A declaration key is
    valid if it names a ``Style`` field or a property some widget declares,
    and a widget declares one by its class body running -- so a sheet naming
    ``marks`` or ``chars`` cannot be read until the class that declares it has
    been imported.  With one such widget an application can import it by hand;
    with a library of them that list is a thing to forget, so this is the one
    call that cannot go stale.

    It gives up the laziness above, deliberately and only for whoever asks:
    the point of the lazy re-export is that *importing a component* does not
    drag in the rest, and this is not that -- it is a caller saying it wants
    all of them.
    """
    for name in __all__:
        getattr(sys.modules[__name__], name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


if TYPE_CHECKING:
    # A module `__getattr__' answers `Any' to a type checker, which would make
    # every component untyped at every call site.  These are the real types;
    # they are never imported at run time, so the laziness above is intact.
    from navml.widgets.button import Button
    from navml.widgets.check_boxes import CheckBoxes
    from navml.widgets.cluster import Cluster
    from navml.widgets.control import Control
    from navml.widgets.desktop import Desktop
    from navml.widgets.dialog import Dialog
    from navml.widgets.field import Field
    from navml.widgets.input_line import InputLine
    from navml.widgets.label import Label
    from navml.widgets.list_viewer import ListViewer
    from navml.widgets.modal import Modal
    from navml.widgets.radio_buttons import RadioButtons
    from navml.widgets.scroll_bar import ScrollBar
    from navml.widgets.spacer import Spacer
    from navml.widgets.static_text import StaticText
    from navml.widgets.timer import Timer
    from navml.widgets.window import Window
