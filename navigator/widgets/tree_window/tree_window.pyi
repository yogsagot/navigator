# navml: generated
"""The merged surface of ``navigator.widgets.tree_window.tree_window``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.commands import Rescan
from navigator.widgets.directory_tree import DirectoryTree
from navml.commands import CloseWindow
from navml.widgets.window import Window

from pathlib import Path
from typing import Any


class TreeWindow(Window, _Component):
    tree: DirectoryTree
    def __init__(self, start: Path | None = ..., hidden: bool = ..., **kwargs: Any) -> None: ...
    async def on_tree_chosen(self, event: _Event) -> bool: ...
    def mounted(self) -> None: ...
    async def on_rescan(self, event: Rescan) -> bool: ...
