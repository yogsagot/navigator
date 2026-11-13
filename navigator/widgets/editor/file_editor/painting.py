"""Painting the text: syntax highlighting on a thread, the info line's indicators, laying out
and drawing the rows.

A mixin of :class:`FileEditor` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``file_editor.py``.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from navkit.capabilities import GLYPHS_UNICODE
from navkit.screen import Surface

from navml.background import Outcome

from navigator.lib.editor import columns
from navigator.lib.editor.document import Pos
from navigator.lib.editor import search
from navigator.lib import highlight
from navigator.lib.viewer import HIDDEN_MARKS
from navigator.widgets.editor.file_editor.helpers import LEX_AHEAD, LEX_LIMIT, _LEXER, _laid_line, _lex_text

if TYPE_CHECKING:
    from navigator.widgets.editor.file_editor.file_editor import FileEditor as _Base
else:
    from navkit.widget import Mixin as _Base


class Painting(_Base):
    """Painting the text: syntax highlighting on a thread, the info line's indicators, laying out"""

    def place_indicator(self) -> tuple[int, int]:
        """Where ``line:column`` stands in :attr:`info_text`, end exclusive: what a
        click asks *Goto Line* of -- ``TInfoLine``'s ``2 < X < Length(S)``."""
        _ = self.info_text
        return self._place_at

    def code_indicator(self) -> tuple[int, int]:
        """Where ``[nnn]`` stands in :attr:`info_text`, end exclusive: what a click
        asks *ASCII Chart* of -- ``TInfoLine``'s ``Length(S) < X <= Length(S)+5``."""
        _ = self.info_text
        return self._code_at

    def stamp(self, line: str) -> None:
        """SmartPad's ``InsertInfo``: *line* after the text's end, an empty line
        under it, and the cursor there.

        DN put the two lines into the text without marking it modified, so a
        pad opened and closed untouched is not saved for the stamp alone; a
        text already changed stays changed.
        """
        was_modified = self.modified
        self._moved()
        self._begin()
        end = self.document.end
        lead = self.document.newline if self.document.lines[end.line] else ""
        self.buffer.insert(end, lead + line + self.document.newline)
        self._end()
        if not was_modified:
            self.buffer.mark_saved()
            self.revision += 1
        self._go(self.document.end)
        rows = max(1, self.height)
        self.top = max(0, self.line - rows + 1)

    # -- syntax highlight --------------------------------------------------------

    def rehighlight(self) -> None:
        """Forget every token and lex again at the next paint: a new text, a new
        name (Save as), or ``highlight.ini`` saved.

        The text's lexer is chosen on the thread each time it lexes, from the
        file's name and first line (:func:`navigator.lib.highlight.lexer_for`), so
        nothing more is needed for a change of either to count.
        """
        stop = getattr(self, "_lex_stop", None)
        if stop is not None:
            stop.set()
        #: Each line's spans, as far as known: right up to ``_lexed``, shifted
        #: with the edits after it until lexed again.
        self._spans: list[list[highlight.Span]] = []
        #: How many lines from the top are lexed as the text now stands.
        self._lexed = 0
        #: The stop flag of the lexing in flight, else None.
        self._lex_stop: threading.Event | None = None
        #: The first line an edit touched while lexing was in flight.
        self._dirty_from: int | None = None
        #: The name and file type the tokens were lexed for, and whether
        #: that had no lexer.
        self._lexed_for = (getattr(self, "path", None), getattr(self, "file_type", ""))
        self._plain = False
        app = self.application
        if app is not None and app.is_running:
            self.invalidate()

    def _follow_tokens(self, kind: str, start: Pos, end: Pos) -> None:
        """An edit made: the tokens move with their text, and everything from the
        edited line on is to be lexed again."""
        if kind == "endings":
            return
        if kind == "replace":
            self.rehighlight()
            return
        if self._lex_stop is not None:
            self._dirty_from = start.line if self._dirty_from is None else min(self._dirty_from, start.line)
        highlight.shift_spans(self._spans, kind, start, end)
        self._lexed = min(self._lexed, start.line)

    def _tokens(self, bottom: int) -> list[list[highlight.Span]] | None:
        """The spans to paint lines up to *bottom* with, or None for plain text;
        lexing is asked for when they are not all known.

        From ``render``, as ``DirectoryTree`` asks for its counts: with no
        application running the answer is there before the frame goes on.
        """
        if not self.syntax_highlight:
            return None
        if self._lexed_for != (self.path, self.file_type):
            self.rehighlight()
        if self._plain:
            return None
        if self._lexed <= bottom and self._lex_stop is None:
            self._lex(bottom + LEX_AHEAD)
        return self._spans

    def _lex(self, until: int) -> None:
        lines = tuple(self.document.lines)
        if sum(map(len, lines)) > LEX_LIMIT:
            self._plain = True
            return
        stop = threading.Event()
        self._lex_stop, self._dirty_from = stop, None
        name = str(self.path) if self.path is not None else ""
        _LEXER.run(self, _lex_text, name, self.file_type, lines, until, stop,
                   done=lambda outcome: self._lexed_text(outcome, stop))

    def _lexed_text(self, outcome: Outcome, stop: threading.Event) -> None:
        """The thread's answer: the lines before any edit made meanwhile are taken."""
        if stop is not self._lex_stop:
            return  # forgotten by rehighlight meanwhile
        self._lex_stop = None
        try:
            label, spans = outcome.result()
        except Exception:
            # A lexer that fails on this text: show it plain rather than not at all.
            label, spans = "", False
        if self.lexer_name != label:
            self.lexer_name = label
        if spans is None:
            return
        if spans is False:
            self._plain, self._spans = True, []
        else:
            valid = len(spans) if self._dirty_from is None else min(len(spans), self._dirty_from)
            self._spans[:valid] = spans[:valid]
            self._lexed = valid
        self._dirty_from = None
        app = self.application
        if app is not None and app.is_running:
            # Not when answered on the spot, from inside ``render``.
            self.invalidate()

    # -- painting ------------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        x, y = self.cursor_cell()
        if 0 <= x < self.width and 0 <= y < self.height:
            return x, y
        return None

    def _laid(self, number: int) -> tuple[list[tuple[str, int]], list[tuple[int, str]] | None, int]:
        """Line *number* as it is painted (:func:`_laid_line`): its cells, their
        reading order when Hebrew or Arabic in them changes it, and how far in
        its first painted cell sits -- right-aligned, a right-to-left line.

        The cursor, the block and a click are all columns of the line as
        written; the order and the shift are what map them to where a column
        is painted.
        """
        lines = self.document.lines
        if not 0 <= number < len(lines):
            return [], None, 0
        return _laid_line(lines[number], self.tab_size, self.width, self.left + self.width)

    def _visual_column(self, number: int, column: int) -> int:
        """Where the text's *column* on line *number* is painted, before scrolling.

        Past a right-to-left line's end the columns run on leftwards from the
        cell left of its text, down to the screen's first.
        """
        row, order, shift = self._laid(number)
        if order is None:
            return column
        if column >= len(row):
            beyond = column - len(row)
            return max(0, shift - 1 - beyond) if shift else len(order) + beyond
        return shift + next((x for x, (at, _) in enumerate(order) if at == column), column)

    def _logical_column(self, number: int, x: int) -> int:
        """The text's column painted at *x* (before scrolling) on line *number*:
        left of a right-to-left line, past its end; right of it, its start."""
        row, order, shift = self._laid(number)
        if order is None:
            return x
        at = x - shift
        if at < 0:
            return len(row) - 1 - at
        if at >= len(order):
            return 0 if shift else len(row) + at - len(order)
        return order[at][0]

    def _block_picked(self, number: int) -> tuple[frozenset[int], bool] | None:
        """For a block the cursor marked (:attr:`_painted_block`): the indices
        of line *number* it holds and whether it holds the line's break; None
        for any other block, or none."""
        if self.block is None or self.block_hidden or self.column_block is not None:
            return None
        if self.block is not self._painted_block:
            return None
        length = len(self.document.lines[number])
        picked: set[int] = set()
        broken = False
        for a, b in self._block_runs():
            if b.line < number or a.line > number:
                continue
            i = a.index if a.line == number else 0
            j = b.index if b.line == number else length
            picked.update(range(i, j))
            broken = broken or b.line > number
        return frozenset(picked), broken

    def _block_columns(self, number: int) -> tuple[int, int] | None:
        """The columns line *number* has in the block, end exclusive, or None.

        A line whose break is in the block gets one more, so an empty line
        inside it shows.
        """
        if self.block_hidden:
            return None
        rectangle = self.rectangle
        if rectangle is not None:
            top, left, bottom, right = rectangle
            return (left, right) if top <= number <= bottom else None
        block = self.block
        if block is None or not block[0].line <= number <= block[1].line:
            return None
        text, tab = self.document.lines[number], self.tab_size
        first = columns.column_of(text, block[0].index, tab) if number == block[0].line else 0
        if number == block[1].line:
            last = columns.column_of(text, block[1].index, tab)
        else:
            last = columns.width(text, tab) + 1
        return (first, last) if first < last else None

    def _painted_rows(self) -> list[tuple[int, list[tuple[str, int]], list[tuple[int, str]] | None, int, int, bool]]:
        """The rows on screen, top first: each ``(line, cells, order, shift,
        base, last)`` -- the line's number, the cells shown (``_laid_line``'s
        row), their painted order or None, how far in the first sits, the
        line's column the cells start at, and whether the row is the line's
        last, where what is past its text is painted.  Unwrapped, a row is a
        line from :attr:`left`, at *base* 0 and always its last."""
        lines = self.document.lines
        found = []
        width, left = self.width, self.left
        if self.soft_wrap:
            for line, row in self.visible_rows():
                found.append((line, *self._row_layout(line, row)))
            return found
        for y in range(self.height):
            number = self.top + y
            if number >= len(lines):
                break
            row, order, shift = _laid_line(lines[number], self.tab_size, width, left + width)
            found.append((number, row, order, shift, 0, True))
        return found

    def render(self, surface: Surface) -> None:
        """The text, the block and the match lit -- and, as DN's ``Draw`` had them,
        the cursor's line in *Current line* (a block or match on it in *Current line
        selected*) and its column on every row in *Current column*, laid last."""
        self.revision
        normal = self.style
        normal_selected = self.part_style("selected")
        surface.fill(0, 0, self.width, self.height, " ", normal)
        lines = self.document.lines
        left, width = self.left, self.width
        tokens = self._tokens(min(len(lines), self.top + self.height) - 1)
        looks: dict[tuple[tuple[str, ...], bool], Any] = {}
        hidden = self.show_hidden
        tier = 0 if self.glyphs >= GLYPHS_UNICODE else 1
        query = self.highlight_query
        if query is not None and not search.valid(query):
            query = None
        # A pattern reaching across lines: its matches in a window round the
        # lines shown, cut into each line's parts (search.window_matches).
        crossing = self._window_marks(query) if query is not None and search.crosses(query) else None
        for y, (number, row, order, shift, base, last) in enumerate(self._painted_rows()):
            style, selected = normal, normal_selected
            current = self.highlight_line and number == self.line
            if current:
                style = self.part_style("current_line")
                selected = self.part_style("current_line_selected")
                surface.fill(0, y, width, 1, " ", style)
            text = lines[number]
            # Hebrew or Arabic in the line: its cells in reading order, each
            # keeping the column it has in the text (navkit.bidi.order_cells),
            # which is what the block, a match and the tokens are told by; a
            # right-to-left line right-aligned, *shift* columns in.  Soft
            # wrapped, *row* is one of the line's rows, *base* columns in, and
            # ordered on its own (:meth:`_painted_rows`); what is past the
            # line's text is painted on its *last* row alone.
            origin = range(len(row)) if order is None else [at for at, _ in order]
            # A block the cursor marked, on such a line: the characters lit
            # are its runs' (_block_runs), and the line break past the text.
            picked = self._block_picked(number) if order is not None else None
            span = None if picked is not None else self._block_columns(number)
            # A column block's columns are painted columns; a match's, the text's.
            painted = span is not None and self.column_block is not None
            span = span or self._found_columns(number)
            if span is not None and base:
                span = (span[0] - base, span[1] - base)
            if span is not None and not last:
                span = (span[0], min(span[1], len(row)))
            if order is not None:
                row = [(shown, row[at][1]) for at, shown in order]
            # Where the line's end is painted: past its text, or left of it.
            end_cell = shift - 1 if shift else len(row)
            if last and picked is not None and picked[1] and left <= end_cell < left + width:
                surface.fill(end_cell - left, y, 1, 1, " ", selected)
            if span is not None and shift and not painted:
                # Past a right-to-left line's end the columns run leftwards.
                first, final = max(span[0], len(row)), span[1]
                if last and first < final:
                    start = max(left, shift - (final - len(row)))
                    stop = min(left + width, shift - (first - len(row)))
                    if start < stop:
                        surface.fill(start - left, y, stop - start, 1, " ", selected)
            elif span is not None:
                # Past the text the columns are as they are; in it, each cell is lit
                # by its own column, below.
                beyond = len(row) if order is not None and not painted else 0
                start, stop = max(span[0], left, beyond), min(span[1], left + width)
                if start < stop:
                    surface.fill(start - left, y, stop - start, 1, " ", selected)
            spans = tokens[number] if tokens is not None and number < len(tokens) else ()
            at = 0
            # The Find bar's matches on this line, as indices: lit under the
            # block and the match found, over the tokens.
            if query is None:
                marks = ()
            elif crossing is not None:
                marks = crossing.get(number, ())
            else:
                marks = search.line_matches(text, query)
            match_style = self.part_style("match", current_line=current) if marks else None
            if hidden and last:
                # The line's ending, a cell past its text, in the colours there.
                end = columns.width(text, self.tab_size) - base
                ending = self.document.endings[number]
                if ending in HIDDEN_MARKS and left <= end_cell < left + width:
                    look = selected if span is not None and span[0] <= end < span[1] else style
                    surface.set_cell(end_cell - left, y, HIDDEN_MARKS[ending][tier], look.derive(dim=True))
            for x in range(width):
                column = x + left - shift
                if column < 0:
                    continue
                if column >= len(row):
                    break
                char, index = row[column]
                if picked is not None and index in picked[0]:
                    cell = selected
                elif span is not None and span[0] <= (column + shift if painted else origin[column]) < span[1]:
                    cell = selected
                elif marks and any(begin <= index < end for begin, end in marks):
                    cell = match_style
                else:
                    cell = style
                    if order is not None:
                        # Reordered, the indices no longer only grow along the row.
                        at = 0
                    # The cells' indices only grow along a row: one pointer will do.
                    while at < len(spans) and spans[at][1] <= index:
                        at += 1
                    if at < len(spans) and spans[at][0] <= index:
                        key = (spans[at][2], current)
                        cell = looks.get(key)
                        if cell is None:
                            cell = looks[key] = self.part_style("token", classes=key[0], current_line=current)
                if char == "":
                    if x == 0:
                        surface.set_cell(x, y, " ", cell)
                    continue
                if x == width - 1 and column + 1 < len(row) and row[column + 1][0] == "":
                    surface.set_cell(x, y, " ", cell)
                    continue
                if hidden and text[index] in " \t" and (
                    text[index] == " " or column == 0 or row[column - 1][1] != index
                ):
                    # A blank, or a tab's first column: its mark, faint.
                    surface.set_cell(x, y, HIDDEN_MARKS[text[index]][tier], cell.derive(dim=True))
                    continue
                surface.set_cell(x, y, char, cell)
        # The cursor's painted column: on a reordered line its column is
        # elsewhere, and soft wrapped on one of its line's rows.
        x, y = self.cursor_cell()
        if self.ruler and self._right_press is not None and 0 <= x < width and 0 <= y < self.height:
            # ``RulerVisible``: from the cursor rightwards, laid before the
            # column as DN laid it; one ``draw_runs``, so a mirrored screen
            # keeps the digits in order.
            looks = {False: self.part_style("ruler"), True: self.part_style("ruler_tens")}
            runs: list[tuple[str, Any]] = []
            for digit, high in columns.ruler(width - x):
                if runs and runs[-1][1] is looks[high]:
                    runs[-1] = (runs[-1][0] + digit, looks[high])
                else:
                    runs.append((digit, looks[high]))
            surface.draw_runs(x, y, runs)
        if self.highlight_column and 0 <= x < width:
            # ``WordRec(B[Delta.X - Pos.X]).Hi := CC[7]``: every row, text or not.
            column_style = self.part_style("current_column")
            for y in range(self.height):
                char = surface.get(x, y)[0] or " "
                surface.set_cell(x, y, char, column_style)
