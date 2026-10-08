"""The calendar window's size and place, and its button (the month is navml's
``CalendarView``)."""

from __future__ import annotations

import datetime

from navkit.events import Event, KeyEvent
from navml.widgets.window import Window

#: The view with a column either side, the button under it, and the frame.
WIDTH, HEIGHT = 26, 13


class CalendarWindow(Window):
    """TVDEMO's ``TCalendarWindow``: a month, today marked."""

    def go_to_today(self) -> None:
        """*Go to current date*: today's month, the cursor on today, the keys
        back on the days."""
        self.month.day = datetime.date.today()
        self.month.section = "days"
        self.month.focus()

    async def on_today_button_click(self, event: Event) -> bool:
        self.go_to_today()
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        """Alt and the button's letter presses it, as a dialog's shortcut walk would."""
        if event.alt and not event.ctrl and len(event.key) == 1 and self.today_button.shortcut_match(event.key):
            return await self.today_button.activate(event.key)
        return await super().on_key(event)
