# navml: generated
"""The merged surface of ``navigator.widgets.manager``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navigator.widgets.console import Console
from navigator.widgets.keybar import KeyBar
from navigator.widgets.menubar import MenuBar
from navigator.widgets.panel import Panel

from pathlib import Path
from navkit.events import KeyEvent
from navkit.reactive import computed
from navkit.screen import Surface
from navkit.stylesheet import Stylesheet
from navkit.widget import Widget
from navigator.scheme import default_scheme


class Manager(_Component):
    console_visible: bool
    menu: MenuBar
    left: Panel
    right: Panel
    console: Console
    keybar: KeyBar
    def __init__(self, left: Path, right: Path, scheme: Stylesheet | None = ..., **kwargs): ...
    def toggle_console(self) -> None: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
    active_panel: Panel
    def switch_panel(self) -> None: ...
    def render(self, surface: Surface) -> None: ...
