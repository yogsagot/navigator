# navml: generated
"""The merged surface of ``navigator.widgets.tree.tree_window.tree_window``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.manager.commands import Rescan
from navigator.widgets.tree.directory_tree import DirectoryTree
from navml.commands import CloseWindow
from navml.widgets.window import Window

from pathlib import Path
from typing import Any
from navkit.screen import Surface


class TreeWindow(Window, _Component):
    tree: DirectoryTree
    def __init__(self, start: Path | None = ..., hidden: bool = ..., **kwargs: Any) -> None: ...
    async def on_tree_chosen(self, event: _Event) -> bool: ...
    def take_keyboard(self) -> None: ...
    async def on_rescan(self, event: Rescan) -> bool: ...
    def _search_label(self) -> tuple[int, str] | None: ...
    def render(self, surface: Surface) -> None: ...
    def cursor_position(self) -> tuple[int, int] | None: ...
