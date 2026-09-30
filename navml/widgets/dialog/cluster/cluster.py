"""What a row of check boxes and a row of radio buttons have in common.

Turbo Vision's ``TCluster``, and written in Python alone for the reason
``Control`` is: it declares and paints for its two subclasses and is never
placed in a document itself.

**A cluster paints its own items.**  There are no child widgets in here, and
that is the rule ``navkit/DESIGN.md``'s *Parts: listing rows do not become
widgets* settles rather than an economy -- "``TListViewer`` draws its own
items and picks a palette entry per item according to its state.  One view,
many items, no per-item objects.  Rows were never objects in the original."  A
cluster is the same shape with a mark in front of each row, and it is why
markup needs no repeater to express one: the items are a *value*, and a value
is something a document can already say.
"""

from __future__ import annotations

from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import DEFAULT_MARKS, MARKS, marks
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty

from navml.widgets.dialog.control import Control, parse_shortcut
from navml.widgets.dialog.static_text import draw_caption


class Cluster(Control):
    """A column of captions, each with a mark in front of it."""

    #: The captions, each with one optional ``~A~`` run.  Declared here
    #: rather than in each subclass's markup because it means the same thing
    #: in both, and because a base that paints them has to be able to paint
    #: none -- a ``Cluster`` with no items is an empty column, not an error.
    items: list[str] = reactive(factory=list)

    #: Which item the keyboard is on, within the cluster.  Turbo Vision calls
    #: it ``Sel``; it is not the *value*, and moving it is not choosing.
    sel: int = reactive(0)

    #: Which characters the marks are drawn from.
    look = StyleProperty(DEFAULT_MARKS, values=tuple(MARKS))

    #: One row, its mark, and the ``~A~`` letter in its caption.
    parts = ("item", "mark", "shortcut")

    #: Where in :func:`navkit.glyphs.marks` this cluster's pair begins: 0 for
    #: a check box, 2 for a radio button.
    mark_offset = 0

    #: What goes around the mark.  ASCII in the original too, and fixed here
    #: rather than in the glyph table for that reason.
    brackets = "[]"

    #: What ``value`` means, which is the subclasses' whole difference.  The
    #: base answers "nothing is on" rather than raising, so that a bare
    #: ``Cluster`` paints instead of failing -- an abstract base that cannot
    #: be rendered is one the library's own smoke test cannot cover.
    value: int = reactive(0)

    def chosen(self, index: int) -> bool:
        """Whether item *index* is on."""
        return False

    def toggle(self, index: int) -> None:
        """Turn item *index* on, or over."""

    # -- columns -------------------------------------------------------------
    #
    # Turbo Vision's ``TCluster.Column``/``Row``: items run down a column as
    # tall as the cluster and on into the next, so four items in two rows are
    # two columns -- which is how DOS Navigator's Copy dialog put its check
    # boxes.  A column is as wide as its longest caption, and the next one
    # starts two cells after it: ``Column`` stepped by the width plus six,
    # which is the four of ``[x]`` and its blank and the two between.  A
    # cluster at least as tall as its items is one column and paints exactly
    # as it did before columns existed.

    def _rows(self) -> int:
        return max(1, self.height)

    def _column_x(self, column: int) -> int:
        rows = self._rows()
        x = 0
        for first in range(0, column * rows, rows):
            widest = max(
                (len(parse_shortcut(item)[0]) for item in self.items[first : first + rows]),
                default=0,
            )
            x += widest + 6
        return x

    def item_at(self, x: int, y: int) -> int:
        """The item painted at *x*, *y*, or -1."""
        rows = self._rows()
        if not 0 <= y < rows or x < 0:
            return -1
        column = 0
        while (column + 1) * rows < len(self.items) and x >= self._column_x(column + 1):
            column += 1
        index = column * rows + y
        return index if index < len(self.items) else -1

    # -- input ---------------------------------------------------------------

    def _move(self, delta: int) -> None:
        if self.items:
            self.sel = min(max(self.sel + delta, 0), len(self.items) - 1)

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert or not self.items:
            return False
        if event.key == "up":
            self._move(-1)
        elif event.key == "down":
            self._move(1)
        elif event.key in ("left", "right") and len(self.items) > self._rows():
            # A column along, as ``TCluster.HandleEvent`` stepped by
            # ``Size.Y``; nowhere to go is a key taken all the same.
            step = self._rows() * (1 if event.key == "right" else -1)
            if 0 <= self.sel + step < len(self.items):
                self.sel += step
        elif event.matches("space"):
            self.toggle(self.sel)
        else:
            return False
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.action != "press" or event.button != "left" or self.inert:
            return False
        index = self.item_at(event.x, event.y)
        if index >= 0:
            self.sel = index
            self.toggle(index)
            return True
        return False

    def shortcut_match(self, letter: str) -> bool:
        """A cluster answers to every letter any of its items marks."""
        if self.inert or not self.visible:
            return False
        return any(
            parse_shortcut(item)[2] == letter.lower() for item in self.items
        )

    async def activate(self, letter: str = "") -> bool:
        """Move to the item that marks *letter*, and turn it on."""
        for index, item in enumerate(self.items):
            if parse_shortcut(item)[2] == letter.lower():
                self.focus()
                self.sel = index
                self.toggle(index)
                return True
        return False

    # -- painting ------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        if self.width < 1 or self.height < 1:
            return
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        glyphs = marks(self.look, self.glyphs)
        off, on = glyphs[self.mark_offset], glyphs[self.mark_offset + 1]
        opening, closing = self.brackets
        rows = self._rows()
        for index, item in enumerate(self.items):
            column, y = divmod(index, rows)
            x = self._column_x(column)
            if x >= self.width:
                break
            style = self.part_style("item", selected=index == self.sel and self.focused)
            mark = self.part_style(
                "mark", checked=self.chosen(index), selected=index == self.sel
            )
            if len(self.items) <= rows:
                surface.fill(0, y, self.width, 1, " ", style)
            surface.draw_text(x, y, opening, mark)
            surface.draw_text(x + 1, y, on if self.chosen(index) else off, mark)
            surface.draw_text(x + 2, y, closing, mark)
            draw_caption(
                surface, x + 4, y, item, style,
                self.part_style("shortcut"), max(0, self.width - x - 4),
            )
