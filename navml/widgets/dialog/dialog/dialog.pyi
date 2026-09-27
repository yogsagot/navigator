# navml: generated
"""The merged surface of ``navml.widgets.dialog.dialog.dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.layout.horizontal_layout import HorizontalLayout
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.dialog.modal import Modal

import asyncio
from typing import Any
from navkit.application import Application
from navkit.events import Event, KeyEvent
from navkit.reactive import reactive
from navkit.widget import Widget


class Dialog(Modal, _Component):
    buttons: str
    prompt: str
    message: StaticText
    row: HorizontalLayout
    ok: Button
    cancel: Button
    info: Button
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
