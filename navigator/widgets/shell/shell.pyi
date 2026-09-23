# navml: generated
"""The merged surface of ``navigator.widgets.shell.shell``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.console import Console
from navigator.widgets.keybar import KeyBar
from navigator.widgets.menubar import MenuBar
from navml.widgets.desktop import Desktop

from pathlib import Path
from navkit.events import Event
from navkit.screen import Surface
from navkit.stylesheet import Stylesheet
from navkit.widget import Widget
from navigator.scheme import default_scheme
from navigator.widgets.manager import Manager


class Shell(_Component):
    console_visible: bool
    menu: MenuBar
    console: Console
    desktop: Desktop
    keybar: KeyBar
    def __init__(self, left: Path, right: Path, scheme: Stylesheet | None = ..., **kwargs): ...
    def toggle_console(self) -> None: ...
    def show_console(self) -> None: ...
    async def on_desktop_emptied(self, event: Event) -> bool: ...
    def render(self, surface: Surface) -> None: ...
