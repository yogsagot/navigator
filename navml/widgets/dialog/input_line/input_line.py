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
A mouse drag sets both the same way, holding the mouse while it lasts, and a
double click selects the word under it.

**Right-to-left text moves as it is painted.**  Left and Right go to the
neighbouring caret place on screen (Ctrl to the nearest word start that way),
as the editor's do, and a selection is what is painted between its two ends
(:meth:`picked`) -- in mixed Hebrew and Latin that can be two stretches of
the text, which a copy joins in reading order and a deletion takes both of.
A line with nothing right-to-left in it keeps the plain index arithmetic.

**The clipboard is Turbo Vision's keys and the terminal's.**  Ctrl+Ins copies
the selection -- or the whole line, which is what DOS Navigator's command line
copied, having no selection -- Shift+Del cuts and Shift+Ins pastes; Ctrl+C
copies while something is selected, and Ctrl+V pastes.  A paste the line asks
for arrives later as a :class:`~navkit.events.PasteEvent`, as one the terminal
makes itself does, and both land in :meth:`on_paste`.  A finished drag is also
the primary selection, and a middle click pastes it, as in a terminal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from navkit.bidi import caret_column, has_rtl, index_at
from navkit.commands import Command
from navkit.events import (
    ContextMenuEvent,
    DoubleClickEvent,
    KeyEvent,
    MouseClickEvent,
    PasteEvent,
)
from navkit.glyphs import DEFAULT_SCROLLBAR, SCROLLBARS, scrollbar
from navkit.i18n import tr
from navkit.reactive import effect, peek, reactive
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.terminal import CURSOR_SHAPES

from navml.widgets.dialog.commands import (
    Clear,
    ClipboardCopy,
    ClipboardCut,
    ClipboardPaste,
    SelectAll,
)
from navml.widgets.dialog.control import Control
from navml.widgets.menu.commands import ShowContextMenu

if TYPE_CHECKING:
    from navml.widgets.menu.context_menu.context_menu import ContextMenu


class InputLine(Control):
    """One line of editable text, with a caret."""

    #: The :class:`~navml.widgets.dialog.history.History` button beside this
    #: line, or None.  Set by the button, which names the line it serves; the
    #: line only needs it for Down, which arrives here because the line holds
    #: the keyboard and the button is not on the way up from it.
    history: Any = None

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

    #: A left button is down and dragging out a selection.
    _dragging = False
    #: Whether the value was last painted on a mirrored surface, which is
    #: what the caret's and a click's columns are counted against.
    _painted_rtl = False

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
    def text_origin(self) -> int:
        """The column ``value[first]`` is painted in: past the left arrow."""
        return 1

    def _index_at(self, x: int) -> int:
        """The index in ``value`` a click at column *x* lands on."""
        shown = self._shown()
        if not self._painted_rtl and not has_rtl(shown):
            return min(max(self.first + x - self.text_origin, 0), len(self.value))
        return self.first + index_at(shown, x - self.text_origin, self._painted_rtl)

    def _shown(self) -> str:
        """What of the value fits, from ``first`` on: what is painted."""
        value = "*" * len(self.value) if self.password else self.value
        return value[self.first : self.first + self.room]

    def _bidi(self) -> bool:
        """Whether the value is laid out other than as typed: right-to-left
        letters in it, or a mirrored screen under it."""
        return self._painted_rtl or (not self.password and has_rtl(self.value))

    @property
    def selected_text(self) -> str:
        return "".join(self.value[index] for index in self.picked())

    @property
    def selection(self) -> tuple[int, int]:
        """The selected run as ``(start, stop)``, empty when there is none --
        from the first character selected to the last, which right-to-left
        text can paint as two stretches (:meth:`picked`)."""
        if self.anchor is None or self.anchor == self.cursor:
            return self.cursor, self.cursor
        picked = self.picked()
        if not picked:
            return self.cursor, self.cursor
        return picked[0], picked[-1] + 1

    def picked(self) -> list[int]:
        """The indices selected, in the text's order: those painted between the
        anchor's caret and the cursor's -- the run between them, unless the
        value is laid out other than as typed."""
        anchor, cursor = self.anchor, self.cursor
        if anchor is None or anchor == cursor:
            return []
        if not self._bidi() or (anchor, cursor) == (0, len(self.value)) or (cursor, anchor) == (0, len(self.value)):
            return list(range(min(anchor, cursor), max(anchor, cursor)))
        value, rtl = self.value, self._painted_rtl
        low, high = sorted((caret_column(value, anchor, rtl), caret_column(value, cursor, rtl)))
        return [index for index in range(len(value))
                if low <= _cell_of(value, index, rtl) < high]

    def select_all(self) -> None:
        self.anchor, self.cursor = 0, len(self.value)

    def _replace_selection(self, text: str) -> None:
        picked = self.picked() if self.anchor is not None else []
        start = picked[0] if picked else self.cursor
        gone = set(picked)
        kept = "".join(char for index, char in enumerate(self.value) if index not in gone)
        value = kept[:start] + text + kept[start:]
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

    def _step(self, rightwards: bool) -> int:
        """The caret place next to the cursor's on screen, rightwards or not.

        Past what is painted, the end of the text lying that way: the line
        scrolls on as it always did.
        """
        if not self._bidi():
            return self.cursor + (1 if rightwards else -1)
        shown, rtl, first = self._shown(), self._painted_rtl, self.first
        here = caret_column(shown, self.cursor - first, rtl)
        places = [(caret_column(shown, index, rtl), first + index)
                  for index in range(len(shown) + 1) if first + index != self.cursor]
        return self._nearest(here, places, rightwards, shown)

    def _word_step(self, rightwards: bool) -> int:
        """Ctrl+Left/Right on laid-out text: the nearest word start on screen
        that way -- each word's first letter in the text, and the end."""
        if not self._bidi():
            return self._word_right() if rightwards else self._word_left()
        shown, rtl, first = self._shown(), self._painted_rtl, self.first
        here = caret_column(shown, self.cursor - first, rtl)
        starts = [index for index in range(len(shown) + 1)
                  if index == len(shown)
                  or (not shown[index].isspace() and (index == 0 or shown[index - 1].isspace()))]
        places = [(caret_column(shown, index, rtl), first + index)
                  for index in starts if first + index != self.cursor]
        return self._nearest(here, places, rightwards, shown)

    def _nearest(self, here: int, places: list[tuple[int, int]], rightwards: bool, shown: str) -> int:
        ahead = [(abs(column - here), index) for column, index in places
                 if (column > here if rightwards else column < here)]
        if ahead:
            return min(ahead)[1]
        rtl = self._painted_rtl
        start, end = caret_column(shown, 0, rtl), caret_column(shown, len(shown), rtl)
        towards_end = (end >= start) == rightwards
        return self.cursor + (1 if towards_end else -1)

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
        if self.inert:
            return False
        shift = event.shift
        if event.matches("ctrl+insert"):
            self.copy(self.selected_text or self.value)
        elif event.matches("ctrl+c"):
            if not self.selected_text:
                return False
            self.copy(self.selected_text)
        elif event.matches("shift+delete"):
            if not self.selected_text:
                return False
            self.cut()
        elif event.matches("shift+insert", "ctrl+v"):
            self.request_paste()
        elif event.is_printable and event.char:
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
        elif event.key in ("left", "right"):
            rightwards = event.key == "right"
            self._move(self._word_step(rightwards) if event.ctrl else self._step(rightwards), shift)
        elif event.key == "home":
            self._move(0, shift)
        elif event.key == "end":
            self._move(len(self.value), shift)
        elif (
            event.matches("down", "alt+down") and self.history is not None
            and self.history.open() is not None
        ):
            # Turbo Vision's THistory took Down from its focused line -- when
            # it had a list to drop.  A ``Field`` with no ``history_id`` still
            # links its (hidden) button, and Down there is the dialog's.
            # Alt+Down too, the drop-down key most toolkits since have used.
            pass
        else:
            # Enter and Escape are *not* claimed: they belong to the dialog,
            # and a field that swallowed them would make every dialog holding
            # one impossible to accept or dismiss from the keyboard.
            return False
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        return self.pointer(event)

    def pointer(self, event: MouseClickEvent) -> bool:
        """A press, a drag or a release on the text: the caret and the selection.

        Public so that a line which paints something before its text -- the
        command line's prompt -- and handles its own presses can hand the
        rest here, having said where its text starts in :attr:`text_origin`.
        """
        if self.inert:
            return False
        if event.button == "middle" and event.action == "press":
            self.request_paste(primary=True)
            return True
        if event.button != "left":
            return False
        app = self.application
        if event.action == "press":
            self._move(self._index_at(event.x), event.shift)
            if self.anchor is None:
                self.anchor = self.cursor
            self._dragging = True
            if app is not None:
                app.capture_mouse(self)
        elif event.action == "move" and self._dragging:
            self.cursor = self._index_at(event.x)
        elif event.action == "release" and self._dragging:
            self._dragging = False
            if self.selected_text and app is not None and not self.password:
                app.copy_to_clipboard(self.selected_text, primary=True)
        else:
            return False
        return True

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        """The word under the pointer, selected -- and so the primary selection."""
        if self.inert or event.button != "left":
            return False
        index = self._index_at(event.x)
        value = self.value
        if index < len(value) and value[index].isspace():
            return True
        start = index
        while start and not value[start - 1].isspace():
            start -= 1
        stop = index
        while stop < len(value) and not value[stop].isspace():
            stop += 1
        self.anchor, self.cursor = start, stop
        self._dragging = False
        app = self.application
        if self.selected_text and app is not None and not self.password:
            app.copy_to_clipboard(self.selected_text, primary=True)
        return True

    # -- the clipboard -------------------------------------------------------

    def cut(self) -> None:
        """The selection to the clipboard, and out of the text."""
        self.copy(self.selected_text)
        self._replace_selection("")

    def copy(self, text: str) -> None:
        app = self.application
        if text and app is not None and not self.password:
            app.copy_to_clipboard(text)

    def request_paste(self, *, primary: bool = False) -> None:
        """Ask for the clipboard; it comes back through :meth:`on_paste`."""
        app = self.application
        if app is not None:
            app.request_clipboard(primary=primary)

    async def on_paste(self, event: PasteEvent) -> bool:
        """Pasted text, typed at the caret: one line, so line breaks become spaces."""
        if self.inert:
            return False
        text = " ".join(event.text.splitlines())
        if text:
            self._replace_selection(text)
        return True

    # -- commands: the clipboard's, which the context menu offers ----------------
    #
    # The keys above stay in ``on_key``: an input line has no key table, so
    # they do not appear in ``keybindings.ini``.  The commands are what the
    # context menu runs, and what a dialog's own menu could.

    def refusal(self, command: Command) -> str:
        if isinstance(command, (ClipboardCut, ClipboardPaste, Clear)) and self.inert:
            return tr("The line cannot be changed now")
        if isinstance(command, (ClipboardCut, Clear)):
            return "" if self.selected_text else tr("Nothing is selected")
        if isinstance(command, ClipboardCopy):
            # Ctrl+Ins copies the whole line when nothing is selected.
            return "" if self.selected_text or self.value else tr("The line is empty")
        if isinstance(command, SelectAll):
            if not self.value:
                return tr("The line is empty")
            return "" if self.selection != (0, len(self.value)) else tr("All of it is selected")
        return super().refusal(command)

    async def on_clipboard_cut(self, command: ClipboardCut) -> bool:
        self.cut()
        return True

    async def on_clipboard_copy(self, command: ClipboardCopy) -> bool:
        self.copy(self.selected_text or self.value)
        return True

    async def on_clipboard_paste(self, command: ClipboardPaste) -> bool:
        self.request_paste()
        return True

    async def on_clear(self, command: Clear) -> bool:
        self._replace_selection("")
        return True

    async def on_select_all(self, command: SelectAll) -> bool:
        self.select_all()
        return True

    # -- the context menu ---------------------------------------------------------
    #
    # ``ContextMenuHost``'s hooks and handlers, written out: a component's
    # hand-written half has one base, its markup's, so the mixin cannot be
    # listed beside ``Control``.  The menu's module is imported when a menu
    # is asked for, so that importing a field does not load the menu group's
    # components (``test_importing_one_component_does_not_load_the_library``).

    def context_menu(self) -> ContextMenu | None:
        """Cut, Copy, Paste, Clear and Select all, built each time it opens.

        Built rather than kept: there is one input line in every field of
        every dialog, and the captions follow a change of language.
        """
        from navml.widgets.menu.context_menu.context_menu import ContextMenu

        if self.inert:
            return None
        menu = ContextMenu()
        menu.add_item(tr("Cu~t~"), ClipboardCut, "Shift-Del")
        menu.add_item(tr("~C~opy"), ClipboardCopy, "Ctrl-Ins")
        menu.add_item(tr("~P~aste"), ClipboardPaste, "Shift-Ins")
        menu.add_item(tr("C~l~ear"), Clear)
        menu.add_line()
        menu.add_item(tr("Select ~a~ll"), SelectAll)
        return menu

    def prepare_context(self, x: int, y: int) -> None:
        """A click outside the selection moves the caret there and drops it,
        as a left click would; one inside keeps it for Cut and Copy."""
        start, stop = self.selection
        index = self._index_at(x)
        if not start <= index < stop:
            self._move(index, False)

    def context_point(self) -> tuple[int, int]:
        from navml.widgets.menu.context_menu.context_menu import default_point

        return default_point(self)

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        from navml.widgets.menu.context_menu.context_menu import open_on_click

        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        from navml.widgets.menu.context_menu.context_menu import open_on_key

        return open_on_key(self)

    async def activate(self, letter: str = "") -> bool:
        """A shortcut aimed at a field means "type here", and selects it all."""
        taken = self.focus()
        if taken:
            self.select_all()
        return taken

    def tooltip_at(self, x: int, y: int) -> str:
        """What the line is for, and the whole text while it is cut.

        What it is for is its own ``tooltip``, else its parent's: a field's
        label and line are its two halves (``Field``, ``MaskedField``), and a
        page says what the field sets on the field.  The whole text follows
        on a line of its own while ``◄`` or ``►`` says some is out of sight --
        never a password's.  A departure: ``TInputLine`` had no tooltip.
        """
        own = self.tooltip or getattr(self.parent, "tooltip", "")
        cut = not self.password and len(self.value) > self.room
        if own and cut:
            return f"{own}\n{self.value}"
        return own or (self.value if cut else "")

    def cursor_position(self) -> tuple[int, int] | None:
        """Where the terminal's own cursor belongs, in this widget: beside the
        character it is before, wherever right-to-left ordering painted that."""
        return self.caret_column(), 0

    def caret_column(self) -> int:
        """The column the caret is painted in (:func:`navkit.bidi.caret_column`)."""
        shown = self._shown()
        if not self._painted_rtl and not has_rtl(shown):
            return self.text_origin + self.cursor - self.first
        return self.text_origin + caret_column(shown, self.cursor - self.first, self._painted_rtl)

    # -- painting ------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        if self.width < 1 or self.height < 1:
            return
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        room = self.room
        if room < 1:
            return
        self.paint_value(surface, self.text_origin, room)
        self._render_arrows(surface, room)

    def paint_value(self, surface: Surface, x: int, room: int) -> None:
        """What of the value fits, at *x*, the selection in its own colour.

        One :meth:`~navkit.screen.Surface.draw_runs` call, so right-to-left
        text in it is ordered as a whole and the selection follows the
        characters it holds wherever they land.
        """
        self._painted_rtl = surface.rtl
        shown = self._shown()
        style, selected = self.style, self.part_style("selection")
        picked = {index - self.first for index in self.picked()}
        runs: list[tuple[str, Any]] = []
        for index, char in enumerate(shown):
            look = selected if index in picked else style
            if runs and runs[-1][1] is look:
                runs[-1] = (runs[-1][0] + char, look)
            else:
                runs.append((char, look))
        surface.draw_runs(x, 0, runs, room)

    def _render_arrows(self, surface: Surface, room: int) -> None:
        """``◄`` and ``►`` where the value runs off either edge."""
        chars = scrollbar(self.chars, self.glyphs)
        arrow = self.part_style("arrow")
        if self.first:
            surface.draw_text(0, 0, chars[2], arrow)
        if self.first + room < len(self.value):
            surface.draw_text(self.width - 1, 0, chars[3], arrow)


def _cell_of(text: str, index: int, rtl: bool) -> int:
    """The column ``text[index]`` is painted in, from where *text* starts --
    where a caret before it sits, as in the editor, whose selection between
    two carets is the same cells from one up to the other."""
    return caret_column(text, index, rtl)
