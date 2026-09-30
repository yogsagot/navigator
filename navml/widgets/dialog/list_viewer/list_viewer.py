"""The model and the painting behind ``list_viewer.nml``.

Lifted out of ``navigator/widgets/panel/panel.py``, which had all of it and
was the only widget in the repository that did.  What stayed behind there is
everything about *files*; what came here is everything about *a list*.

**The three invariants are effects, and their declaration order is their flush
order.**  Clamp the cursor onto a row that exists, then scroll far enough to
show it.  Holding them as effects rather than doing the work in whatever moved
the cursor is what makes them hold no matter which path changed the state --
including a terminal resize, which an imperative version gets wrong.

**They are declared in `mounted()`, not `__init__`.**  ``remove()`` disposes a
subtree's effects, and every widget in a dialog can be removed and put back.
``Panel`` could declare them in its constructor because the desktop never lets
it go; a library widget has no such promise.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import computed, effect, peek, reactive
from navkit.screen import Surface
from navkit.style import Style

from navml.widgets.dialog.control import Control
from navml.widgets.dialog.scroll_bar import ScrollEvent

#: How many rows one wheel notch moves.
WHEEL_ROWS = 3


class ListViewer(Control):
    """A framed list with a cursor, a title and a footer."""

    #: The path across the top frame, one row, the summary along the bottom,
    #: a message in place of the rows, and the rule between two columns.
    parts = ("title", "row", "footer", "error", "divider")

    #: A message shown instead of the rows -- a directory that would not open,
    #: a search that found nothing.  Not markup's, because a subclass sets it
    #: from something it caught.
    error: str | None = reactive(None)

    #: Whether the list draws its own frame.  Turbo Vision's list views had
    #: none -- a dialog's frame or a window's was theirs -- and a file panel
    #: has one; a list set inside a dialog, as DOS Navigator's tree in *Choose
    #: Directory* is, turns it off and gives the frame's cells to its rows.
    #: The scroll bar then takes the last column, as ``TScrollBar`` sat beside
    #: its view.
    framed: bool = reactive(True)

    @computed
    def inset(self) -> int:
        """Where the rows begin: inside the frame, or at the edge without one."""
        return 1 if self.framed else 0

    @computed
    def inner_width(self) -> int:
        """Columns a row may use: between the frame, or up to the scroll bar."""
        return max(0, self.width - 2 if self.framed else self.width - 1)

    def mounted(self) -> None:
        super().mounted()
        # Declaration order is flush order: put the cursor on a row that
        # exists, then scroll to it.
        effect(self, ListViewer._clamp_cursor)
        # Looked up on the class, so a subclass that lays its items out other
        # than one per row can say how the scroll follows.
        effect(self, type(self)._follow_cursor)

    # -- the model -----------------------------------------------------------

    @computed
    def rows(self) -> int:
        """How many listing lines fit between the frames and the header."""
        return max(0, self.height - 2 * self.inset - self.header)

    @computed
    def capacity(self) -> int:
        """How many items are on show at once: one per row, unless a subclass says."""
        return self.rows

    @computed
    def selected(self) -> Any:
        """The item the cursor is on, if the list has one."""
        if 0 <= self.cursor < len(self.items):
            return self.items[self.cursor]
        return None

    def _clamp_cursor(self) -> None:
        """Keep the cursor on a row that exists, however the list changed.

        Assigning what it also reads is allowed here: an effect's own writes
        are part of the run it is in and do not wake it again.
        """
        last = len(self.items) - 1
        self.cursor = min(max(self.cursor, 0), last) if last >= 0 else 0

    def _follow_cursor(self) -> None:
        """Scroll just far enough to keep the cursor on screen.

        ``scroll`` is read with :func:`~navkit.reactive.peek` because this is
        the effect that assigns it; subscribing to it would be a loop.
        """
        cursor, rows = self.cursor, self.rows
        scroll = peek(self, ListViewer.scroll)
        if cursor < scroll:
            self.scroll = cursor
        elif rows and cursor >= scroll + rows:
            self.scroll = cursor - rows + 1

    def move_cursor(self, delta: int) -> None:
        if not self.items:
            return
        # Deliberately unclamped: _clamp_cursor owns that invariant.
        self.cursor += delta

    def page(self) -> int:
        """How far PageUp and PageDown move."""
        return max(1, self.capacity - 1)

    async def choose(self) -> bool:
        """What Enter or a double click means.  Nothing, until a subclass."""
        return False

    # -- what a subclass fills in --------------------------------------------

    def row_text(self, index: int, item: Any) -> str:
        """The text for one row.  ``str(item)`` unless told otherwise."""
        return str(item)

    def row_selected(self, index: int) -> bool:
        """Whether row *index* is the one under the cursor, showing.

        The cursor shows only on the list that has the keyboard, so the two
        conditions are ANDed here rather than left to a ``:focused`` selector
        -- the row *fill* is gated on the same answer and has to agree.
        """
        return index == self.cursor and self.focused

    def row_style(self, index: int, item: Any) -> Style:
        """How one row should look, including whether it is the cursor."""
        return self.part_style("row", selected=self.row_selected(index))

    def render_row(self, surface: Surface, y: int, index: int, item: Any) -> None:
        """Paint one row into the already-filled band at *y*."""
        surface.draw_text(self.inset, y, self.row_text(index, item),
                          self.row_style(index, item), self.inner_width)

    def title_text(self) -> str:
        return ""

    def footer_text(self) -> str:
        return ""

    # -- input ---------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        if event.key == "up":
            self.move_cursor(-1)
        elif event.key == "down":
            self.move_cursor(1)
        elif event.key == "pageup" and not event.ctrl:
            # Not Ctrl+PgUp: a file panel's "parent directory", which a list
            # taking it as PgUp would hide from every key table behind it.
            self.move_cursor(-self.page())
        elif event.key == "pagedown":
            self.move_cursor(self.page())
        elif event.key == "home":
            self.move_cursor(-len(self.items))
        elif event.key == "end":
            self.move_cursor(len(self.items))
        elif event.matches("enter"):
            # A bare Enter only: Ctrl+Enter and Alt+Enter are other commands,
            # and a list that took them as Enter would hide them from every
            # key table behind it.
            return await self.choose()
        else:
            return False
        return True

    def row_at(self, y: int) -> int | None:
        """Which item is painted at *y*, in this widget's coordinates."""
        row = y - self.inset - self.header
        if 0 <= row < self.rows:
            index = self.scroll + row
            if index < len(self.items):
                return index
        return None

    def index_at(self, x: int, y: int) -> int | None:
        """Which item is painted at *x*, *y*.  The row's, unless a subclass says."""
        return self.row_at(y)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if self.inert:
            return False
        if event.is_wheel:
            step = -WHEEL_ROWS if event.button == "wheel_up" else WHEEL_ROWS
            self.move_cursor(step)
            return True
        if event.action != "press" or event.button != "left":
            return False
        index = self.index_at(event.x, event.y)
        if index is not None:
            self.cursor = index
            return True
        return False

    async def on_double_click(self, event: MouseClickEvent) -> bool:
        """Open the row that was double-clicked.

        It only has to open it: navkit delivers the press that completed the
        double click *as well*, and that press has already moved the cursor
        onto this row -- which is what the additive delivery is for.
        """
        if event.button != "left" or self.index_at(event.x, event.y) is None:
            return False
        return await self.choose()

    async def on_bar_scroll(self, event: ScrollEvent) -> bool:
        """The user worked the scrollbar: move the cursor where it asked.

        Named by the generator's ``on_<id>_<event>`` convention.  The bar's
        value is the cursor, so this is the whole of it -- the scroll follows.
        """
        self.cursor = event.value
        return True

    # -- painting ------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        inset = self.inset
        if self.framed:
            if self.width < 2 or self.height < 2:
                return
            surface.draw_box(
                0, 0, self.width, self.height, self.style,
                charset=self.box_charset(), fill=" ",
            )
            self._render_label(surface, 0, self.title_text(), "title")
            self._render_label(surface, self.height - 1, self.footer_text(), "footer")
        else:
            # The rows' columns only: the scroll bar paints its own, and below
            # its end the cells are whatever the list stands on -- a window's
            # frame, when the bar sits on it.
            surface.fill(0, 0, self.inner_width, self.height, " ", self.style)
        self.render_header(surface)
        if self.error is not None:
            surface.draw_text(
                inset + 1, inset + self.header, self.error,
                self.part_style("error"), max(0, self.width - 4),
            )
            return
        self.render_items(surface)

    def render_items(self, surface: Surface) -> None:
        """Paint the items on show, one per row."""
        inset = self.inset
        for row in range(self.rows):
            index = self.scroll + row
            if index >= len(self.items):
                break
            y = inset + self.header + row
            item = self.items[index]
            # **Filled only when it is the cursor row.**  An unselected row is
            # drawn as text on whatever the list already painted, and the gaps
            # between its columns keep the list's own style.  Filling them
            # instead would change the style of cells that are blank -- which
            # looks identical and is not: ``render_diff`` compares cells by
            # style and emits an SGR sequence for every run that differs, so a
            # fill nobody can see is real bytes on the wire.
            if self.row_selected(index):
                surface.fill(inset, y, self.inner_width, 1, " ",
                             self.row_style(index, item))
            self.render_row(surface, y, index, item)

    def render_header(self, surface: Surface) -> None:
        """The band between the top frame and the rows.  Empty by default."""

    def _render_label(self, surface: Surface, y: int, text: str, part: str) -> None:
        if not text:
            return
        surface.draw_text(
            max(1, (self.width - len(text)) // 2), y, text, self.part_style(part)
        )
