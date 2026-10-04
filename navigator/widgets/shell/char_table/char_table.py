"""The grid inside *ASCII Chart*: DOS Navigator's ``TTable`` (``ASCIITAB.PAS``).

All 256 characters of code page 437, 32 to a row and eight rows, each drawn as
a VGA drew it (:func:`navigator.viewer.cp437`).  The block cursor stands on
the character in hand, :attr:`CharTable.code`; the arrows move it a cell,
Home and End to the first and the last, and a press or a drag puts it under
the pointer.  A double click is Enter's (``ChosenEvent``), as ``TTable`` put
the character back as a key press.
"""

from __future__ import annotations

from typing import Any

from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navml.widgets.dialog.tree_view import ChosenEvent

from navigator.viewer import cp437

#: Characters to a row, and rows.
COLUMNS, ROWS = 32, 8


def glyph(code: int) -> str:
    """What the chart shows for *code*: the VGA's glyph, a blank for 0."""
    return cp437(code)


class CharTable(Widget):
    """``TTable``: the characters, and the one the cursor is on."""

    emits = (ChosenEvent,)

    #: The character under the cursor, 0 to 255.
    code: int = reactive(112)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.can_focus = True

    def render(self, surface: Surface) -> None:
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        for row in range(min(ROWS, self.height)):
            for column in range(min(COLUMNS, self.width)):
                surface.set_cell(column, row, glyph(row * COLUMNS + column), style)

    def cursor_position(self) -> tuple[int, int] | None:
        return self.code % COLUMNS, self.code // COLUMNS

    def _move(self, column: int, row: int) -> None:
        column = min(max(column, 0), COLUMNS - 1)
        row = min(max(row, 0), ROWS - 1)
        self.code = row * COLUMNS + column

    async def on_key(self, event: KeyEvent) -> bool:
        column, row = self.code % COLUMNS, self.code // COLUMNS
        if event.matches("home"):
            self.code = 0
        elif event.matches("end"):
            self.code = COLUMNS * ROWS - 1
        elif event.matches("up"):
            self._move(column, row - 1)
        elif event.matches("down"):
            self._move(column, row + 1)
        elif event.matches("left"):
            self._move(column - 1, row)
        elif event.matches("right"):
            self._move(column + 1, row)
        else:
            return False
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.button != "left" or event.action not in ("press", "move"):
            return event.button == "left"
        self.focus()
        self._move(event.x, event.y)
        return True

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        if event.button != "left":
            return False
        self._move(event.x, event.y)
        await self.emit(ChosenEvent(self.code))
        return True
