"""What the *Character Table* answers: the character taken, or None.

**Typing searches**, wherever the keyboard is: a printable key or Backspace
that the control with the keyboard does not take goes to the search line.
DOS Navigator's chart took a typed character at once instead (``SetData``),
which made sense for 256 of them; among a hundred and forty thousand the
character to be found is the one that cannot be typed.  The search runs on
the name list (:func:`~navigator.lib.utilities.unicode_table.search`) and its
results are the first group of the list, *Search results*, chosen as soon as
they are in.

Enter, Ctrl+B, Ctrl+P, *Insert* or a double click in the grid take the
character under the grid's cursor; Ctrl+C or *Copy* put it on the clipboard
and take nothing.  Either puts it at the front of *Recent*, the list's first
group in every grouping (:class:`~navigator.models.recent_char.RecentChar`).
The line under the list filters its groups by name as it is typed, and the
*X* beside it empties it, as Esc does while the line has the keyboard and
holds something; *Search results* and *Recent* stay whatever it
holds.  The chart reopens on the grouping, group and character last left, as
``ASCIITable`` kept its ``const C``.

The whole code space is read once per process, on a thread
(:func:`~navigator.lib.utilities.unicode_table.build_index`): blocks and
*Recent* are there at once, categories, the Nerd sets and the search as soon
as it is done.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event, KeyEvent
from navkit.glyphs import GLYPHS_NERD, GLYPHS_UNICODE
from navkit.i18n import tr
from navkit.reactive import effect
from navml.background import Background, Outcome
from navml.widgets.dialog.commands import Cancel
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.utilities import unicode_table
from navigator.lib.utilities.unicode_table import Category, Index

#: The groupings, in the radio buttons' order.
BLOCKS, GENERAL, NERD = 0, 1, 2

#: What the chart was last left on: the grouping, the group and the
#: character.  It first opens on ``p`` in Basic Latin, where *ASCII Chart* did.
_last: dict[str, Any] = {"grouping": BLOCKS, "group": "block:Basic Latin", "code": 0x70}

#: The index, once read: one for the Nerd tier and one without.
_indexes: dict[bool, Index] = {}

_background = Background("chartable", workers=1)

RECENT = Category("recent", "", "Recent")
FOUND = Category("found", "", "Search results")


class UnicodeChart(Dialog):
    """*Character Table*: a character, picked, found or copied.  *glyphs* is
    the tier of whatever opened it, the Nerd sets being offered only in the
    Nerd tier."""

    def __init__(self, glyphs: int = GLYPHS_UNICODE, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        # A symbol, not a word: set here because a markup literal is translated.
        self.clear_filter.text = "X"
        self.nerd = glyphs >= GLYPHS_NERD
        groupings = [tr("~B~locks"), tr("~C~ategories")]
        if self.nerd:
            groupings.append(tr("~N~erd Fonts"))
        self.grouping.items = groupings
        self.grouping.value = self.grouping.sel = min(_last["grouping"], len(groupings) - 1)
        #: The groups the list shows, in its order.
        self.categories: list[Category] = []
        #: The ident of the group the grid shows.
        self._shown = ""
        #: The grouping the list was last filled for.
        self._grouped = -1
        #: The search's results, and the query they are for.
        self._found: list[int] | None = None
        self._query = ""
        #: The query whose results the list holds.
        self.searched = ""
        #: The filter the list was last filled for, lower-cased.
        self._filtered = ""
        self._recent = unicode_table.recent()
        self._list(_last["group"])
        group = self._category(_last["group"]) or self.categories[0]
        self._show(group, code=_last["code"])

    @property
    def index(self) -> Index | None:
        return _indexes.get(self.nerd)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.insert_button, self.copy_button, self.abandon)

    def mounted(self) -> None:
        super().mounted()
        effect(self, UnicodeChart._follow_grouping)
        effect(self, UnicodeChart._follow_group)
        effect(self, UnicodeChart._follow_search)
        effect(self, UnicodeChart._follow_filter)
        effect(self, UnicodeChart._describe)
        if self.index is None:
            _background.run(self, unicode_table.build_index, self.nerd, done=self._indexed)

    # -- the groups ----------------------------------------------------------------------

    def _grouped_categories(self) -> list[Category]:
        grouping = self.grouping.value
        if grouping == GENERAL:
            return unicode_table.general_categories()
        if grouping == NERD and self.nerd:
            return unicode_table.nerd_categories()
        return unicode_table.block_categories()

    def _category(self, ident: str) -> Category | None:
        return next((c for c in self.categories if c.ident == ident), None)

    @staticmethod
    def caption(category: Category) -> str:
        """What the list and the grid call *category*.  A block's, a
        category's and a Nerd set's names are the standards' own and are
        not translated."""
        if category.kind == "recent":
            return tr("Recent")
        if category.kind == "found":
            return tr("Search results")
        return category.name

    def _list(self, keep: str) -> None:
        """Fill the list for the grouping chosen and the filter typed, the
        cursor on *keep* if it is there, else on the first group the filter
        let through."""
        self._grouped = self.grouping.value
        self._filtered = self.filter.value.strip().casefold()
        pinned = ([FOUND] if self._found is not None else []) + [RECENT]
        grouped = [c for c in self._grouped_categories() if self._filtered in self.caption(c).casefold()]
        self.categories = pinned + grouped
        self.groups.items = [self.caption(category) for category in self.categories]
        first = len(pinned) if self._filtered and grouped else 0
        self.groups.cursor = next((i for i, c in enumerate(self.categories) if c.ident == keep), first)

    def _codes(self, category: Category) -> list[int] | None:
        if category.kind == "recent":
            return self._recent
        if category.kind == "found":
            return self._found if self._found is not None else []
        return unicode_table.characters(category, self.index)

    def _show(self, category: Category, code: int | None = None) -> None:
        """*category* in the grid, the cursor on *code* if it has it."""
        self._shown = category.ident
        self.grid.caption = self.caption(category)
        codes = self._codes(category)
        if codes is None:
            self.grid.show([])
            self.grid.error = tr("Reading the character names...")
            return
        self.grid.error = None if codes else (
            tr("Nothing taken yet") if category.kind == "recent" else tr("Nothing found"))
        at = codes.index(code) if code is not None and code in codes else 0
        self.grid.show(codes, at)

    def _follow_grouping(self) -> None:
        if self.grouping.value != self._grouped:
            self._list(self._shown)
            self._show(self.categories[self.groups.cursor])

    def _follow_filter(self) -> None:
        if self.filter.value.strip().casefold() != self._filtered:
            self._list(self._shown)
            current = self.categories[self.groups.cursor]
            if current.ident != self._shown:
                self._show(current)

    def _follow_group(self) -> None:
        cursor = self.groups.cursor
        if 0 <= cursor < len(self.categories) and self.categories[cursor].ident != self._shown:
            self._show(self.categories[cursor])

    def _indexed(self, outcome: Outcome) -> None:
        """The index is in: what waited on it, shown."""
        _indexes[self.nerd] = outcome.result()
        current = self._category(self._shown)
        if current is not None and current.kind in ("general", "nerd", "block"):
            self._show(current, self.grid.code)
        if self._query:
            self._search(self._query)

    # -- the search ----------------------------------------------------------------------

    def _follow_search(self) -> None:
        text = self.search.value.strip()
        if text == self._query:
            return
        self._query = text
        if not text:
            self._found = None
            current = self._shown
            self._list(current)
            if current == FOUND.ident:
                self._show(self.categories[self.groups.cursor])
            return
        self._search(text)

    def _search(self, text: str) -> None:
        index = self.index
        if index is None:
            self._found_codes(text, None)
            return
        _background.run(self, unicode_table.search, text, index,
                        done=lambda outcome: self._found_codes(text, outcome.result()))

    def _found_codes(self, text: str, codes: list[int] | None) -> None:
        """The search for *text* has *codes* (None: the index is not in yet)."""
        if text != self._query:
            return  # typed on since
        self.searched = text if codes is not None else ""
        self._found = codes if codes is not None else []
        self._list(FOUND.ident)
        self._show(FOUND)
        if codes is None:
            self.grid.error = tr("Reading the character names...")

    # -- the character -------------------------------------------------------------------

    def _describe(self) -> None:
        code = self.grid.code
        self.info.text = "" if code is None else "\n".join(
            unicode_table.describe(code, self.index.nerd if self.index is not None else None))

    def _keep(self, code: int) -> None:
        """*code* into *Recent*, and where the chart was into ``_last``."""
        unicode_table.remember(code)
        _last.update(grouping=self.grouping.value, code=code,
                     group=self._shown if self._shown != FOUND.ident else RECENT.ident)

    def accept(self) -> str | None:
        code = self.grid.code
        return None if code is None else chr(code)

    def take(self) -> None:
        code = self.grid.code
        if code is None:
            return
        self._keep(code)
        self.record_history()
        self.close(chr(code))

    def copy_out(self) -> None:
        code = self.grid.code
        app = self.application
        if code is None or app is None:
            return
        app.copy_to_clipboard(chr(code))
        self._keep(code)
        self.record_history()
        self.close(None)

    async def on_insert_button_click(self, event: Event) -> bool:
        self.take()
        return True

    async def on_copy_button_click(self, event: Event) -> bool:
        self.copy_out()
        return True

    def clear_filter_line(self) -> None:
        self.filter.value = ""
        self.filter.cursor = 0
        self.filter.focus()

    async def on_clear_filter_click(self, event: Event) -> bool:
        self.clear_filter_line()
        return True

    async def on_cancel(self, event: Cancel) -> bool:
        """Esc in a filter line holding something empties it, and the next one closes."""
        if self.filter.focused and self.filter.value:
            self.clear_filter_line()
            return True
        return await super().on_cancel(event)

    async def on_grid_chosen(self, event: Any) -> bool:
        self.take()
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("ctrl+b") or event.matches("ctrl+p"):
            self.take()
            return True
        if event.matches("ctrl+c") or event.matches("ctrl+insert"):
            self.copy_out()
            return True
        typed = event.is_printable and event.char and not event.ctrl and not event.alt
        if (typed or event.matches("backspace")) and not self.search.focused:
            self.search.focus()
            self.search.anchor = None
            self.search.cursor = len(self.search.value)
            return await self.search.on_key(event)
        return await super().on_key(event)


async def pick_character(app: Any, glyphs: int) -> str | None:
    """The chart for *glyphs*, and the character taken: *ASCII Chart* in the
    ASCII tier, the glyph it shows -- ``│`` for 179, a NUL for 0 -- and this
    chart in any other.  None if nothing was."""
    if glyphs < GLYPHS_UNICODE:
        from navigator.widgets.shell.ascii_chart import AsciiChart
        from navigator.widgets.shell.char_table.char_table import glyph

        code = await AsciiChart().execute(app)
        return None if code is None else "\x00" if code == 0 else glyph(code)
    return await UnicodeChart(glyphs=glyphs).execute(app)
