# navml: generated
"""The merged surface of ``navml.widgets.button.button``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.static_text import StaticText

from dataclasses import dataclass
from typing import Any
from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget


class ClickEvent(Event): ...


class Button(_Component):
    text: str
    caption: StaticText
    enabled: bool
    emits: _Any
    def __init__(self, text: str = ..., **kwargs: Any) -> None: ...
    async def press(self) -> bool: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
    async def on_mouse_click(self, event: MouseClickEvent) -> bool: ...
    def render(self, surface: Surface) -> None: ...
