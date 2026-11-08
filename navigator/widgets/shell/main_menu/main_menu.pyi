# navml: generated
"""The merged surface of ``navigator.widgets.shell.main_menu.main_menu``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navigator.commands import AsciiTable, NewView, OpenSmartpad, PrintFile, Quit, Refresh, ScreenGrab, ShowUserScreen, ToggleConsole
from navigator.widgets.manager.commands import RestoreTrash, AlternateEdit, AlternateView, ArchiveFiles, Calculator, ChangeAttributes, ChangeLeft, ChangeRight, Copy, Delete, DeleteSingle, DiffFiles, Edit, EditNamed, ExtractArchive, ExtractTo, ArcTest, OpenArchive, MultiRename, Undo, FindFile, ReplaceInFiles, OpenWith, HideInactive, HideLeft, HideRight, MakeDirectory, MakeLink, EditLinkTarget, LinkAbsolute, LinkRelative, SelectBrokenLinks, SelectBadNames, ShowHardLinks, QuickRename, RenameMove, SwapPanels, ToggleMiller, UserMenu, UuDecode, UuEncode, SplitCombine, CalculateChecksums, VerifyChecksums, EncryptFiles, DecryptFiles, ConvertText, View, ViewAsDataBase, ViewAsHex, ViewAsSpreadsheet, ViewAsText, MountImage, UnmountImage
from navigator.widgets.shell.commands import OpenEdit, OpenView, About, OpenCommandPalette, CloseRootAccess, ToggleRootAccess, ShowBackground, EditLinks, FtpLink, GvfsLink, S3Link, DockerLink, PodmanLink, AdbLink, RcloneLink, DockerShell, PodmanShell, AdbShell, Game, HangUp, NavyLink, Terminal, SetupLink, SmbLink, SaversSetup, CountrySetup, ScreenRest, ToggleTrashCan, OpenTrash, EmptyTrash, ChangeColors, ColumnDefaults, HighlightGroups, EditQuickRun, ExtFileEdit, EditHGL, EditMacros, ExternalViewers, ExternalEditors, LoadColors, StoreColors, LoadDesktop, SaveDesktop, DriveInfoSetup, EditHistory, EnvEdit, ExecuteOsCommand, HistoryList, FuzzyHistory, OpenCalendar, SystemInfo, EditorDefaults, FileManagerDefaults, FileManagerSetup, InterfaceSetup, KeyBindingsSetup, LocalMenuFileEdit, MenuFileEdit, NewManager, OpenTreeWindow, OpenUsageWindow, OpenVolumesWindow, OpenProcessWindow, OpenServiceWindow, OpenMonitorWindow, SetupConfirmation, Settings, StartupSetup, SystemSetup, ViewHistory
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
    file_rename_tools: SubMenu
    file_archive: SubMenu
    file_symlinks: SubMenu
    file_restore_trash: MenuItem
    file_encoding: SubMenu
    file_checksums: SubMenu
    file_encryption: SubMenu
    disk: SubMenu
    utilities: SubMenu
    utilities_link: SubMenu
    utilities_shell: SubMenu
    root_access: MenuItem
    manager: SubMenu
    options: SubMenu
    options_configuration: SubMenu
    options_file_manager: SubMenu
    options_archives: SubMenu
    window: SubMenu
    def __init__(self, **kwargs: _Any) -> None: ...
