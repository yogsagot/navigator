# navml: generated
"""The merged surface of ``navigator.widgets.shell.main_menu.main_menu``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navigator.commands import AsciiTable, OpenSmartpad, PrintFile, Quit, Refresh, ScreenGrab, ShowUserScreen, ToggleConsole
from navigator.widgets.manager.commands import AlternateEdit, AlternateView, Calculator, ChangeAttributes, ChangeLeft, ChangeRight, Copy, Delete, DeleteSingle, Edit, EditNamed, FindFile, HideInactive, HideLeft, HideRight, MakeDirectory, MakeLink, RenameMove, SwapPanels, UserMenu, UuDecode, UuEncode, View, ViewAsHex, ViewAsText
from navigator.widgets.shell.commands import About, ChangeColors, ColumnDefaults, HighlightGroups, EditQuickRun, ExtFileEdit, ExternalViewers, ExternalEditors, LoadColors, StoreColors, LoadDesktop, SaveDesktop, DriveInfoSetup, EditHistory, EnvEdit, ExecuteOsCommand, HistoryList, SystemInfo, EditorDefaults, FileManagerDefaults, FileManagerSetup, InterfaceSetup, LocalMenuFileEdit, MenuFileEdit, NewManager, OpenTreeWindow, SetupConfirmation, StartupSetup, SystemSetup, ViewHistory
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
    manager: SubMenu
    options: SubMenu
    options_configuration: SubMenu
    options_file_manager: SubMenu
    options_archives: SubMenu
    window: SubMenu
    def __init__(self, **kwargs: _Any) -> None: ...
