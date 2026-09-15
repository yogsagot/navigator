# navml: generated
"""The merged surface of ``navml.widgets.button``.

A stub replaces its module for a type checker, so this carries both halves:
the markup half's properties and ids, and the hand-written half's members --
the event class it declares included, since that is part of what the public
module name offers.
"""

from typing import Any as _Any

from navkit.events import Event, KeyEvent, MouseEvent
from navkit.screen import Surface
from navkit.widget import Widget as _Widget

from navml.widgets.label import Label

class ClickEvent(Event): ...

class Button(_Widget):
    text: str
    caption: Label
    emits: tuple[type[Event], ...]
    enabled: bool
    def __init__(self, text: str = ..., **kwargs: _Any) -> None: ...
    async def press(self) -> bool: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
    async def on_mouse(self, event: MouseEvent) -> bool: ...
    def layout(self, width: int, height: int) -> None: ...
    def render(self, surface: Surface) -> None: ...
