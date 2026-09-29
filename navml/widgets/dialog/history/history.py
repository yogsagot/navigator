"""The button beside an input line that drops its history: Turbo Vision's
``THistory``, ``THistoryWindow`` and ``THistoryViewer``.

DOS Navigator's sources replace Turbo Vision's ``HistList`` (see
:mod:`navml.history`) and keep the three views stock, so this follows Borland's
``Dialogs`` unit:

* **The button is three cells, ``▐↓▌``**: the arrow in the *History button*
  slot [53] and the half-blocks either side in *History sides* [54].  A dialog
  script puts it straight after its line -- ``InputLine 2, 2, 44, 3`` and then
  ``History 44, 2, hsMakeDir`` -- and names the list by id.
* **A click on it, or Down in the linked line, drops the list**, after
  recording what the line holds now, so the text being replaced is not lost.
* **The list is a framed window one column wider than the line on each side
  and eight rows tall**, from the row above the line, clipped to the dialog --
  ``Dec(R.A.X); Inc(R.B.X); Inc(R.B.Y, 7); Dec(R.A.Y)`` and an intersect.  It
  opens on the *second* entry, because the first is the text just recorded.
* **Enter or a double click puts the entry in the line**, selected whole, so
  typing replaces it; Esc leaves the line as it was.
* **Accepting the dialog records every line that has a history**, which is
  what Turbo Vision's ``cmRecordHistory`` broadcast did; cancelling records
  nothing.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.reactive import bind, effect, reactive, untracked
from navkit.screen import Surface
from navkit.widget import Widget

from navml.component import take_declared
from navml.history import HISTORY, HistoryStore
from navml.widgets.dialog.list_viewer import ListViewer

#: ``#222 #25 #221`` in code page 437, and what an ASCII terminal gets instead.
BUTTON = {"dos": "▐↓▌", "ascii": "[v]"}

#: How many rows the list adds below the line: Turbo Vision's ``Inc(R.B.Y, 7)``.
DROP = 7


class History(Widget):
    """Three cells beside an :class:`InputLine`, and the list they drop."""

    #: The arrow; the sides are the widget's own style.
    parts = ("arrow",)

    #: The input line whose text this remembers and replaces.
    link: Any = reactive(None)
    #: Which list: every button naming the same id shares one.
    history_id: str = reactive("")

    def __init__(self, **kwargs: Any) -> None:
        take_declared(self, kwargs)
        super().__init__(**kwargs)
        #: Where the lists are kept; the shared :data:`~navml.history.HISTORY`
        #: unless a program hands in another.
        self.store: HistoryStore = HISTORY

    def mounted(self) -> None:
        super().mounted()
        # The line has to know its button, because Down arrives at the line:
        # it holds the keyboard, and a button beside it is not on the way up.
        effect(self, History._attach)

    def _attach(self) -> None:
        link = self.link
        if link is not None:
            with untracked():
                link.history = self

    def unmounting(self) -> None:
        link = self.link
        if link is not None and getattr(link, "history", None) is self:
            link.history = None
        super().unmounting()

    # -- the list ------------------------------------------------------------------

    def record(self) -> None:
        """Remember what the line holds now: ``RecordHistory``."""
        if self.link is not None and self.history_id:
            self.store.add(self.history_id, self.link.value)

    def open(self) -> HistoryList | None:
        """Record the line, then drop the list over it.  None if it cannot."""
        app, link = self.application, self.link
        if app is None or link is None or not self.history_id or link.inert:
            return None
        self.record()
        entries = self.store.entries(self.history_id)
        if not entries:
            return None
        x, y, width, height = self._drop_rect()
        window = HistoryList(self)
        window.items = entries
        window.cursor = 1 if len(entries) > 1 else 0
        window.x = bind(lambda o, v=x: v)
        window.y = bind(lambda o, v=y: v)
        window.width = bind(lambda o, v=width: v)
        window.height = bind(lambda o, v=height: v)
        app.overlay(window)
        return window

    def _drop_rect(self) -> tuple[int, int, int, int]:
        """Where the list goes, in screen coordinates, as ``THistory`` works it out.

        One column wider than the line on either side, from the row above it
        to seven rows below it, clipped to the modal the line is in -- or to
        the screen, when it is in none.
        """
        link = self.link
        lx, ly = link.offset()
        lx, ly = lx + link.x, ly + link.y
        left, top = lx - 1, ly - 1
        right, bottom = lx + link.width + 1, ly + 1 + DROP
        owner = _modal_of(link) or self.application.root
        ox, oy = owner.offset()
        ox, oy = ox + owner.x, oy + owner.y
        left, top = max(left, ox), max(top, oy)
        right = min(right, ox + owner.width)
        bottom = min(bottom, oy + owner.height) - 1
        return left, top, max(0, right - left), max(0, bottom - top)

    def choose(self, text: str) -> None:
        """Put *text* in the line, selected whole so typing replaces it."""
        link = self.link
        link.value = text
        link.select_all()
        link.focus()

    # -- painting and input --------------------------------------------------------

    def render(self, surface: Surface) -> None:
        glyphs = BUTTON["dos" if self.glyphs >= GLYPHS_UNICODE else "ascii"]
        surface.draw_text(0, 0, glyphs[0], self.style)
        surface.draw_text(1, 0, glyphs[1], self.part_style("arrow"))
        surface.draw_text(2, 0, glyphs[2], self.style)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.action != "press" or event.button != "left":
            return False
        self.open()
        return True


class HistoryList(ListViewer):
    """The dropped list: a framed, modal :class:`ListViewer` of one history.

    Turbo Vision built it from a window, a viewer and a scroll bar; a
    ``ListViewer`` is all three already -- its frame, its rows and a scroll
    bar on its right edge.
    """

    #: ``THistoryWindow`` was a window, and cast a window's shadow.
    shadow: bool = True

    def __init__(self, button: History, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: The button that dropped this, and the line it fills.
        self.button = button
        self.modal = True

    def layout(self, width: int, height: int) -> None:
        """Keep the rectangle the button worked out; a cascade must not refit it."""

    async def choose(self) -> bool:
        """Enter or a double click: the entry goes into the line."""
        text = self.selected
        self.close()
        if text is not None:
            self.button.choose(text)
        return True

    def close(self) -> None:
        if self.parent is not None:
            self.parent.remove(self)

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("escape"):
            self.close()
            return True
        await super().on_key(event)
        # A modal list keeps every other key: nothing behind it may act.
        return True


def _modal_of(widget: Widget) -> Widget | None:
    """The nearest ancestor that is a modal, which is what the list is clipped to."""
    node = widget.parent
    while node is not None:
        if node.modal:
            return node
        node = node.parent
    return None
