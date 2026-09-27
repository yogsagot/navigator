# navml: generated
"""The merged surface of ``navigator.widgets.manager.manager``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navigator.commands import Copy, Delete, Edit, MakeDirectory, RenameMove
from navigator.commands import Rescan, SwitchPanel, UserMenu, View
from navigator.widgets.panel import Panel
from navml.widgets.layout.horizontal_layout import HorizontalLayout
from navml.widgets.window import Window

from pathlib import Path
from navkit.reactive import computed
from navml.widgets.dialog.dialog import Dialog
from navigator.widgets.mkdir_dialog import MkdirDialog


class Manager(Window, _Component):
    panels: HorizontalLayout
    left: Panel
    right: Panel
    framed: _Any
    def __init__(self, left: Path, right: Path, **kwargs): ...
    async def on_switch_panel(self, event: SwitchPanel) -> bool: ...
    async def on_rescan(self, event: Rescan) -> bool: ...
    async def on_make_directory(self, event: MakeDirectory) -> bool: ...
    async def make_directory(self) -> None: ...
    active_panel: Panel
    def switch_panel(self) -> None: ...
