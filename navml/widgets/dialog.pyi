# navml: generated
"""The merged surface of ``navml.widgets.dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.button import Button
from navml.widgets.label import Label

from navkit.events import Event
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget


class Dialog(_Component):
    prompt: str
    message: Label
    ok: Button
    cancel: Button
    info: Button
    result: bool | None
    def __init__(self, **kwargs: _Any) -> None: ...
    async def on_cancel_click(self, event: _Event) -> bool: ...
    async def on_ok_click(self, event: Event) -> bool: ...
    async def on_click(self, event: Event) -> bool: ...
    async def show_info(self, event: Event) -> None: ...
    def render(self, surface: Surface) -> None: ...
