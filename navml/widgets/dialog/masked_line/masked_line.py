"""A line whose digits have fixed places: a date, a time.

Not Turbo Vision's, whose input line took any text and left the checking to
a validator on OK.  This is the line a date and a time want instead: the
separators are part of it and cannot be typed over or deleted, and the only
thing that goes in is a digit, at the place for one.

* **``mask`` says the shape**: ``9`` is a place for a digit, anything else is
  painted as itself and stepped over -- ``99-99-9999`` is a date.
  :func:`mask_for` derives one from a ``strftime`` format.  **``base`` says
  which digits** go in: ten by default, eight for a file mode, which then
  refuses an ``8`` or a ``9`` and steps in eights.  A place may hold
  something else the program put there -- a ``?`` for *not known* -- which
  is typed over like a blank.
* **A digit overwrites the place under the caret** and the caret goes on to
  the next, staying on the last.  **Left and Right** move between the
  places, and **Home and End** jump to the first and the last.
* **Up and Down step the number under the caret** by the place's value --
  one on the units, ten on the tens -- with the caret staying put, and
  **PgUp and PgDn by ten times that**.  The line's button decides what that
  means when it has a ``step`` (a date steps as a calendar does, carrying a
  day past the month's end into the next); without one the run of digits is
  a plain number, carrying within itself and wrapping, ``99`` to ``00``.
* **Backspace and Delete blank the place under the caret**: Delete leaves
  the caret there, Backspace then steps it back a place, so held down it
  clears the line backwards as it would any text.
* **Every other key is refused**, letters and pastes included, apart from
  those that belong to the dialog (Tab, Shift+Tab, Esc, Enter, Alt+letter)
  and Alt+Down, which drops its button's picker.
* **An empty line stays empty** until a digit goes in, and shows the
  separators meanwhile, so *leave it as it is* is still something the line
  can say.  The first digit fills the rest with blanks, which a reader of
  ``value`` then refuses as incomplete; blanking the last digit there is
  makes the line empty again.
* **A click puts the caret on the place under it**, or the next one; there
  is no selection to drag.
"""

from __future__ import annotations

from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent, PasteEvent
from navkit.reactive import reactive
from navkit.screen import Surface

from navml.widgets.dialog.input_line import InputLine

#: A place for a digit, in a mask.
DIGIT = "9"

#: What each ``strftime`` directive a date or a time uses takes in a mask.
_DIRECTIVES = {"d": "99", "m": "99", "y": "99", "Y": "9999", "H": "99", "M": "99", "S": "99"}


def spans(format: str) -> list[tuple[int, int, str]]:
    """Where each directive of a ``strftime`` *format* sits in its mask.

    ``(start, length, directive)`` for each, so ``%d-%m-%Y`` is
    ``[(0, 2, "d"), (3, 2, "m"), (6, 4, "Y")]``.
    """
    found, at, index = [], 0, 0
    while index < len(format):
        if format[index] == "%" and index + 1 < len(format):
            directive = format[index + 1]
            length = len(_DIRECTIVES.get(directive, ""))
            found.append((at, length, directive))
            at += length
            index += 2
        else:
            at += 1
            index += 1
    return found


def mask_for(format: str) -> str:
    """The mask a ``strftime`` *format* of numbers spells: ``%d-%m-%Y`` is ``99-99-9999``.

    ``ValueError`` for a directive that is not a fixed run of digits.
    """
    mask, index = [], 0
    while index < len(format):
        char = format[index]
        if char == "%" and index + 1 < len(format):
            directive = format[index + 1]
            if directive not in _DIRECTIVES:
                raise ValueError(f"%{directive} is not a fixed run of digits")
            mask.append(_DIRECTIVES[directive])
            index += 2
        else:
            if char == DIGIT:
                raise ValueError(f"{format!r} has a literal {DIGIT}, which a mask cannot tell from a digit")
            mask.append(char)
            index += 1
    return "".join(mask)


class MaskedLine(InputLine):
    """An input line of digits in fixed places, typed over, never inserted into."""

    #: The shape: ``9`` a digit's place, anything else a literal.
    mask: str = reactive("")
    #: Which digits a place takes, ``0`` to ``base - 1``, and what the plain
    #: stepping carries in.
    base: int = reactive(10)

    # -- the places ----------------------------------------------------------

    @property
    def places(self) -> list[int]:
        """The indices a digit may go at."""
        return [index for index, char in enumerate(self.mask) if char == DIGIT]

    @property
    def blank(self) -> str:
        """The mask with every place empty: what the first digit fills in."""
        return "".join(" " if char == DIGIT else char for char in self.mask)

    def _place_from(self, index: int, step: int = 1) -> int | None:
        """The first place at or past *index* going *step*-wise, or None."""
        places = self.places
        if step > 0:
            return next((p for p in places if p >= index), None)
        return next((p for p in reversed(places) if p <= index), None)

    def _settle(self) -> None:
        """Put the caret on a place: the one it is on, or the next, or the last."""
        places = self.places
        if not places:
            return
        place = self._place_from(self.cursor)
        self.cursor = place if place is not None else places[-1]
        self.anchor = None

    # -- input ---------------------------------------------------------------

    def accepts(self, char: str) -> bool:
        """Whether *char* is a digit this line's base has."""
        return char.isdigit() and int(char) < self.base

    def type_digit(self, digit: str) -> None:
        places = self.places
        if not places or not self.accepts(digit):
            return
        value = self.value if len(self.value) == len(self.mask) else self.blank
        self._settle()
        at = self.cursor
        self.value = value[:at] + digit + value[at + 1 :]
        later = self._place_from(at + 1)
        self.cursor = later if later is not None else at
        self.anchor = None

    def blank_place(self) -> None:
        """Blank the place under the caret; the line is empty once every place is."""
        if len(self.value) != len(self.mask):
            return
        self._settle()
        at = self.cursor
        value = self.value[:at] + " " + self.value[at + 1 :]
        self.value = "" if value == self.blank else value
        self.cursor = at

    def step_place(self, delta: int) -> None:
        """Step the number under the caret by *delta* times the place's value.

        The button's ``step`` answers when there is one; otherwise the run of
        digits around the caret is a number on its own, blanks reading as 0.
        """
        if not self.places:
            return
        self._settle()
        at = self.cursor
        button = self.history
        step = getattr(button, "step", None)
        stepped = step(self.value, at, delta) if step is not None else None
        if stepped is None:
            stepped = self._step_run(at, delta)
        self.value = stepped
        self.cursor = at

    def _step_run(self, at: int, delta: int) -> str:
        """The value with the digit run around *at* stepped, carrying and wrapping within it."""
        value = self.value if len(self.value) == len(self.mask) else self.blank
        start = at
        while start > 0 and self.mask[start - 1] == DIGIT:
            start -= 1
        stop = at + 1
        while stop < len(self.mask) and self.mask[stop] == DIGIT:
            stop += 1
        base, width = self.base, stop - start
        number = 0
        for char in value[start:stop]:
            number = number * base + (int(char) if self.accepts(char) else 0)
        number = (number + delta * base ** (stop - 1 - at)) % base ** width
        digits = []
        for _ in range(width):
            number, digit = divmod(number, base)
            digits.append(str(digit))
        return value[:start] + "".join(reversed(digits)) + value[stop:]

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        if event.matches("alt+down"):
            return await super().on_key(event)
        if event.alt or event.matches("tab", "shift+tab", "escape", "enter"):
            return False
        steps = {"up": 1, "down": -1, "pageup": 10, "pagedown": -10}
        if event.name in steps:
            self.step_place(steps[event.name])
            return True
        if event.is_printable and event.char and self.accepts(event.char):
            self.type_digit(event.char)
        elif event.matches("delete"):
            self.blank_place()
        elif event.matches("backspace"):
            self.blank_place()
            self._settle()
            earlier = self._place_from(self.cursor - 1, -1)
            if earlier is not None:
                self.cursor = earlier
        elif event.matches("left"):
            self._settle()
            earlier = self._place_from(self.cursor - 1, -1)
            if earlier is not None:
                self.cursor = earlier
        elif event.matches("home", "end"):
            places = self.places
            self.cursor = places[0] if event.matches("home") else places[-1]
            self.anchor = None
        elif event.matches("right"):
            self._settle()
            later = self._place_from(self.cursor + 1)
            if later is not None:
                self.cursor = later
        # Anything else is refused, and taken so nothing behind acts on it.
        return True

    async def on_paste(self, event: PasteEvent) -> bool:
        return not self.inert

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if self.inert or event.button != "left":
            return False
        if event.action == "press":
            self.focus()
            self.cursor = min(self._index_at(event.x), max(0, len(self.mask) - 1))
            self._settle()
        return True

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        return not self.inert

    def select_all(self) -> None:
        """Nothing is selected in a masked line: the caret goes to the first place."""
        self.cursor = 0
        self._settle()

    # -- painting ------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        super().render(surface)
        if not self.value and self.room > 0:
            surface.draw_text(1, 0, self.blank, self.style, self.room)
