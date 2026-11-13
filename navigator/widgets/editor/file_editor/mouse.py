"""The mouse and the context menu: placing the cursor, marking by dragging, double clicks,
the right button.

A mixin of :class:`FileEditor` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``file_editor.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from navkit.events import ContextMenuEvent, DoubleClickEvent, MouseClickEvent
from navkit.i18n import tr

from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click

from navigator.widgets.editor.commands import (
    Replace,
    StartSearch,
    GotoLineNumber,
    CapitalizeBlock,
    IndentBlock,
    LowcaseBlock,
    UnindentBlock,
    UpcaseBlock,
    Clear,
    ClipboardCopy,
    ClipboardCut,
    ClipboardPaste,
    SaveText,
    SelectAll,
    DeleteLine,
    DeleteWordLeft,
    Undo,
    Redo,
)
from navigator.lib.editor import columns
from navigator.lib.editor.document import Pos
from navigator.lib.editor.search import BREAK_CHARS
from navigator.widgets.editor.file_editor.helpers import WHEEL_ROWS

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navigator.widgets.editor.file_editor.file_editor_surface import FileEditor as _Base
else:
    from navkit.widget import Mixin as _Base


class Mouse(_Base):
    """The mouse and the context menu: placing the cursor, marking by dragging, double clicks,"""

    # -- the context menu ----------------------------------------------------------

    def context_menu(self) -> ContextMenu:
        """The Editor menu's first group, the block's most used, and Save.

        Built each time it opens, so its captions follow the language.  Each
        key is read off the key tables, so a rebinding shows here too.
        """
        menu = ContextMenu()
        menu.add_item(tr("~U~ndo"), Undo)
        menu.add_item(tr("R~e~do"), Redo)
        menu.add_line()
        menu.add_item(tr("Cu~t~"), ClipboardCut)
        menu.add_item(tr("~C~opy"), ClipboardCopy)
        menu.add_item(tr("~P~aste"), ClipboardPaste)
        menu.add_item(tr("C~l~ear"), Clear)
        menu.add_item(tr("~D~elete line"), DeleteLine)
        menu.add_item(tr("Delete ~w~ord left"), DeleteWordLeft)
        menu.add_item(tr("Select ~a~ll"), SelectAll)
        menu.add_line()
        menu.add_item(tr("~F~ind..."), StartSearch)
        menu.add_item(tr("~R~eplace..."), Replace)
        menu.add_item(tr("~G~o to line..."), GotoLineNumber)
        menu.add_line()
        menu.add_item(tr("~I~ndent block"), IndentBlock)
        menu.add_item(tr("U~n~indent block"), UnindentBlock)
        case = menu.add_submenu(tr("Change ca~s~e"))
        case.add_item(tr("~U~pper case"), UpcaseBlock)
        case.add_item(tr("~L~ower case"), LowcaseBlock)
        case.add_item(tr("~C~apitalize"), CapitalizeBlock)
        menu.add_line()
        menu.add_item(tr("Sa~v~e"), SaveText)
        return menu

    def prepare_context(self, x: int, y: int) -> None:
        """A right click outside the block puts the cursor there and drops
        the block, as a left click does; one inside keeps both, so Cut and
        Copy act on what was clicked."""
        line, col = self.cell_at(x, y)
        picked = self._block_picked(line)
        if picked is not None:
            row = columns.cells(self.document.lines[line], self.tab_size)
            if col < len(row) and row[col][1] in picked[0]:
                return
        else:
            span = self._block_columns(line)
            if span is not None and span[0] <= col < span[1]:
                return
        self._moved()
        self._unmark()
        self._move_to(line, col)

    # -- the mouse -----------------------------------------------------------------

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.is_wheel:
            if event.button in ("wheel_up", "wheel_down"):
                step = -WHEEL_ROWS if event.button == "wheel_up" else WHEEL_ROWS
                self._scroll_view(step)
                return True
            return False
        app = self.application
        if event.button == "middle" and event.action == "press":
            # The primary selection, as the console and the input lines paste it
            # -- an addition: DN's buttons other than the left showed the ruler.
            if app is not None:
                app.request_clipboard(primary=True)
            return True
        if event.button == "right" or self._right_press is not None:
            if self._right_button(event):
                return True
        if event.button == "right":
            return False
        if event.button != "left":
            return False
        if event.action == "press":
            self.focus()
            self._moved()
            before = self._here()
            # Shift+click extends the block -- an addition: DN's press always
            # began afresh (BlockOff).  Ctrl+click is Shift+click too, for
            # terminals that keep Shift+click for their own selection (VTE's:
            # xfce4-terminal), as in panels -- unless the pointer then moves:
            # a Ctrl+drag marks whole lines, DN's LineMarking (MICROED.PAS:3233).
            # Not under Vertical blocks, where a rectangle has no whole lines.
            extend = event.shift or event.ctrl
            self._point(event, extending=extend)
            here = self._here()
            self._line_from = self.line if event.ctrl and not event.shift and not self.vertical_blocks else None
            if extend:
                # Shift+click: the block's far end stays, as Shift+movement keeps it.
                self._extend_block(before)
                ends = self._block_ends()
                self._drag_from = here if ends is None else (ends[0] if here == ends[1] else ends[1])
            else:
                self._unmark()
                self._drag_from = here
            self._drag_word = None
            self._press_cell = (event.x, event.y)
            if app is not None:
                app.capture_mouse(self)
        elif event.action == "move" and self._drag_from is not None:
            if self._press_cell == (event.x, event.y):
                return True
            self._press_cell = None
            # Past the top or bottom row the text scrolls a line at a time.
            if event.y < 0:
                self._scroll_view(-1)
            elif event.y >= self.height:
                self._scroll_view(1)
            self._point(event, extending=True)
            if self._line_from is not None:
                self._mark_lines(self._line_from, self.line)
            elif self._drag_word is not None:
                self._mark_words_to()
            else:
                self._mark_to(self._drag_from)
        elif event.action == "release" and self._drag_from is not None:
            self._drag_from = None
            self._line_from = None
            self._drag_word = None
            self._copy_primary()
        else:
            return False
        return True

    def _right_button(self, event: MouseClickEvent) -> bool:
        """The right button: a click is the context menu, a drag DN's column ruler.

        ``MICROED.PAS``'s right press put the cursor at the pointer and set
        ``RulerVisible``; while it was held the cursor followed the pointer,
        scrolling past the edges, and the release took the ruler away.  Here
        the press takes the mouse -- so navkit offers no menu for it -- and
        waits: the first move to another cell shows the ruler and moves the
        cursor, and a release that never moved opens the context menu, as a
        press would have.  Departures (asked for): the menu opens on the
        release, the ruler on the first move, so a click never flashes it;
        and the block is kept, where DN's ``BlockOff`` hid it -- a glance at
        a column should not cost a marked block.
        """
        app = self.application
        if event.action == "press":
            if event.button != "right":
                self._end_ruler()  # a release lost: what was left is let go
                return False
            self.focus()
            self._right_press = event
            if app is not None:
                app.capture_mouse(self)
            return True
        press = self._right_press
        if press is None:
            return False
        if event.action == "move":
            if not self.ruler and (event.x, event.y) == (press.x, press.y):
                return True
            self.ruler = True
            self._moved()
            # Past the top or bottom row the text scrolls a line at a time.
            if event.y < 0:
                self._scroll_view(-1)
            elif event.y >= self.height:
                self._scroll_view(1)
            self._point(event, extending=False)
            return True
        if event.action == "release":
            dragged = self.ruler
            self._end_ruler()
            if not dragged:
                open_on_click(self, ContextMenuEvent.of(press))
            return True
        return True

    def _end_ruler(self) -> None:
        self._right_press = None
        self.ruler = False

    def unmounting(self) -> None:
        self._end_ruler()
        super().unmounting()

    def _point(self, event: MouseClickEvent, extending: bool = False) -> None:
        """The cursor to the cell under *event*, held inside the text's rows."""
        y = min(max(event.y, 0), max(0, self.height - 1))
        self._extending = extending
        try:
            self._move_to(*self.cell_at(event.x, y))
        finally:
            self._extending = False

    def _mark_to(self, anchor: Any) -> None:
        self._set_block(anchor, self._here())

    def _mark_lines(self, first: int, last: int) -> None:
        """A Ctrl+drag: lines *first* to *last*, either way round, whole -- the
        break after the last included, as ``LineMarking``'s release rounded it."""
        top, bottom = min(first, last), max(first, last)
        if bottom + 1 < len(self.document):
            self._set_block(Pos(top, 0), Pos(bottom + 1, 0))
        else:
            self._set_block(Pos(top, 0), Pos(bottom, len(self._text(bottom))))

    def _copy_primary(self) -> None:
        """A block marked by the mouse is the primary selection, as a drag elsewhere is."""
        self._copy_block(primary=True)

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        """The word under the pointer, marked: the run between two ``BREAK_CHARS``.

        The button is still down and the mouse still captured from the press,
        so a drag that follows goes on marking, a whole word at a time.
        """
        if event.button != "left":
            return False
        self._point(event)
        at = self._mark_pos()
        word = self._dn_word(at)
        self._drag_word = word if word is not None else (at, at)
        self._drag_from = at
        if self._mark_word():
            self._copy_primary()
        return True

    def _word_at(self, at: Pos) -> tuple[Pos, Pos]:
        """The word *at* lies in, ``(start, stop)``; *at* twice when it is on none."""
        text = self._text(at.line)
        if at.index >= len(text) or text[at.index] in BREAK_CHARS:
            return at, at
        start, stop = at.index, at.index
        while start and text[start - 1] not in BREAK_CHARS:
            start -= 1
        while stop < len(text) and text[stop] not in BREAK_CHARS:
            stop += 1
        return Pos(at.line, start), Pos(at.line, stop)

    def _dn_word(self, at: Pos) -> tuple[Pos, Pos] | None:
        """``cmMarkWord``'s word (``MICROED.PAS:2933``), ``(start, stop)``, or None.

        On a word's first character, that word; else ``WordLeft`` -- the start of
        this word or the one before it on the line -- and, when there is none
        before *at* on the line, ``WordRight``'s next word, on this line or a later
        one.  So a blank between two words gives the one before it.
        """
        text = self._text(at.line)
        index = min(at.index, len(text))
        on_start = (index < len(text) and text[index] not in BREAK_CHARS
                    and (index == 0 or text[index - 1] in BREAK_CHARS))
        start: Pos | None = Pos(at.line, index) if on_start else None
        if start is None:
            back = index
            while back > 0 and text[back - 1] in BREAK_CHARS:
                back -= 1
            while back > 0 and text[back - 1] not in BREAK_CHARS:
                back -= 1
            if back < len(text) and text[back] not in BREAK_CHARS:
                start = Pos(at.line, back)
        if start is None:
            start = self._word_right(Pos(at.line, index))
            text = self._text(start.line)
            if start.index >= len(text) or text[start.index] in BREAK_CHARS:
                return None
        text = self._text(start.line)
        stop = start.index
        while stop < len(text) and text[stop] not in BREAK_CHARS:
            stop += 1
        return start, Pos(start.line, stop)

    def _mark_word(self) -> bool:
        """``cmMarkWord``: :meth:`_dn_word` marked, the cursor at its start; False on none."""
        word = self._dn_word(self._mark_pos())
        if word is None:
            return False
        start, stop = word
        self._mark_span(start, stop)
        self._go(start)
        return True

    def _mark_span(self, start: Pos, stop: Pos) -> None:
        """Mark from *start* to *stop*, as the kind of block in force."""
        if self.vertical_blocks:
            self.block_hidden = False
            self.column_block = ((start.line, self._painted_column(start)), (stop.line, self._painted_column(stop)))
        else:
            self._set_block(start, stop)

    def _mark_words_to(self) -> None:
        """A drag after a double-click: from the word it marked to the whole word
        under the pointer, the cursor on the end that moves."""
        first, last = self._drag_word
        start, stop = self._word_at(self._mark_pos())
        if start < first:
            self._mark_span(start, last)
            self._go(start)
        else:
            stop = max(stop, last)
            self._mark_span(first, stop)
            self._go(stop)
