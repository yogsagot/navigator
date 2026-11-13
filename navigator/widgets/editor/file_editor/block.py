"""The block: marking it, its ends, and the ^K block commands -- copy, move, indent, sort,
calculate, change case -- and the word's or the line's case.

A mixin of :class:`FileEditor` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``file_editor.py``.
"""

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING, Any, Callable

from navkit.bidi import text_rtl
from navkit.i18n import tr

from navigator.widgets.editor.commands import (
    CapString,
    CapWord,
    LowString,
    LowWord,
    UpString,
    UpWord,
    CalcBlock,
    SortBlock,
    CapitalizeBlock,
    CopyBlock,
    MoveBlockEnd,
    MoveBlockStart,
    HideBlock,
    IndentBlock,
    LowcaseBlock,
    BlockEnd,
    BlockStart,
    MarkLine,
    MarkWord,
    MoveBlock,
    UnindentBlock,
    UpcaseBlock,
)
from navigator.lib.editor import columns
from navigator.lib.editor.document import BREAK, Pos, shifted
from navigator.lib.editor.search import BREAK_CHARS
from navigator.widgets.editor.file_editor.helpers import _COLUMN_CLIP, _laid_line, _painted_spans, block_sum, capitalize

if TYPE_CHECKING:
    from navigator.widgets.editor.file_editor.file_editor import FileEditor as _Base
else:
    from navkit.widget import Mixin as _Base


class Block(_Base):
    """The block: marking it, its ends, and the ^K block commands -- copy, move, indent, sort,"""

    # -- the block ---------------------------------------------------------------
    #
    # Two kinds, one at a time.  A stream block's ends are places in the text
    # (``Pos``); a column block's are screen cells ``(line, col)``, the corners
    # of a rectangle.  Marking speaks of "ends" either way -- ``_here`` is the
    # cursor as the kind in force sees it -- so Shift+movement, Shift+click
    # and a drag are the same code for both.

    def _mark_pos(self) -> Pos:
        """The cursor as a place a block can end at: past a line's end, its end."""
        index, _ = self._index()
        return Pos(self.line, min(index, len(self._text())))

    def _here(self) -> Any:
        """The cursor as an end of the kind of block in force.  A column block's
        corner takes the column Up/Down aim for, so Shift+Down across a short
        line keeps the rectangle's width rather than losing it there."""
        if self.vertical_blocks:
            if self._goal is not None:
                return (self.line, self._goal)
            return (self.line, self._visual_column(self.line, self.col))
        return self._mark_pos()

    def _block_ends(self) -> tuple[Any, Any] | None:
        return self.column_block if self.vertical_blocks else self.block

    @property
    def marked(self) -> bool:
        """Whether a block is marked, shown or hidden."""
        return self.block is not None or self.column_block is not None

    @property
    def has_block(self) -> bool:
        """DN's ``BlockVisible and ValidBlock``: a block marked and shown, to act on."""
        return self.marked and not self.block_hidden

    def _unmark(self) -> None:
        self.block = None
        self.column_block = None
        self.block_hidden = False
        self._half_mark = None

    def _set_block(self, anchor: Any, here: Any) -> None:
        """Mark from *anchor* to *here*; nothing, if the two enclose nothing."""
        self.block_hidden = False
        if self.vertical_blocks:
            self.column_block = (anchor, here) if anchor[1] != here[1] else None
        else:
            self.block = (min(anchor, here), max(anchor, here)) if anchor != here else None
            self._painted_block = self.block

    def _extend_block(self, before: Any) -> None:
        ends = self._block_ends()
        anchor = before
        if ends is not None and before in ends:
            anchor = ends[1] if before == ends[0] else ends[0]
        self._set_block(anchor, self._here())

    @property
    def rectangle(self) -> tuple[int, int, int, int] | None:
        """The column block as ``(top, left, bottom, right)``: lines inclusive, columns end-exclusive."""
        corners = self.column_block
        if corners is None:
            return None
        (a, x), (b, y) = corners
        return min(a, b), min(x, y), max(a, b), max(x, y)

    def _follow_edit(self, kind: str, start: Pos, end: Pos) -> None:
        """An edit made: the block's ends move with the text around them.

        A column block keeps its columns and moves only by whole lines, when
        an edit adds or takes out line breaks above it.
        """
        self._half_mark = None
        if self.buffer.editing is not self and self in self.buffer.views:
            # Another view's edit (Window > *New view*): this one repaints,
            # and its cursor moves with the text around it, as the block does.
            self.revision += 1
            if kind not in ("endings", "replace"):
                anchor = getattr(self, "_anchor", None)
                here = shifted(anchor if anchor is not None else self._mark_pos(), kind, start, end)
                self._anchor = here
                self.line = min(here.line, len(self.document) - 1)
                text = self.document.lines[self.line]
                self.col = columns.column_of(text, min(here.index, len(text)), self.tab_size)
        if kind == "endings":
            return  # every line as it was: only their terminators changed
        if kind == "replace":
            # The whole text read again: nothing marked in it means the same.
            self._unmark()
            self.line = min(self.line, len(self.document) - 1)
            return
        block = self.block
        if block is not None:
            painted = block is self._painted_block
            first = shifted(block[0], kind, start, end)
            last = shifted(block[1], kind, start, end, stay=True)
            self.block = (first, last) if first < last else None
            if painted:
                self._painted_block = self.block
        corners = self.column_block
        if corners is not None and end.line != start.line:
            def moved(cell: tuple[int, int]) -> tuple[int, int]:
                line, col = cell
                # A break typed at a line's very start pushes it down, block and all.
                return shifted(Pos(line, 0), kind, start, end).line, col
            self.column_block = (moved(corners[0]), moved(corners[1]))

    def _rect_spans(self, number: int, left: int, right: int) -> tuple[list[tuple[int, int]], int]:
        """What of line *number* is painted in columns *left* to *right* (end
        exclusive): the stretches of its text, in order, and how many columns
        of it there are.

        A column block's columns are where things are painted, so on a line
        Hebrew or Arabic reorders they hold characters scattered in the text.
        Elsewhere the one stretch :func:`columns.span` gives, as ever.
        """
        text = self.document.lines[number] if number < len(self.document) else ""
        tab = self.tab_size
        row, order, shift = self._laid(number)
        if order is None:
            i, j = columns.span(text, left, right, tab)
            return [(i, j)], columns.column_of(text, j, tab) - columns.column_of(text, i, tab)
        bases = sorted({row[at][1] for at, shown in order if shown})
        reach = {base: (bases[k + 1] if k + 1 < len(bases) else len(text)) for k, base in enumerate(bases)}
        inside = range(max(0, left - shift), min(right - shift, len(order)))
        picked = sorted({
            i for x in inside if order[x][1]
            for i in range(row[order[x][0]][1], reach[row[order[x][0]][1]])
        })
        spans: list[tuple[int, int]] = []
        for i in picked:
            if spans and spans[-1][1] == i:
                spans[-1] = (spans[-1][0], i + 1)
            else:
                spans.append((i, i + 1))
        return spans, len(inside)

    def _line_spans(self, number: int) -> list[tuple[int, int]] | None:
        """The stretches of line *number* the block holds, as string indices,
        whatever its kind; None for a line outside it."""
        if self.column_block is not None:
            top, left, bottom, right = self.rectangle
            return self._rect_spans(number, left, right)[0] if top <= number <= bottom else None
        if self.block is None:
            return None
        start, end = self.block
        if not start.line <= number <= end.line:
            return None
        length = len(self.document.lines[number])
        spans = [
            (a.index if a.line == number else 0, b.index if b.line == number else length)
            for a, b in self._block_runs() if a.line <= number <= b.line
        ]
        return [(i, j) for i, j in spans if i < j] or [(0, 0)]

    def _painted_column(self, pos: Pos) -> int:
        """Where the character at *pos* is painted: a column block's corners are."""
        return self._visual_column(pos.line, self._column(pos))

    def _column_pieces(self) -> list[str]:
        """Each line's part of the column block, padded out to its width."""
        top, left, bottom, right = self.rectangle
        pieces = []
        for number in range(top, bottom + 1):
            text = self.document.lines[number] if number < len(self.document) else ""
            spans, shown = self._rect_spans(number, left, right)
            piece = "".join(text[i:j] for i, j in spans)
            pieces.append(piece + " " * max(0, (right - left) - shown))
        return pieces

    def _block_runs(self) -> list[tuple[Pos, Pos]]:
        """The stream block as the stretches of the text it holds, in order.

        One, the block itself, unless the cursor marked it (:attr:`_painted_block`)
        across a line Hebrew or Arabic reorders.  Then that line holds what is
        painted between the ends: between the two on the block's one line; on
        its first line, from the start's cell to the end the line reads towards
        (the left of a right-to-left one), on its last, from where the line
        begins to the end's cell; the lines between whole, line breaks with them.
        """
        block = self.block
        if block is None:
            return []
        if block is not self._painted_block:
            return [block]
        key = (block, self.revision, self.tab_size)
        if self._runs_cache is not None and self._runs_cache[0] == key:
            return self._runs_cache[1]
        start, end = block
        lines = self.document.lines
        runs: list[tuple[Pos, Pos]] = []
        for number in range(start.line, end.line + 1):
            text = lines[number]
            first = start.index if number == start.line else 0
            last = end.index if number == end.line else len(text)
            spans = _painted_spans(
                text, self.tab_size,
                start.index if number == start.line else None,
                end.index if number == end.line else None,
            )
            if spans is None:
                spans = [(first, last)] if first < last else []
            runs.extend((Pos(number, i), Pos(number, j)) for i, j in spans)
            if number < end.line:
                runs.append((Pos(number, len(text)), Pos(number + 1, 0)))
        merged: list[tuple[Pos, Pos]] = []
        for run in runs:
            if merged and merged[-1][1] == run[0]:
                merged[-1] = (merged[-1][0], run[1])
            else:
                merged.append(run)
        self._runs_cache = (key, merged)
        return merged

    def _block_raw(self) -> str:
        """The stream block's text, in the file's own line breaks."""
        return "".join(self.document.text(a, b) for a, b in self._block_runs())

    @property
    def block_text(self) -> str:
        """What the block holds, its line breaks plain ``\\n``: what a copy hands out.

        A column block's lines lose the blanks that only padded them out.
        """
        if self.column_block is not None:
            return "\n".join(piece.rstrip(" ") for piece in self._column_pieces())
        if self.block is None:
            return ""
        return BREAK.sub("\n", self._block_raw())

    def _take_block(self) -> None:
        """Delete the block inside an open group; the cursor to where it began."""
        if self.column_block is not None:
            top, left, bottom, right = self.rectangle
            corner = self._logical_column(top, left)
            for number in range(top, min(bottom, len(self.document) - 1) + 1):
                text = self.document.lines[number]
                for i, j in reversed(self._rect_spans(number, left, right)[0]):
                    if self.overwrite:
                        # ``BlockDelete`` in overwrite (``udClearBlock``): the
                        # rectangle's cells made blanks, the columns kept.
                        wide = (columns.column_of(text, j, self.tab_size)
                                - columns.column_of(text, i, self.tab_size))
                        self.buffer.delete(Pos(number, i), Pos(number, j))
                        self.buffer.insert(Pos(number, i), " " * wide)
                    else:
                        self.buffer.delete(Pos(number, i), Pos(number, j))
            self.column_block = None
            if not self.overwrite:
                # Only inserting did ``BlockDelete`` move the cursor.
                self._go_column(top, corner)
            return
        runs = self._block_runs()
        if runs:
            for a, b in reversed(runs):
                self.buffer.delete(a, b)
            self.block = None
            self._go(runs[0][0])

    def _delete_block(self) -> None:
        if not self.has_block:
            return
        self._begin()
        self._take_block()
        self._end()

    def _copy_block(self, *, primary: bool = False) -> None:
        """Hand the block to the clipboard; a column block is remembered as one.

        So pasting it back puts it in as a rectangle, as DN's clipboard knew
        a vertical block from a stream one.
        """
        app = self.application
        if not self.has_block or app is None:
            return
        text = self.block_text
        if self.column_block is not None:
            _COLUMN_CLIP.clear()
            _COLUMN_CLIP[text] = self._column_pieces()
        app.copy_to_clipboard(text, primary=primary)

    # -- the ^K and ^Q commands -------------------------------------------------

    def _ordered_ends(self) -> tuple[Any, Any] | None:
        """The block's start and end in the kind in force: places, or corner cells."""
        if self.vertical_blocks:
            rectangle = self.rectangle
            if rectangle is None:
                return None
            top, left, bottom, right = rectangle
            return (top, left), (bottom, right)
        return self.block

    def _set_ordered(self, start: Any, end: Any) -> None:
        self.block_hidden = False
        if self.vertical_blocks:
            fits = start[0] <= end[0] and start[1] < end[1]
            self.column_block = (start, end) if fits else None
        else:
            self.block = (start, end) if start < end else None
            self._painted_block = self.block

    def _mark_end(self, *, first: bool) -> None:
        """^K B (*first*) or ^K K: one end of the block at the cursor.

        With a block marked, that end moves.  With none, the end waits for
        the other one, and the two make the block once both are set.
        """
        here = self._here()
        ends = self._ordered_ends()
        if ends is None:
            half = self._half_mark
            if half is not None and half[1] != first:
                self._half_mark = None
                self._set_ordered(*((here, half[0]) if first else (half[0], here)))
            else:
                self._half_mark = (here, first)
            return
        start, end = ends
        self._set_ordered(*((here, end) if first else (start, here)))

    async def on_block_start(self, event: BlockStart) -> bool:
        self._mark_end(first=True)
        return True

    async def on_block_end(self, event: BlockEnd) -> bool:
        self._mark_end(first=False)
        return True

    async def on_hide_block(self, event: HideBlock) -> bool:
        """``cmHideBlock``: ``BlockVisible := not BlockVisible``."""
        self.block_hidden = not self.block_hidden
        return True

    async def on_mark_word(self, event: MarkWord) -> bool:
        self._unmark()
        self._mark_word()
        return True

    async def on_mark_line(self, event: MarkLine) -> bool:
        """The cursor's line, its break included; as a column block, its width."""
        self._unmark()
        line, text = self.line, self._text()
        if self.vertical_blocks:
            width = columns.width(text, self.tab_size)
            if width:
                self.column_block = ((line, 0), (line, width))
        elif line + 1 < len(self.document):
            self.block = (Pos(line, 0), Pos(line + 1, 0))
        elif text:
            self.block = (Pos(line, 0), Pos(line, len(text)))
        return True

    async def on_move_block_start(self, event: MoveBlockStart) -> bool:
        self._moved()
        start, _ = self._ordered_ends()
        self._go_column(*start) if self.vertical_blocks else self._go(start)
        return True

    async def on_move_block_end(self, event: MoveBlockEnd) -> bool:
        self._moved()
        _, end = self._ordered_ends()
        self._go_column(*end) if self.vertical_blocks else self._go(end)
        return True

    async def on_copy_block(self, event: CopyBlock) -> bool:
        """^K C: the block's text again at the cursor, and the copy marked."""
        line, col = self.line, self.col
        self._moved()
        self._begin()
        if self.column_block is not None:
            pieces = self._column_pieces()
            _, left, _, right = self.rectangle
            width = right - left
            self._put_rectangle(pieces, line, col)
            painted = self._visual_column(line, col)
            self.column_block = ((line, painted), (line + len(pieces) - 1, painted + width))
            self._go_column(line, col)
        else:
            text = self._block_raw()
            at = self._pad()
            end = self.buffer.insert(at, text)
            self.block = (at, end)
            self._go(at)
        self._end()
        return True

    async def on_move_block(self, event: MoveBlock) -> bool:
        """^K V: the block taken out and put in at the cursor, still marked.

        Nothing happens with the cursor inside the block, where it would be
        put into itself.
        """
        line, col = self.line, self.col
        if self.column_block is not None:
            top, left, bottom, right = self.rectangle
            painted = self._visual_column(line, col)
            if top <= line <= bottom and left <= painted < right:
                return True
            pieces = self._column_pieces()
            self._moved()
            self._begin()
            self._take_block()
            if top <= line <= bottom and painted >= right:
                col = self._logical_column(line, painted - (right - left))
            self._put_rectangle(pieces, line, col)
            painted = self._visual_column(line, col)
            self.column_block = ((line, painted), (line + len(pieces) - 1, painted + right - left))
            self._go_column(line, col)
            self._end()
            return True
        here = self._mark_pos()
        if any(a < here < b for a, b in self._block_runs()):
            return True
        self._moved()
        self._begin()
        at = self._pad()
        # The runs again: padding the cursor's line may have moved them.
        pieces = []
        for a, b in reversed(self._block_runs()):
            pieces.append(self.buffer.delete(a, b))
            at = shifted(at, "delete", a, b)
        text = "".join(reversed(pieces))
        stop = self.buffer.insert(at, text)
        self.block = (at, stop)
        self._go(at)
        self._end()
        return True

    def _block_lines(self) -> range:
        """The lines the block touches; a stream block ending at a line's start
        does not touch that line."""
        if self.column_block is not None:
            top, _, bottom, _ = self.rectangle
            return range(top, min(bottom, len(self.document) - 1) + 1)
        start, end = self.block
        last = end.line - 1 if end.index == 0 and end.line > start.line else end.line
        return range(start.line, last + 1)

    async def on_indent_block(self, event: IndentBlock) -> bool:
        """^K I (``IndentBlock``, ``EDITOR.PAS:299``): a blank at column 0 of every line
        of the block, an empty one too, whatever kind of block it is; a column
        block's corners stay where they were, as DN put ``Mark`` back.

        Tab's (*stop*, a departure) puts a tab stop's width of blanks at a column
        block's left column instead, and leaves empty lines alone.
        """
        if not event.stop:
            block = self.block
            corners = self.column_block
            self._moved()
            self._begin()
            for number in self._block_lines():
                self.buffer.insert(Pos(number, 0), " ")
            if block is not None and block[0].index == 0 and self.block is not None:
                self.block = (Pos(block[0].line, 0), self.block[1])
            if corners is not None:
                self.column_block = corners
            self._end()
            return True
        left = self.rectangle[1] if self.column_block is not None else 0
        blanks = " " * (self.tab_size if event.stop else 1)
        if event.stop and self.insert_tabs and self.column_block is None:
            # *Tab characters*: a tab before each line.  A rectangle keeps
            # blanks, a tab in it widening by where it lands.
            blanks = "\t"
        block = self.block
        self._moved()
        self._begin()
        for number in self._block_lines():
            text = self.document.lines[number]
            index = self._painted_insert(number, left, blanks) if self.column_block is not None else None
            if index is not None:
                self.buffer.insert(Pos(number, index), blanks)
                continue
            index, past = columns.index_at(text, left, self.tab_size)
            if not past and index < len(text):
                self.buffer.insert(Pos(number, index), blanks)
        if block is not None and block[0].index == 0:
            # The blank went before the block's first character, and into it.
            self.block = (Pos(block[0].line, 0), self.block[1])
        self._end()
        return True

    def _painted_insert(self, number: int, left: int, blanks: str) -> int | None:
        """Where in line *number* *blanks* go so that they are painted at column
        *left*, what was painted there pushed along to the right; None on a
        line that reads as written (the column is the text's, as ever) or past
        its painted end.

        A column block's left edge is a painted column.  On a line Hebrew or
        Arabic reorders the character painted there may be read either way,
        so the blanks are tried before it and after it in the text, the line
        laid out each time, and the place that paints them nearest the edge
        wins -- on it, or else the closer; even, before a left-to-right
        character, after a right-to-left one, which is where they would go
        between letters of its own kind.

        On a right-to-left line, right-aligned (:func:`_laid_line`), the
        blanks go in just left of the edge instead: what is painted from the
        edge on stays where it is, and the rest of the line grows to the left.
        """
        text = self.document.lines[number]
        tab = self.tab_size
        row, order, shift = self._laid(number)
        if order is None or not 0 <= left - shift < len(order):
            return None
        at = left - shift
        while at > 0 and order[at][1] == "":
            at -= 1  # the second half of a wide character: its owner
        start = row[order[at][0]][1]
        stop = start + 1
        while stop < len(text) and unicodedata.combining(text[stop]):
            stop += 1
        wanted = left - len(blanks) if shift else left
        best: tuple[int, int] | None = None  # (distance, index)
        for index in ((stop, start) if text_rtl(text[start]) else (start, stop)):
            new = text[:index] + blanks + text[index:]
            cells, laid, moved = _laid_line(new, tab, self.width, len(new))
            if laid is None:
                continue
            put = sorted(
                moved + x for x, (column, shown) in enumerate(laid)
                if shown and index <= cells[column][1] < index + len(blanks)
            )
            if not put:
                continue
            distance = abs(put[0] - wanted)
            if best is None or distance < best[0]:
                best = (distance, index)
        return best[1] if best is not None else (stop if text_rtl(text[start]) else start)

    def _blank_at(self, number: int, left: int) -> bool:
        """Whether line *number* has a blank at column *left* that an unindent can take."""
        text = self.document.lines[number]
        index, past = columns.index_at(text, left, self.tab_size)
        return not past and index < len(text) and text[index] in " \t"

    def _text_column(self, number: int, painted: int) -> int:
        """The text's column of what line *number* paints at column *painted*:
        a column block's left edge, for an unindent -- the cell left of it on
        a right-to-left line, where an indent put its blank (_painted_insert)."""
        row, order, shift = self._laid(number)
        if order is None:
            return painted
        at = painted - shift - (1 if shift else 0)
        if at < 0:
            return len(row) - 1 - at  # left of a right-aligned line: past its end
        if at >= len(order):
            return len(row) + at - len(order)
        return order[at][0]

    async def on_unindent_block(self, event: UnindentBlock) -> bool:
        """^K U (``UnIndentBlock``, ``EDITOR.PAS:280``): column 0 out of every line of
        the block, whatever kind of block it is -- or nothing at all unless every
        line with text starts with a blank.  A leading tab gives way to one
        column fewer of spaces.

        Shift+Tab's (*stop*) takes out up to a tab stop's width of columns,
        one at a time the same way, so a line with fewer blanks loses those it has.
        With the cursor outside the block, or no block, it unindents the
        cursor's line instead, the cursor moving left with its text.
        """
        if not event.stop:
            lines = [n for n in self._block_lines() if self.document.lines[n]]
            if not lines or any(self.document.lines[n][0] not in " \t" for n in lines):
                return True
            corners = self.column_block
            self._moved()
            self._begin()
            for number in lines:
                text = self.document.lines[number]
                width = columns.advance(text[0], 0, self.tab_size)
                self.buffer.delete(Pos(number, 0), Pos(number, 1))
                if width > 1:
                    self.buffer.insert(Pos(number, 0), " " * (width - 1))
            if corners is not None:
                self.column_block = corners
            self._end()
            return True
        alone = event.stop and not self._cursor_in_block()
        if alone:
            lines, left = range(self.line, min(self.line + 1, len(self.document))), 0
        else:
            lines = self._block_lines()
            left = self.rectangle[1] if self.column_block is not None else 0
        # A column block's left edge is a painted column (_rect_spans): the
        # blank taken is the one painted there, wherever the text has it.
        painted = self.column_block is not None and not alone

        def column(number: int) -> int:
            return self._text_column(number, left) if painted else left

        if not any(self._blank_at(number, column(number)) for number in lines):
            # Nothing indented: no edit, and the typing run before goes on.
            return True
        self._moved()
        self._begin()
        taken = 0
        for number in lines:
            taken = 0
            for _ in range(self.tab_size if event.stop else 1):
                text = self.document.lines[number]
                index, past = columns.index_at(text, column(number), self.tab_size)
                if past or index >= len(text) or text[index] not in " \t":
                    break
                width = columns.advance(text[index], columns.column_of(text, index, self.tab_size),
                                        self.tab_size)
                self.buffer.delete(Pos(number, index), Pos(number, index + 1))
                if width > 1:
                    self.buffer.insert(Pos(number, index), " " * (width - 1))
                taken += 1
        if alone and taken:
            self._go_column(self.line, max(0, self.col - taken))
        self._end()
        return True

    @staticmethod
    def _word_span(text: str, i: int, j: int) -> tuple[int, int]:
        """``ChangeBlockCase``'s widening (``EDITOR.PAS:741-752``): *i* back to its
        word's start when it stands in a word, *j* on to its word's end unless
        it is a line's start.  DN's start stopped on the break before the word;
        here on the word, which changes nothing a case change can see and keeps
        a block from starting on a blank."""
        if i < len(text) and text[i] not in BREAK_CHARS:
            while i > 0 and text[i - 1] not in BREAK_CHARS:
                i -= 1
        if j > 0:
            while j < len(text) and text[j] not in BREAK_CHARS:
                j += 1
        return i, j

    def _recase(self, change: Callable[[str], str]) -> None:
        """The block's text through *change*, widened to whole words as
        ``ChangeBlockCase`` did: a stream block keeps the widened extent, a column
        block its corners (``ChangeVertBlockCase`` put ``Mark`` back)."""
        self._moved()
        self._begin()
        if self.column_block is not None:
            top, left, bottom, right = self.rectangle
            corners = self.column_block
            for number in self._block_lines():
                spans = sorted(self._rect_spans(number, left, right)[0])
                if spans:
                    text = self.document.lines[number]
                    first, _ = self._word_span(text, spans[0][0], spans[0][0])
                    _, last = self._word_span(text, spans[-1][1], spans[-1][1])
                    spans[0] = (first, spans[0][1])
                    spans[-1] = (spans[-1][0], last)
                for i, j in reversed(spans):
                    text = self.document.lines[number]
                    new = change(text[i:j])
                    if new != text[i:j]:
                        self.buffer.delete(Pos(number, i), Pos(number, j))
                        self.buffer.insert(Pos(number, i), new)
            self.column_block = corners
        elif self.block is not self._painted_block or self._block_runs() == [tuple(self.block)]:
            # The block as one stretch of text: no line it crosses is reordered.
            painted = self.block is self._painted_block
            start, end = self.block
            index, _ = self._word_span(self._text(start.line), start.index, start.index)
            start = Pos(start.line, index)
            if end.index > 0:
                _, index = self._word_span(self._text(end.line), end.index, end.index)
                end = Pos(end.line, index)
            old = self.document.text(start, end)
            new = change(old)
            if new != old:
                self.buffer.delete(start, end)
                end = self.buffer.insert(start, new)
            self.block = (start, end)
            if painted:
                self._painted_block = self.block  # still the cursor's, as it was
        else:
            # A reordered line's lit runs are no one span of text, so they are
            # not widened to whole words (a departure from ChangeBlockCase).
            # What is lit, each stretch on its own, and the block still marked
            # between its ends -- moved where a stretch grew or shrank (``ß``
            # to ``SS``): after one by the difference, inside one (a caret on a
            # reordered line can be) by what precedes it, recased.
            ends = list(self.block)
            for start, end in reversed(self._block_runs()):
                old = self.document.text(start, end)
                new = change(old)
                if new == old:
                    continue
                inside = {
                    k: Pos(at.line, head.index + len(change(self.document.text(head, at))))
                    for k, at in enumerate(ends) if start < at < end
                    for head in (start if at.line == start.line else Pos(at.line, 0),)
                }
                self.buffer.delete(start, end)
                stop = self.buffer.insert(start, new)
                ends = [
                    inside[k] if k in inside
                    else Pos(stop.line, stop.index + at.index - end.index) if at.line == end.line and at >= end
                    else at
                    for k, at in enumerate(ends)
                ]
            self.block = self._painted_block = (ends[0], ends[1]) if ends[0] < ends[1] else None
        self._end()

    async def on_sort_block(self, event: SortBlock) -> bool:
        """``SortBlock`` (``EDITOR.PAS``): the lines the column block spans, ordered by
        what stands in its columns.

        Only a column block says which columns; a stream block is told so, as
        ``ErrMsg(dlED_VertNeed)`` told it.  The keys compare as strings, case
        and all, as Pascal's ``<`` compared them.  Each line keeps the ending of
        the place it lands in.  Two departures: a stable sort, where DN's
        quicksort could swap lines whose keys are equal, and an undo, where DN
        threw its undo record away.
        """
        if self.column_block is None:
            from navml.widgets.dialog.dialog import Dialog

            app = self.application
            if app is not None:
                self.spawn(Dialog(title=tr("Error"), prompt=tr("Vertical blocks need for this operation"),
                              buttons="ok").execute(app))
            return True
        top, left, bottom, right = self.rectangle
        lines = self.document.lines
        bottom = min(bottom, len(lines) - 1)
        if bottom <= top:
            return True
        tab = self.tab_size

        keys = {
            number: "".join(lines[number][i:j] for i, j in self._rect_spans(number, left, right)[0])
            for number in range(top, bottom + 1)
        }
        old = lines[top:bottom + 1]
        new = [lines[number] for number in sorted(range(top, bottom + 1), key=keys.__getitem__)]
        if new == old:
            return True
        endings = self.document.endings[top:bottom]
        text = "".join(line + ending for line, ending in zip(new, endings)) + new[-1]
        corners = self.column_block
        self._moved()
        self._begin()
        self.buffer.delete(Pos(top, 0), Pos(bottom, len(lines[bottom])))
        self.buffer.insert(Pos(top, 0), text)
        self.column_block = corners
        self._end()
        return True

    async def on_calc_block(self, event: CalcBlock) -> bool:
        """``CalcBlock`` (``EDITOR.PAS``): the numbers in the column block's columns,
        added up and put on the clipboard (``cmPutInClipboard``), the text
        untouched -- the sum is pasted where it is wanted.  A stream block gets
        ``dlED_VertNeed``, as for Sort."""
        app = self.application
        if self.column_block is None:
            from navml.widgets.dialog.dialog import Dialog

            if app is not None:
                self.spawn(Dialog(title=tr("Error"), prompt=tr("Vertical blocks need for this operation"),
                              buttons="ok").execute(app))
            return True
        top, left, bottom, right = self.rectangle
        lines = self.document.lines
        pieces = []
        for number in range(top, min(bottom, len(lines) - 1) + 1):
            spans = self._rect_spans(number, left, right)[0]
            pieces.append("".join(lines[number][i:j] for i, j in spans))
        if app is not None:
            app.copy_to_clipboard(block_sum(pieces))
        return True

    async def on_upcase_block(self, event: UpcaseBlock) -> bool:
        self._recase(str.upper)
        return True

    async def on_lowcase_block(self, event: LowcaseBlock) -> bool:
        self._recase(str.lower)
        return True

    async def on_capitalize_block(self, event: CapitalizeBlock) -> bool:
        self._recase(capitalize)
        return True

    # -- the word's or the line's case ----------------------------------------------------

    def _recase_here(self, change: Callable[[str], str], *, line: bool) -> None:
        """The case of the word at the cursor, or of the whole *line*: DN's
        ``cmUpWord`` .. ``cmCapString``.

        Nothing on a blank line.  The line loses its trailing blanks either way.
        The word runs back from the cursor to a ``BREAK_CHARS`` character and on
        to the next, so one just behind the cursor counts.  The cursor stays;
        one undo step.
        """
        text = self._text()
        if not text.strip(" "):
            return
        kept = text.rstrip(" ")
        if line:
            new = change(kept)
        else:
            index = min(self._mark_pos().index, len(kept))
            start = index
            while start and kept[start - 1] not in BREAK_CHARS:
                start -= 1
            stop = start
            while stop < len(kept) and kept[stop] not in BREAK_CHARS:
                stop += 1
            new = kept[:start] + change(kept[start:stop]) + kept[stop:]
        if new == text:
            return
        number, col = self.line, self.col
        self._moved()
        self._begin()
        self.buffer.delete(Pos(number, 0), Pos(number, len(text)))
        self.buffer.insert(Pos(number, 0), new)
        self._end()
        self._go_column(number, col)

    async def on_up_word(self, event: UpWord) -> bool:
        self._recase_here(str.upper, line=False)
        return True

    async def on_low_word(self, event: LowWord) -> bool:
        self._recase_here(str.lower, line=False)
        return True

    async def on_cap_word(self, event: CapWord) -> bool:
        self._recase_here(capitalize, line=False)
        return True

    async def on_up_string(self, event: UpString) -> bool:
        self._recase_here(str.upper, line=True)
        return True

    async def on_low_string(self, event: LowString) -> bool:
        self._recase_here(str.lower, line=True)
        return True

    async def on_cap_string(self, event: CapString) -> bool:
        self._recase_here(capitalize, line=True)
        return True

    def block_indicator(self) -> tuple[int, int]:
        """Where ``(↔)``/``(↕)`` stands in :attr:`info_text`, end exclusive: what a
        click switches -- ``TInfoLine``'s ``Length(S)+7 .. Length(S)+9``, worked out
        from the text itself because the code before it may be longer than three."""
        _ = self.info_text
        return self._block_at
