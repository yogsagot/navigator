"""The programmer's bits, to flip: Windows' *bit toggling keypad*.

Not DN's: a departure, asked for.  Sixty-four bits in four rows of sixteen,
the highest first, each row between its highest and lowest bit's number; a
bit past the word is greyed and stays as it is.  A click on a bit, or Space
or Enter on the one the arrows are on, flips it: :class:`BitFlipped`, which
the window turns into the line's new value.  Numbers read left to right on
a mirrored screen too, as the console's do.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navml.widgets.dialog.control import Control

#: How many bits a row holds, and how many rows there are.
ROW_BITS, ROWS = 16, 4
#: The cells a row's numbers take on either side of its bits.
LABEL = 4


@dataclass(frozen=True, slots=True)
class BitFlipped(Event):
    """Bit *bit* (0 the lowest) was flipped."""

    bit: int


def bit_column(index: int) -> int:
    """Where, from the row's first bit, bit *index* of a row (0 the leftmost) is drawn:
    a blank between bits, two between nibbles."""
    return index * 2 + index // 4 * 2


#: The cells a row's bits take.
ROW_WIDTH = bit_column(ROW_BITS - 1) + 1


class BitGrid(Control):
    """A word's bits, one row of sixteen to a line."""

    #: The word's bits, unsigned.
    value: int = reactive(0)
    #: The word's width: bits from here up are greyed.
    bits: int = reactive(64)
    #: The bit the keyboard is on.
    cursor: int = reactive(0)

    parts = ("bit", "label")
    mirrors = False

    def _origin(self) -> tuple[int, int]:
        """The first row's first bit, the grid centred in the widget."""
        width = LABEL + ROW_WIDTH + LABEL
        tall = ROWS * 2 - 1
        return max(0, (self.width - width) // 2) + LABEL, max(0, (self.height - tall) // 2)

    def render(self, surface: Surface) -> None:
        style, label = self.style, self.part_style("label")
        surface.fill(0, 0, self.width, self.height, " ", style)
        left, top = self._origin()
        for row in range(ROWS):
            high = (ROWS - row) * ROW_BITS - 1
            y = top + row * 2
            surface.draw_text(left - LABEL, y, f"{high:>2}", label)
            surface.draw_text(left + ROW_WIDTH + 2, y, f"{high - ROW_BITS + 1:<2}", label)
            for index in range(ROW_BITS):
                bit = high - index
                on = bool(self.value >> bit & 1)
                look = self.part_style("bit", set=on, outside=bit >= self.bits,
                                       selected=self.focused and bit == self.cursor)
                surface.draw_text(left + bit_column(index), y, "1" if on else "0", look)

    def bit_at(self, x: int, y: int) -> int | None:
        """The bit drawn at *x*, *y*, or None."""
        left, top = self._origin()
        row, odd = divmod(y - top, 2)
        if odd or not 0 <= row < ROWS:
            return None
        for index in range(ROW_BITS):
            if x - left == bit_column(index):
                return (ROWS - row) * ROW_BITS - 1 - index
        return None

    async def flip(self, bit: int) -> bool:
        if bit >= self.bits or self.inert:
            return True
        self.cursor = bit
        return await self.emit(BitFlipped(bit))

    async def on_key(self, event: KeyEvent) -> bool:
        moves = {"left": 1, "right": -1, "up": ROW_BITS, "down": -ROW_BITS}
        for name, by in moves.items():
            if event.matches(name):
                self.cursor = (self.cursor + by) % (ROW_BITS * ROWS)
                return True
        if event.matches("home"):
            self.cursor = self.bits - 1
            return True
        if event.matches("end"):
            self.cursor = 0
            return True
        if event.matches("space", "enter") or event.char == " ":
            return await self.flip(self.cursor)
        return False

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.action != "press" or event.button != "left":
            return False
        bit = self.bit_at(event.x, event.y)
        return False if bit is None else await self.flip(bit)
