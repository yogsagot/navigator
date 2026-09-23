# navml: generated
"""The merged surface of ``navigator.widgets.manager.manager``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navigator.widgets.panel import Panel
from navml.widgets.window import Window

from pathlib import Path
from navkit.events import KeyEvent
from navkit.reactive import computed
from navml.widgets.dialog import Dialog
from navigator.widgets.mkdir_dialog import MkdirDialog


class Manager(Window, _Component):
    left: Panel
    right: Panel
    framed: _Any
    def __init__(self, left: Path, right: Path, **kwargs): ...
    async def on_key(self, event: KeyEvent) -> bool: ...
    async def make_directory(self) -> None: ...
    active_panel: Panel
    def switch_panel(self) -> None: ...
