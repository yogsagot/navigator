# navml: generated
"""The merged surface of ``navigator.widgets.edit_window.edit_window``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.commands import SaveText
from navigator.widgets.file_editor import FileEditor
from navml.commands import CloseWindow
from navml.widgets.dialog.scroll_bar import ScrollBar
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.window import Window

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from navkit.events import Event
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent


class FileSaved(Event): ...


class EditWindow(Window, _Component):
    editor: FileEditor
    vbar: ScrollBar
    hbar: ScrollBar
    info: StaticText
    emits: _Any
    def __init__(self, path: Path | str, *, new: bool = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def list_name(self) -> str: ...
    async def on_save_text(self, event: SaveText) -> bool: ...
    async def save(self) -> bool: ...
    def must_ask(self) -> bool: ...
    async def ask_to_close(self) -> bool: ...
    async def on_vbar_scroll(self, event: ScrollEvent) -> bool: ...
    async def on_hbar_scroll(self, event: ScrollEvent) -> bool: ...
