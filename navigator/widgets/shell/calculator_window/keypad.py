"""The button calculators' pads: a table of :class:`Key` as buttons.

Not DN's: a departure, asked for -- DOS Navigator's calculator was the one
line.  A pad's buttons never take the keyboard, so the expression line keeps
it and a click goes in where its cursor is; a press is :class:`PadPressed`,
carrying the key, which the window acts on.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.events import Event
from navkit.glyphs import GLYPHS_ASCII
from navml.widgets.dialog.button import Button
from navml.widgets.layout.grid_layout import GridLayout


@dataclass(frozen=True)
class Key:
    """One button of a pad: what it shows and what it does to the line."""

    caption: str
    #: ``insert`` *arg*; ``wrap`` the trailing operand in *arg*
    #: (:func:`~navigator.lib.utilities.calculator.wrap_last`); ``negate``,
    #: ``percent``, ``clear``, ``entry``, ``back``, ``equals``, ``exponent``;
    #: ``second`` and ``hyp``, the toggles; ``memory`` *arg* (``clear``,
    #: ``recall``, ``add``, ``subtract``, ``store``); ``bits``.
    action: str
    arg: str = ""
    #: The caption on the ASCII tier, for one that is not ASCII.
    ascii: str = ""
    #: What the key is while *2nd* is on, *hyp* is on, or both are.
    second: Key | None = None
    hyp: Key | None = None
    both: Key | None = None
    #: Its colours' class: ``digit``, ``operator``, ``equals``, ``function`` or ``control``.
    role: str = "function"

    def variant(self, second: bool, hyp: bool) -> Key:
        """The key this one is under the toggles."""
        if second and hyp and self.both is not None:
            return self.both
        if hyp and self.hyp is not None:
            return self.hyp
        if second and self.second is not None:
            return self.second
        return self

    @property
    def digit(self) -> int | None:
        """The digit this key types, for the programmer's base to allow or not."""
        if self.action == "insert" and len(self.arg) == 1 and self.arg in "0123456789ABCDEF":
            return int(self.arg, 16)
        return None


@dataclass(frozen=True, slots=True)
class PadPressed(Event):
    """A pad's key was pressed, by the mouse or a Space."""

    key: Key


class PadButton(Button):
    """A pad's button: pressed, it says which key it is, and it never takes
    the keyboard from the expression line."""

    accepts_focus = False

    def __init__(self, key: Key, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.key = key
        self.add_class(key.role)

    async def press(self) -> bool:
        if self.inert:
            return False
        return await self.emit(PadPressed(self.key))


class Keypad(GridLayout):
    """A pad's keys in rows, every button the same size."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.table: list[list[Key]] = []
        self.second = self.hyp = False
        #: The base digits are typed in: a digit at or past it is greyed.
        self.radix = 16

    def show(self, table: list[list[Key]]) -> None:
        """*table*'s keys as this pad's buttons, row by row."""
        for child in list(self.children):
            self.remove(child)
        self.table = table
        self.columns = max((len(row) for row in table), default=1)
        for row in table:
            for key in row:
                self.add(PadButton(key))
        self.refresh()

    def refresh(self) -> None:
        """Each button's caption under the toggles, and its digit allowed or not."""
        ascii_only = self.glyphs <= GLYPHS_ASCII
        keys = [key for row in self.table for key in row]
        for button, key in zip(self.buttons(), keys, strict=True):
            shown = key.variant(self.second, self.hyp)
            button.key = shown
            button.text = shown.ascii if ascii_only and shown.ascii else shown.caption
            digit = shown.digit
            button.disabled = digit is not None and digit >= self.radix

    def buttons(self) -> list[PadButton]:
        return [child for child in self.children if isinstance(child, PadButton)]
