# navml: generated
"""The merged surface of ``navigator.widgets.shell.main_menu.main_menu``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navigator.commands import AsciiTable, OpenSmartpad, PrintFile, Quit, Refresh, ScreenGrab, ShowUserScreen, ToggleConsole
from navigator.widgets.manager.commands import RestoreTrash, AlternateEdit, AlternateView, ArchiveFiles, Calculator, ChangeAttributes, ChangeLeft, ChangeRight, Copy, Delete, DeleteSingle, DiffFiles, Edit, EditNamed, ExtractArchive, FindFile, OpenWith, HideInactive, HideLeft, HideRight, MakeDirectory, MakeLink, QuickRename, RenameMove, SwapPanels, ToggleMiller, UserMenu, UuDecode, UuEncode, CalculateChecksums, VerifyChecksums, View, ViewAsDataBase, ViewAsHex, ViewAsText
from navigator.widgets.shell.commands import OpenEdit, OpenView, About, CloseRootAccess, EditLinks, FtpLink, GvfsLink, S3Link, Game, HangUp, NavyLink, SetupLink, SmbLink, SaversSetup, CountrySetup, ScreenRest, ToggleTrashCan, OpenTrash, EmptyTrash, ChangeColors, ColumnDefaults, HighlightGroups, EditQuickRun, ExtFileEdit, EditHGL, ExternalViewers, ExternalEditors, LoadColors, StoreColors, LoadDesktop, SaveDesktop, DriveInfoSetup, EditHistory, EnvEdit, ExecuteOsCommand, HistoryList, OpenCalendar, SystemInfo, EditorDefaults, FileManagerDefaults, FileManagerSetup, InterfaceSetup, KeyBindingsSetup, LocalMenuFileEdit, MenuFileEdit, NewManager, OpenTreeWindow, OpenVolumesWindow, SetupConfirmation, Settings, StartupSetup, SystemSetup, ViewHistory
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
    file_restore_trash: MenuItem
    file_checksums: SubMenu
    disk: SubMenu
    utilities: SubMenu
    manager: SubMenu
    options: SubMenu
    options_configuration: SubMenu
    options_file_manager: SubMenu
    options_archives: SubMenu
    window: SubMenu
    def __init__(self, **kwargs: _Any) -> None: ...
