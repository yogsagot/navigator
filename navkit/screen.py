"""The screen buffer.

Widgets never write to the terminal.  They paint cells into a
:class:`ScreenBuffer`, and once a frame is complete :func:`render_diff`
compares it against the previously flushed buffer and emits only the escape
sequences needed to turn one into the other.
"""

from __future__ import annotations

import unicodedata

from navkit.style import DEFAULT_STYLE, RESET_SGR, Style

#: A painted cell: the character it shows and the style it shows it in.  The
#: character is ``""`` for the second half of a double-width character, which
#: the owning cell already emitted.
type Cell = tuple[str, Style]

SINGLE_BOX = "┌┐└┘─│"
DOUBLE_BOX = "╔╗╚╝═║"


def char_width(char: str) -> int:
    """Return how many terminal cells *char* occupies (0, 1 or 2)."""
    if not char:
        return 0
    code = ord(char)
    if code < 0x20 or 0x7F <= code < 0xA0:
        return 0
    if unicodedata.combining(char):
        return 0
    return 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1


class ScreenBuffer:
    """A grid of cells that widgets render into.

    All drawing methods clip silently against the buffer's bounds, so a widget
    may paint at negative or oversized coordinates without checking first.
    """

    __slots__ = ("width", "height", "_rows")

    def __init__(self, width: int, height: int, style: Style = DEFAULT_STYLE):
        self.width = max(0, width)
        self.height = max(0, height)
        self._rows: list[list[Cell]] = []
        self.clear(style)

    def resize(self, width: int, height: int, style: Style = DEFAULT_STYLE) -> None:
        """Resize the buffer, discarding its contents."""
        self.width = max(0, width)
        self.height = max(0, height)
        self.clear(style)

    def clear(self, style: Style = DEFAULT_STYLE, char: str = " ") -> None:
        """Fill the whole buffer with *char* in *style*."""
        blank: Cell = (char, style)
        self._rows = [[blank] * self.width for _ in range(self.height)]

    def get(self, x: int, y: int) -> Cell:
        """Return the cell at *x*, *y*, or a blank cell if out of bounds."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self._rows[y][x]
        return (" ", DEFAULT_STYLE)

    def set_cell(self, x: int, y: int, char: str, style: Style = DEFAULT_STYLE) -> int:
        """Paint a single character and return how many cells it consumed."""
        if not (0 <= y < self.height) or not (0 <= x < self.width):
            return max(1, char_width(char))
        width = char_width(char)
        if width == 0:
            return 0
        row = self._rows[y]
        row[x] = (char, style)
        if width == 2:
            if x + 1 < self.width:
                row[x + 1] = ("", style)
            else:
                # No room for the trailing half -- show a blank instead of
                # letting the terminal wrap it onto the next line.
                row[x] = (" ", style)
        return width

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        style: Style = DEFAULT_STYLE,
        max_width: int | None = None,
    ) -> int:
        """Paint *text* starting at *x*, *y*; return the cells consumed."""
        limit = self.width - x if max_width is None else min(max_width, self.width - x)
        used = 0
        for char in text:
            width = char_width(char)
            if width == 0:
                continue
            if used + width > limit:
                break
            self.set_cell(x + used, y, char, style)
            used += width
        return used

    def fill(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        char: str = " ",
        style: Style = DEFAULT_STYLE,
    ) -> None:
        """Fill a rectangle with *char*."""
        for row in range(max(0, y), min(self.height, y + height)):
            for col in range(max(0, x), min(self.width, x + width)):
                self._rows[row][col] = (char, style)

    def draw_box(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        style: Style = DEFAULT_STYLE,
        *,
        double: bool = False,
        fill: str | None = None,
    ) -> None:
        """Draw a box frame, optionally filling its interior with *fill*."""
        if width < 2 or height < 2:
            return
        tl, tr, bl, br, horizontal, vertical = DOUBLE_BOX if double else SINGLE_BOX
        right = x + width - 1
        bottom = y + height - 1
        if fill is not None:
            self.fill(x + 1, y + 1, width - 2, height - 2, fill, style)
        for col in range(x + 1, right):
            self.set_cell(col, y, horizontal, style)
            self.set_cell(col, bottom, horizontal, style)
        for row in range(y + 1, bottom):
            self.set_cell(x, row, vertical, style)
            self.set_cell(right, row, vertical, style)
        self.set_cell(x, y, tl, style)
        self.set_cell(right, y, tr, style)
        self.set_cell(x, bottom, bl, style)
        self.set_cell(right, bottom, br, style)

    def copy_from(self, other: ScreenBuffer) -> None:
        """Make this buffer an independent copy of *other*."""
        self.width = other.width
        self.height = other.height
        self._rows = [row.copy() for row in other._rows]


def render_diff(previous: ScreenBuffer | None, current: ScreenBuffer) -> str:
    """Return the escape sequences turning *previous* into *current*.

    Passing ``None`` -- or a buffer of a different size, as happens right after
    a resize -- forces a full repaint.
    """
    full = (
        previous is None
        or previous.width != current.width
        or previous.height != current.height
    )
    out: list[str] = []
    if full:
        out.append(RESET_SGR + "\x1b[H\x1b[2J")

    style: Style | None = None
    cursor: tuple[int, int] | None = None

    for y in range(current.height):
        x = 0
        while x < current.width:
            cell = current.get(x, y)
            char, cell_style = cell
            if char == "":
                # Trailing half of a wide character; its owner emitted it.
                x += 1
                continue
            width = max(1, char_width(char))
            if not full and previous is not None and previous.get(x, y) == cell:
                x += width
                continue
            if cursor != (x, y):
                out.append(f"\x1b[{y + 1};{x + 1}H")
            if cell_style != style:
                out.append(cell_style.sgr())
                style = cell_style
            out.append(char)
            cursor = (x + width, y)
            x += width

    if out:
        out.append(RESET_SGR)
    return "".join(out)