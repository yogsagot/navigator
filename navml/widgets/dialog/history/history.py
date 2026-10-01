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

And one thing Turbo Vision's did not do: **a button given ``choices`` drops
those instead** -- a fixed list the program hands in, such as the users a
file may be given to.  It records nothing, because what the line held is not
something to remember, and it opens on the entry the line already names.  A
history is capped at twenty and shared by id, and neither suits a list read
from ``/etc/passwd``.

**Typing in such a list searches it**: the panel's quick search, the name
beginning with what was typed (case folded, ``*`` and ``?`` wildcards), the
first from the top and then onward as the text grows, a character that would
name nothing refused, Backspace taking one back.  ``Search: ...`` shows on
the list's bottom edge with the caret after it.  A history list does not
search, as Turbo Vision's did not.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.reactive import bind, effect, peek, reactive, untracked
from navkit.screen import Surface
from navkit.widget import Widget

from navml.component import take_declared
from navml.history import HISTORY, HistoryStore
from navml.quick_search import name_pattern
from navml.widgets.dialog.drop_down import DropDown
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
    #: A fixed list to drop instead of the history, when not empty.
    choices: list[str] = reactive(factory=list)

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
        """Remember what the line holds now: ``RecordHistory``.

        Nothing for a button with :attr:`choices`, whose list is not a history.
        """
        if self.link is not None and self.history_id and not self.choices:
            self.store.add(self.history_id, self.link.value)

    def open(self) -> HistoryList | None:
        """Record the line, then drop the list over it.  None if it cannot.

        With :attr:`choices`, drop those, on the one the line holds.
        """
        app, link = self.application, self.link
        if app is None or link is None or link.inert:
            return None
        if self.choices:
            entries = list(self.choices)
            cursor = entries.index(link.value) if link.value in entries else 0
        elif self.history_id:
            self.record()
            entries = self.store.entries(self.history_id)
            cursor = 1 if len(entries) > 1 else 0
        else:
            return None
        if not entries:
            return None
        x, y, width, height = self._drop_rect()
        window = HistoryList(self)
        window.items = entries
        window.cursor = cursor
        window.type_to_search = bool(self.choices)
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

    def popup_origin(self, width: int, height: int) -> tuple[int, int]:
        """Where a popup *width* by *height* goes, in screen coordinates.

        Under the line, from the column left of it, when it fits on the
        screen; over it when it does not; and pushed in from the screen's
        edges either way.  Not clipped to the dialog, as the history list is:
        a calendar is a fixed size, and cut short it would lose its weeks.
        """
        link = self.link
        lx, ly = link.offset()
        lx, ly = lx + link.x, ly + link.y
        root = self.application.root
        x, y = lx - 1, ly + 1
        if y + height > root.height and ly - height >= 0:
            y = ly - height
        x = max(0, min(x, root.width - width))
        y = max(0, min(y, root.height - height))
        return x, y

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


class HistoryList(ListViewer, DropDown):
    """The dropped list: a framed, modal :class:`ListViewer` of one history.

    Turbo Vision built it from a window, a viewer and a scroll bar; a
    ``ListViewer`` is all three already -- its frame, its rows and a scroll
    bar on its right edge.
    """

    #: Whether a printable key searches the list: on for a button's
    #: ``choices``, off for a history.
    type_to_search: bool = reactive(False)
    #: What has been typed, or None while no search is on.
    search: str | None = reactive(None)

    SEARCH_LABEL = " Search: "

    def __init__(self, button: History, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: The button that dropped this, and the line it fills.
        self.button = button

    # -- the quick search ----------------------------------------------------------

    def _find(self, text: str, start: int) -> int | None:
        """The first row from *start* on, wrapping, whose text *text* begins."""
        pattern = name_pattern(text)
        rows = self.items
        for step in range(len(rows)):
            index = (start + step) % len(rows)
            if pattern.match(self.row_text(index, rows[index])):
                return index
        return None

    def search_for(self, text: str) -> bool:
        """Move to the first row *text* begins, and remember it; False if none.

        A new search looks from the top, a longer one from where the last
        stopped -- so the row it is on still matches if it can.
        """
        current = peek(self, HistoryList.search)
        start = self.cursor if current and text.startswith(current) else 0
        found = self._find(text, start)
        if found is None:
            return False
        self.cursor = found
        self.search = text
        return True

    def footer_text(self) -> str:
        if self.search is None:
            return super().footer_text()
        return f"{self.SEARCH_LABEL}{self.search} "

    def cursor_position(self) -> tuple[int, int] | None:
        """While searching, the caret after what has been typed, on the bottom edge."""
        if self.search is None or not self.framed:
            return None
        x = self.label_x(self.footer_text()) + len(self.SEARCH_LABEL) + len(self.search)
        return min(x, self.width - 2), self.height - 1

    def layout(self, width: int, height: int) -> None:
        """Keep the rectangle the button worked out; a cascade must not refit it."""

    async def choose(self) -> bool:
        """Enter or a double click: the entry goes into the line."""
        text = self.selected
        self.close()
        if text is not None:
            self.button.choose(text)
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("escape"):
            self.close()
            return True
        if self.type_to_search:
            text = self.search or ""
            if event.is_printable and event.char and not event.ctrl and not event.alt:
                self.search_for(text + event.char)
                return True
            if event.matches("backspace") and self.search is not None:
                if len(text) > 1:
                    self.search = text[:-1]
                else:
                    self.search = None
                return True
            self.search = None
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
