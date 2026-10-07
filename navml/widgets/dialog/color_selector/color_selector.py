"""Turbo Vision's ``TColorSelector`` and ``TColorDisplay`` (COLORSEL.PAS).

Python alone, as :class:`~navml.widgets.dialog.check_boxes.CheckBoxes` is:
both paint every cell they have and place nothing, so a markup half would say
only what the class statement says.

**The colours are the sixteen of the PC's attribute byte, in its order** --
black, blue, green, cyan, red, magenta, brown, light gray, and their bright
halves -- because that is the order the grid is read in (row by row, four to a
row, as ``TColorSelector.Draw`` laid it out) and the index a caller keeps.
They are painted by *name*, so ``blue`` is whatever the terminal, or a pinned
palette, draws for blue.

A cell is a swatch of three blanks on the colour rather than TV's three
``█`` in it, which is the same picture on every glyph tier; the chosen one
carries a mark in its middle, TV's ``#8``.  ``color`` is ``-1`` when what the
caller holds is not one of the sixteen -- a true colour, the terminal's
default -- and then no cell is marked.
"""

from __future__ import annotations

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.style import Style
from navkit.stylesheet import COLOR_NAMES

from navml.widgets.dialog.control import Control

#: The attribute byte's sixteen colours, in its order, by navkit's names.
COLORS = (
    "black", "blue", "green", "cyan",
    "red", "magenta", "brown", "light_gray",
    "dark_gray", "light_blue", "light_green", "light_cyan",
    "light_red", "light_magenta", "yellow", "white",
)

#: The grid's width in cells, TV's ``Width = 4``.
WIDTH = 4

#: A cell's width in columns.
CELL = 3


class ColorSelector(Control):
    """``TColorSelector``: a four-by-four grid of colours, one of them chosen."""

    #: The chosen colour's index in :data:`COLORS`, or ``-1`` for none.
    color: int = reactive(-1)

    #: The mark on the chosen cell.  TV drew ``#8``, the inverse bullet.
    mark = "◘"
    ascii_mark = "*"

    def choose(self, color: int) -> None:
        """*color* chosen.  TV broadcast ``cmColorForegroundChanged``; here
        ``color`` is reactive, and the owner follows it."""
        self.color = color

    async def on_key(self, event: KeyEvent) -> bool:
        last = len(COLORS) - 1
        color = max(0, self.color)
        if event.name == "left":
            self.choose(color - 1 if color > 0 else last)
        elif event.name == "right":
            self.choose(color + 1 if color < last else 0)
        elif event.name == "up":
            # TV's kbUp: a row up, and off the top row onto the last row one
            # column to the left, so a held key walks every colour.
            if color > WIDTH - 1:
                self.choose(color - WIDTH)
            else:
                self.choose(last if color == 0 else color + last - WIDTH)
        elif event.name == "down":
            if color < last - (WIDTH - 1):
                self.choose(color + WIDTH)
            else:
                self.choose(0 if color == last else color - (last - WIDTH))
        else:
            return False
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.action != "press" or event.button != "left" or self.inert:
            return False
        column, row = event.x // CELL, event.y
        if 0 <= column < WIDTH and 0 <= row < len(COLORS) // WIDTH:
            self.choose(row * WIDTH + column)
        return True

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        mark = self.mark if self.glyphs > 1 else self.ascii_mark
        for index, name in enumerate(COLORS):
            row, column = divmod(index, WIDTH)
            colour = COLOR_NAMES[name]
            swatch = Style(fg=colour, bg=colour)
            surface.fill(column * CELL, row, CELL, 1, " ", swatch)
            if index == self.color:
                # Drawn black on the lighter half and white on the darker, so
                # the mark shows on every swatch.
                ink = COLOR_NAMES["black" if index in (2, 3, 6, 7) or index >= 9 else "white"]
                surface.set_cell(column * CELL + 1, row, mark, Style(fg=ink, bg=colour))

    def cursor_position(self) -> tuple[int, int] | None:
        if self.color < 0:
            return None
        row, column = divmod(self.color, WIDTH)
        return column * CELL + 1, row


class ColorDisplay(Control):
    """``TColorDisplay``: a sample of text in the style being chosen."""

    accepts_focus = False

    #: What is shown, repeated across the view -- DN's ``' '+dlColorsText``.
    text: str = reactive(" Text ")

    #: The style the sample is drawn in.
    sample: Style = reactive(Style())

    def render(self, surface: Surface) -> None:
        if not self.text:
            return
        line = (self.text * (self.width // len(self.text) + 1))[: self.width]
        for y in range(self.height):
            for x, char in enumerate(line):
                surface.set_cell(x, y, char, self.sample)
