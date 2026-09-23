# navml: generated
"""The merged surface of ``navml.widgets.dialog.dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.button import Button
from navml.widgets.static_text import StaticText
from navml.widgets.window import Window

import asyncio
from typing import Any
from navkit.application import Application
from navkit.events import Event, KeyEvent
from navkit.reactive import reactive
from navkit.widget import Widget


class Dialog(Window, _Component):
    dialog_width: int
    dialog_height: int
    buttons: str
    prompt: str
    button_row: _Any
    message: StaticText
    ok: Button
    cancel: Button
    info: Button
    modal: bool
    result: Any
    def __init__(self, **kwargs: Any) -> None: ...
    async def on_cancel_click(self, event: _Event) -> bool: ...
    async def execute(self, app: Application | None = ...) -> Any: ...
    def close(self, result: Any = ...) -> None: ...
    def accept(self) -> Any: ...
    def unmounting(self) -> None: ...
    def focusable(self) -> list[Widget]: ...
    buttons_row: tuple[Widget, ...]
    default_button: Widget | None
    async def on_key(self, event: KeyEvent) -> bool: ...
    def _application_or_raise(self) -> Application: ...
    async def on_ok_click(self, event: Event) -> bool: ...
    async def on_click(self, event: Event) -> bool: ...
    async def show_info(self, event: Event) -> None: ...
