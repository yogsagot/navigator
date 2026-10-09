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
    "Button": "dialog.button",
    "Calendar": "dialog.date_button",
    "CalendarView": "dialog.date_button",
    "CheckBoxes": "dialog.check_boxes",
    "ChoiceField": "dialog.choice_field",
    "ChoiceLine": "dialog.choice_line",
    "Cluster": "dialog.cluster",
    "ColorDisplay": "dialog.color_selector",
    "ColorSelector": "dialog.color_selector",
    "Control": "dialog.control",
    "DateButton": "dialog.date_button",
    "DateField": "dialog.date_field",
    "Desktop": "desktop",
    "Dialog": "dialog.dialog",
    "DropDown": "dialog.drop_down",
    "DockLayout": "layout.dock_layout",
    "Field": "dialog.field",
    "FileDialog": "dialog.file_dialog",
    "FileInfoPane": "dialog.file_list",
    "FileList": "dialog.file_list",
    "GridLayout": "layout.grid_layout",
    "GroupBox": "dialog.group_box",
    "History": "dialog.history",
    "HorizontalLayout": "layout.horizontal_layout",
    "InputLine": "dialog.input_line",
    "Label": "dialog.label",
    "Layout": "layout.layout",
    "LinearLayout": "layout.layout",
    "ListViewer": "dialog.list_viewer",
    "MaskedField": "dialog.masked_field",
    "MaskedLine": "dialog.masked_line",
    "MenuBar": "menu.menu_bar",
    "MenuBox": "menu.menu_box",
    "MenuItem": "menu.menu_item",
    "MenuLine": "menu.menu_line",
    "Modal": "dialog.modal",
    "OptionItem": "option_strip",
    "OptionStrip": "option_strip",
    "PopupMenu": "menu.popup_menu",
    "ProgressBar": "progress_bar",
    "RadioButtons": "dialog.radio_buttons",
    "ScrollBar": "dialog.scroll_bar",
    "Spacer": "spacer",
    "Spinner": "spinner",
    "StackLayout": "layout.stack_layout",
    "StaticText": "dialog.static_text",
    "SubMenu": "menu.sub_menu",
    "TimeButton": "dialog.time_button",
    "TimeField": "dialog.time_field",
    "TimePicker": "dialog.time_button",
    "Timer": "timer",
    "TreeView": "dialog.tree_view",
    "VerticalLayout": "layout.vertical_layout",
    "Window": "window",
    "WindowList": "window_list",
    "WindowManagerDialog": "window_manager",
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
    from navml.widgets.dialog.button import Button
    from navml.widgets.dialog.check_boxes import CheckBoxes
    from navml.widgets.dialog.cluster import Cluster
    from navml.widgets.dialog.color_selector import ColorDisplay, ColorSelector
    from navml.widgets.dialog.control import Control
    from navml.widgets.desktop import Desktop
    from navml.widgets.dialog.dialog import Dialog
    from navml.widgets.dialog.drop_down import DropDown
    from navml.widgets.layout.dock_layout import DockLayout
    from navml.widgets.dialog.field import Field
    from navml.widgets.dialog.file_dialog import FileDialog
    from navml.widgets.dialog.file_list import FileInfoPane, FileList
    from navml.widgets.dialog.choice_field import ChoiceField
    from navml.widgets.dialog.choice_line import ChoiceLine
    from navml.widgets.dialog.date_button import Calendar, CalendarView, DateButton
    from navml.widgets.dialog.date_field import DateField
    from navml.widgets.dialog.time_button import TimeButton, TimePicker
    from navml.widgets.dialog.time_field import TimeField
    from navml.widgets.dialog.masked_field import MaskedField
    from navml.widgets.dialog.masked_line import MaskedLine
    from navml.widgets.layout.grid_layout import GridLayout
    from navml.widgets.dialog.group_box import GroupBox
    from navml.widgets.dialog.history import History
    from navml.widgets.layout.horizontal_layout import HorizontalLayout
    from navml.widgets.dialog.input_line import InputLine
    from navml.widgets.dialog.label import Label
    from navml.widgets.layout.layout import Layout, LinearLayout
    from navml.widgets.dialog.list_viewer import ListViewer
    from navml.widgets.dialog.tree_view import TreeView
    from navml.widgets.menu.menu_bar import MenuBar
    from navml.widgets.menu.menu_box import MenuBox
    from navml.widgets.menu.menu_item import MenuItem
    from navml.widgets.menu.menu_line import MenuLine
    from navml.widgets.menu.sub_menu import SubMenu
    from navml.widgets.dialog.modal import Modal
    from navml.widgets.menu.popup_menu import PopupMenu
    from navml.widgets.dialog.radio_buttons import RadioButtons
    from navml.widgets.dialog.scroll_bar import ScrollBar
    from navml.widgets.option_strip import OptionItem, OptionStrip
    from navml.widgets.progress_bar import ProgressBar
    from navml.widgets.spacer import Spacer
    from navml.widgets.spinner import Spinner
    from navml.widgets.layout.stack_layout import StackLayout
    from navml.widgets.dialog.static_text import StaticText
    from navml.widgets.timer import Timer
    from navml.widgets.layout.vertical_layout import VerticalLayout
    from navml.widgets.window import Window
    from navml.widgets.window_list import WindowList
    from navml.widgets.window_manager import WindowManagerDialog
