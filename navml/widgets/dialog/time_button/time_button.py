"""The ``▐↓▌`` beside a time line, and the clock face it drops.

Neither DOS Navigator nor Turbo Vision had one; it is the calendar's
companion, and built the same way (see :mod:`navml.widgets.dialog.date_button`).

* **The button reads the line by its ``time_format``** (``%H:%M:%S`` unless
  told) and opens on that time, or on the present one; choosing writes it
  back in the same format.  A format without ``%S`` drops seconds from the
  face too.  A 12-hour format (``%I`` and ``%p``) is read and written with
  ``am``/``pm`` (``spell_time``/``read_time``), and the face shows the hour
  1 to 12 with an ``am``/``pm`` column last, which Up and Down turn over and
  ``A`` or ``P`` typed anywhere sets; two digits typed into the hour are an
  hour of the half day shown.
* **Alt+Down in the line drops the face, as a click does.**  **Up and Down
  in the line step the time** (:meth:`TimeButton.step`) by the value of the
  place under the caret, carrying as a clock does and wrapping round the
  day: ``23:59:30`` and a minute is ``00:00:30``.  A line that does not read
  as a time yet starts from now.
* **The keys**: Left, Right, Tab and Shift+Tab pick the hours, minutes or
  seconds; Up and Down step the one picked by one, PgUp and PgDn by ten,
  wrapping round; two digits typed set it and go on to the next; ``N`` is now.
  Enter chooses; Esc leaves the line as it was.
* **The mouse**: a click on a number picks it, a click on the ``▲`` or ``▼``
  over and under it steps it, and the wheel over a number steps that one.
"""

from __future__ import annotations

import datetime
from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.reactive import bind, reactive
from navkit.screen import Surface

from navml.component import take_declared
from navml.widgets.dialog.drop_down import DropDown
from navml.widgets.dialog.history import History
from navml.widgets.dialog.masked_line.masked_line import read_time, spans, spell_time

#: Over and under the number picked, and what an ASCII terminal gets.
ARROWS = {"dos": "▲▼", "ascii": "^v"}

#: How far each of hours, minutes and seconds goes before it wraps.
LIMITS = (24, 60, 60)


class TimePicker(DropDown):
    """Hours, minutes and perhaps seconds, framed and modal, one of them picked."""

    #: The frame and three rows: the up arrow, the numbers, the down arrow.
    HEIGHT = 5

    parts = ("value", "separator", "arrow")

    #: The hours, minutes and seconds.
    values: tuple = reactive((0, 0, 0))
    #: Which of them the keys step: 0, 1 or 2.
    column: int = reactive(0)
    #: Whether the seconds are shown and stepped.
    seconds: bool = reactive(True)
    #: Whether the hour is shown 1 to 12, with an ``am``/``pm`` column last.
    #: :attr:`values` stay 24-hour either way.
    twelve: bool = reactive(False)

    def __init__(self, button: TimeButton | None = None, when: datetime.time | None = None,
                 seconds: bool = True, twelve: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.button = button
        self.seconds = seconds
        self.twelve = twelve
        when = when or datetime.datetime.now().time()
        self.values = (when.hour, when.minute, when.second if seconds else 0)
        #: The first digit typed into the column, waiting for its second.
        self._typed: str = ""

    @staticmethod
    def width_for(seconds: bool, twelve: bool = False) -> int:
        """`` 14 : 25 : 57 `` inside the frame, or without its last third,
        and five columns more for a 12-hour face's ``am``/``pm``."""
        return (16 if seconds else 11) + (5 if twelve else 0)

    def layout(self, width: int, height: int) -> None:
        """Keep the rectangle the button worked out."""

    # -- the model -----------------------------------------------------------

    @property
    def numbers(self) -> int:
        """How many columns are numbers: hours, minutes and perhaps seconds."""
        return 3 if self.seconds else 2

    @property
    def columns(self) -> int:
        return self.numbers + (1 if self.twelve else 0)

    @property
    def meridiem(self) -> int | None:
        """The ``am``/``pm`` column, or None on a 24-hour face."""
        return self.numbers if self.twelve else None

    def set_half(self, pm: bool) -> None:
        """The same hour in the morning, or in the afternoon."""
        values = list(self.values)
        values[0] = values[0] % 12 + (12 if pm else 0)
        self.values = tuple(values)
        self._typed = ""

    @property
    def time(self) -> datetime.time:
        hours, minutes, seconds = self.values
        return datetime.time(hours, minutes, seconds)

    def step(self, delta: int, column: int | None = None) -> None:
        """Step one number by *delta*, wrapping round its limit."""
        column = self.column if column is None else column
        if column == self.meridiem:
            self.set_half(self.values[0] < 12)
            return
        values = list(self.values)
        values[column] = (values[column] + delta) % LIMITS[column]
        self.values = tuple(values)
        self._typed = ""

    def pick(self, column: int) -> None:
        self.column = max(0, min(column, self.columns - 1))
        self._typed = ""

    def type_digit(self, digit: str) -> None:
        """A digit typed: the first sets the number, the second finishes it.

        On a 12-hour face the hour typed is one of the half day shown, ``12``
        its first; a digit on the ``am``/``pm`` column is refused.
        """
        if self.column == self.meridiem:
            return
        twelve_hour = self.twelve and self.column == 0
        limit = 13 if twelve_hour else LIMITS[self.column]
        values = list(self.values)
        if self._typed:
            number = int(self._typed + digit)
            number = number if number < limit else int(digit)
            done = True
        else:
            number, done = int(digit), False
        if twelve_hour:
            number = number % 12 + (12 if values[0] >= 12 else 0)
        values[self.column] = number
        self.values = tuple(values)
        if done:
            self.pick(self.column + 1 if self.column + 1 < self.numbers else self.column)
        else:
            self._typed = digit

    def choose(self) -> None:
        self.close()
        if self.button is not None:
            self.button.pick(self.time)

    # -- input ---------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("escape"):
            self.close()
        elif event.matches("enter"):
            self.choose()
        elif event.matches("up"):
            self.step(1)
        elif event.matches("down"):
            self.step(-1)
        elif event.matches("pageup"):
            self.step(10)
        elif event.matches("pagedown"):
            self.step(-10)
        elif event.matches("left", "shift+tab"):
            self.pick(self.column - 1)
        elif event.matches("right", "tab"):
            self.pick(self.column + 1)
        elif event.matches("home"):
            self.pick(0)
        elif event.matches("end"):
            self.pick(self.columns - 1)
        elif event.char and event.char.isdigit() and event.is_printable:
            self.type_digit(event.char)
        elif self.twelve and event.char in ("a", "A", "p", "P"):
            self.set_half(event.char in ("p", "P"))
        elif event.char in ("n", "N"):
            now = datetime.datetime.now().time()
            self.values = (now.hour, now.minute, now.second if self.seconds else 0)
            self._typed = ""
        return True

    def column_at(self, x: int) -> int | None:
        for column in range(self.columns):
            if 2 + 5 * column <= x <= 3 + 5 * column:
                return column
        return None

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        column = self.column_at(event.x)
        if event.is_wheel:
            if column is not None:
                self.step(1 if event.button == "wheel_up" else -1, column)
            return True
        if event.action != "press" or event.button != "left" or column is None:
            return True
        self.pick(column)
        if event.y == 1:
            self.step(1)
        elif event.y == 3:
            self.step(-1)
        return True

    # -- painting ------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        if self.width < 2 or self.height < 2:
            return
        surface.draw_box(0, 0, self.width, self.height, self.style,
                         charset=self.box_charset(), fill=" ")
        arrows = ARROWS["dos" if self.glyphs >= GLYPHS_UNICODE else "ascii"]
        arrow = self.part_style("arrow")
        x = 2 + 5 * self.column
        surface.draw_text(x, 1, arrows[0] * 2, arrow)
        surface.draw_text(x, 3, arrows[1] * 2, arrow)
        separator = self.part_style("separator")
        for column in range(self.columns):
            if column == self.meridiem:
                text = "am" if self.values[0] < 12 else "pm"
            elif column == 0 and self.twelve:
                text = f"{(self.values[0] - 1) % 12 + 1:02}"
            else:
                text = f"{self.values[column]:02}"
                if column:
                    surface.draw_text(5 * column, 2, ":", separator)
            surface.draw_text(
                2 + 5 * column, 2, text,
                self.part_style("value", selected=column == self.column),
            )


class TimeButton(History):
    """Three cells beside a time line, and the face they drop."""


    #: How the line spells a time: ``strftime``'s directives.
    time_format: str = reactive("%H:%M:%S")

    def __init__(self, **kwargs: Any) -> None:
        take_declared(self, kwargs)
        super().__init__(**kwargs)

    def record(self) -> None:
        """A time line has no history to record into."""

    def parse(self, text: str) -> datetime.time | None:
        """The time *text* names in :attr:`time_format`, or None."""
        try:
            return read_time(text.strip(), self.time_format)
        except ValueError:
            return None

    def open(self) -> TimePicker | None:
        """Drop the face on the line's time, or on now.  None if it cannot."""
        app, link = self.application, self.link
        if app is None or link is None or link.inert:
            return None
        seconds, twelve = "%S" in self.time_format, "%p" in self.time_format
        popup = TimePicker(self, self.parse(link.value), seconds=seconds, twelve=twelve)
        width = TimePicker.width_for(seconds, twelve)
        x, y = self.popup_origin(width, TimePicker.HEIGHT)
        popup.x = bind(lambda o, v=x: v)
        popup.y = bind(lambda o, v=y: v)
        popup.width = bind(lambda o, v=width: v)
        popup.height = bind(lambda o: TimePicker.HEIGHT)
        app.overlay(popup)
        return popup

    def step(self, text: str, index: int, delta: int) -> str | None:
        """*text* with its time stepped by *delta* at the place *index*.

        Now, if *text* is not a time yet.  None for a place no directive
        covers, which leaves the line to step it as a number.
        """
        when = self.parse(text)
        if when is None:
            return spell_time(datetime.datetime.now(), self.time_format)
        # ``%p`` has one place: a step either way turns the half day over.
        seconds = {"H": 3600, "I": 3600, "M": 60, "S": 1, "p": 43200}
        for start, length, directive in spans(self.time_format):
            if start <= index < start + length and directive in seconds:
                if directive == "p":
                    amount = seconds["p"]
                else:
                    amount = delta * 10 ** (start + length - 1 - index) * seconds[directive]
                total = (when.hour * 3600 + when.minute * 60 + when.second + amount) % 86400
                stepped = datetime.time(total // 3600, total // 60 % 60, total % 60)
                return spell_time(stepped, self.time_format)
        return None

    def pick(self, when: datetime.time) -> None:
        """*when* into the line, in the line's own spelling."""
        self.choose(spell_time(when, self.time_format))
