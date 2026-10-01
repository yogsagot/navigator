# navml: generated
"""The merged surface of ``navigator.widgets.editor.edit_window.edit_window``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.commands import SaveText, Undo
from navigator.widgets.editor.file_editor import FileEditor
from navml.commands import CloseWindow
from navml.widgets.dialog.scroll_bar import ScrollBar
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.menu.menu_item import MenuItem
from navml.widgets.menu.menu_line import MenuLine
from navml.widgets.menu.sub_menu import SubMenu
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
    edit_menu: SubMenu
    edit_menu_file: SubMenu
    edit_menu_edit: SubMenu
    edit_menu_search: SubMenu
    edit_menu_paragraph: SubMenu
    edit_menu_block: SubMenu
    edit_menu_misc: SubMenu
    edit_menu_misc_uppercase: SubMenu
    edit_menu_misc_lowercase: SubMenu
    edit_menu_misc_capitalize: SubMenu
    edit_menu_options: SubMenu
    emits: _Any
    def __init__(self, path: Path | str, *, new: bool = ..., **kwargs: Any) -> None: ...
    def take_keyboard(self) -> None: ...
    def list_name(self) -> str: ...
    async def on_save_text(self, event: SaveText) -> bool: ...
    async def save(self) -> bool: ...
    def must_ask(self) -> bool: ...
    async def ask_to_close(self) -> bool: ...
    async def on_vbar_scroll(self, event: ScrollEvent) -> bool: ...
    async def on_hbar_scroll(self, event: ScrollEvent) -> bool: ...
