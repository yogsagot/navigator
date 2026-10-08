"""The ``▐↓▌`` beside a date line, and the calendar it drops.

Not DOS Navigator's, which had no calendar, but Turbo Vision's: the
``TCalendarView`` of Borland's TVDEMO -- the month and year on the top row
between two arrows that turn the month, the weekday names under it, and the
days in a grid of six weeks.  What it adds is a cursor, because the demo's
calendar only looked and this one chooses.

* **The button is :class:`History`'s three cells**, and finds its line the
  same way.  It reads the line's text by its ``date_format`` (``strftime``'s
  spelling, ``%d-%m-%Y`` unless told) and opens on that day, or on today when
  the line holds none; choosing writes the day back in the same format.
* **Alt+Down in the line drops the calendar**, as a click does.  **Up and
  Down in the line step the date** (:meth:`DateButton.step`) by the value of
  the place under the caret -- a day or ten on the day, a month or ten on the
  month, a year to a thousand on the year -- carrying as a calendar does:
  ``31-10`` and a day is ``01-11``, ``31-01`` and a month is ``28-02``.  A
  line that does not read as a date yet starts from today.
* **The keys**: the arrows move a day or a week, PgUp and PgDn a month,
  Ctrl+PgUp and Ctrl+PgDn a year, Home and End to the month's first and last
  day, ``T`` to today.  Enter or Space chooses; Esc leaves the line as it was.
* **The mouse**: a click on a day chooses it, a click on an arrow or the
  wheel turns the month.
* **The month and the year are picked too.**  A click on either in the top
  row drops a list of them over it -- the twelve months, or two hundred years
  around the one shown -- that typing searches as a choices list does, so
  ``19`` finds the nineteen-hundreds.  From the keys, ``M`` and ``Y`` drop
  them, and Tab and Shift+Tab move between the days, the month and the year:
  on the month or the year, Left and Right step it, Enter or Down drops
  its list, and Home and End go to January and December -- on the year, to
  its first day and its last.  A pick puts the keys back on the days, so Enter then chooses.
* **Weeks start on Monday**, ISO's order, where TVDEMO's started on Sunday;
  ``first_weekday`` says otherwise.  Today is marked in the ``today`` state.
"""

from __future__ import annotations

import calendar as _calendar
import datetime
from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.reactive import bind, reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navml.component import take_declared
from navml.widgets.dialog.drop_down import DropDown
from navml.widgets.dialog.history import History, HistoryList
from navml.widgets.dialog.masked_line.masked_line import spans

#: The month arrows, and what an ASCII terminal gets instead.
ARROWS = {"dos": "◄►", "ascii": "<>"}


#: What Tab steps through: the grid, then the top row's two halves.
SECTIONS = ("days", "month", "year")

#: How many years either side of the one shown the year list offers.
YEARS_AROUND = 100


class _Choice:
    """What a dropped month or year list calls back: a :class:`HistoryList`
    asks its button for nothing but ``choose``."""

    def __init__(self, choose: Any) -> None:
        self.choose = choose


def add_months(day: datetime.date, months: int) -> datetime.date:
    """*day*, *months* on, on the same day of the month or the last one there is."""
    index = day.year * 12 + day.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    last = _calendar.monthrange(year, month)[1]
    return day.replace(year=year, month=month, day=min(day.day, last))


class CalendarView(Widget):
    """A month of days with a cursor on one of them: TVDEMO's ``TCalendarView``.

    What :class:`Calendar` drops and Navigator's *Calendar* window holds.  It
    moves and pages and picks a month or a year, and paints itself :attr:`inset`
    cells in from its edges -- one for the drop-down, which draws its frame
    there, none in a window, whose frame is the window's.  Enter, Space and a
    click on a day call :meth:`picked`, which is the drop-down's choice and
    nothing here; Esc is not this view's.
    """

    #: Three columns a day, seven days and a blank either side.
    WIDTH = 22
    #: The month row, the weekday row and six weeks.
    HEIGHT = 8

    #: How far in from each edge the month is painted.
    inset = 0

    parts = ("title", "arrow", "weekday", "day")

    #: The day the cursor is on; the month shown is its month.
    day: datetime.date = reactive(datetime.date(2000, 1, 1))
    #: The first column's weekday: 0 is Monday, 6 is Sunday.
    first_weekday: int = reactive(0)
    #: Where the keys are: the ``days``, or the top row's ``month`` or ``year``.
    section: str = reactive("days")

    def __init__(self, day: datetime.date | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.day = day or datetime.date.today()

    # -- the model -----------------------------------------------------------

    def weeks(self) -> list[list[datetime.date | None]]:
        """The month shown, as six weeks of seven, None outside it."""
        cal = _calendar.Calendar(self.first_weekday)
        weeks = [
            [day if day.month == self.day.month else None for day in week]
            for week in cal.monthdatescalendar(self.day.year, self.day.month)
        ]
        while len(weeks) < 6:
            weeks.append([None] * 7)
        return weeks

    def move(self, days: int) -> None:
        try:
            self.day = self.day + datetime.timedelta(days=days)
        except OverflowError:
            pass

    def turn(self, months: int) -> None:
        if 1 <= self.day.year + (self.day.month - 1 + months) // 12 <= 9999:
            self.day = add_months(self.day, months)

    def set_month(self, month: int) -> None:
        """A month picked from the list: shown, and the keys back on the days."""
        self.turn(month - self.day.month)
        self.section = "days"

    def set_year(self, year: int) -> None:
        """A year picked from the list: shown, and the keys back on the days."""
        self.turn(12 * (year - self.day.year))
        self.section = "days"

    # -- the top row ---------------------------------------------------------

    def title_spans(self) -> tuple[tuple[int, str], tuple[int, str]]:
        """Where the month's name and the year are painted, and what they say."""
        month, year = _calendar.month_name[self.day.month], str(self.day.year)
        inner = self.width - 2 * self.inset
        start = self.inset + max(0, (inner - len(month) - 1 - len(year)) // 2)
        return (start, month), (start + len(month) + 1, year)

    def drop(self, section: str) -> HistoryList | None:
        """Drop the month list or the year list over its name, on the one shown."""
        app = self.application
        if app is None:
            return None
        self.section = section
        if section == "month":
            items = list(_calendar.month_name)[1:]
            current = self.day.month - 1
            chosen = lambda text: self.set_month(items.index(text) + 1)  # noqa: E731
        else:
            first = max(1, self.day.year - YEARS_AROUND)
            last = min(9999, self.day.year + YEARS_AROUND)
            items = [str(year) for year in range(first, last + 1)]
            current = self.day.year - first
            chosen = lambda text: self.set_year(int(text))  # noqa: E731
        window = HistoryList(_Choice(chosen))
        window.items = items
        window.cursor = current
        window.type_to_search = True
        # Over its own name, from the top row down, one column out each side
        # and room for the scroll bar; pushed in from the screen's edges.
        (mx, _), (yx, _) = self.title_spans()
        ox, oy = self.offset()
        widest = max(len(item) for item in items)
        # Wide enough for `` Search: 1985 `` on its bottom edge as well.
        width, height = max(widest + 3, 16), min(len(items) + 2, 14)
        root = app.root
        x = ox + self.x + (mx if section == "month" else yx) - 1
        y = oy + self.y + self.inset - 1
        x = max(0, min(x, root.width - width))
        y = max(0, min(y, root.height - height))
        window.x = bind(lambda o, v=x: v)
        window.y = bind(lambda o, v=y: v)
        window.width = bind(lambda o, v=width: v)
        window.height = bind(lambda o, v=height: v)
        app.overlay(window)
        return window

    def picked(self) -> None:
        """Enter, Space or a click on a day: nothing, for a view that only shows."""

    # -- input ---------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        day = self.day
        section = self.section
        if event.matches("tab", "shift+tab"):
            step = -1 if event.shift else 1
            self.section = SECTIONS[(SECTIONS.index(section) + step) % len(SECTIONS)]
        elif event.char in ("m", "M"):
            self.drop("month")
        elif event.char in ("y", "Y"):
            self.drop("year")
        elif section != "days":
            # The month or the year: stepped, or its list dropped.
            months = 1 if section == "month" else 12
            if event.matches("enter", "space", "down"):
                self.drop(section)
            elif event.matches("left"):
                self.turn(-months)
            elif event.matches("right"):
                self.turn(months)
            elif event.matches("home", "end"):
                # The year's first or last month; on the year, its first or
                # last day.
                last = event.matches("end")
                if section == "month":
                    self.turn((12 if last else 1) - day.month)
                else:
                    self.day = datetime.date(day.year, 12, 31) if last else datetime.date(day.year, 1, 1)
        elif event.matches("enter", "space"):
            self.picked()
        elif event.matches("left"):
            self.move(-1)
        elif event.matches("right"):
            self.move(1)
        elif event.matches("up"):
            self.move(-7)
        elif event.matches("down"):
            self.move(7)
        elif event.matches("pageup"):
            self.turn(-1)
        elif event.matches("pagedown"):
            self.turn(1)
        elif event.matches("ctrl+pageup"):
            self.turn(-12)
        elif event.matches("ctrl+pagedown"):
            self.turn(12)
        elif event.matches("home"):
            self.day = day.replace(day=1)
        elif event.matches("end"):
            self.day = day.replace(day=_calendar.monthrange(day.year, day.month)[1])
        elif event.char in ("t", "T"):
            self.day = datetime.date.today()
        else:
            return False
        return True

    def day_at(self, x: int, y: int) -> datetime.date | None:
        """The day painted at *x*, *y*, if any."""
        inset = self.inset
        row, column = y - inset - 2, (x - inset) // 3
        if not (0 <= row < 6 and 0 <= column < 7 and inset <= x < inset + 3 * 7):
            return None
        return self.weeks()[row][column]

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.is_wheel:
            self.turn(-1 if event.button == "wheel_up" else 1)
            return True
        if event.action != "press" or event.button != "left":
            return True
        (mx, month), (yx, year) = self.title_spans()
        inset, top = self.inset, event.y == self.inset
        if top and inset <= event.x <= inset + 2:
            self.turn(-1)
        elif top and self.width - inset - 3 <= event.x <= self.width - inset - 1:
            self.turn(1)
        elif top and mx <= event.x < mx + len(month):
            self.drop("month")
        elif top and yx <= event.x < yx + len(year):
            self.drop("year")
        else:
            day = self.day_at(event.x, event.y)
            if day is not None:
                self.day = day
                self.picked()
        if self.can_focus and self.application is not None and self.application.focused is not self:
            self.focus()
        return True

    # -- painting ------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        inset = self.inset
        if self.width < 2 * inset + 2 or self.height < 2 * inset + 2:
            return
        if inset:
            surface.draw_box(0, 0, self.width, self.height, self.style,
                             charset=self.box_charset(), fill=" ")
        else:
            surface.fill(0, 0, self.width, self.height, " ", self.style)
        day = self.day
        arrows = ARROWS["dos" if self.glyphs >= GLYPHS_UNICODE else "ascii"]
        arrow = self.part_style("arrow")
        surface.draw_text(inset + 1, inset, arrows[0], arrow)
        surface.draw_text(self.width - inset - 2, inset, arrows[1], arrow)
        (mx, month), (yx, year) = self.title_spans()
        surface.draw_text(mx, inset, month, self.part_style("title", selected=self.section == "month"))
        surface.draw_text(yx, inset, year, self.part_style("title", selected=self.section == "year"))
        names = [_calendar.day_abbr[(self.first_weekday + i) % 7][:2] for i in range(7)]
        weekday = self.part_style("weekday")
        for column, name in enumerate(names):
            surface.draw_text(inset + 1 + 3 * column, inset + 1, name, weekday)
        today = datetime.date.today()
        for row, week in enumerate(self.weeks()):
            for column, cell in enumerate(week):
                if cell is None:
                    continue
                style = self.part_style(
                    "day", selected=cell == day and self.section == "days", today=cell == today
                )
                surface.draw_text(inset + 3 * column, inset + 2 + row, f"{cell.day:>3}", style)


class Calendar(CalendarView, DropDown):
    """A month of days, framed and modal, dropped by a :class:`DateButton`."""

    #: The view and the frame round it.
    WIDTH = CalendarView.WIDTH + 2
    HEIGHT = CalendarView.HEIGHT + 2

    inset = 1

    def __init__(self, button: DateButton | None = None, day: datetime.date | None = None,
                 **kwargs: Any) -> None:
        super().__init__(day, **kwargs)
        #: The button that dropped this, and the line it fills.
        self.button = button

    def layout(self, width: int, height: int) -> None:
        """Keep the rectangle the button worked out; a cascade must not refit it."""

    def picked(self) -> None:
        self.choose()

    def choose(self) -> None:
        """The day goes into the line, and the calendar comes down."""
        self.close()
        if self.button is not None:
            self.button.pick(self.day)

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("escape"):
            self.close()
        else:
            await super().on_key(event)
        # A modal calendar keeps every other key: nothing behind it may act.
        return True


class DateButton(History):
    """Three cells beside a date line, and the calendar they drop."""


    #: How the line spells a date: ``strftime``'s directives.
    date_format: str = reactive("%d-%m-%Y")

    def __init__(self, **kwargs: Any) -> None:
        take_declared(self, kwargs)
        super().__init__(**kwargs)

    def record(self) -> None:
        """A date line has no history to record into."""

    def parse(self, text: str) -> datetime.date | None:
        """The day *text* names in :attr:`date_format`, or None."""
        try:
            return datetime.datetime.strptime(text.strip(), self.date_format).date()
        except ValueError:
            return None

    def open(self) -> Calendar | None:
        """Drop the calendar on the line's day, or on today.  None if it cannot."""
        app, link = self.application, self.link
        if app is None or link is None or link.inert:
            return None
        popup = Calendar(self, self.parse(link.value))
        x, y = self.popup_origin(Calendar.WIDTH, Calendar.HEIGHT)
        popup.x = bind(lambda o, v=x: v)
        popup.y = bind(lambda o, v=y: v)
        popup.width = bind(lambda o: Calendar.WIDTH)
        popup.height = bind(lambda o: Calendar.HEIGHT)
        app.overlay(popup)
        return popup

    def step(self, text: str, index: int, delta: int) -> str | None:
        """*text* with its date stepped by *delta* at the place *index*.

        Today, if *text* is not a date yet; *text* unchanged if the step
        would leave the years a ``date`` can hold.  None for a place no
        directive covers, which leaves the line to step it as a number.
        """
        day = self.parse(text)
        if day is None:
            return datetime.date.today().strftime(self.date_format)
        for start, length, directive in spans(self.date_format):
            if start <= index < start + length:
                amount = delta * 10 ** (start + length - 1 - index)
                try:
                    if directive == "d":
                        day = day + datetime.timedelta(days=amount)
                    elif directive == "m":
                        day = add_months(day, amount)
                    elif directive in ("Y", "y"):
                        day = add_months(day, 12 * amount)
                    else:
                        return None
                except (OverflowError, ValueError):
                    return text
                if not 1 <= day.year <= 9999:
                    return text
                return day.strftime(self.date_format)
        return None

    def pick(self, day: datetime.date) -> None:
        """*day* into the line, in the line's own spelling."""
        self.choose(day.strftime(self.date_format))
