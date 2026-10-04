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

The screens come in groups, by the rule *Components come in groups* in
`navml/DESIGN.md` sets for the library: `shell/` (the root and what stands
around the windows), `manager/` (the file manager and its panels),
`file_ops/` (copy, move, link, mkdir and erase), `tree/`, `viewer/`,
`editor/` and `setup/` (the Options dialogs), each a directory of components whose `__init__.py` is a docstring
and imports nothing.  `about_dialog/` belongs to none and stays at the top.
`_WIDGETS` maps a name to its dotted path, so `from navigator.widgets import
Panel` does not care which group `Panel` is in.

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
    "AsciiChart": "shell.ascii_chart",
    "CharTable": "shell.char_table",
    "AboutDialog": "about_dialog",
    "AttrDialog": "file_ops.attr_dialog",
    "BookmarkLabelDialog": "manager.bookmark_label_dialog",
    "ChangeDirDialog": "tree.change_dir_dialog",
    "Clock": "shell.clock",
    "ConfirmationsDialog": "setup.confirmations_dialog",
    "CopyDialog": "file_ops.copy_dialog",
    "CopyProgress": "file_ops.copy_progress",
    "CommandLine": "shell.command_line",
    "DeleteDialog": "file_ops.delete_dialog",
    "DeleteProgress": "file_ops.delete_progress",
    "CompletionList": "shell.completion_list",
    "Console": "shell.console",
    "DirEntry": "manager.panel",
    "DirectoryTree": "tree.directory_tree",
    "EditorDefaultsDialog": "setup.editor_defaults_dialog",
    "EditFileDialog": "editor.edit_file_dialog",
    "EditWindow": "editor.edit_window",
    "EraseQuery": "file_ops.erase_query",
    "ExitDialog": "shell.exit_dialog",
    "FileEditor": "editor.file_editor",
    "FindDialog": "editor.find_dialog",
    "ReplaceQuery": "editor.replace_query",
    "GotoLineDialog": "editor.goto_line_dialog",
    "InfoLine": "editor.file_editor",
    "FileHistoryDialog": "shell.file_history_dialog",
    "FileRecordList": "shell.file_record_list",
    "FileViewer": "viewer.file_viewer",
    "FileWindow": "viewer.file_window",
    "FMDefaultsDialog": "setup.fm_defaults_dialog",
    "FMSetupDialog": "setup.fm_setup_dialog",
    "GotoDialog": "viewer.goto_dialog",
    "InterfaceDialog": "setup.interface_dialog",
    "KeyBar": "shell.keybar",
    "LinkDialog": "file_ops.link_dialog",
    "MainMenu": "shell.main_menu",
    "Manager": "manager.manager",
    "MkdirDialog": "file_ops.mkdir_dialog",
    "OverwriteQuery": "file_ops.overwrite_query",
    "Panel": "manager.panel",
    "QuickViewer": "viewer.quick_viewer",
    "SearchProgress": "viewer.search_progress",
    "SelectDialog": "manager.select_dialog",
    "Shell": "shell.shell",
    "StartupDialog": "setup.startup_dialog",
    "SystemSetupDialog": "setup.system_setup_dialog",
    "TreeWindow": "tree.tree_window",
    "ViewerFindDialog": "viewer.viewer_find_dialog",
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
    from navigator.widgets.about_dialog import AboutDialog
    from navigator.widgets.file_ops.attr_dialog import AttrDialog
    from navigator.widgets.manager.bookmark_label_dialog import BookmarkLabelDialog
    from navigator.widgets.tree.change_dir_dialog import ChangeDirDialog
    from navigator.widgets.shell.clock import Clock
    from navigator.widgets.file_ops.copy_dialog import CopyDialog
    from navigator.widgets.file_ops.copy_progress import CopyProgress
    from navigator.widgets.shell.command_line import CommandLine
    from navigator.widgets.shell.completion_list import CompletionList
    from navigator.widgets.shell.console import Console
    from navigator.widgets.file_ops.delete_dialog import DeleteDialog
    from navigator.widgets.file_ops.delete_progress import DeleteProgress
    from navigator.widgets.tree.directory_tree import DirectoryTree
    from navigator.widgets.editor.edit_file_dialog import EditFileDialog
    from navigator.widgets.editor.edit_window import EditWindow
    from navigator.widgets.file_ops.erase_query import EraseQuery
    from navigator.widgets.editor.file_editor import FileEditor, InfoLine
    from navigator.widgets.editor.find_dialog import FindDialog
    from navigator.widgets.editor.replace_query import ReplaceQuery
    from navigator.widgets.editor.goto_line_dialog import GotoLineDialog
    from navigator.widgets.shell.file_history_dialog import FileHistoryDialog
    from navigator.widgets.shell.file_record_list import FileRecordList
    from navigator.widgets.shell.ascii_chart import AsciiChart
    from navigator.widgets.shell.char_table import CharTable
    from navigator.widgets.viewer.file_viewer import FileViewer
    from navigator.widgets.viewer.file_window import FileWindow
    from navigator.widgets.viewer.goto_dialog import GotoDialog
    from navigator.widgets.shell.keybar import KeyBar
    from navigator.widgets.file_ops.link_dialog import LinkDialog
    from navigator.widgets.manager.manager import Manager
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog
    from navigator.widgets.file_ops.overwrite_query import OverwriteQuery
    from navigator.widgets.shell.main_menu import MainMenu
    from navigator.widgets.manager.panel import DirEntry, Panel
    from navigator.widgets.viewer.quick_viewer import QuickViewer
    from navigator.widgets.viewer.search_progress import SearchProgress
    from navigator.widgets.manager.select_dialog import SelectDialog
    from navigator.widgets.shell.shell import Shell
    from navigator.widgets.tree.tree_window import TreeWindow
    from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog
    from navigator.widgets.setup.confirmations_dialog import ConfirmationsDialog
    from navigator.widgets.setup.editor_defaults_dialog import EditorDefaultsDialog
    from navigator.widgets.setup.fm_defaults_dialog import FMDefaultsDialog
    from navigator.widgets.setup.fm_setup_dialog import FMSetupDialog
    from navigator.widgets.setup.interface_dialog import InterfaceDialog
    from navigator.widgets.setup.startup_dialog import StartupDialog
    from navigator.widgets.setup.system_setup_dialog import SystemSetupDialog
    from navigator.widgets.shell.exit_dialog import ExitDialog
