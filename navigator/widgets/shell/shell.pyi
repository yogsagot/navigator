# navml: generated
"""The merged surface of ``navigator.widgets.shell.shell``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.clock import Clock
from navigator.widgets.console import Console
from navigator.widgets.keybar import KeyBar
from navigator.widgets.main_menu import MainMenu
from navml.widgets.desktop import Desktop
from navml.widgets.layout.dock_layout import DockLayout

from pathlib import Path
from typing import Any
from navkit.events import Event, KeyEvent
from navkit.screen import Surface
from navkit.stylesheet import Stylesheet
from navml.commands import OpenMenu
from navigator.commands import NewManager, OpenTreeWindow
from navigator.scheme import default_scheme
from navigator.widgets.manager import Manager


class Shell(DockLayout, _Component):
    console_visible: bool
    menu: MainMenu
    clock: Clock
    console: Console
    desktop: Desktop
    keybar: KeyBar
    def __init__(self, left: Path, right: Path, scheme: Stylesheet | None = ..., **kwargs): ...
    def toggle_console(self) -> None: ...
    def show_console(self) -> None: ...
    async def on_open_menu(self, event: OpenMenu) -> bool: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
    active_manager: Manager | None
    async def on_new_manager(self, event: NewManager) -> bool: ...
    async def on_open_tree_window(self, event: OpenTreeWindow) -> bool: ...
    async def on_chosen(self, event: Any) -> bool: ...
    async def on_desktop_opened(self, event: Event) -> bool: ...
    async def on_desktop_emptied(self, event: Event) -> bool: ...
    def render(self, surface: Surface) -> None: ...
