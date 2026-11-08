"""What the Find bar does: the search as it is typed, the count, the arrows and the replacing.

A departure, asked for (IntelliJ IDEA's find bar): DN searched only from its
*Find* and *Replace* dialogs, which F7 and Ctrl+F7 keep.

**Incremental.**  Opening remembers where the search starts -- the start of the
one-line block or the word it is seeded with, else the cursor -- and every
change of the text or a switch looks for the first match from there, round
from the text's start past its end, and shows it as F7 does
(``FileEditor.show_found``).  Nothing found puts the cursor back there.  The
next and previous matches go round the same way; the bar never says *Search
string not found*.

**Every match on screen is lit** while the bar shows: ``FileEditor.highlight_query``
is the search, and ``render`` paints its matches as ``FileEditor::match``.

**The count runs on a thread** (``Background``), over a copy of the lines, at
most ``search.MATCH_LIMIT``: the text may be large and the loop has to keep
painting.  A stale answer -- the text or the search changed meanwhile -- is
dropped by its generation.  Where the cursor is among them is worked out on
the loop from the sorted list.

**What it writes back.**  The text and the three switches go to
:data:`navigator.lib.editor.search.SEARCH`, whole text and forward, so
Shift+F7 and Alt+F7 go on with what the bar last searched for; the new text
does not, the bar's replacing being its own.
"""

from __future__ import annotations

import bisect
from typing import Any

from navkit.capabilities import GLYPHS_UNICODE
from navkit.events import KeyEvent, MouseClickEvent
from navkit.i18n import tr, tr_n
from navkit.reactive import effect, reactive, untracked
from navkit.screen import Surface
from navkit.tooltip import with_keys
from navkit import commands
from navkit.widget import Widget

from navml.background import Background, Outcome

from navigator.lib.editor import search
from navigator.lib.editor.document import Pos
from navigator.lib.editor.search import SearchData
from navigator.widgets.editor.commands import (
    CloseFindBar,
    FindNext,
    FindPrevious,
    ReplaceMatch,
    ReplaceMatches,
    SwitchMatchCase,
    SwitchRegex,
    SwitchWholeWords,
)

#: The count's columns.  The text lines end 28 columns short of the right
#: frame (the markup's ``parent.width - 29``): ``Aa W .*``, the count and the
#: arrows, a blank between each.
COUNT_WIDTH = 11

#: One pool for the counting; a newer count makes an older one's answer stale.
_COUNTER = Background("find-count", workers=1)


class FindBar(Widget):
    """The Find bar, or with :attr:`replace` the Replace bar, over the editor's corner."""

    parts = ("switch", "count", "error", "arrow", "button")

    #: *Replace* has no key of its own -- Enter in the new text is
    #: ``FindNext``'s -- but Key bindings can give it one.
    keyless_commands = (ReplaceMatch,)

    #: *Match case*, *Whole words*, *Regular expression*.
    case: bool = reactive(False)
    whole: bool = reactive(False)
    regex: bool = reactive(False)

    #: Bumped when a count comes in, so the bar paints it.
    counted: int = reactive(0)

    #: Said in the count's place until the next search: *N replaced*.
    notice: str = reactive("")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.visible = False
        #: Where the incremental search starts.
        self._origin = Pos(0, 0)
        #: The last count's matches, and what they were counted for.
        self._matches: list[tuple[int, int, int, int]] | None = None
        self._generation = 0
        #: What a click at a cell does: ``(x, width, y, what)``.
        self._hits: list[tuple[int, int, int, Any]] = []

    def mounted(self) -> None:
        super().mounted()
        effect(self, FindBar._follow_query)
        effect(self, FindBar._count)

    # -- the editor and the search ------------------------------------------------------

    @property
    def editor(self) -> Any:
        return self.parent.editor

    def data(self) -> SearchData:
        """The search the bar sets up now."""
        return SearchData(
            text=self.query.value, new=self.new.value if self.replace else None,
            case=self.case, whole=self.whole, regex=self.regex, prompt=False,
            from_cursor=True,
        )

    def open(self, *, replace: bool) -> None:
        """Show the bar, Find or Replace, seeded and searching from where the cursor is.

        Shown already, the text it holds stays (IDEA's way) unless the editor
        has a one-line block; the keyboard goes to the text either way."""
        editor = self.editor
        word, origin = editor.search_seed()
        was_open = self.visible
        self.replace = replace
        self.visible = True
        if word and (not was_open or editor.has_block):
            self.query.value = word
        elif not was_open and not word:
            self.query.value = self.query.value or search.SEARCH.text
        if not was_open:
            self.case, self.whole, self.regex = search.SEARCH.case, search.SEARCH.whole, search.SEARCH.regex
        self._origin = origin
        entry = self.query.entry
        entry.cursor = len(entry.value)
        entry.select_all()
        entry.focus()
        self._incremental()

    def close(self) -> None:
        """Put the bar away, its matches no longer lit, the keyboard back in the editor."""
        if not self.visible:
            return
        self.query.history.record()
        if self.replace:
            self.new.history.record()
        self.visible = False
        self.notice = ""
        editor = self.editor
        editor.highlight_query = None
        editor.focus()

    def _follow_query(self) -> None:
        """A change of the text or a switch: search again from the origin."""
        if not self.visible:
            return
        self.query.value, self.case, self.whole, self.regex  # noqa: B018 -- what is followed
        with untracked():
            self._incremental()

    def _incremental(self) -> None:
        data = self.data()
        self.notice = ""
        record = search.SEARCH
        record.text, record.case, record.whole, record.regex = data.text, data.case, data.whole, data.regex
        record.new, record.selected, record.backward = None, False, False
        editor = self.editor
        editor.highlight_query = data if data.text else None
        if not search.valid(data):
            editor.place_cursor(self._origin)
            return
        found = self._find(self._origin, data, backward=False)
        if found is None:
            editor.place_cursor(self._origin)
        else:
            editor.show_found(found, backward=False)

    def _find(self, at: Pos, data: SearchData, *, backward: bool) -> tuple[Pos, Pos] | None:
        """The match from *at*, round from the other end of the text when there is none."""
        editor = self.editor
        found = editor.find(at, data, backward=backward)
        if found is None:
            found = editor.find(editor.document.end if backward else Pos(0, 0), data, backward=backward)
        return found

    def step(self, *, backward: bool) -> None:
        """The next match, or the one before: from the match lit, else from the cursor."""
        data = self.data()
        if not search.valid(data):
            return
        self.notice = ""
        editor = self.editor
        shown = editor.found_on_display()
        if shown is not None:
            at = shown[0] if backward else shown[1]
        else:
            at = editor._mark_pos()
        found = self._find(at, data, backward=backward)
        if found is not None:
            # Show it as a forward search does, the cursor after it, so the
            # bar's arrows and Shift+F7 go on from the same place.
            editor.show_found(found, backward=False)

    def replace_one(self) -> None:
        """*Replace*: the match lit replaced and the next one found; with none lit, the
        next one found first, as IDEA does."""
        data = self.data()
        if not search.valid(data):
            return
        editor = self.editor
        shown = editor.found_on_display()
        if shown is None:
            self.step(backward=False)
            return
        end = editor.replace_found(shown, editor.replacement(shown, data))
        found = self._find(end, data, backward=False)
        if found is not None:
            editor.show_found(found, backward=False)

    def replace_every(self) -> None:
        """*All*: every match replaced, one undo step, and how many said where the count was."""
        data = self.data()
        if not search.valid(data):
            return
        made = self.editor.replace_all(data)
        self.notice = tr_n("{n} replaced", "{n} replaced", made)

    # -- the count -------------------------------------------------------------------------

    def _count(self) -> None:
        """Count the matches again whenever the search or the text changes."""
        if not self.visible:
            return
        data = SearchData(text=self.query.value, case=self.case, whole=self.whole, regex=self.regex)
        editor = self.editor
        editor.revision  # noqa: B018 -- followed
        with untracked():
            self._generation += 1
            generation = self._generation
            self._matches = None
            if not search.valid(data):
                self.counted += 1
                return
            lines = list(editor.document.lines)

            def done(outcome: Outcome) -> None:
                if generation != self._generation:
                    return
                try:
                    self._matches = outcome.result()
                except Exception:  # noqa: BLE001 -- a count that failed counts nothing
                    self._matches = []
                self.counted += 1

            _COUNTER.run(self, search.all_matches, lines, data, done=done)

    def count_text(self) -> tuple[str, bool]:
        """What the count's place says, and whether it is said as an error."""
        self.counted  # noqa: B018 -- painted again when a count comes in
        if self.notice:
            return self.notice, False
        data = self.data()
        if not data.text:
            return "", False
        if not search.valid(data):
            return tr("Bad pattern"), True
        matches = self._matches
        if matches is None:
            return "…" if self.glyphs >= GLYPHS_UNICODE else "...", False
        if not matches:
            return tr("No matches"), True
        total = f"{len(matches)}+" if len(matches) >= search.MATCH_LIMIT else str(len(matches))
        editor = self.editor
        editor.line, editor.col, editor.revision  # noqa: B018 -- the cursor moving repaints
        shown = editor.found_on_display()
        if shown is None:
            return f"?/{total}", False
        key = (shown[0].line, shown[0].index, shown[1].line, shown[1].index)
        at = bisect.bisect_left(matches, key)
        if at < len(matches) and matches[at] == key:
            return f"{at + 1}/{total}", False
        return f"?/{total}", False

    # -- painting --------------------------------------------------------------------------

    def _glyph(self, unicode: str, ascii: str) -> str:
        return unicode if self.glyphs >= GLYPHS_UNICODE else ascii

    def render(self, surface: Surface) -> None:
        width, height = self.width, self.height
        if width < 2 or height < 2:
            return
        style = self.style
        surface.draw_box(0, 0, width, height, style, charset=self.box_charset(), fill=" ")
        self._hits = hits = []
        x = 1 + max(4, width - 29)
        switch = self.part_style("switch")
        lit = self.part_style("switch", checked=True)
        for offset, label, on, what in (
            (1, "Aa", self.case, SwitchMatchCase),
            (4, "W", self.whole, SwitchWholeWords),
            (6, ".*", self.regex, SwitchRegex),
        ):
            surface.draw_text(x + offset, 1, label, lit if on else switch)
            hits.append((x + offset, len(label), 1, what))
        text, error = self.count_text()
        look = self.part_style("error") if error else self.part_style("count")
        surface.draw_text(x + 9, 1, text, look, max_width=COUNT_WIDTH)
        arrow = self.part_style("arrow")
        for offset, label, what in (
            (21, self._glyph("↑", "^"), FindPrevious),
            (23, self._glyph("↓", "v"), FindNext),
            (25, self._glyph("×", "x"), CloseFindBar),
        ):
            surface.draw_text(x + offset, 1, label, arrow)
            hits.append((x + offset, 1, 1, what))
        if self.replace and height >= 4:
            button = self.part_style("button")
            for offset, label, what in ((1, tr("Replace"), ReplaceMatch), (10, tr("All"), ReplaceMatches)):
                used = surface.draw_text(x + offset, 2, label, button, max_width=max(0, width - 1 - x - offset))
                hits.append((x + offset, used, 2, what))

    def _hit(self, x: int, y: int) -> Any:
        for left, size, row, what in self._hits:
            if row == y and left <= x < left + size:
                return what
        return None

    # -- input -----------------------------------------------------------------------------

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.button != "left" or event.is_wheel:
            return True
        if event.action == "press":
            what = self._hit(event.x, event.y)
            if what is not None and self.application is not None:
                await commands.run(self.application, what, self.query.entry)
        # A press anywhere on the bar is the bar's, so none reaches the text beneath.
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        """Tab and Shift+Tab between the text to find and the new text."""
        if self.replace and event.matches("tab", "shift+tab"):
            entry = self.new.entry if self.query.entry.focused else self.query.entry
            entry.focus()
            return True
        return False

    def tooltip_at(self, x: int, y: int) -> str:
        what = self._hit(x, y)
        if what is None:
            return super().tooltip_at(x, y)
        names = {
            SwitchMatchCase: tr("Match case"),
            SwitchWholeWords: tr("Whole words"),
            SwitchRegex: tr("Regular expression"),
            FindPrevious: tr("Previous match"),
            FindNext: tr("Next match"),
            CloseFindBar: tr("Close"),
            ReplaceMatch: tr("Replace the match found"),
            ReplaceMatches: tr("Replace every match"),
        }
        app = self.application
        key = commands.key_for(app, what, self.query.entry) if app is not None else None
        return with_keys(names[what], commands.key_label(key) if key else "")

    # -- the commands ----------------------------------------------------------------------

    async def on_find_next(self, command: FindNext) -> bool:
        # Enter in the new text replaces, as IDEA's does.
        if self.replace and self.new.entry.focused:
            self.replace_one()
        else:
            self.step(backward=False)
        return True

    async def on_find_previous(self, command: FindPrevious) -> bool:
        self.step(backward=True)
        return True

    async def on_switch_match_case(self, command: SwitchMatchCase) -> bool:
        self.case = not self.case
        return True

    async def on_switch_whole_words(self, command: SwitchWholeWords) -> bool:
        self.whole = not self.whole
        return True

    async def on_switch_regex(self, command: SwitchRegex) -> bool:
        self.regex = not self.regex
        return True

    async def on_replace_match(self, command: ReplaceMatch) -> bool:
        if not self.replace:
            return False
        self.replace_one()
        return True

    async def on_replace_matches(self, command: ReplaceMatches) -> bool:
        if not self.replace:
            return False
        self.replace_every()
        return True

    def checks(self, command: Any) -> bool | None:
        if isinstance(command, SwitchMatchCase):
            return self.case
        if isinstance(command, SwitchWholeWords):
            return self.whole
        if isinstance(command, SwitchRegex):
            return self.regex
        return super().checks(command)
