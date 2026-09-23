"""The handlers behind ``label.nml``.

Nothing but the painting.  ``label.nml`` declares the two properties and this
file reads them, which is the division the file layout is for -- and it is worth
noticing that the markup half of this component has no children at all: a
document is a good place to say *what a widget has* even when it places nothing.

This file never names the generated class.  ``class Label(Widget)`` is what a
Python-only component would say too, which is what lets a component gain or lose
its markup half without being edited.
"""

from __future__ import annotations

from navkit.screen import Surface
from navkit.widget import Widget


class Label(Widget):
    """A line of text."""

    def render(self, surface: Surface) -> None:
        text = self.text[: max(0, self.width)]
        if self.align == "right":
            x = max(0, self.width - len(text))
        elif self.align == "center":
            x = max(0, (self.width - len(text)) // 2)
        else:
            x = 0
        surface.draw_text(x, 0, text, self.style)
