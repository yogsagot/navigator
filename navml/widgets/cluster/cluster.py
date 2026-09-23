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

from navml.widgets.control import Control, parse_shortcut
from navml.widgets.static_text import draw_caption


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

    # -- input ---------------------------------------------------------------

    def _move(self, delta: int) -> None:
        if self.items:
            self.sel = min(max(self.sel + delta, 0), len(self.items) - 1)

    async def on_key(self, event: KeyEvent) -> bool:
        if self.disabled or not self.items:
            return False
        if event.key == "up":
            self._move(-1)
        elif event.key == "down":
            self._move(1)
        elif event.matches("space"):
            self.toggle(self.sel)
        else:
            return False
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.action != "press" or event.button != "left" or self.disabled:
            return False
        if 0 <= event.y < len(self.items):
            self.sel = event.y
            self.toggle(event.y)
            return True
        return False

    def shortcut_match(self, letter: str) -> bool:
        """A cluster answers to every letter any of its items marks."""
        if self.disabled or not self.visible:
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
        for index, item in enumerate(self.items[: self.height]):
            style = self.part_style("item", selected=index == self.sel and self.focused)
            mark = self.part_style(
                "mark", checked=self.chosen(index), selected=index == self.sel
            )
            surface.fill(0, index, self.width, 1, " ", style)
            surface.draw_text(0, index, opening, mark)
            surface.draw_text(1, index, on if self.chosen(index) else off, mark)
            surface.draw_text(2, index, closing, mark)
            draw_caption(
                surface, 4, index, item, style,
                self.part_style("shortcut"), max(0, self.width - 4),
            )
