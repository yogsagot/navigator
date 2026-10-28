"""The grid inside the *Character Table*: any number of characters, a row of
them to a list row.

Not DOS Navigator's ``TTable`` (that is :class:`CharTable`, 256 cells that
always fit): a list of characters can be a hundred thousand long, so this is
a :class:`ListViewer` whose items are *rows* of codes, and which scrolls, pages
and carries a scroll bar the way any list does.  :attr:`column` is the cell
across the row the cursor is on, and :attr:`code` the character under the
two together.

**A cell is three columns**: a blank and then the character, which leaves
the second column for one that is two cells wide (``字``, most emoji) and
for a Nerd Font icon drawn wider than the font's own measure says
(``navigator/lib/appearance/icons.py`` says why that happens).  What a cell
shows is :func:`~navigator.lib.utilities.unicode_table.display`'s, a mark on
its dotted circle.

The arrows move a cell, Left and Right running on round the row's ends;
Home and End go to the first and the last character; a press or a drag puts
the cursor under the pointer, and a double click or Enter is
:class:`ChosenEvent`, as ``TTable`` put the character back as a key press.
The cursor cell is shown whether the grid has the keyboard or not: it is the
character the info line describes and Enter would take.

**The character under the pointer describes itself in a tooltip**, as the
info line describes the cursor's (``unicode_table.describe``): its code
point, name, category, decimal code, UTF-8 bytes and block.  A departure:
DN's ``TTable`` had no tooltip.
"""

from __future__ import annotations

from typing import Any, Callable

from navkit.events import KeyEvent, MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import computed, effect, peek, reactive
from navkit.screen import Surface

from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent

from navigator.lib.utilities.unicode_table import describe, display

#: Columns a character is given.
CELL = 3


class UnicodeGrid(ListViewer):
    """The characters of a category, :attr:`columns` to a row."""

    emits = (ChosenEvent,)

    #: Every character shown, in order.  Replaced through :meth:`show`.
    codes: list[int] = reactive(factory=list)

    #: The cell across the cursor's row.
    column: int = reactive(0)

    #: Across the top frame: the category's name.
    caption: str = reactive("")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: Where :meth:`show` asked the cursor to go, for the layout to put it.
        self._start: int | None = None
        #: The columns the rows were last cut to.
        self._laid = 1
        #: Where the tooltips find the Nerd Font's icon names, to name an icon
        #: by: the chart's index once read, None before that or below that tier.
        self.nerd_names: Callable[[], dict[int, tuple[str, ...]] | None] = lambda: None

    def mounted(self) -> None:
        super().mounted()
        effect(self, UnicodeGrid._layout)

    @computed
    def columns(self) -> int:
        return max(1, self.inner_width // CELL)

    @computed
    def index(self) -> int:
        """Where in :attr:`codes` the cursor is, or -1 with nothing shown."""
        if not self.codes:
            return -1
        return min(self.cursor * self.columns + self.column, len(self.codes) - 1)

    @computed
    def code(self) -> int | None:
        """The character under the cursor."""
        index = self.index
        return self.codes[index] if index >= 0 else None

    def show(self, codes: list[int], at: int = 0) -> None:
        """List *codes*, the cursor on the *at*-th."""
        self._start = at
        if codes == peek(self, UnicodeGrid.codes):
            self._layout()
        self.codes = list(codes)

    def go_to(self, at: int) -> None:
        """The cursor onto the *at*-th character, clamped."""
        last = len(self.codes) - 1
        at = min(max(at, 0), last) if last >= 0 else 0
        self.cursor, self.column = divmod(at, self.columns)

    def _layout(self) -> None:
        """Cut :attr:`codes` into rows for the width there is, keeping the
        cursor on its character when only the width changed."""
        codes, columns = self.codes, self.columns
        if self._start is not None:
            at, self._start = self._start, None
        else:
            at = peek(self, ListViewer.cursor) * self._laid + peek(self, UnicodeGrid.column)
        self._laid = columns
        self.items = [codes[i:i + columns] for i in range(0, len(codes), columns)]
        last = len(codes) - 1
        at = min(max(at, 0), last) if last >= 0 else 0
        self.cursor, self.column = divmod(at, columns)

    # -- what ListViewer asks --------------------------------------------------------

    def title_text(self) -> str:
        return f" {self.caption} " if self.caption else ""

    def footer_text(self) -> str:
        if not self.codes:
            return ""
        return " " + tr("{at} of {count}").format(at=self.index + 1, count=len(self.codes)) + " "

    async def choose(self) -> bool:
        if self.code is None:
            return False
        await self.emit(ChosenEvent(self.code))
        return True

    def tooltip_at(self, x: int, y: int) -> str:
        """The character under the pointer, described as the info line does
        the cursor's; the grid's own tooltip between cells."""
        at = self.index_at(x, y)
        if at is None:
            return super().tooltip_at(x, y)
        return "\n".join(describe(self.codes[at], self.nerd_names()))

    def index_at(self, x: int, y: int) -> int | None:
        row = self.row_at(y)
        column = (x - self.inset) // CELL
        if row is None or x < self.inset or column >= self.columns:
            return None
        at = row * self.columns + column
        return at if at < len(self.codes) else None

    # -- input -----------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        if event.matches("left"):
            self.go_to(self.index - 1)
        elif event.matches("right"):
            self.go_to(self.index + 1)
        elif event.matches("home"):
            self.go_to(0)
        elif event.matches("end"):
            self.go_to(len(self.codes) - 1)
        else:
            return await super().on_key(event)
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.button == "left" and event.action in ("press", "move") and not self.inert:
            at = self.index_at(event.x, event.y)
            if at is not None:
                self.focus()
                self.go_to(at)
                return True
        return await super().on_mouse_click(event)

    async def on_double_click(self, event: MouseClickEvent) -> bool:
        if event.button != "left" or self.index_at(event.x, event.y) is None:
            return False
        self.go_to(self.index_at(event.x, event.y))
        return await self.choose()

    # -- painting --------------------------------------------------------------------

    def render_items(self, surface: Surface) -> None:
        inset, columns, index = self.inset, self.columns, self.index
        plain = self.part_style("row", selected=False)
        chosen = self.part_style("row", selected=True)
        for row in range(self.rows):
            line = self.scroll + row
            if line >= len(self.items):
                break
            y = inset + self.header + row
            for column, code in enumerate(self.items[line]):
                x = inset + column * CELL
                style = chosen if line * columns + column == index else plain
                if style is chosen:
                    surface.fill(x, y, CELL, 1, " ", style)
                surface.set_cell(x + 1, y, display(code), style)
