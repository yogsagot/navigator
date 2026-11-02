"""``TCalcView``: a CSV or TSV file's rows in DN's spreadsheet frame, a cell the cursor.

**Written in Python alone**: everything it shows is painted.  The layout is
``TCalcView.Draw``'s, top to bottom:

- the cell's name (``TInfoView``, ``B3``) and its whole text (``TCalcInfo``);
- a rule, then the column letters, centred in each column (``Dig``);
- the file's header row, frozen as titles -- a departure: a ``.WKZ`` had none;
- a rule, then the rows, each after its number in a gutter (DN's five
  columns, wider for a longer file), the cells between ``│``.

A number is right-aligned in its cell, as DN aligned a value.  A cell's line
breaks and tabs show as blanks; Enter (``ShowCell``) shows it whole.

The cursor is a cell, ``col`` and ``row``; ``row`` counts the rows *shown*,
which :attr:`order` -- a sort, a departure -- maps to the file's.  ``left``
and ``top`` are the first column and row on screen, kept so the cursor shows.
Keys are ``TCalcView.HandleEvent``'s: arrows, Home to ``A1``, End to the last
cell, and ``cmChangeWidth``'s mode (:attr:`resizing`), whose Left and Right
narrow and widen the cursor's column until Enter or Esc.
"""

from __future__ import annotations

from array import array
from typing import Any

from navkit.bidi import display_width
from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.i18n import tr
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget
from navml.widgets.menu.context_menu import ContextMenu, ContextMenuHost

from navigator.lib.viewer.table import TableSource, cell_name, column_name, number

#: How far Ctrl+Left/Right and the width mode may take a column.
WIDEST = 200
#: Rows a wheel notch moves.
WHEEL_ROWS = 3


#: The columns a cell takes beyond its width: a blank either side, and its rule.
PAD = 3


def flat(text: str) -> str:
    """*text* on one line: a line break or a tab is a blank."""
    return "".join(" " if char in "\r\n\t\v\f" else char for char in text.replace("\r\n", "\n"))


class SheetView(ContextMenuHost, Widget):
    """The rows of a :class:`~navigator.lib.viewer.table.TableSource`, a cell at a time."""

    #: The letters, numbers and rules (``GetColor(1)``); the cursor's cell
    #: (``GetColor(3)``); the header's titles; the cell's name on top.
    parts = ("headings", "cursor", "titles", "name")

    #: The cursor: a column, and a row as shown.
    col: int = reactive(0)
    row: int = reactive(0)
    #: The first column and row on screen.
    left: int = reactive(0)
    top: int = reactive(0)
    #: ``cmChangeWidth``'s mode.
    resizing: bool = reactive(False)
    #: Bumped when the source finds more rows or a sort lands: a repaint.
    generation: int = reactive(0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.can_focus = True
        self.source: TableSource | None = None
        #: Each column's width, as measured and as changed since.
        self.widths: list[int] = []
        #: The rows shown, as indices of the file's; None for the file's order.
        self.order: array | None = None
        #: The sort in force: ``(column, descending)``, or None.
        self.sort: tuple[int, bool] | None = None

    # -- the file --------------------------------------------------------------------

    def show(self, source: TableSource, row: int = 0) -> None:
        """Show *source* from row *row*, its widths measured."""
        self.source = source
        source.measure()
        self.widths = list(source.widths)
        self.order, self.sort = None, None
        self.col = self.left = 0
        self.row = max(0, row)
        self.top = 0
        self.refresh()

    def refresh(self) -> None:
        """More rows found, or the order changed: paint again."""
        source = self.source
        if source is not None and len(self.widths) < source.columns:
            self.widths += source.widths[len(self.widths):]
        self.generation += 1
        self.invalidate()

    @property
    def count(self) -> int:
        return self.source.count if self.source is not None else 0

    @property
    def columns(self) -> int:
        return len(self.widths)

    def file_row(self, row: int) -> int:
        """The file's row shown as row *row*."""
        order = self.order
        return order[row] if order is not None and row < len(order) else row

    def cells(self, row: int) -> list[str] | None:
        source = self.source
        return None if source is None or not 0 <= row < self.count else source.row(self.file_row(row))

    def cell(self, row: int | None = None, col: int | None = None) -> str:
        """The text of a cell, the cursor's by default; "" for none."""
        cells = self.cells(self.row if row is None else row)
        col = self.col if col is None else col
        return cells[col] if cells is not None and col < len(cells) else ""

    # -- geometry --------------------------------------------------------------------

    @property
    def gutter(self) -> int:
        """Columns the row numbers take before their rule: DN's five at least."""
        return max(5, len(str(max(1, self.count)))) + 1

    @property
    def first_row_y(self) -> int:
        """The line the first row is painted on: under the cell line, a
        rule, the letters, the titles if any, and a rule."""
        header = self.source is not None and self.source.dialect.header
        return 5 if header else 4

    @property
    def page(self) -> int:
        return max(1, self.height - self.first_row_y)

    def shown_columns(self) -> list[int]:
        """The columns that fit whole from ``left`` on -- one at least."""
        shown, x = [], self.gutter + 1
        for column in range(self.left, self.columns):
            x += self.widths[column] + PAD
            if x > self.width and shown:
                break
            shown.append(column)
        return shown

    def column_x(self, column: int) -> int | None:
        """Where *column*'s cell starts on screen, if it is shown."""
        x = self.gutter + 1
        for shown in self.shown_columns():
            if shown == column:
                return x
            x += self.widths[shown] + PAD
        return None

    def _clamp(self) -> None:
        self.row = max(0, min(self.row, self.count - 1)) if self.count else 0
        self.col = max(0, min(self.col, self.columns - 1)) if self.columns else 0
        page = self.page
        if self.top > self.row:
            self.top = self.row
        if self.row >= self.top + page:
            self.top = self.row - page + 1
        self.top = max(0, self.top)
        if self.left > self.col:
            self.left = self.col
        while self.col not in self.shown_columns() and self.left < self.col:
            self.left += 1

    def go(self, col: int | None = None, row: int | None = None) -> None:
        if col is not None:
            self.col = col
        if row is not None:
            self.row = row
        self._clamp()

    # -- keys ------------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.source is None:
            return False
        key = event.name
        if self.resizing:
            return self._resize_key(key)
        page = self.page
        moves = {
            "left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1),
            "pageup": (0, -page), "pagedown": (0, page),
        }
        if key in moves:
            dx, dy = moves[key]
            self.go(col=self.col + dx, row=self.row + dy)
        elif key == "home":
            # DN's kbHome: A1.
            self.go(col=0, row=0)
            self.left = self.top = 0
        elif key == "end":
            # DN's kbEnd: the last cell there is.
            self.go(col=self.columns - 1, row=self.count - 1)
        elif key == "ctrl+home":
            self.go(col=0)
        elif key == "ctrl+end":
            self.go(col=self.columns - 1)
        elif key == "ctrl+pageup":
            self.go(row=0)
        elif key == "ctrl+pagedown":
            self.go(row=self.count - 1)
        elif key in ("ctrl+left", "ctrl+right"):
            # A departure: DN reached a column's width through the menu only.
            self.widen(-1 if key == "ctrl+left" else 1)
        else:
            return False
        return True

    def _resize_key(self, key: str) -> bool:
        """``cmChangeWidth``'s loop: Left, Right, and Enter or Esc to end it."""
        if key in ("left", "right"):
            self.widen(-1 if key == "left" else 1)
        elif key in ("enter", "escape"):
            self.resizing = False
        return True

    def widen(self, delta: int) -> None:
        """The cursor's column one narrower or wider, between 1 and :data:`WIDEST`."""
        if not self.widths:
            return
        self.widths[self.col] = max(1, min(WIDEST, self.widths[self.col] + delta))
        self._clamp()
        self.refresh()

    # -- the mouse -------------------------------------------------------------------

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if self.source is None:
            return False
        if event.is_wheel:
            if event.button in ("wheel_up", "wheel_down"):
                step = -WHEEL_ROWS if event.button == "wheel_up" else WHEEL_ROWS
                self.top = max(0, min(self.top + step, max(0, self.count - self.page)))
                self.row = max(self.top, min(self.row, self.top + self.page - 1))
                return True
            return False
        if event.action != "press" or event.button != "left":
            return False
        self.focus()
        cell = self.cell_at(event.x, event.y)
        if cell is not None:
            # A departure: DN's spreadsheet took the mouse on its scroll bars only.
            self.go(*cell)
        return True

    def cell_at(self, x: int, y: int) -> tuple[int, int] | None:
        """The column and row shown at *x*, *y*, or None off every cell."""
        row = self.top + y - self.first_row_y
        if y < self.first_row_y or row >= self.count:
            return None
        left = self.gutter + 1
        for column in self.shown_columns():
            width = self.widths[column] + PAD
            if left <= x < left + width:
                return column, row
            left += width
        return None

    # -- the context menu ------------------------------------------------------------

    def prepare_context(self, x: int, y: int) -> None:
        cell = self.cell_at(x, y)
        if cell is not None:
            self.go(*cell)

    def context_point(self) -> tuple[int, int]:
        x = self.column_x(self.col)
        return (x if x is not None else 0), min(self.row - self.top + self.first_row_y + 1, max(0, self.height - 1))

    def context_menu(self) -> ContextMenu | None:
        """The window's *Table* menu's most used entries, built each time so
        its captions follow the language."""
        from navml.commands import CloseWindow

        from navigator.widgets.viewer.commands import (
            ContinueSearch,
            FindCell,
            GotoCell,
            ShowCell,
            SortColumn,
            ViewSheetAsText,
        )

        if self.source is None:
            return None
        menu = ContextMenu()
        menu.add_item(tr("~V~iew cell..."), ShowCell)
        menu.add_item(tr("~S~ort by column"), SortColumn)
        menu.add_line()
        menu.add_item(tr("~F~ind..."), FindCell)
        menu.add_item(tr("Search a~g~ain"), ContinueSearch)
        menu.add_item(tr("Go to cell ~n~umber..."), GotoCell)
        menu.add_line()
        menu.add_item(tr("As ~t~ext"), ViewSheetAsText)
        menu.add_item(tr("~C~lose"), CloseWindow)
        return menu

    # -- painting --------------------------------------------------------------------

    def _rules(self) -> tuple[str, str, str]:
        """The vertical, horizontal and crossing rule, in the glyph tier."""
        return ("│", "─", "┼") if self.glyphs >= GLYPHS_UNICODE else ("|", "-", "+")

    def cursor_position(self) -> tuple[int, int] | None:
        return None

    def render(self, surface: Surface) -> None:
        width, height = self.width, self.height
        plain, headings, titles = self.style, self.part_style("headings"), self.part_style("titles")
        cursor, name_style = self.part_style("cursor"), self.part_style("name")
        surface.fill(0, 0, width, height, " ", plain)
        source = self.source
        if source is None or not width or not height:
            return
        self._clamp()
        bar, dash, cross = self._rules()
        gutter = self.gutter
        shown = self.shown_columns()

        # The cell line: its name, then its text.
        surface.fill(0, 0, gutter, 1, " ", name_style)
        name = cell_name(self.col, self.row) if self.count else ""
        surface.draw_text(max(0, (gutter - len(name)) // 2), 0, name, name_style, gutter)
        surface.draw_text(gutter, 0, bar, headings, 1)
        surface.draw_text(gutter + 2, 0, flat(self.cell()), plain, max(0, width - gutter - 2))

        def rule(y: int) -> None:
            surface.draw_text(0, y, dash * width, headings)
            surface.draw_text(gutter, y, cross, headings, 1)
            x = gutter + 1
            for column in shown:
                x += self.widths[column] + PAD
                if x - 1 < width:
                    surface.draw_text(x - 1, y, cross, headings, 1)

        def separators(y: int, style: Any) -> None:
            surface.draw_text(gutter, y, bar, style, 1)
            x = gutter + 1
            for column in shown:
                x += self.widths[column] + PAD
                if x - 1 < width:
                    surface.draw_text(x - 1, y, bar, style, 1)

        rule(1)
        # The letters, centred, as ``Dig`` was.
        surface.fill(0, 2, width, 1, " ", headings)
        x = gutter + 1
        for column in shown:
            cell_width = self.widths[column]
            letters = column_name(column)
            surface.draw_text(x + 1 + max(0, (cell_width - len(letters)) // 2), 2, letters, headings,
                              max(0, min(cell_width, width - x - 1)))
            x += cell_width + PAD
        separators(2, headings)
        y = 3
        titles_row = source.titles()
        if source.dialect.header:
            surface.fill(0, y, width, 1, " ", titles)
            self._cells(surface, y, titles_row or [], shown, titles, None)
            separators(y, headings)
            y += 1
        rule(y)
        y += 1
        for offset in range(height - y):
            row = self.top + offset
            cells = self.cells(row)
            if cells is None:
                break
            number_text = str(row + 1).rjust(gutter - 1)
            surface.draw_text(0, y + offset, number_text, headings, gutter)
            self._cells(surface, y + offset, cells, shown, plain, cursor if row == self.row else None)
            separators(y + offset, headings)

    def _cells(self, surface: Surface, y: int, cells: list[str], shown: list[int], style: Any,
               cursor: Any) -> None:
        """One row's cells across the columns shown; the cursor's in *cursor*."""
        x = self.gutter + 1
        for column in shown:
            cell_width = self.widths[column]
            look = cursor if cursor is not None and column == self.col else style
            if look is not style:
                surface.fill(x, y, min(cell_width + 2, max(0, self.width - x)), 1, " ", look)
            text = flat(cells[column]) if column < len(cells) else ""
            at = x + 1
            if number(text) is not None and display_width(text) < cell_width:
                # A value, right-aligned as DN put one.
                at += cell_width - display_width(text.strip())
                text = text.strip()
            surface.draw_text(at, y, text, look, max(0, min(cell_width - (at - x - 1), self.width - at)))
            x += cell_width + PAD


__all__ = ["SheetView", "flat"]
