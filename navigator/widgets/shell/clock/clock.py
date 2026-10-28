"""The painting behind ``clock.nml``.

This file never names the generated class.  ``class Clock(Widget)`` is the
base the markup's bare ``Clock:`` head asks for.
"""

from __future__ import annotations

from datetime import datetime

from navkit.events import MouseClickEvent
from navkit.i18n import tr
from navkit.screen import Surface
from navkit.widget import Widget

from navigator.lib.config import country
from navigator.widgets.shell.commands import OpenCalendar


def now() -> datetime:
    """The wall clock.  A function of its own so a test can replace it."""
    return datetime.now()


def weekday_names() -> list[str]:
    """Monday to Sunday, in the current language."""
    return [tr("Monday"), tr("Tuesday"), tr("Wednesday"), tr("Thursday"), tr("Friday"),
            tr("Saturday"), tr("Sunday")]


class Clock(Widget):
    """``HH:MM`` in 24-hour time, or ``hh:MMam`` in 12 (*Country support*),
    with the colon shown while ``blink`` is set."""

    def text(self) -> str:
        """What the clock shows this second."""
        return country.time_text(now().timestamp(), separator=":" if self.blink else " ")

    def tooltip_at(self, x: int, y: int) -> str:
        """Today's weekday and date in *Country support*'s format, and what a
        click does -- the date being what the corner leaves out."""
        today = now()
        day = tr("{weekday}, {date}").format(
            weekday=weekday_names()[today.weekday()], date=country.date_text(today.timestamp()),
        )
        return f"{day}\n{tr('Click for the calendar')}"

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
