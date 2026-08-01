"""The screen buffer and the views widgets paint through.

Widgets never write to the terminal.  They paint cells into a
:class:`Surface`, and once a frame is complete :func:`render_diff` compares
the finished :class:`ScreenBuffer` against the previously flushed one and
emits only the escape sequences needed to turn one into the other.

There are two kinds of surface.  :class:`ScreenBuffer` owns a grid of cells;
a *view* owns nothing and forwards to another surface, shifting coordinates
and clipping to a rectangle.  A widget is handed a view of its own area, so
it paints from ``0, 0`` in its own size and physically cannot draw outside
itself -- no widget needs to know where on the screen it ended up, and none
can scribble on its neighbours.
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
    if code < 0x7F:
        # Printable ASCII is always one cell and never combining.  Worth
        # saying so: this runs for every character of every frame, and the
        # unicodedata lookups below are far from free.
        return 1
    if unicodedata.combining(char):
        return 0
    return 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1


class Surface:
    """Somewhere a widget can paint, in its own coordinates.

    Subclasses provide :meth:`get`, :meth:`set_cell` and :meth:`fill`; the
    rest is written in terms of those, so it works the same whether the cells
    are really there or the calls are being forwarded to a parent.

    All drawing clips silently against ``width`` x ``height``, so a widget may
    paint at negative or oversized coordinates without checking first.
    """

    __slots__ = ()

    #: The area available, starting at ``0, 0``.
    width: int
    height: int

    def get(self, x: int, y: int) -> Cell:
        """Return the cell at *x*, *y*, or a blank cell if out of bounds."""
        raise NotImplementedError

    def set_cell(self, x: int, y: int, char: str, style: Style = DEFAULT_STYLE) -> int:
        """Paint a single character and return how many cells it consumed."""
        raise NotImplementedError

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
        raise NotImplementedError

    def view(self, x: int, y: int, width: int, height: int) -> Surface:
        """A surface onto the *width* x *height* area at *x*, *y*.

        Painting through it is offset by *x*, *y* and clipped to the
        rectangle, so what the caller sees is a surface of its own.  Views
        nest: taking a view of a view intersects the two clips.
        """
        return _View(self, x, y, width, height)

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


class _View(Surface):
    """A shifted, clipped window onto another surface.

    It holds no cells of its own, so handing one to every widget on every
    frame costs an object and nothing else -- there is no second copy of the
    screen to composite afterwards.
    """

    __slots__ = ("_target", "_x", "_y", "width", "height")

    def __init__(self, target: Surface, x: int, y: int, width: int, height: int):
        self._target = target
        self._x = x
        self._y = y
        # The declared size, not what survives clipping against the target: a
        # widget hanging off the edge of the screen should still lay its own
        # contents out as though it were whole.
        self.width = max(0, width)
        self.height = max(0, height)

    def get(self, x: int, y: int) -> Cell:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return (" ", DEFAULT_STYLE)
        return self._target.get(self._x + x, self._y + y)

    def set_cell(self, x: int, y: int, char: str, style: Style = DEFAULT_STYLE) -> int:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return max(1, char_width(char))
        if char_width(char) == 2 and x + 1 >= self.width:
            # The trailing half would land on whatever is beside this widget,
            # so show a blank rather than let it escape -- the same bargain
            # ScreenBuffer makes at the edge of the screen.
            self._target.set_cell(self._x + x, self._y + y, " ", style)
            return 2
        return self._target.set_cell(self._x + x, self._y + y, char, style)

    def fill(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        char: str = " ",
        style: Style = DEFAULT_STYLE,
    ) -> None:
        left, top = max(0, x), max(0, y)
        right, bottom = min(self.width, x + width), min(self.height, y + height)
        if right > left and bottom > top:
            self._target.fill(
                self._x + left, self._y + top, right - left, bottom - top, char, style
            )


class ScreenBuffer(Surface):
    """A grid of cells: the surface a whole frame is composed in."""

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
        cell: Cell = (char, style)
        left, right = max(0, x), min(self.width, x + width)
        if right <= left:
            return
        span = [cell] * (right - left)
        for row in range(max(0, y), min(self.height, y + height)):
            self._rows[row][left:right] = span

    def copy_from(self, other: ScreenBuffer) -> None:
        """Make this buffer an independent copy of *other*."""
        self.width = other.width
        self.height = other.height
        self._rows = [row.copy() for row in other._rows]


def render_diff(previous: ScreenBuffer | None, current: ScreenBuffer) -> str:
    """Return the escape sequences turning *previous* into *current*.

    Passing ``None`` -- or a buffer of a different size, as happens right after
    a resize -- forces a full repaint.

    Most frames change a handful of rows, so each row is first compared whole:
    one list comparison in C rules out a row that nobody touched, and only the
    survivors are walked cell by cell.  On a large terminal that is the
    difference between the diff costing more than the render and costing
    almost nothing.
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
        if not full and previous is not None and previous._rows[y] == current._rows[y]:
            # Nothing on this row moved.  Skipping it is safe: emitting
            # nothing leaves the terminal's cursor and pending SGR exactly
            # where the rows above left them.
            continue
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