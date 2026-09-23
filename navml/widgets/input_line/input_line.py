"""The editing and the painting behind ``input_line.nml``.

Three things here are worth knowing before changing any of them.

**The caret is the terminal's own.**  ``cursor_position()`` answers in the
widget's own coordinates and navkit places the real cursor there at the end of
each frame, for whichever widget the keys are going to -- so a caret is never
shown on a line that cannot receive what is typed, and no reversed cell has to
stand in for one.

**The scroll follows the cursor from an effect, and the effect lives in
``mounted()``.**  ``remove()`` disposes a subtree's effects, so a widget that
can be taken out and put back -- which every widget in a dialog can -- declares
them where they will be declared again.  The effect reads ``first`` with
:func:`~navkit.reactive.peek` because it is the thing that assigns it; the
same shape ``Panel._follow_cursor`` has, and for the same reason.

**Selection is an anchor and a cursor**, not a pair of ordered bounds.  The
anchor is where the selection started and may be to the right of the cursor,
which is what makes shift-left and shift-right symmetrical without a branch.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import DEFAULT_SCROLLBAR, SCROLLBARS, scrollbar
from navkit.reactive import effect, peek, reactive
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.terminal import CURSOR_SHAPES

from navml.widgets.control import Control


class InputLine(Control):
    """One line of editable text, with a caret."""

    #: Where the caret is, as an index into ``value``.
    cursor: int = reactive(0)

    #: The first character shown, which is how a long value scrolls.
    first: int = reactive(0)

    #: Where the selection started, or ``None``.  May be either side of
    #: ``cursor``: an anchor is a place, not a bound.
    anchor: int | None = reactive(None)

    #: A bar, because this is a text field and that is what a text field's
    #: caret looks like.  Re-declared with the vocabulary ``Widget`` already
    #: registered and a different default, which navkit permits -- the
    #: registry holds the type and the words, not the default.
    caret = StyleProperty("bar", values=tuple(CURSOR_SHAPES))

    #: Which characters the scroll arrows are drawn from.
    chars = StyleProperty(DEFAULT_SCROLLBAR, values=tuple(SCROLLBARS))

    #: ``[52] Input arrow`` and the selected run.
    parts = ("arrow", "selection")

    def mounted(self) -> None:
        super().mounted()
        effect(self, InputLine._follow_cursor)

    # -- the model -----------------------------------------------------------

    @property
    def room(self) -> int:
        """Columns available for text: the width, less one either side."""
        return max(0, self.width - 2)

    def _follow_cursor(self) -> None:
        """Scroll just far enough to keep the caret visible."""
        cursor, room = self.cursor, self.room
        first = peek(self, InputLine.first)
        if cursor < first:
            self.first = cursor
        elif room and cursor >= first + room:
            self.first = cursor - room + 1
        elif first and cursor <= first:
            self.first = max(0, cursor)

    @property
    def selection(self) -> tuple[int, int]:
        """The selected run as ``(start, stop)``, empty when there is none."""
        if self.anchor is None or self.anchor == self.cursor:
            return self.cursor, self.cursor
        return min(self.anchor, self.cursor), max(self.anchor, self.cursor)

    def select_all(self) -> None:
        self.anchor, self.cursor = 0, len(self.value)

    def _replace_selection(self, text: str) -> None:
        start, stop = self.selection
        value = self.value[:start] + text + self.value[stop:]
        if self.max_length and len(value) > self.max_length:
            return
        self.value = value
        self.cursor = start + len(text)
        self.anchor = None

    def _move(self, where: int, extend: bool) -> None:
        where = min(max(where, 0), len(self.value))
        if extend and self.anchor is None:
            self.anchor = self.cursor
        elif not extend:
            self.anchor = None
        self.cursor = where

    def _word_left(self) -> int:
        index = self.cursor
        while index and self.value[index - 1].isspace():
            index -= 1
        while index and not self.value[index - 1].isspace():
            index -= 1
        return index

    def _word_right(self) -> int:
        index, end = self.cursor, len(self.value)
        while index < end and not self.value[index].isspace():
            index += 1
        while index < end and self.value[index].isspace():
            index += 1
        return index

    # -- input ---------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.disabled:
            return False
        shift = event.shift
        if event.is_printable and event.char:
            self._replace_selection(event.char)
        elif event.matches("backspace"):
            start, stop = self.selection
            if start != stop:
                self._replace_selection("")
            elif self.cursor:
                self.value = self.value[: self.cursor - 1] + self.value[self.cursor :]
                self.cursor -= 1
        elif event.matches("delete"):
            start, stop = self.selection
            if start != stop:
                self._replace_selection("")
            elif self.cursor < len(self.value):
                self.value = self.value[: self.cursor] + self.value[self.cursor + 1 :]
        elif event.key == "left":
            self._move(self._word_left() if event.ctrl else self.cursor - 1, shift)
        elif event.key == "right":
            self._move(self._word_right() if event.ctrl else self.cursor + 1, shift)
        elif event.key == "home":
            self._move(0, shift)
        elif event.key == "end":
            self._move(len(self.value), shift)
        else:
            # Enter and Escape are *not* claimed: they belong to the dialog,
            # and a field that swallowed them would make every dialog holding
            # one impossible to accept or dismiss from the keyboard.
            return False
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.action != "press" or event.button != "left" or self.disabled:
            return False
        self._move(self.first + max(0, event.x - 1), event.shift)
        return True

    async def activate(self, letter: str = "") -> bool:
        """A shortcut aimed at a field means "type here", and selects it all."""
        taken = self.focus()
        if taken:
            self.select_all()
        return taken

    def cursor_position(self) -> tuple[int, int] | None:
        """Where the terminal's own cursor belongs, in this widget."""
        return 1 + self.cursor - self.first, 0

    # -- painting ------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        if self.width < 1 or self.height < 1:
            return
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        room = self.room
        if room < 1:
            return
        shown = self.value[self.first : self.first + room]
        surface.draw_text(1, 0, shown, style, room)

        start, stop = self.selection
        if start != stop:
            run = self.value[max(start, self.first) : min(stop, self.first + room)]
            if run:
                surface.draw_text(
                    1 + max(0, start - self.first), 0, run,
                    self.part_style("selection"), room,
                )
        self._render_arrows(surface, room)

    def _render_arrows(self, surface: Surface, room: int) -> None:
        """``◄`` and ``►`` where the value runs off either edge."""
        chars = scrollbar(self.chars, self.glyphs)
        arrow = self.part_style("arrow")
        if self.first:
            surface.draw_text(0, 0, chars[2], arrow)
        if self.first + room < len(self.value):
            surface.draw_text(self.width - 1, 0, chars[3], arrow)
