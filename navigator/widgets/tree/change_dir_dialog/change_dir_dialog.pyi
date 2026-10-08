# navml: generated
"""The merged surface of ``navigator.widgets.tree.change_dir_dialog.change_dir_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.dialog.tree_view import TreeView

from pathlib import Path
from typing import Any
from navkit.events import Event
from navkit.i18n import tr
from navigator.widgets.tree.directory_tree.directory_tree import directory_root, show_path


class ChangeDirDialog(Dialog, _Component):
    tree: TreeView
    where: StaticText
    pick: Button
    drive: Button
    reread: Button
    mkdir: Button
    abandon: Button
    def __init__(self, start: Path | None = ..., hidden: bool = ..., **kwargs: Any) -> None: ...
    async def on_drive_click(self, event: _Event) -> bool: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> Path | None: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_tree_chosen(self, event: Any) -> bool: ...
    async def on_reread_click(self, event: Event) -> bool: ...
    async def on_mkdir_click(self, event: Event) -> bool: ...
    async def make_directory(self) -> None: ...
