"""Searching and replacing, and paragraph formatting (^B and Ctrl+J F).

A mixin of :class:`FileEditor` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``file_editor.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import sys

from navigator.widgets.editor.commands import (
    FCenter,
    FJustify,
    LCenter,
    LJustify,
    LLeft,
    LRight,
    FLeft,
    FRight,
    StartSearch,
)
from navigator.lib.editor import columns
from navigator.lib.editor.document import Pos
from navigator.lib.editor import search
from navigator.lib.editor.search import BREAK_CHARS, SearchData

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navigator.widgets.editor.file_editor.file_editor_surface import FileEditor as _Base
else:
    from navkit.widget import Mixin as _Base


class Search(_Base):
    """Searching and replacing, and paragraph formatting (^B and Ctrl+J F)."""

    # -- the search ----------------------------------------------------------------------

    def word_at_cursor(self) -> str:
        """``StartSearch``'s first guess: the word the cursor is on, or nothing."""
        text = self._text()
        index = self._mark_pos().index
        if index >= len(text) or text[index] in BREAK_CHARS:
            return ""
        start, stop = index, index
        while start and text[start - 1] not in BREAK_CHARS:
            start -= 1
        while stop < len(text) and text[stop] not in BREAK_CHARS:
            stop += 1
        return text[start:stop]

    def search_seed(self) -> tuple[str, Pos]:
        """What the Find bar starts with, and the place it searches from: a block
        within one line, else the word at the cursor, either from its start;
        neither, nothing from the cursor."""
        block = self.block
        if self.has_block and block is not None and block[0].line == block[1].line and block[0] != block[1]:
            start, end = block
            return self.document.lines[start.line][start.index:end.index], start
        here = self._mark_pos()
        word = self.word_at_cursor()
        if not word:
            return "", here
        text, index = self.document.lines[here.line], here.index
        while index and text[index - 1] not in BREAK_CHARS:
            index -= 1
        return word, Pos(here.line, index)

    def place_cursor(self, pos: Pos) -> None:
        """The cursor put on *pos*, a place in the text, and brought into view."""
        self._moved()
        self._go(pos)

    def _search_bounds(self, number: int) -> tuple[int, int] | None:
        """The part of line *number* the block covers, as indices -- *Selected text*:
        from its first stretch's start to its last's end; :meth:`find` passes
        over a match that is not wholly inside one stretch.

        A departure: a stream block over several lines is clipped at its start on
        its first line too, where DN clipped the start column only for a block
        within one line or a column block (``MICROED.PAS:1468``), searching that
        first line from its beginning."""
        spans = self._line_spans(number)
        if spans is None:
            return None
        return spans[0][0], spans[-1][1]

    def find(self, at: Pos, data: SearchData, *, backward: bool) -> tuple[Pos, Pos] | None:
        """The next match of *data* from *at*: the whole text, or the block's part of it.
        A pattern reaching across lines finds nothing in a column block, whose
        pieces are not one text."""
        if not data.selected:
            return search.find(self.document.lines, at, data, backward=backward)
        if search.crosses(data):
            if self.column_block is not None:
                return None
            return search.find(self.document.lines, at, data, backward=backward, bounds=self._search_bounds)
        while True:
            found = search.find(self.document.lines, at, data, backward=backward, bounds=self._search_bounds)
            if found is None:
                return None
            start, end = found
            spans = self._line_spans(start.line) or []
            if any(i <= start.index and end.index <= j for i, j in spans):
                return found
            # Between two stretches of a block painted across a reordered line:
            # not in it.  On from the next place.
            at = Pos(start.line, start.index + 1) if not backward else Pos(end.line, end.index - 1)

    def show_found(self, found: tuple[Pos, Pos], *, backward: bool) -> None:
        """The cursor after the match -- before it, searching backward -- and the match
        lit (``SearchActive``) until the cursor or the text moves."""
        self._moved()
        self._go(found[0] if backward else found[1])
        self._found = found
        self._found_for = (self.line, self.col, self.revision)

    def found_on_display(self) -> tuple[Pos, Pos] | None:
        """``SearchOnDisplay``: the match still lit, if the cursor and text are as it left them."""
        if self._found is not None and self._found_for == (self.line, self.col, self.revision):
            return self._found
        return None

    def replacement(self, found: tuple[Pos, Pos], data: SearchData) -> str:
        """What *found* is replaced by, a line break in it this text's own."""
        return search.replacement(self.document.lines, found, data, newline=self.document.newline)

    def replace_found(self, found: tuple[Pos, Pos], new: str) -> Pos:
        """One replacement, an undo step of its own as DN's ``udReplace``; where it ends."""
        self._moved()
        self._begin()
        self.buffer.delete(*found)
        end = self.buffer.insert(found[0], new)
        self._end()
        return end

    def replace_all(self, data: SearchData) -> int:
        """The Find bar's *All*: every match of *data* replaced, in one undo step
        (a departure: DN's *Change all* made each its own); how many.  Last
        first, so the places found before stand."""
        found = search.all_matches(self.document.lines, data, limit=sys.maxsize)
        if not found:
            return 0
        self._moved()
        self._begin()
        for number, start, last, end in reversed(found):
            place = (Pos(number, start), Pos(last, end))
            new = self.replacement(place, data)
            self.buffer.delete(*place)
            self.buffer.insert(place[0], new)
        self._end()
        self._found = None
        return len(found)

    def _window_marks(self, query: SearchData) -> dict[int, list[tuple[int, int]]]:
        """:func:`search.window_matches` for the lines on screen, kept until the
        text, the view or the query changes -- never the whole text a frame."""
        shown = [line for line, _ in self.visible_rows()] or [self.top]
        key = (self.revision, shown[0], shown[-1], query.text, query.case, query.whole)
        if self._marks_cache is None or self._marks_cache[0] != key:
            self._marks_cache = (key, search.window_matches(self.document.lines, shown[0], shown[-1], query))
        return self._marks_cache[1]

    def _found_columns(self, number: int) -> tuple[int, int] | None:
        """The columns of line *number* the match lit covers -- a match reaching
        across lines (the Find bar's) on each of them, the break's cell too
        where it goes on past a line's end, as a stream block's does."""
        found, mark = self._found, self._found_for
        if found is None or mark != (self.line, self.col, self.revision):
            return None
        start, end = found
        if not start.line <= number <= end.line:
            return None
        text, tab = self.document.lines[number], self.tab_size
        first = columns.column_of(text, start.index, tab) if number == start.line else 0
        last = (columns.column_of(text, end.index, tab) if number == end.line
                else columns.width(text, tab) + 1)
        return first, last

    # -- paragraph formatting -------------------------------------------------------------

    #: Which ``FormatBlock`` each command asks for.
    FORMATS = {FJustify: "justify", FRight: "right", FLeft: "left", FCenter: "center"}

    def format_block(self, mode: str) -> None:
        """``FormatBlock``: the stream block's whole lines as one paragraph, laid out
        between this editor's margins (:mod:`navigator.lib.editor.paragraph`).

        The lines go in one undo step; the block then covers the new lines,
        from the start of the first to the start of the line after them, and
        the cursor is at its start.
        """
        from navigator.lib.editor.paragraph import format_lines

        if self.block is None or self.block_hidden:
            return
        start, end = self.block
        last = end.line - 1 if end.index == 0 and end.line > start.line else end.line
        left, right, indent = self.margins
        new = format_lines(self.document.lines[start.line:last + 1], mode,
                           left=left, right=right, indent=indent)
        self._moved()
        self._begin()
        self.buffer.delete(Pos(start.line, 0), Pos(last, len(self.document.lines[last])))
        self.buffer.insert(Pos(start.line, 0), self.document.newline.join(new))
        self._end()
        after = start.line + len(new)
        stop = Pos(after, 0) if after < len(self.document) else self.document.end
        self.block = (Pos(start.line, 0), stop) if stop > Pos(start.line, 0) else None
        self._go(Pos(start.line, 0))

    async def on_f_justify(self, event: FJustify) -> bool:
        self.format_block("justify")
        return True

    async def on_f_right(self, event: FRight) -> bool:
        self.format_block("right")
        return True

    async def on_f_left(self, event: FLeft) -> bool:
        self.format_block("left")
        return True

    async def on_f_center(self, event: FCenter) -> bool:
        self.format_block("center")
        return True

    def format_line(self, mode: str) -> None:
        """``cmLJustify``/``cmLRight``/``cmLLeft``/``cmLCenter``: the cursor's
        line made the block, shown, and formatted as the block is
        (``EDITOR.PAS``: ``Mark.A.X := 0; Mark.B.X := Length(GetLine(...));
        BlockVisible := On; FormatBlock``).  The block then covers what the
        line became, as DN's did.  An empty line is an empty block, which
        :meth:`format_block` leaves, as ``ValidBlock`` did."""
        if self.vertical_blocks:
            return
        self._unmark()
        line = self.line
        self.block = (Pos(line, 0), Pos(line, len(self.document.lines[line])))
        self.block_hidden = False
        if self.block[0] == self.block[1]:
            self.block = None
            return
        self.format_block(mode)

    async def on_l_justify(self, event: LJustify) -> bool:
        self.format_line("justify")
        return True

    async def on_l_right(self, event: LRight) -> bool:
        self.format_line("right")
        return True

    async def on_l_left(self, event: LLeft) -> bool:
        self.format_line("left")
        return True

    async def on_l_center(self, event: LCenter) -> bool:
        self.format_line("center")
        return True
