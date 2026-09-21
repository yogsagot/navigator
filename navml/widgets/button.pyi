# navml: generated
"""The merged surface of ``navml.widgets.button``.

A stub replaces its module for a type checker, so this carries both halves:
the markup half's properties and ids, and the hand-written half's members --
the event class it declares included, since that is part of what the public
module name offers.
"""

from typing import Any as _Any

from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.screen import Surface

from navml.component import Component as _Component
from navml.widgets.label import Label

class ClickEvent(Event): ...

class Button(_Component):
    text: str
    caption: Label
    emits: tuple[type[Event], ...]
    enabled: bool
    def __init__(self, text: str = ..., **kwargs: _Any) -> None: ...
    async def press(self) -> bool: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
    async def on_mouse_click(self, event: MouseClickEvent) -> bool: ...
    def render(self, surface: Surface) -> None: ...
