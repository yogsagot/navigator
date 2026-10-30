"""The calendar window's size and place, its button, its calendar system and
what of it is shown (the month is navml's ``CalendarView``)."""

from __future__ import annotations

import datetime
from typing import Any

from navkit.events import ContextMenuEvent, Event, KeyEvent
from navkit.i18n import tr
from navkit.reactive import bind, effect
from navml.calendars import SYSTEMS
from navml.commands import CloseWindow
from navml.widgets.dialog.commands import (
    ChooseMonth,
    ChooseYear,
    GoToToday,
    NextMonth,
    NextYear,
    PreviousMonth,
    PreviousYear,
    SetCalendarSystem,
    SetCalendarView,
    SwapCalendars,
)
from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click, open_on_key
from navml.widgets.window import Window

from navigator.lib.config import country

#: The view with a column either side, the button under it, and the frame;
#: the height is the most, six weeks and the row spelling the day.
WIDTH, HEIGHT = 26, 14
#: With *Both months*: the second view, three columns after the first.
WIDE = WIDTH + 25


def view_captions() -> dict[str, str]:
    """*View*'s choices by ``CountryData.VIEWS`` key, in the current language."""
    return {
        "only": tr("~S~elected calendar only"),
        "gregorian_grid": tr("~G~regorian month, selected date"),
        "selected_grid": tr("Selected ~m~onth, Gregorian date"),
        "both": tr("~B~oth months side by side"),
    }


class CalendarWindow(Window):
    """TVDEMO's ``TCalendarWindow``: a month, today marked."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The day spelled under the weeks and the week's first day, following
        # *Country support* --
        # navml's view knows no country, so it is told from here.
        for view in (self.month, self.other):
            view.first_weekday = bind(lambda w: country.first_weekday())
        # The month in the menu's calendar, else *Country support*'s, and the
        # day spelled in the Gregorian -- or as *View* says: in the calendar
        # under the Gregorian month, and not at all under one month alone or
        # two side by side, whose grids already say it.
        self.month.system = bind(lambda w: "gregorian" if self.gregorian_grid() else self.calendar_system())
        self.month.date_format = bind(lambda w: "" if self.calendar_view() in ("only", "both") else country.date_format())
        self.month.label = bind(lambda w: self.calendar_system() if self.calendar_view() == "gregorian_grid"
                                else "gregorian")
        # Side by side, the calendar first and the Gregorian beside it.
        self.other.system = bind(lambda w: "gregorian")
        # Only the weeks the month has, the row spelling the day (if any)
        # right under them, then a blank and the button.
        for view in (self.month, self.other):
            view.compact = True
            view.height = bind(lambda w: 2 + self.rows() + self.spelled_rows())
        self.today_button.y = bind(lambda w: 1 + 2 + self.rows() + self.spelled_rows() + 1)
        self.other.visible = bind(lambda w: self.both())
        for key, system in SYSTEMS.items():
            item = self.system_menu.add_item("", SetCalendarSystem(key))
            item.text = bind(lambda w, system=system: system.caption())
        for key in view_captions():
            item = self.view_menu.add_item("", SetCalendarView(key))
            item.text = bind(lambda w, key=key: view_captions()[key])

    def mounted(self) -> None:
        super().mounted()
        effect(self, CalendarWindow._follow_month)
        effect(self, CalendarWindow._follow_other)
        effect(self, CalendarWindow._fit)

    def _follow_month(self) -> None:
        """The second month on the first's day..."""
        self.other.day = self.month.day

    def _follow_other(self) -> None:
        """...and the first on the second's, whichever the keys moved."""
        self.month.day = self.other.day

    def _fit(self) -> None:
        """Wide enough for the months shown, kept on the desktop."""
        width, height = self.size()
        desktop = self.parent
        if desktop is None or (self.width, self.height) == (width, height):
            return
        x = max(0, min(self.x, desktop.width - width))
        self.locate(x, self.y, min(width, desktop.width), min(height, desktop.height))

    def size(self) -> tuple[int, int]:
        """The window's width and height for the months it shows."""
        # The frame, the month and weekday rows, the weeks, the spelled row,
        # a blank, and the button with its shadow.
        return (WIDE if self.both() else WIDTH), 2 + 2 + self.rows() + self.spelled_rows() + 1 + 2

    def rows(self) -> int:
        """The weeks the months shown paint: the most either has, side by
        side, so their rows line up."""
        return max(self.month.rows(), self.other.rows() if self.both() else 0)

    def spelled_rows(self) -> int:
        """1 with a row under the weeks spelling the day, else 0."""
        return 0 if self.unspelled() else 1

    def unspelled(self) -> bool:
        """No row under the weeks spells the day: *Selected calendar only*
        and *Both months*, whose grids already say it."""
        return self.calendar_view() in ("only", "both")

    def calendar_view(self) -> str:
        """What of the calendar system is shown: the menu's choice, else
        *Country support*'s; a key no view has is the calendar's month."""
        key = self.display or country.calendar_view()
        return key if key in view_captions() else "selected_grid"

    def both(self) -> bool:
        """Two months side by side: *Both months*, in a calendar not the Gregorian."""
        return self.calendar_view() == "both" and self.calendar_system() != "gregorian"

    def gregorian_grid(self) -> bool:
        """The first month is the Gregorian: *Gregorian month*, or *Selected
        calendar only* swapped -- side by side it is the second."""
        view = self.calendar_view()
        return view == "gregorian_grid" or (view == "only" and self.swapped)

    def view(self) -> Any:
        """The month the keys are on: the second while it has them, else the first."""
        app = self.application
        return self.other if self.both() and app is not None and app.focused is self.other else self.month

    def calendar_system(self) -> str:
        """The calendar the month is in: the menu's choice, else *Country
        support*'s; a key no calendar has is the Gregorian."""
        key = self.chosen or country.calendar_system()
        return key if key in SYSTEMS else "gregorian"

    def go_to_today(self) -> None:
        """*Go to current date*: today's month, the cursor on today, the keys
        back on the days."""
        view = self.view()
        view.day = datetime.date.today()
        view.section = "days"
        view.focus()

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
        view = self.view()
        view.focus()
        return await view.emit(command)

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

    async def on_set_calendar_system(self, command: SetCalendarSystem) -> bool:
        self.chosen = command.calendar
        if not self.both():
            self.month.focus()
        return True

    async def on_swap_calendars(self, command: SwapCalendars) -> bool:
        """``C``: the month in the other of the two -- *Gregorian month* and
        *Selected month* trade places, *Selected calendar only* shows the
        Gregorian alone and back."""
        if self.refusal(command):
            return True
        view = self.calendar_view()
        if view == "only":
            self.swapped = not self.swapped
        else:
            self.display = "selected_grid" if view == "gregorian_grid" else "gregorian_grid"
        return True

    def refusal(self, command: Any) -> str:
        if isinstance(command, SwapCalendars):
            if self.calendar_system() == "gregorian":
                return tr("The calendar system is the Gregorian")
            if self.calendar_view() == "both":
                return tr("Both months are shown")
        return super().refusal(command)

    def key_hints(self) -> list[tuple[str, str]]:
        """``C`` and the calendar it puts the month in, while it can."""
        if self.refusal(SwapCalendars()):
            return super().key_hints()
        if not self.gregorian_grid():
            # Its own short word, where the bar is tight; menus keep the name.
            return [("C", tr("Gregorian")), *super().key_hints()]
        return [("C", SYSTEMS[self.calendar_system()].name()), *super().key_hints()]

    async def on_set_calendar_view(self, command: SetCalendarView) -> bool:
        self.display = command.view
        self.swapped = False
        if not self.both():
            self.month.focus()
        return True

    def checks(self, command: object) -> bool | None:
        """The calendar the month is in, ticked."""
        if isinstance(command, SetCalendarSystem):
            return self.calendar_system() == command.calendar
        if isinstance(command, SetCalendarView):
            return self.calendar_view() == command.view
        return super().checks(command)

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # ``InputLine``'s are -- this half has one base, its markup's.

    def prepare_context(self, x: int, y: int) -> None:
        """A right click on a day puts the cursor on it."""
        for month in (self.month, self.other):
            day = month.day_at(x - month.x, y - month.y) if month.visible else None
            if day is not None:
                month.day = day
                month.section = "days"
                month.focus()

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
        menu.add_item(tr("S~w~ap calendars"), SwapCalendars, "C")
        menu.add_line()
        systems = menu.add_submenu(tr("Calendar ~s~ystem"))
        for key, system in SYSTEMS.items():
            systems.add_item(system.caption(), SetCalendarSystem(key))
        views = menu.add_submenu(tr("Calendar ~v~iew"))
        for key, caption in view_captions().items():
            views.add_item(caption, SetCalendarView(key))
        menu.add_line()
        menu.add_item(tr("~C~lose"), CloseWindow)
        return menu

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        return open_on_key(self)
