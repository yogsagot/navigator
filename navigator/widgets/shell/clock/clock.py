"""The painting behind ``clock.nml``.

This file never names the generated class.  ``class Clock(Widget)`` is the
base the markup's bare ``Clock:`` head asks for.
"""

from __future__ import annotations

from datetime import datetime

from navkit.events import MouseClickEvent
from navkit.screen import Surface
from navkit.widget import Widget

from navigator.lib.config import country
from navigator.widgets.shell.commands import OpenCalendar


def now() -> datetime:
    """The wall clock.  A function of its own so a test can replace it."""
    return datetime.now()


class Clock(Widget):
    """``HH:MM`` in 24-hour time, or ``hh:MMam`` in 12 (*Country support*),
    with the colon shown while ``blink`` is set."""

    def text(self) -> str:
        """What the clock shows this second."""
        return country.time_text(now().timestamp(), separator=":" if self.blink else " ")

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press opens Utilities > *Calendar* under the clock, or closes it
        when it is open -- not DN's, whose clock did nothing with a click;
        asked for."""
        if event.action != "press" or event.button != "left":
            return False
        app = self.application
        if app is not None:
            await app.run_command(OpenCalendar(under_clock=True))
        return True

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        surface.draw_text(0, 0, self.text(), self.style)
