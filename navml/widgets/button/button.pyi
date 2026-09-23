# navml: generated
"""The merged surface of ``navml.widgets.button.button``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.control import Control
from navml.widgets.static_text import StaticText

from dataclasses import dataclass
from typing import Any
from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.screen import Surface
from navkit.style import Style


class ClickEvent(Event): ...


class Button(Control, _Component):
    text: str
    default: bool
    caption: StaticText
    emits: _Any
    parts: _Any
    def __init__(self, text: str = ..., **kwargs: Any) -> None: ...
    async def press(self) -> bool: ...
    async def activate(self, letter: str = ...) -> bool: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
    async def on_mouse_click(self, event: MouseClickEvent) -> bool: ...
    face: tuple[int, int]
    def render(self, surface: Surface) -> None: ...
    def _render_shadow(self, surface: Surface, width: int, height: int) -> None: ...
