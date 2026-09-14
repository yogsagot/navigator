"""The handlers behind ``button.nml``.

This file never names the generated class.  ``class Button(Widget)`` is what a
Python-only component would say too, which is what lets a component gain or
lose its markup half without this file changing -- see *Why the generated base
is hidden* in ``navml/DESIGN.md``.  The base repeats the one the markup
declares, and :mod:`navml._merge` refuses the pair if the two disagree.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget


class Button(Widget):
    """A pressable box."""

    #: Held down for as long as the key that pressed it is being handled.  A
    #: real one will be a signal, which navkit does not have yet.
    pressed: bool = reactive(False)

    def __init__(self, text: str = "", **kwargs: Any) -> None:
        # The markup half's tree is built by this call, so every id is live
        # from the next line on.
        super().__init__(**kwargs)
        self.text = text

    def press(self) -> None:
        self.pressed = not self.pressed

    def on_key(self, event: KeyEvent) -> bool:
        if event.name in ("enter", "space"):
            self.press()
            return True
        return False

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
