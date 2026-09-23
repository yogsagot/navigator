# navml: generated
"""The merged surface of ``navml.widgets.scroll_bar.scroll_bar``."""

from typing import Any as _Any

from navml.component import Component as _Component

from dataclasses import dataclass
from navkit.events import Event, MouseClickEvent
from navkit.glyphs import DEFAULT_SCROLLBAR, SCROLLBARS, scrollbar
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget


class ScrollEvent(Event): ...


class ScrollBar(_Component):
    orientation: str
    value: int
    maximum: int
    page: int
    step: int
    emits: _Any
    chars: _Any
    parts: _Any
    def __init__(self, **kwargs: _Any) -> None: ...
    vertical: bool
    length: int
    track: int
    thumb: int
    def _ask(self, value: int) -> int: ...
    async def scroll_to(self, value: int) -> bool: ...
    async def on_mouse_click(self, event: MouseClickEvent) -> bool: ...
    def render(self, surface: Surface) -> None: ...
