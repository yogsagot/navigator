"""The cursor and how it moves: positions, soft wrap's rows of lines, the movement commands.

A mixin of :class:`FileEditor` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``file_editor.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from navkit.bidi import has_rtl, text_rtl

from navigator.widgets.editor.commands import (
    LineEnd,
    LineStart,
    MoveDown,
    MoveLeft,
    MoveRight,
    MoveUp,
    PageDown,
    PageUp,
    ScreenBottom,
    ScreenTop,
    ScrollDown,
    ScrollUp,
    TextEnd,
    TextStart,
    WordLeft,
    WordRight,
)
from navigator.lib.editor import columns
from navigator.lib.editor.document import Pos
from navigator.lib.editor import softwrap
from navigator.lib.editor.search import BREAK_CHARS
from navigator.widgets.editor.file_editor.helpers import _marking, _ordered

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navigator.widgets.editor.file_editor.file_editor_surface import FileEditor as _Base
else:
    from navkit.widget import Mixin as _Base


class Cursor(_Base):
    """The cursor and how it moves: positions, soft wrap's rows of lines, the movement commands."""

    # -- the cursor --------------------------------------------------------------

    def _text(self, line: int | None = None) -> str:
        return self.document.lines[self.line if line is None else line]

    def _index(self) -> tuple[int, int]:
        """The cursor as a string index, and the blanks it lies past the end."""
        return columns.index_at(self._text(), self.col, self.tab_size)

    def _pos(self) -> Pos:
        return Pos(self.line, self._index()[0])

    def _column(self, pos: Pos) -> int:
        return columns.column_of(self.document.lines[pos.line], pos.index, self.tab_size)

    def _go(self, pos: Pos) -> None:
        """Put the cursor on *pos*, a string index, and bring it into view."""
        self.line = pos.line
        self.col = self._column(pos)
        self._goal = None
        self._follow()

    def _go_column(self, line: int, col: int) -> None:
        self.line = max(0, min(line, len(self.document) - 1))
        self.col = max(0, col)
        self._goal = None
        self._follow()

    @property
    def _free(self) -> bool:
        """Whether a movement may leave the cursor past a line's end: drawing lines
        and marking a column block need the cells there."""
        return bool(self.draw_mode) or (self.vertical_blocks and self._extending)

    def _line_width(self, line: int) -> int:
        return columns.width(self.document.lines[line], self.tab_size)

    def _move_to(self, line: int, col: int) -> None:
        """A movement to *line*, *col*: the column held to the line's end unless
        :attr:`_free`."""
        line = max(0, min(line, len(self.document) - 1))
        if not self._free:
            col = min(col, self._line_width(line))
        self._go_column(line, col)

    def _move_rows(self, count: int) -> None:
        """Soft wrapped, Up/Down and the like: *count* rows on, aiming for the
        screen column the run of them started from, so a short row on the way
        does not lose it."""
        row, x = self._locate(self.line, self.col)
        goal = x if self._goal is None else self._goal
        line, row = self._step_rows(self.line, row, count)
        self._move_to(line, self._column_at(line, row, goal))
        self._goal = goal

    def _move_vertically(self, line: int) -> None:
        """Up/Down and the like: to *line*, aiming for the column the run of
        them started from, so a short line on the way does not lose it."""
        goal = self.col if self._goal is None else self._goal
        self._move_to(line, goal)
        self._goal = goal

    def _follow(self) -> None:
        """Scroll so the cursor is on screen: DN's ``ScrollTo``.  Sideways by
        where its column is painted, which on a reordered line is elsewhere."""
        rows, cols = max(1, self.height), max(1, self.width)
        if self.soft_wrap:
            self._follow_rows(rows)
            return
        if self.line < self.top:
            self.top = self.line
        elif self.line >= self.top + rows:
            self.top = self.line - rows + 1
        x = self._visual_column(self.line, self.col)
        if x < self.left:
            self.left = x
        elif x >= self.left + cols:
            self.left = x - cols + 1

    # -- soft wrap: rows of lines (:mod:`navigator.lib.editor.softwrap`) ---------

    def settle_modes(self) -> None:
        """Soft wrap gives way to column blocks: a rectangle is columns of
        lines as written, and over wrapped rows it would be ragged pieces."""
        if self.soft_wrap and self.vertical_blocks:
            self.soft_wrap = False
        if not self.soft_wrap:
            self.top_row = 0

    def _rows(self, number: int) -> list[tuple[int, int]]:
        """Line *number*'s rows, each its columns ``(start, stop)``: the whole
        line, unwrapped."""
        text = self.document.lines[number]
        if not self.soft_wrap:
            return [(0, columns.width(text, self.tab_size))]
        key = (text, max(1, self.width), self.tab_size)
        found = self._wrap_cache.get(key)
        if found is None:
            if len(self._wrap_cache) > 4096:
                self._wrap_cache.clear()
            found = self._wrap_cache[key] = softwrap.rows(columns.cells(text, self.tab_size), key[1])
        return found

    def _row_layout(self, number: int, row: int) -> tuple[list[tuple[str, int]], list[tuple[int, str]] | None, int, int, bool]:
        """Row *row* of line *number* as it is painted: its cells, their
        order when Hebrew or Arabic changes it -- each row ordered on its own,
        as the bidi algorithm orders after breaking lines -- how far in it
        sits (a right-to-left line's rows right-aligned), the line's column
        it starts at, and whether it is the line's last."""
        text = self.document.lines[number]
        line_rows = self._rows(number)
        row = max(0, min(row, len(line_rows) - 1))
        start, stop = line_rows[row]
        cells = columns.cells(text, self.tab_size)[start:stop]
        last = row == len(line_rows) - 1
        if not has_rtl(text):
            return cells, None, 0, start, last
        order = _ordered([char for char, _ in cells])
        if order is None or not text_rtl(text):
            return cells, order, 0, start, last
        width = max(1, self.width)
        shift = max(width, len(order) + 1) - len(order) if last else max(0, width - len(order))
        return cells, order, shift, start, last

    def _locate(self, line: int, col: int) -> tuple[int, int]:
        """The row *col* of *line* is on, and the screen column it is painted at."""
        line_rows = self._rows(line)
        row, _ = softwrap.locate(line_rows, col)
        cells, order, shift, base, last = self._row_layout(line, row)
        at = col - base
        if order is None:
            return row, at
        if at >= len(cells):
            beyond = at - len(cells)
            return row, (max(0, shift - 1 - beyond) if shift else len(order) + beyond)
        return row, shift + next((x for x, (where, _) in enumerate(order) if where == at), at)

    def _column_at(self, line: int, row: int, x: int) -> int:
        """The column of *line* painted at screen column *x* on its row *row*."""
        line_rows = self._rows(line)
        row = max(0, min(row, len(line_rows) - 1))
        cells, order, shift, base, last = self._row_layout(line, row)
        if order is None:
            return softwrap.column_at(line_rows, row, x)
        at = x - shift
        if at < 0:
            return base + (len(cells) - 1 - at if last else 0)
        if at >= len(order):
            return base + (0 if shift else len(cells) + (at - len(order) if last else -1))
        return base + order[at][0]

    def _step_rows(self, line: int, row: int, count: int) -> tuple[int, int]:
        """The row *count* rows on from row *row* of *line* (back, when
        negative), held to the text's first and last rows."""
        last_line = len(self.document) - 1
        while count > 0:
            if row + 1 < len(self._rows(line)):
                row += 1
            elif line < last_line:
                line, row = line + 1, 0
            else:
                break
            count -= 1
        while count < 0:
            if row > 0:
                row -= 1
            elif line > 0:
                line -= 1
                row = len(self._rows(line)) - 1
            else:
                break
            count += 1
        return line, row

    def _rows_from(self, line: int, row: int, limit: int) -> int:
        """How many rows there are from row *row* of *line* to the text's end,
        counted no further than *limit*."""
        count, lines = 0, len(self.document)
        while line < lines and count < limit:
            count += len(self._rows(line)) - row
            line, row = line + 1, 0
        return min(count, limit)

    def _row_offset(self, line: int, row: int) -> int:
        """How many rows below the view's first row *line*'s *row* is (above,
        negative), told exactly within the screen and as "beyond" outside it."""
        here = (self.top, min(self.top_row, len(self._rows(self.top)) - 1))
        if (line, row) < here:
            if self.top - line > self.height:
                return -self.height - 1
            count, at = 0, here
            while at > (line, row):
                at = self._step_rows(at[0], at[1], -1)
                count -= 1
            return count
        if line - self.top > self.height:
            return self.height + 1
        count, at = 0, here
        while at < (line, row) and count <= self.height:
            nxt = self._step_rows(at[0], at[1], 1)
            if nxt == at:
                break
            at = nxt
            count += 1
        return count

    def _follow_rows(self, rows: int) -> None:
        """:meth:`_follow` soft wrapped: the cursor's row kept on screen, rows
        at a time, and never a sideways scroll."""
        self.left = 0
        self.top = max(0, min(self.top, len(self.document) - 1))
        self.top_row = max(0, min(self.top_row, len(self._rows(self.top)) - 1))
        row, _ = self._locate(self.line, self.col)
        offset = self._row_offset(self.line, row)
        if offset < 0:
            self.top, self.top_row = self.line, row
        elif offset >= rows:
            self.top, self.top_row = self._step_rows(self.line, row, -(rows - 1))

    def _scroll_view(self, count: int) -> None:
        """The view *count* rows down (up, negative): lines unwrapped."""
        if self.soft_wrap:
            self.top, self.top_row = self._step_rows(self.top, self.top_row, count)
        else:
            self.top = max(0, min(self.top + count, len(self.document) - 1))

    def visible_rows(self) -> list[tuple[int, int]]:
        """Each screen row's line and which of its rows it is, top first --
        what :class:`LineGutter` numbers (a line's first row alone)."""
        self.revision
        if not self.soft_wrap:
            return [(number, 0) for number in range(self.top, min(len(self.document), self.top + self.height))]
        found, (line, row) = [], (self.top, self.top_row)
        while len(found) < self.height and line < len(self.document):
            line_rows = self._rows(line)
            while row < len(line_rows) and len(found) < self.height:
                found.append((line, row))
                row += 1
            line, row = line + 1, 0
        return found

    def cell_at(self, x: int, y: int) -> tuple[int, int]:
        """The text's line and column painted at *x*, *y* of the area."""
        if self.soft_wrap:
            line, row = self._step_rows(self.top, self.top_row, max(0, y))
            return line, self._column_at(line, row, max(0, x))
        line = max(0, min(self.top + max(y, 0), len(self.document) - 1))
        return line, self._logical_column(line, self.left + max(0, x))

    def cursor_cell(self) -> tuple[int, int]:
        """Where the cursor is painted in the area -- off it, outside."""
        if self.soft_wrap:
            row, x = self._locate(self.line, self.col)
            return x, self._row_offset(self.line, row)
        return self._visual_column(self.line, self.col) - self.left, self.line - self.top

    def layout(self, width: int, height: int) -> None:
        super().layout(width, height)
        self._follow()

    def _moved(self) -> None:
        """A movement ends the typing run an undo would take back together."""
        self.buffer.seal()

    # -- movements ---------------------------------------------------------------

    def _step_visually(self, step: int) -> bool:
        """Left (*step* -1) or Right (+1) by where the columns are painted, on a
        line Hebrew or Arabic reorders; False on any other line, which the
        column-by-column movement below serves as it always has.

        A departure: DN knew no right-to-left text.  The cursor goes to the
        neighbouring painted cell, so it runs with the arrow through Hebrew
        and Latin alike.  Off the end of the line's start it stays; off the
        end its text reads to it goes past it, as on any line, and from there
        on to the next line the way Right always has -- the right-hand end and
        Right on a left-to-right line, the left-hand end and Left on a
        right-to-left one, which is right-aligned (:func:`_laid_line`).
        """
        if not 0 <= self.line < len(self.document):
            return False
        row, order, visual, shift = self._painted_here()
        if order is None:
            return False
        here = row[order[visual][0]][1] if 0 <= visual < len(order) else None
        target = visual + step
        while 0 <= target < len(order) and (order[target][1] == "" or row[order[target][0]][1] == here):
            target += step  # the rest of a tab or a wide character: the same place
        if 0 <= target < len(order):
            at = order[target][0]
            self._go_column(self.line, columns.column_of(self._text(), row[at][1], self.tab_size))
            return True
        if (target >= len(order)) == bool(shift):
            return True  # off the line's start
        beyond = -1 - target if shift else target - len(order)
        if beyond == 0 or self._free:
            self._go_column(self.line, len(row) + beyond)
            return True
        if not shift:
            return False
        if self.line + 1 < len(self.document):
            self._go_column(self.line + 1, 0)
        return True

    def _painted_here(self) -> tuple[list[tuple[str, int]], list[tuple[int, str]] | None, int, int]:
        """The cursor's line as cells, their painted order (None when the line
        reads as written), the cell of that order the cursor is on -- past the
        text, as many cells past it as the cursor's column is, to the left of
        a right-to-left line -- and how far in the line is painted."""
        row, order, shift = self._laid(self.line)
        if order is None:
            return row, None, self.col, 0
        if self.col < len(row):
            # A column inside a tab or a wide character is that character's;
            # an alef's beside its lam is the blank left for it (_ordered).
            index = row[self.col][1]
            visual = next(
                (x for x, (at, shown) in enumerate(order) if row[at][1] == index and shown != ""),
                next(x for x, (at, _) in enumerate(order) if at == self.col),
            )
        elif shift:
            visual = -1 - (self.col - len(row))
        else:
            visual = len(order) + self.col - len(row)
        return row, order, visual, shift

    def _word_visually(self, step: int) -> bool:
        """Ctrl+Left (*step* -1) or Ctrl+Right (+1) by where words are painted, on
        a line Hebrew or Arabic reorders; False on any other line.

        Every word's start -- its first letter in the text, the right-hand end
        of a Hebrew word -- is a stop, and so is the end of the line; the cursor
        goes to the nearest stop that way on screen.  With none left that way
        it goes on to the line before or after as DN's ``WordLeft`` and
        ``WordRight`` do -- after, the way the line reads.  A departure, as
        Left and Right are (_step_visually).
        """
        if not 0 <= self.line < len(self.document):
            return False
        row, order, visual, shift = self._painted_here()
        if order is None:
            return False
        text = self._text()
        stops: dict[int, int] = {}  # painted cell: index in the text
        for x, (at, shown) in enumerate(order):
            index = row[at][1]
            if shown and text[index] not in BREAK_CHARS and (index == 0 or text[index - 1] in BREAK_CHARS):
                stops.setdefault(x, index)
        stops[-1 if shift else len(order)] = len(text)
        ahead = [x for x in stops if (x - visual) * step > 0]
        if ahead:
            self._go(Pos(self.line, stops[min(ahead, key=lambda x: abs(x - visual))]))
        elif (step < 0) != bool(shift):
            self._go(self._word_left(Pos(self.line, 0)))
        else:
            self._go(self._word_right(Pos(self.line, len(text))))
        return True

    @_marking
    async def on_move_left(self, event: MoveLeft) -> bool:
        """One column left; over a tab or a wide character, to its start."""
        self._moved()
        if self._step_visually(-1):
            return True
        index, past = self._index()
        text = self._text()
        if self.col == 0 and self.line > 0 and not self._free:
            self._move_to(self.line - 1, self._line_width(self.line - 1))
        elif past or index >= len(text):
            self._go_column(self.line, self.col - 1)
        elif columns.column_of(text, index, self.tab_size) < self.col:
            self._go(Pos(self.line, index))
        elif index > 0:
            self._go(Pos(self.line, index - 1))
        return True

    @_marking
    async def on_move_right(self, event: MoveRight) -> bool:
        self._moved()
        if self._step_visually(1):
            return True
        index, past = self._index()
        text = self._text()
        if self._free and (past or index >= len(text)):
            self._go_column(self.line, self.col + 1)
        elif index >= len(text):
            if self.line + 1 < len(self.document):
                self._go_column(self.line + 1, 0)
        else:
            self._go(Pos(self.line, index + 1))
        return True

    @_marking
    async def on_move_up(self, event: MoveUp) -> bool:
        self._moved()
        if self.soft_wrap:
            self._move_rows(-1)
        else:
            self._move_vertically(self.line - 1)
        return True

    @_marking
    async def on_move_down(self, event: MoveDown) -> bool:
        self._moved()
        if self.soft_wrap:
            self._move_rows(1)
        else:
            self._move_vertically(self.line + 1)
        return True

    @_marking
    async def on_line_start(self, event: LineStart) -> bool:
        self._moved()
        self._go_column(self.line, 0)
        return True

    @_marking
    async def on_line_end(self, event: LineEnd) -> bool:
        """``cmEnd``: after the last character that is not a blank."""
        self._moved()
        text = self._text()
        self._go(Pos(self.line, len(text.rstrip(" "))))
        return True

    @_marking
    async def on_page_up(self, event: PageUp) -> bool:
        self._moved()
        rows = max(1, self.height)
        if self.soft_wrap:
            self._scroll_view(-rows)
            self._move_rows(-rows)
            return True
        self.top = max(0, self.top - rows)
        self._move_vertically(self.line - rows)
        return True

    @_marking
    async def on_page_down(self, event: PageDown) -> bool:
        self._moved()
        rows = max(1, self.height)
        if self.soft_wrap:
            # No further than leaves the last row at the bottom.
            left = self._rows_from(self.top, self.top_row, 2 * rows) - rows
            self._scroll_view(max(0, min(rows, left)))
            self._move_rows(rows)
            return True
        last = len(self.document) - 1
        self.top = max(0, min(self.top + rows, last - rows + 1))
        self._move_vertically(self.line + rows)
        return True

    @_marking
    async def on_screen_top(self, event: ScreenTop) -> bool:
        self._moved()
        if self.soft_wrap:
            row, _ = self._locate(self.line, self.col)
            self._move_rows(-self._row_offset(self.line, row))
            return True
        self._move_vertically(self.top)
        return True

    @_marking
    async def on_screen_bottom(self, event: ScreenBottom) -> bool:
        self._moved()
        if self.soft_wrap:
            row, _ = self._locate(self.line, self.col)
            self._move_rows(max(1, self.height) - 1 - self._row_offset(self.line, row))
            return True
        self._move_vertically(self.top + max(1, self.height) - 1)
        return True

    @_marking
    async def on_text_start(self, event: TextStart) -> bool:
        """Ctrl+PgUp: the first line, the column kept -- DN's scroll bar took
        ``kbCtrlPgUp`` and set ``Min`` alone (``VIEWS.PAS:2350``)."""
        self._moved()
        self._move_vertically(0)
        return True

    @_marking
    async def on_text_end(self, event: TextEnd) -> bool:
        """Ctrl+PgDn: the last line, the column kept (``kbCtrlPgDn``, ``Max``)."""
        self._moved()
        self._move_vertically(len(self.document) - 1)
        return True

    async def on_scroll_up(self, event: ScrollUp) -> bool:
        """``cmScrollUp``: the view a line up; the cursor moves only to stay on it.
        Soft wrapped, a row."""
        if self.soft_wrap:
            if (self.top, self.top_row) > (0, 0):
                self._moved()
                self._scroll_view(-1)
                row, _ = self._locate(self.line, self.col)
                if self._row_offset(self.line, row) >= max(1, self.height):
                    self._move_rows(-1)
            return True
        if self.top > 0:
            self._moved()
            self.top -= 1
            if self.line >= self.top + max(1, self.height):
                self._move_vertically(self.line - 1)
        return True

    async def on_scroll_down(self, event: ScrollDown) -> bool:
        if self.soft_wrap:
            if self._rows_from(self.top, self.top_row, 2) > 1:
                self._moved()
                self._scroll_view(1)
                row, _ = self._locate(self.line, self.col)
                if self._row_offset(self.line, row) < 0:
                    self._move_rows(1)
            return True
        if self.top < len(self.document) - 1:
            self._moved()
            self.top += 1
            if self.line < self.top:
                self._move_vertically(self.top)
        return True

    def _word_left(self, pos: Pos) -> Pos:
        """DN's ``WordLeft``: to the start of this word or the one before."""
        lines = self.document.lines
        line, index = pos.line, min(pos.index, len(lines[pos.line]))
        while True:
            text = lines[line]
            if index > 0:
                while index > 0 and text[index - 1] in BREAK_CHARS:
                    index -= 1
                while index > 0 and text[index - 1] not in BREAK_CHARS:
                    index -= 1
                if index < len(text) and text[index] not in BREAK_CHARS:
                    return Pos(line, index)
            if line == 0:
                return Pos(0, 0)
            line -= 1
            index = len(lines[line])

    def _word_right(self, pos: Pos) -> Pos:
        """DN's ``WordRight``: to the start of the next word."""
        lines = self.document.lines
        line, index = pos.line, pos.index
        text = lines[line]
        started_inside = index < len(text)
        while index < len(text) and text[index] not in BREAK_CHARS:
            index += 1
        while index < len(text) and text[index] in BREAK_CHARS:
            index += 1
        if index < len(text) or (started_inside and index == len(text)):
            return Pos(line, index)
        while line + 1 < len(lines):
            line += 1
            text = lines[line]
            index = 0
            if text and text[0] not in BREAK_CHARS:
                return Pos(line, 0)
            while index < len(text) and text[index] in BREAK_CHARS:
                index += 1
            if index < len(text):
                return Pos(line, index)
        return Pos(line, len(text))

    @_marking
    async def on_word_left(self, event: WordLeft) -> bool:
        self._moved()
        if not self._word_visually(-1):
            self._go(self._word_left(self._pos()))
        return True

    @_marking
    async def on_word_right(self, event: WordRight) -> bool:
        self._moved()
        if not self._word_visually(1):
            self._go(self._word_right(self._pos()))
        return True

    def go_to_line(self, number: int) -> None:
        """``ScrollTo(Delta.X, I-1)``: line *number*, counted from 1, at the same
        column; past the end, the last line."""
        self._moved()
        self._move_to(number - 1, self.col)
