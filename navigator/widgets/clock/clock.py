"""The painting behind ``clock.nml``.

This file never names the generated class.  ``class Clock(Widget)`` is the
base the markup's bare ``Clock:`` head asks for.
"""

from __future__ import annotations

from datetime import datetime

from navkit.screen import Surface
from navkit.widget import Widget


def now() -> datetime:
    """The wall clock.  A function of its own so a test can replace it."""
    return datetime.now()


class Clock(Widget):
    """``HH:MM`` in 24-hour time, with the colon shown while ``blink`` is set."""

    def text(self) -> str:
        """What the clock shows this second."""
        return now().strftime("%H:%M" if self.blink else "%H %M")

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        surface.draw_text(0, 0, self.text(), self.style)
