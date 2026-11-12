# navml: generated
"""The merged surface of ``navigator.widgets.shell.command_palette.command_palette``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.input_line import InputLine
from navml.widgets.dialog.static_text import StaticText
from navigator.widgets.shell.command_palette.command_list import CommandList
from navml.widgets.dialog.commands import Default

from dataclasses import dataclass
from typing import Any
from navkit import commands
from navkit.commands import Command, command_of
from navkit.events import KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect
from navkit.widget import Widget
from navml import fuzzy
from navml.widgets.dialog.commands import Cancel, Default
from navml.widgets.dialog.control import parse_shortcut
from navml.widgets.menu.menu_box.menu_box import key_caption
from navml.widgets.menu.menu_item import MenuItem
from navml.widgets.menu.sub_menu import SubMenu


class Entry(object): ...


class Found(object): ...


class CommandPalette(Dialog, _Component):
    filter: InputLine
    results: CommandList
    hint: StaticText
    def __init__(self, behind: Widget | None = ..., **kwargs: Any) -> None: ...
    async def on_default(self, event: _Any) -> bool: ...
    def mounted(self) -> None: ...
    def _follow_filter(self) -> None: ...
    def _describe(self) -> None: ...
    def take(self) -> bool: ...
    def accept(self) -> Command | None: ...
    def enables(self, command: Command) -> bool: ...
    async def on_cancel(self, event: Cancel) -> bool: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
