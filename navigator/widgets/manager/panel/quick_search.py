"""Ctrl+S quick search, and the mouse's left button.

A mixin of :class:`Panel` (``navkit.widget.Mixin``): methods only; its state,
keys and the listing are in ``panel.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from navkit.bidi import display_width
from navkit.events import KeyEvent, MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import peek

from navml.quick_search import name_pattern

from navigator.settings import SETTINGS
from navigator.widgets.manager.commands import ChangeDirectory, ChangeDrive

if TYPE_CHECKING:
    from navigator.widgets.manager.panel.panel import Panel as _Base
else:
    from navkit.widget import Mixin as _Base


class QuickSearching(_Base):
    """Ctrl+S quick search, and the mouse's left button."""

    # -- quick search --------------------------------------------------------

    @property
    def edits_text(self) -> bool:
        """True while searching, so the command line's Enter, Home, End and
        Tab step aside -- Enter ends the search and then chooses the entry
        found, rather than running the line."""
        return self.quick_search is not None

    def start_quick_search(self) -> None:
        """Ctrl+S: start searching, with nothing typed yet."""
        if self.quick_search is None:
            self.quick_search = ""

    def _find(self, text: str, start: int) -> int | None:
        """The first entry from *start* on, wrapping, whose name *text* begins.

        Case folded, and ``*`` and ``?`` are wildcards, as they are in
        Midnight Commander's; everything else is literal.  ``..`` is never
        found: it is not a name anybody searches for.
        """
        pattern = name_pattern(text)
        items = self.items
        for step in range(len(items)):
            index = (start + step) % len(items)
            name = items[index].name
            if name != ".." and pattern.match(name):
                return index
        return None

    def _search_key(self, event: KeyEvent) -> bool:
        """A key while searching: True if the search took it.

        Esc ends the search where it stands.  Any other key that is not the
        search's ends it too and is declined, so it goes on to do what it
        always does -- Enter descends into what was found, Down moves, F3
        views.
        """
        text = self.quick_search or ""
        if event.key in ("insert", "kp_plus", "kp_minus", "kp_multiply") and not (event.ctrl or event.alt):
            # DN's ``GotoKb``: Ins and the Gray keys tag as ever, and the
            # search stays on -- unless the key's box (Gray ±'s *Select*)
            # takes the keyboard, which ends a search as anything does.  The
            # keypad's alone: a bare ``+``, ``-`` or ``*`` is searched, as a
            # name may hold one and some terminals send the Gray keys so.
            return False
        if event.char == "\\" and event.is_printable:
            # ``cmChangeDir`` with the letters typed (DN's ``PutEvent`` replay).
            self.quick_search = None
            self.spawn(self.emit(ChangeDirectory(search=text)))
            return True
        if event.is_printable:
            found = self._find(text + event.char, self.cursor)
            if found is not None:
                self.cursor = found
                self.quick_search = text + event.char
            return True
        if event.matches("backspace"):
            self.quick_search = text[:-1]
            return True
        if event.matches("ctrl+s"):
            if text:
                found = self._find(text, self.cursor + 1)
                if found is not None:
                    self.cursor = found
            return True
        self.quick_search = None
        return event.matches("escape")

    def _end_search_unfocused(self) -> None:
        """The search ends when the keyboard leaves the panel."""
        if not self.focus_within and peek(self, type(self).quick_search) is not None:
            self.quick_search = None

    @property
    def search_label(self) -> str:
        """What the footer says before the typed text while searching."""
        return f" {tr('Search:')} "

    def cursor_position(self) -> tuple[int, int] | None:
        """While searching, the caret after what has been typed, on the footer.

        A departure: DN's caret sat in the cursor row's name, over the letters
        matched (``FLPANEL.PAS``); the footer leaves the name its columns, and
        mc shows its search there."""
        text = self.quick_search
        if text is None or not self.framed:
            return None
        footer = self.footer_text()
        x = self.label_x(footer) + display_width(self.search_label) + display_width(text)
        return min(x, self.width - 2), self.height - 1

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if self._drag is not None and event.action in ("move", "release"):
            return self._dragging(event)
        if event.action == "press" and not event.is_wheel and not self.inert:
            part = self.info_part_at(event.x, event.y)
            if part is not None and self._info_press(event, part):
                return True
        if event.button == "middle" and event.action == "press":
            # The middle button (the wheel pressed) tags as DN's right button
            # did, whatever *Right button* says: with the right one opening
            # the context menu, this is where DN's tagging went.
            return self._right_marking(event)
        if event.button == "right" or self._right_mark is not None:
            if self._right_mark is not None or (
                event.action == "press" and self._right_selects()
            ):
                return self._right_marking(event)
        if event.action == "press" and not event.is_wheel:
            self.quick_search = None
        if (event.action == "press" and event.button == "left" and not event.is_wheel
                and not (event.shift or event.ctrl or event.alt) and not self.inert):
            part = self.title_part_at(event.x, event.y)
            if part is not None:
                # ``TTopView``: this panel's, so it takes the keyboard first.
                self.focus()
                self.spawn(self.emit(ChangeDrive() if part == "drive" else ChangeDirectory()))
                return True
        if (event.action == "press" and event.button == "left" and (event.shift or event.ctrl)
                and not event.is_wheel and not self.inert):
            index = self.index_at(event.x, event.y)
            if index is not None:
                return self._shift_select(index)
        taken = await super().on_mouse_click(event)
        if (not taken and not self.inert and event.action == "press" and event.button == "left"
                and not event.is_wheel):
            key = self.heading_at(event.x, event.y)
            if key is not None and self.sort_by_column(key):
                return True
        if (taken and event.action == "press" and event.button == "left"
                and SETTINGS.file_manager.drag_drop_columns):
            # File Manager Setup's *Drag-and-drop*: the press may be a drag's
            # start, which the first move with the button held decides.
            index = self.index_at(event.x, event.y)
            app = self.application
            if index is not None and app is not None:
                self._drag = {"index": index, "label": None, "entries": None}
                app.capture_mouse(self)
        return taken
