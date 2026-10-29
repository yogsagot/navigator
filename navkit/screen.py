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
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING

from navkit import glyphs
from bidi.mirror import MIRRORED

from navkit.bidi import layout
from navkit.style import DEFAULT_STYLE, RESET_SGR, Style

if TYPE_CHECKING:
    # Only for the annotation: the renderer takes whatever it is handed, and
    # importing it for real would tie the buffer to the terminal layer.
    from navkit.capabilities import TerminalInfo

#: A painted cell: the character it shows and the style it shows it in.  The
#: character is ``""`` for the second half of a double-width character, which
#: the owning cell already emitted.
type Cell = tuple[str, Style]

#: Re-exported so that a caller already holding a ``Surface`` need not reach
#: for another module to name the commonest two.  They live in
#: :mod:`navkit.glyphs` with the rest of the vocabulary, because deciding
#: *which* set to draw is a question about the terminal and this module is
#: deliberately innocent of those.
SINGLE_BOX = glyphs.SINGLE_BOX
DOUBLE_BOX = glyphs.DOUBLE_BOX

#: What a right-to-left screen draws in place of each character when it is
#: mirrored: corners and junctions, half blocks, pointers and arrows, brackets.
#: An involution, which is what :meth:`Surface.draw_runs` relies on -- text it
#: writes on a right-to-left surface is swapped through this beforehand, so
#: that the mirror puts it back, while a frame drawn cell by cell is mirrored.
_FLIP_PAIRS = (
    "┌┐", "└┘", "├┤", "╔╗", "╚╝", "╠╣", "╒╕", "╘╛", "╓╖", "╙╜", "╞╡", "╟╢",
    "╭╮", "╰╯", "▌▐", "▖▗", "▘▝", "◄►", "◀▶", "◂▸", "◁▷", "←→", "⇐⇒", "↖↗",
    "↙↘", "⟨⟩", "()", "[]", "{}", "<>", "«»", "‹›", "/\\", "▏▕",
)
FLIP: dict[str, str] = {}
for _a, _b in _FLIP_PAIRS:
    FLIP[_a], FLIP[_b] = _b, _a
del _a, _b


def char_width(char: str) -> int:
    """Return how many terminal cells *char* occupies (0, 1 or 2).

    A cell may hold a base and the marks combined onto it (``◌́``), which
    measures as its base does.
    """
    if not char:
        return 0
    if len(char) > 1:
        if is_flag(char):
            return 2
        return char_width(char[0])
    code = ord(char)
    if code < 0x20 or 0x7F <= code < 0xA0:
        return 0
    if code < 0x7F:
        # Printable ASCII is always one cell and never combining.  Worth
        # saying so: this runs for every character of every frame, and the
        # unicodedata lookups below are far from free.
        return 1
    if unicodedata.combining(char) or unicodedata.category(char) in ("Mn", "Me", "Cf"):
        # Marks draw on the cell before them; format characters -- marks of
        # direction, joiners, the soft hyphen -- draw nothing at all.
        return 0
    # The Private Use Area reports "A" here and so measures one cell, which is
    # what a Nerd Font *Mono* build patches its icons to.  The plain build
    # draws some of them two cells wide and there is no table that would say
    # so, which is why a widget reserves the second cell rather than trusting
    # this -- see ``Panel``'s icon gutter.
    return 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1


def _regional(char: str) -> bool:
    """Whether *char* is a Regional Indicator letter, half of a flag."""
    return "\U0001f1e6" <= char <= "\U0001f1ff"


def is_flag(cell: str) -> bool:
    """Whether *cell* is a flag: two Regional Indicators, ``🇱🇻``.

    Each half measures one cell, but a terminal that knows the pair draws
    one emoji two cells wide over both.  So the pair is kept in one cell,
    the way a wide character is, and a diff can never rewrite half of it
    and leave the other half drawn as a letter.
    """
    return len(cell) >= 2 and _regional(cell[0]) and _regional(cell[1])


def _fitting(text: str, limit: int) -> int:
    """How much of *text*, from the start, fits in *limit* cells."""
    used = 0
    for index, char in enumerate(text):
        width = char_width(char)
        if used + width > limit:
            return index
        used += width
    return len(text)


def _blit_bounds(
    target: Surface,
    source: Surface,
    x: int,
    y: int,
    src_x: int,
    src_y: int,
    width: int | None,
    height: int | None,
) -> tuple[int, int, int, int]:
    """The source-relative rectangle a blit actually has to walk.

    Clipped against both surfaces at once, so neither the loop nor the row
    copy below it ever visits a cell that one of the two would throw away.
    """
    span = (source.width - src_x) if width is None else width
    rows = (source.height - src_y) if height is None else height
    left = max(0, -x, -src_x)
    top = max(0, -y, -src_y)
    right = min(span, target.width - x, source.width - src_x)
    bottom = min(rows, target.height - y, source.height - src_y)
    return left, top, max(left, right), max(top, bottom)


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
    #: Whether what is painted here is shown mirrored, the whole screen
    #: flipped left for right as a right-to-left language reads it.  Text is
    #: laid out with that in mind (see :meth:`draw_runs`); everything else is
    #: painted as it would be left to right and mirrored with the screen.
    rtl: bool

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

    def view(
        self, x: int, y: int, width: int, height: int, rtl: bool | None = None
    ) -> Surface:
        """A surface onto the *width* x *height* area at *x*, *y*.

        Painting through it is offset by *x*, *y* and clipped to the
        rectangle, so what the caller sees is a surface of its own.  Views
        nest: taking a view of a view intersects the two clips.  *rtl*
        overrides the direction a view inherits (see :attr:`rtl`).
        """
        return _View(self, x, y, width, height, rtl)

    def blit(
        self,
        source: Surface,
        x: int = 0,
        y: int = 0,
        src_x: int = 0,
        src_y: int = 0,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """Copy a rectangle of cells out of *source* and into *x*, *y* here.

        The generic implementation, written in terms of :meth:`get` and
        :meth:`set_cell` so any surface has it; :class:`ScreenBuffer` and
        :class:`_View` override it with something that moves whole rows.

        Both edges of a copy can fall in the middle of a double-width
        character.  A cell whose owner was clipped away, and a wide character
        whose trailing half was, both become a blank -- the same bargain
        :meth:`ScreenBuffer.set_cell` makes at the edge of the screen.
        """
        left, top, right, bottom = _blit_bounds(
            self, source, x, y, src_x, src_y, width, height
        )
        for row in range(top, bottom):
            for col in range(left, right):
                char, style = source.get(src_x + col, src_y + row)
                if char == "":
                    # The trailing half of a wide character.  Its owner
                    # painted both cells, unless the owner is the cell we just
                    # clipped off the left edge -- then there is nothing to
                    # show but a blank.
                    if col == left:
                        self.set_cell(x + col, y + row, " ", style)
                    continue
                if char_width(char) == 2 and col + 1 >= right:
                    self.set_cell(x + col, y + row, " ", style)
                    continue
                self.set_cell(x + col, y + row, char, style)

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        style: Style = DEFAULT_STYLE,
        max_width: int | None = None,
    ) -> int:
        """Paint *text* starting at *x*, *y*; return the cells consumed."""
        if text.isascii() and not self.rtl:
            # Nearly every string a frame paints: nothing to order, no marks,
            # no wide characters.  Worth its own path for that reason alone.
            limit = self.width - x if max_width is None else min(max_width, self.width - x)
            used = 0
            for char in text:
                if used >= limit:
                    break
                if " " <= char < "\x7f":
                    self.set_cell(x + used, y, char, style)
                    used += 1
            return used
        return self.draw_runs(x, y, ((text, style),), max_width)

    def draw_runs(
        self,
        x: int,
        y: int,
        runs: Iterable[tuple[str, Style]],
        max_width: int | None = None,
    ) -> int:
        """Paint *runs*, one piece of text in several styles; return the cells used.

        One call rather than one per run, because the pieces are one string
        to whoever reads it: Hebrew or Arabic in it is ordered as a whole
        (:func:`navkit.bidi.layout`), a highlighted letter keeps its style
        wherever its word puts it, and an Arabic letter joins its neighbour
        across the change of colour.  What does not fit in *max_width* is cut
        off the logical end -- the end a reader reaches last.

        On a right-to-left surface the cells are written in reverse, each
        glyph swapped through :data:`FLIP`, so the screen's mirror shows them
        the right way round and the text ends up against the right-hand edge
        of where it was put, which is where right-to-left text starts.
        """
        limit = self.width - x if max_width is None else min(max_width, self.width - x)
        if limit <= 0:
            return 0
        parts: list[str] = []
        styles: list[Style] = []
        for piece, piece_style in runs:
            parts.append(piece)
            styles.extend([piece_style] * len(piece))
        text = "".join(parts)
        cells = layout(text, self.rtl)
        widths = [char_width(cell) for _, cell in cells]
        if sum(widths) > limit:
            text = text[: _fitting(text, limit)]
            cells = layout(text, self.rtl)
            widths = [char_width(cell) for _, cell in cells]
        used = 0
        if self.rtl:
            total = sum(widths)
            for (index, cell), width in zip(cells, widths):
                if width == 0:
                    continue
                used += width
                char = FLIP.get(cell[0], cell[0]) + cell[1:] if cell[0] in FLIP else cell
                self.set_cell(x + total - used, y, char, styles[index])
            return used
        for (index, cell), width in zip(cells, widths):
            if width == 0:
                continue
            self.set_cell(x + used, y, cell, styles[index])
            used += width
        return used

    def mirror(self) -> None:
        """Reverse every row of this surface in place, glyphs through :data:`FLIP`.

        A double-width character stays whole, its owner first.  What a whole
        right-to-left screen goes through on its way out, and what a widget
        that keeps left to right inside it (``Widget.mirrors``) goes through
        first, so the two cancel there.
        """
        for y in range(self.height):
            units: list[tuple[str, Style]] = []
            x = 0
            while x < self.width:
                char, style = self.get(x, y)
                if char == "":
                    char = " "  # a trailing half whose owner is out of reach
                units.append((FLIP.get(char, char), style))
                x += max(1, char_width(char))
            x = 0
            for char, style in reversed(units):
                x += self.set_cell(x, y, char, style) or 1

    def draw_box(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        style: Style = DEFAULT_STYLE,
        *,
        charset: str = SINGLE_BOX,
        fill: str | None = None,
    ) -> None:
        """Draw a box frame, optionally filling its interior with *fill*.

        *charset* is the six characters themselves -- top-left, top-right,
        bottom-left, bottom-right, horizontal, vertical -- and not a name for
        them.  Which set a widget asks for is a question about the stylesheet
        and the terminal's font, and both are answered before this is called;
        see :func:`navkit.glyphs.charset`.
        """
        if width < 2 or height < 2:
            return
        tl, tr, bl, br, horizontal, vertical = charset
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

    __slots__ = ("_target", "_x", "_y", "width", "height", "rtl")

    def __init__(
        self, target: Surface, x: int, y: int, width: int, height: int, rtl: bool | None = None
    ):
        self._target = target
        self.rtl = target.rtl if rtl is None else rtl
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

    def blit(
        self,
        source: Surface,
        x: int = 0,
        y: int = 0,
        src_x: int = 0,
        src_y: int = 0,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        # Clip here, then hand the whole rectangle to the target in one call.
        # Forwarding rather than looping is what lets a widget -- which only
        # ever sees a view -- reach ScreenBuffer's row copy underneath.
        left, top, right, bottom = _blit_bounds(
            self, source, x, y, src_x, src_y, width, height
        )
        if right <= left or bottom <= top:
            return
        self._target.blit(
            source,
            self._x + x + left,
            self._y + y + top,
            src_x + left,
            src_y + top,
            right - left,
            bottom - top,
        )


class ScreenBuffer(Surface):
    """A grid of cells: the surface a whole frame is composed in."""

    __slots__ = ("width", "height", "_rows", "rtl")

    def __init__(self, width: int, height: int, style: Style = DEFAULT_STYLE):
        self.width = max(0, width)
        self.height = max(0, height)
        self.rtl = False
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

    def blit(
        self,
        source: Surface,
        x: int = 0,
        y: int = 0,
        src_x: int = 0,
        src_y: int = 0,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        if not isinstance(source, ScreenBuffer):
            super().blit(source, x, y, src_x, src_y, width, height)
            return
        left, top, right, bottom = _blit_bounds(
            self, source, x, y, src_x, src_y, width, height
        )
        if right <= left or bottom <= top:
            return
        # Both grids hold cells in the same representation, so a row is a
        # slice assignment -- one list copy in C rather than a Python call per
        # cell.  This is the path a console screen full of output takes every
        # frame, which is the whole reason for the override.
        for row in range(top, bottom):
            span = source._rows[src_y + row][src_x + left : src_x + right]
            if span[0][0] == "":
                # Its owner was clipped off the left edge.
                span[0] = (" ", span[0][1])
            if char_width(span[-1][0]) == 2:
                # Its trailing half was clipped off the right edge.
                span[-1] = (" ", span[-1][1])
            self._rows[y + row][x + left : x + right] = span

    def restyle(self, transform: Callable[[Style], Style]) -> None:
        """Replace every cell's style with ``transform(style)``, keeping its character.

        *transform* is called once per distinct style rather than once per
        cell, since a frame holds a few dozen styles over thousands of cells.
        Those are told apart by identity, not by value: hashing a style is a
        Python-level walk over its fields, and doing that for every cell was
        most of what this cost.  The entry keeps the style alive, so its id
        cannot be reused by a style made later in the same pass.
        """
        seen: dict[int, tuple[Style, Style]] = {}
        for row in self._rows:
            for x, (char, style) in enumerate(row):
                entry = seen.get(id(style))
                if entry is None:
                    entry = seen[id(style)] = (style, transform(style))
                row[x] = (char, entry[1])

    def mirrored(self) -> ScreenBuffer:
        """A copy of this buffer reversed left for right (:meth:`Surface.mirror`).

        Done on the rows directly: it runs over the whole screen every frame
        of a right-to-left session.
        """
        out = ScreenBuffer(0, 0)
        out.width, out.height, out.rtl = self.width, self.height, self.rtl
        flip = FLIP
        rows = []
        for row in self._rows:
            new = row[::-1]
            x = 0
            while x < len(new):
                char, style = new[x]
                if char == "":
                    # The trailing half of a wide character now comes before
                    # its owner: swap them back.
                    if x + 1 < len(new):
                        new[x], new[x + 1] = new[x + 1], ("", style)
                        x += 1
                    else:
                        new[x] = (" ", style)
                elif char in flip:
                    new[x] = (flip[char], style)
                x += 1
            rows.append(new)
        out._rows = rows
        return out

    def copy_from(self, other: ScreenBuffer) -> None:
        """Make this buffer an independent copy of *other*."""
        self.width = other.width
        self.height = other.height
        self.rtl = other.rtl
        self._rows = [row.copy() for row in other._rows]


def for_words(buffer: ScreenBuffer) -> ScreenBuffer:
    """*buffer* as kitty must be sent it (``TerminalInfo.bidi`` ``"words"``).

    kitty draws some glyphs reversed, whatever order they arrive in, while
    each cell keeps its own colours.  A run of cells -- unbroken by a space, a
    box-drawing or block character, or a change of weight or slant; a change
    of colour does not break one -- that starts with an Arabic letter is
    drawn reversed to its end, brackets mirrored, Latin and digits after the
    Arabic included.  Hebrew is reversed a stretch of Hebrew letters at a
    time, whatever is around it.  Navigator has already put every glyph where
    it belongs (:mod:`navkit.bidi`), so those glyphs are sent reversed,
    each cell's style left where it is, for kitty to put back.  Found by
    writing runs to kitty and reading back what it drew; nothing documents it.
    """
    out = ScreenBuffer(0, 0)
    out.width, out.height, out.rtl = buffer.width, buffer.height, buffer.rtl
    rows = []
    for row in buffer._rows:
        if not any(char >= "\u0590" for char, _ in row):
            rows.append(row)  # nothing right-to-left: the row as it is
            continue
        new = list(row)
        start = 0
        while start < len(new):
            if _breaks_run(new[start][0]):
                start += 1
                continue
            face = _face(new[start][1])
            end = start
            while end < len(new) and not _breaks_run(new[end][0]) and _face(new[end][1]) == face:
                end += 1
            if _starts_arabic(new[start:end]):
                _reverse_glyphs(new, start, end)
            else:
                at = start
                while at < end:
                    if _hebrew(new[at][0]):
                        stop = at
                        while stop < end and _hebrew(new[stop][0]):
                            stop += 1
                        _reverse_glyphs(new, at, stop)
                        at = stop
                    else:
                        at += 1
            start = end
        rows.append(new)
    out._rows = rows
    return out


def _reverse_glyphs(row: list[Cell], start: int, end: int) -> None:
    """Reverse the glyphs of *row* from *start* to *end*, mirrored, keeping its styles."""
    glyphs = [MIRRORED.get(c[:1], c[:1]) + c[1:] for c, _ in reversed(row[start:end])]
    row[start:end] = [(g, st) for g, (_, st) in zip(glyphs, row[start:end])]


def _hebrew(char: str) -> bool:
    return "\u0590" <= char[:1] <= "\u05ff" or "\ufb1d" <= char[:1] <= "\ufb4f"


def _breaks_run(char: str) -> bool:
    return char in ("", " ") or "\u2500" <= char[:1] <= "\u259f"


def _face(style: Style) -> tuple[bool, bool]:
    return style.bold, style.italic


def _starts_arabic(cells: list[Cell]) -> bool:
    for char, _ in cells:
        kind = unicodedata.bidirectional(char[:1])
        if kind == "AL":
            return True
        if kind in ("L", "R"):
            return False
    return False


def render_diff(
    previous: ScreenBuffer | None,
    current: ScreenBuffer,
    info: TerminalInfo | None = None,
) -> str:
    """Return the escape sequences turning *previous* into *current*.

    Passing ``None`` -- or a buffer of a different size, as happens right after
    a resize -- forces a full repaint.

    *info* is where a colour the terminal cannot name is quantised to one it
    can: this is the last place a :class:`~navkit.style.Style` exists before it
    becomes bytes, so it is the only place that decision belongs.  ``None``
    means emit what the styles say, which is what a caller rendering to a
    string rather than to a tty wants.

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
    link: str | None = None
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
                out.append(info.sgr(cell_style) if info else cell_style.sgr())
                style = cell_style
                # A link is an attribute the terminal keeps like SGR's, so it
                # is switched only where it changes; a cursor jump does not
                # end it, which is why every cell written is compared.
                target = cell_style.link if info is None or info.hyperlinks else None
                if target != link:
                    out.append(hyperlink(target))
                    link = target
            out.append(char)
            cursor = (x + width, y)
            x += width

    if link is not None:
        out.append(hyperlink(None))
    if out:
        out.append(RESET_SGR)
    return "".join(out)


def hyperlink(url: str | None) -> str:
    """OSC 8: the cells written next link to *url*, or to nothing.

    The URL is written as given apart from the control characters, which
    would end the sequence early and leave the rest of it on the screen.
    """
    if url is None:
        return "\x1b]8;;\x1b\\"
    safe = "".join(c for c in url if c.isprintable())
    return f"\x1b]8;;{safe}\x1b\\"