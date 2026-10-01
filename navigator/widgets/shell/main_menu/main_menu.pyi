# navml: generated
"""The merged surface of ``navigator.widgets.shell.main_menu.main_menu``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navigator.commands import About, Calculator, ChangeAttributes, ChangeDirectory, Copy, Delete, DeleteSingle, Edit, InvertSelection, MakeDirectory, MakeLink, NewManager, OpenTreeWindow, QuickSearch, QuickView, Quit, RenameMove, Rescan, SelectGroup, ToggleConsole, ToggleHidden, ToggleShowMode, ToggleTree, UnselectGroup, UserMenu, View, ViewAsHex, ViewAsText
from navml.commands import CascadeWindows, CloseAllWindows, CloseWindow, NextWindow, PreviousWindow, SizeMoveWindow, TileWindows, WindowManager, ZoomWindow
from navml.widgets.menu.menu_bar import MenuBar
from navml.widgets.menu.menu_item import MenuItem
from navml.widgets.menu.menu_line import MenuLine
from navml.widgets.menu.sub_menu import SubMenu


class MainMenu(MenuBar, _Component):
    system: SubMenu
    file: SubMenu
    file_view: SubMenu
    file_edit: SubMenu
    disk: SubMenu
    utilities: SubMenu
    panel: SubMenu
    manager: SubMenu
    options: SubMenu
    options_configuration: SubMenu
    options_file_manager: SubMenu
    options_archives: SubMenu
    window: SubMenu
    def __init__(self, **kwargs: _Any) -> None: ...
