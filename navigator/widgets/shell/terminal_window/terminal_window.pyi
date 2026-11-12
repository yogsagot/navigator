# navml: generated
"""The merged surface of ``navigator.widgets.shell.terminal_window.terminal_window``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.shell.terminal_view import TerminalView
from navml.widgets.dialog.scroll_bar import ScrollBar
from navml.widgets.window import Window

import os
from pathlib import Path
from typing import Any, Callable
from navkit.i18n import tr
from navkit.reactive import bind
from navml.widgets.dialog.dialog import Dialog
from navigator.settings import SETTINGS


class TerminalWindow(Window, _Component):
    view: TerminalView
    bar: ScrollBar
    def __init__(self, command: str = ..., cwd: Path | None = ..., *, shell: str | None = ..., title: str | None = ..., on_close: Callable[[], Any] | None = ..., closes: bool | Callable[[int], bool] = ..., **kwargs: Any) -> None: ...
    def caption(self) -> str: ...
    def command_ended(self, status: int) -> None: ...
    async def on_bar_scroll(self, event: Any) -> bool: ...
    def list_name(self) -> str: ...
    def short_name(self) -> str: ...
    def key_hints(self) -> list[tuple[str, str]]: ...
    def must_ask(self) -> bool: ...
    async def ask_to_close(self) -> bool: ...
    def close(self) -> None: ...
