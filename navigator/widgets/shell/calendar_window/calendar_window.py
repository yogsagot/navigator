"""The calendar window's size and place, and its button (the month is navml's
``CalendarView``)."""

from __future__ import annotations

import datetime

from navkit.events import ContextMenuEvent, Event, KeyEvent
from navkit.i18n import tr
from navml.commands import CloseWindow
from navml.widgets.dialog.commands import (
    ChooseMonth,
    ChooseYear,
    GoToToday,
    NextMonth,
    NextYear,
    PreviousMonth,
    PreviousYear,
)
from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click, open_on_key
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

    # -- the *Calendar* menu -----------------------------------------------------
    #
    # Its commands are the month view's, which answers them first while it has
    # the keyboard.  With the button holding it the view is not on the way
    # out, so the window hands them on, and the keys go back to the days.

    async def _month(self, command: object) -> bool:
        self.month.focus()
        return await self.month.emit(command)

    async def on_previous_month(self, command: PreviousMonth) -> bool:
        return await self._month(command)

    async def on_next_month(self, command: NextMonth) -> bool:
        return await self._month(command)

    async def on_previous_year(self, command: PreviousYear) -> bool:
        return await self._month(command)

    async def on_next_year(self, command: NextYear) -> bool:
        return await self._month(command)

    async def on_choose_month(self, command: ChooseMonth) -> bool:
        return await self._month(command)

    async def on_choose_year(self, command: ChooseYear) -> bool:
        return await self._month(command)

    async def on_go_to_today(self, command: GoToToday) -> bool:
        self.go_to_today()
        return True

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # ``InputLine``'s are -- this half has one base, its markup's.

    def prepare_context(self, x: int, y: int) -> None:
        """A right click on a day puts the cursor on it."""
        month = self.month
        day = month.day_at(x - month.x, y - month.y)
        if day is not None:
            month.day = day
            month.section = "days"

    def context_menu(self) -> ContextMenu:
        """The *Calendar* menu's entries, built each time so its captions follow the language."""
        menu = ContextMenu()
        menu.add_item(tr("~P~revious month"), PreviousMonth, "PgUp")
        menu.add_item(tr("~N~ext month"), NextMonth, "PgDn")
        menu.add_item(tr("P~r~evious year"), PreviousYear, "Ctrl-PgUp")
        menu.add_item(tr("Ne~x~t year"), NextYear, "Ctrl-PgDn")
        menu.add_line()
        menu.add_item(tr("Choose ~m~onth..."), ChooseMonth, "M")
        menu.add_item(tr("Choose ~y~ear..."), ChooseYear, "Y")
        menu.add_line()
        menu.add_item(tr("Go to current ~d~ate"), GoToToday, "T")
        menu.add_line()
        menu.add_item(tr("~C~lose"), CloseWindow)
        return menu

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        return open_on_key(self)
