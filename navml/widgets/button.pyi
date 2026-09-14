# navml: generated
"""The merged surface of ``navml.widgets.button``.

A stub replaces its module for a type checker, so this carries both halves:
the markup half's properties and ids, and the hand-written half's members.
"""

from typing import Any as _Any

from navkit.events import KeyEvent
from navkit.screen import Surface
from navkit.widget import Widget as _Widget

from navml.widgets.label import Label

class Button(_Widget):
    text: str
    caption: Label
    pressed: bool
    def __init__(self, text: str = ..., **kwargs: _Any) -> None: ...
    def press(self) -> None: ...
    def on_key(self, event: KeyEvent) -> bool: ...
    def layout(self, width: int, height: int) -> None: ...
    def render(self, surface: Surface) -> None: ...
