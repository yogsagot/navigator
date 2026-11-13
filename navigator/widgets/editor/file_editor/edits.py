"""Edits: typing and inserting, new lines, tabs, deleting, undo and redo, and the keys the table
cannot name.

A mixin of :class:`FileEditor` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``file_editor.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from navkit import commands
from navkit.events import KeyEvent, PasteEvent

from navigator.widgets.editor.commands import (
    CloseFindBar,
    DuplicateLine,
    IndentBlock,
    SelectAll,
    DeleteBack,
    DeleteChar,
    DeleteLine,
    DeleteToEnd,
    DeleteWordLeft,
    DeleteWordRight,
    InsertLine,
    NewLine,
    TabKey,
    Undo,
    Redo,
)
from navigator.lib.editor import columns
from navigator.lib.editor.document import BREAK, Pos
from navigator.lib.editor.search import BREAK_CHARS
from navigator.settings import SETTINGS
from navigator.widgets.editor.file_editor.helpers import _COLUMN_CLIP

if TYPE_CHECKING:
    from navigator.widgets.editor.file_editor.file_editor import FileEditor as _Base
else:
    from navkit.widget import Mixin as _Base


class Edits(_Base):
    """Edits: typing and inserting, new lines, tabs, deleting, undo and redo, and the keys the table"""

    # -- edits -------------------------------------------------------------------

    def _begin(self, merge: str | None = None) -> None:
        self._edit_here()
        self.buffer.begin((self.line, self.col), merge)

    @staticmethod
    def _overwrites_blocks() -> bool:
        """DN's ``EdOpt and (ebfPbl + ebfObl) = ebfObl``: *Overwrite blocks* on and
        *Persistent blocks* off, the one pair under which an edit takes the block."""
        editor = SETTINGS.editor
        return editor.overwrite_blocks and not editor.persistent_blocks

    def _cursor_in_block(self) -> bool:
        """Whether the cursor stands in the shown block, either end included.

        A stream block runs from its start to its end in the text; a column
        block is its rectangle, the column just past its right edge counting as
        that edge, where Shift+Right leaves the cursor.
        """
        if not self.has_block:
            return False
        rectangle = self.rectangle
        if rectangle is not None:
            top, left, bottom, right = rectangle
            painted = self._visual_column(self.line, self.col)
            return top <= self.line <= bottom and left <= painted <= right
        here = self._mark_pos()
        return any(start <= here <= end for start, end in self._block_runs())

    def _takes_block(self) -> bool:
        """Whether an edit at the cursor replaces the block instead.

        DN's rule, :meth:`_overwrites_blocks`, and -- a departure, asked for --
        whenever the cursor stands in the block, whatever the setup says: what
        is typed or pasted there replaces it, and Del, Backspace or Enter there
        takes it, as a modern editor's selection does.
        """
        return self.has_block and (self._overwrites_blocks() or self._cursor_in_block())

    def _block_off(self) -> None:
        """``BlockOff``: with *Persistent blocks* off the block goes; on, it stays."""
        if not SETTINGS.editor.persistent_blocks:
            self._unmark()

    def _begin_typed(self, merge: str | None = None) -> None:
        """:meth:`_begin` what is typed or pasted: ``InputChar``'s and ``PasteBlock``'s
        ``DeleteBlock`` under :meth:`_overwrites_blocks`, then ``BlockOff``.

        A block taken goes in the same undo group as what replaces it, and
        starts a group of its own rather than joining a run of typing before it.
        """
        if self._takes_block():
            self._moved()
            self._begin(merge)
            self._take_block()
            return
        self._block_off()
        self._begin(merge)

    def _deleting_block(self) -> bool:
        """Del's ``DeleteBlock`` under :meth:`_takes_block`: the block alone.

        Otherwise the block goes (``BlockOff``, with *Persistent blocks* off)
        and Del deletes as ever."""
        if self._takes_block():
            self._delete_block()
            return True
        self._block_off()
        return False

    def _end(self) -> None:
        self.buffer.end()
        self.revision += 1
        self._follow()

    def _pad(self) -> Pos:
        """The cursor as a place in the text, blanks written up to it first.

        Turbo Vision's cursor may stand past a line's end; typing there fills
        the gap with blanks, which is what DN's ``WorkString`` held anyway.
        """
        index, past = self._index()
        if past:
            self.buffer.insert(Pos(self.line, index), " " * past)
            index += past
        return Pos(self.line, index)

    def type_text(self, text: str) -> None:
        """Characters typed at the cursor, inserted or over what is there.

        Typed at or past the right margin with *Auto wrap* on, the line then
        wraps (:meth:`_wrap`), as ``InputChar`` called ``SplitString`` once
        ``LastX >= RightSide``.
        """
        column = self.col
        pair = self._bracket_pair(text)
        self._begin_typed("type")
        at = self._pad()
        if self.overwrite:
            line = self._text()
            stop = min(len(line), at.index + len(text))
            self.buffer.delete(at, Pos(at.line, stop))
        end = self.buffer.insert(at, pair or text)
        self._go(Pos(at.line, at.index + 1) if pair else end)
        self._end()
        if self.autowrap and column >= self.margins[1]:
            self._wrap()

    #: ``InputChar``'s three pairs.
    BRACKET_PAIRS = {"(": "()", "{": "{}", "[": "[]"}

    def _bracket_pair(self, text: str) -> str | None:
        """The pair *AutoBrackets* types for *text*, or None.

        Only in insert mode -- overwrite put the character alone -- and only at
        the line's end or before a blank (``LastX >= WL`` or a ``' '`` there), so
        a bracket typed in front of a word stays single.
        """
        if not self.auto_brackets or self.overwrite or text not in self.BRACKET_PAIRS:
            return None
        index, past = self._index()
        line = self._text()
        if past or index >= len(line) or line[index] == " ":
            return self.BRACKET_PAIRS[text]
        return None

    def _wrap(self) -> None:
        """``SplitString``: the cursor's line split at the margin, an undo step of its own."""
        from navigator.lib.editor.paragraph import wrap_line

        left, right, _ = self.margins
        text = self._text()
        split = wrap_line(text, self._mark_pos().index, left=left, right=right,
                          justify=self.justify_on_wrap)
        if split is None:
            return
        head, tail, (down, index) = split
        line = self.line
        self._moved()
        self._begin()
        self.buffer.delete(Pos(line, 0), Pos(line, len(text)))
        self.buffer.insert(Pos(line, 0), head + self.document.newline + tail)
        self._end()
        self._go(Pos(line + down, index))

    def insert_text(self, text: str) -> None:
        """A paste: line breaks become the file's own, the cursor after what went in.

        A departure, asked for: DN's ``InsertBlock(..., On)`` marked the paste and
        left the cursor at its start; here nothing is marked, as in a modern editor.

        Text a column block was copied as goes back in as a rectangle
        (:meth:`_insert_rectangle`) -- and so does any text while *Vertical
        blocks* is on, cut at its breaks, as ``InsertBlock`` put every paste
        in under ``VertBlock``.  In overwrite a rectangle's pieces replace
        their width of each line.
        """
        pieces = _COLUMN_CLIP.get(BREAK.sub("\n", text))
        if pieces is None and self.vertical_blocks:
            pieces = BREAK.sub("\n", text).split("\n")
            if len(pieces) > 1 and pieces[-1] == "":
                pieces.pop()  # the break after the last line ends it, it is not a line
        if pieces is not None:
            self._insert_rectangle(pieces)
            return
        text = BREAK.sub(self.document.newline, text)
        self._begin_typed()
        end = self.buffer.insert(self._pad(), text)
        self._go(end)
        self._end()

    def _insert_rectangle(self, pieces: list[str]) -> None:
        """Each piece at the cursor's column, one line under another.

        Short lines are padded out to the column and lines are added past the
        text's end; a piece with nothing after it loses its padding.  The
        cursor stays at the top-left corner.
        """
        self._begin_typed()
        line, col = self.line, self.col
        self._put_rectangle(pieces, line, col, replace=self.overwrite)
        self._go_column(line, col)
        self._end()

    def _put_rectangle(self, pieces: list[str], line: int, col: int, *, replace: bool = False) -> None:
        """:meth:`_insert_rectangle`'s edits, inside a group the caller opened.

        *replace* (overwrite) first takes each piece's width of its line from
        *col* on, as ``InsertBlock``'s ``Delete(S2, Delta.X+1, Length(S1))``."""
        for offset, piece in enumerate(pieces):
            number = line + offset
            if number >= len(self.document):
                self.buffer.insert(self.document.end, self.document.newline)
            text = self.document.lines[number]
            index, past = columns.index_at(text, col, self.tab_size)
            if replace and index < len(text):
                end, _ = columns.index_at(text, col + columns.width(piece, self.tab_size), self.tab_size)
                self.buffer.delete(Pos(number, index), Pos(number, end))
                text = self.document.lines[number]
            if index >= len(text):
                piece = piece.rstrip(" ")
                if not piece:
                    continue
            if past:
                self.buffer.insert(Pos(number, index), " " * past)
                index += past
            self.buffer.insert(Pos(number, index), piece)

    async def on_new_line(self, event: NewLine) -> bool:
        """``MakeEnter``.

        In overwrite, no split: the cursor to the next line's start, a line
        added past the last.  Inserting, the line is split at the cursor, the
        part kept losing its trailing blanks and the part moved down the line's
        last ones.  With *Autoindent* the moved part's leading blanks give way to
        the indent of the part kept -- of the whole line, if that part is blank
        -- and the cursor goes to it; without, it moves as it is and the cursor
        to its start.  A new line with nothing after its indent is left empty,
        the cursor waiting at the indent, as DN's trimmed it once left.  Tabs
        count as blanks in the trimming, as they do in the indent: DN, which
        expanded tabs, only ever had spaces to trim.

        A departure: with *Autoindent*, a line of nothing but blanks gives the
        cursor's column -- its own blanks up to the cursor, then the virtual
        columns past its end -- so Enter after Enter stays at the indent, where
        DN's had no text to take one from and went back to the start.  The new
        line is still left empty.

        Inserting with the cursor in the block, the block goes first and the
        break takes its place, one undo step (:meth:`_cursor_in_block`, a
        departure).
        """
        if self.overwrite:
            self._moved()
            if self.line == len(self.document) - 1:
                self._begin()
                self.buffer.insert(self.document.end, self.document.newline)
                self._end()
            self._go_column(self.line + 1, 0)
            return True
        if self._cursor_in_block():
            self._moved()
            self._begin()
            self._take_block()
        else:
            self._block_off()
            self._begin()
        line = self.line
        indent = self._split_line()
        self._go_column(line + 1, indent)
        self._end()
        return True

    def _split_line(self) -> int:
        """``MakeEnter``'s split at the cursor, inside a group the caller opened
        (see :meth:`on_new_line`): the column the moved part's text starts in."""
        index, past = self._index()
        text = self._text()
        line = self.line
        at = min(index, len(text))
        kept = text[:at].rstrip(" \t")
        moved = text[at:].rstrip(" \t")
        indent = ""
        lead = 0
        if self.auto_indent:
            lead = len(moved) - len(moved.lstrip(" \t"))
            moved = moved[lead:]
            if not text.strip(" \t"):
                start = columns.width(text[:at], self.tab_size)
                virtual = columns.fill(start, start + past, self.tab_size) if self.insert_tabs else " " * past
                indent = text[:at] + virtual
            else:
                source = kept if kept.strip(" \t") else text
                indent = source[:len(source) - len(source.lstrip(" \t"))]
        # Right to left, so each edit leaves the places of the next alone.
        end = len(text.rstrip(" \t"))
        if end > at:
            self.buffer.delete(Pos(line, end), Pos(line, len(text)))
        else:
            self.buffer.delete(Pos(line, at), Pos(line, len(text)))
        if lead:
            self.buffer.delete(Pos(line, at), Pos(line, at + lead))
        self.buffer.insert(Pos(line, at), self.document.newline + (indent if moved else ""))
        if len(kept) < at:
            self.buffer.delete(Pos(line, len(kept)), Pos(line, at))
        return columns.width(indent, self.tab_size)

    async def on_duplicate_line(self, event: DuplicateLine) -> bool:
        """``cmDuplicateLine``: ``FileLines^.AtInsert(LastY+1, GetLine(LastY))``, one undo
        step.  The copy is put after the line's own text, so the line keeps its
        ending and the copy takes the file's usual break before it."""
        line, col = self.line, self.col
        text = self._text()
        self._moved()
        self._begin()
        self.buffer.insert(Pos(line, len(text)), self.document.newline + text)
        self._end()
        self._go_column(line, col)
        return True

    async def on_insert_line(self, event: InsertLine) -> bool:
        """``cmInsLine``: ``BlockOff``, then ``MakeEnter`` with the cursor put back.

        Inserting, Enter's split (:meth:`_split_line`: the part kept losing
        its trailing blanks, the part moved its indent under *Autoindent*),
        the cursor staying where it was.  In overwrite ``MakeEnter`` splits
        nothing: on the last line an empty one is added after it, elsewhere
        nothing happens.  A block is let go, never taken (``BlockOff``).
        """
        line, col = self.line, self.col
        self._block_off()
        self._moved()
        if self.overwrite:
            if line == len(self.document) - 1:
                self._begin()
                self.buffer.insert(self.document.end, self.document.newline)
                self._end()
            self._go_column(line, col)
            return True
        self._begin()
        self._split_line()
        self._end()
        self._go_column(line, col)
        return True

    async def on_tab_key(self, event: TabKey) -> bool:
        """``DoTab``: blanks to under the next word of the line above
        (:func:`~navigator.lib.editor.columns.smart_tab`) -- or, on the first
        line or past the end of the one above, ``MakeTab``'s next stop; over
        them, not in, in overwrite.

        With the cursor in the block, ^K I by a tab stop instead
        (:meth:`on_indent_block`) -- a departure, asked for, as Shift+Tab is ^K U.
        """
        if self._cursor_in_block():
            return await self.on_indent_block(IndentBlock(stop=True))
        stop = self._tab_stop()
        if self.overwrite:
            self._overwrite_tab(stop)
            return True
        self._begin("type")
        # Again: a block replaced has moved the cursor to where it began.
        stop = self._tab_stop()
        if self.insert_tabs:
            # From where the text really ends, past it: no blanks before the tabs.
            index, past = self._index()
            self.buffer.insert(Pos(self.line, index), columns.fill(self.col - past, stop, self.tab_size))
        else:
            at = self._pad()
            self.buffer.insert(at, " " * (stop - self.col))
        self._go_column(self.line, stop)
        self._end()
        return True

    def _overwrite_tab(self, stop: int) -> None:
        """``InsertSpace`` in overwrite: each column crossed inside the text made
        a blank -- a character crossed becomes as many blanks as it is wide,
        so the columns after it stay -- and past the end the cursor just goes
        on, nothing written, as DN's ``Inc(LastX)`` left it (the next
        character typed pads to it)."""
        text = self._text()
        start, _ = columns.index_at(text, self.col, self.tab_size)
        end, _ = columns.index_at(text, stop, self.tab_size)
        # A character straddling the stop is crossed too: its columns before it.
        if end < len(text) and columns.column_of(text, end, self.tab_size) < stop:
            end += 1
        crossed = text[start:end]
        if crossed and crossed.strip(" "):
            first = columns.column_of(text, start, self.tab_size)
            last = columns.column_of(text, end, self.tab_size)
            self._begin("type")
            self.buffer.delete(Pos(self.line, start), Pos(self.line, end))
            self.buffer.insert(Pos(self.line, start), " " * (last - first))
            self._end()
        else:
            self._moved()
        self._go_column(self.line, stop)

    def _tab_stop(self) -> int:
        """Where Tab takes the cursor: under the line above as ``DoTab`` reads
        it, else the next multiple of the tab size (``MakeTab``)."""
        if self.line > 0:
            smart = columns.smart_tab(self.document.lines[self.line - 1], self.col, self.tab_size)
            if smart is not None:
                return smart
        return (self.col // self.tab_size + 1) * self.tab_size

    def _unindent(self) -> bool:
        """``MakeBack``'s ``BackIndent``: back to the indent of a line above.

        Only on a line's first character -- blanks before the cursor and none
        under it -- or anywhere on an all-blank line, and not on the first line.
        The nearest line above with text and a narrower indent says how far;
        the blanks before the cursor become that many spaces, as DN wrote
        them.  No such line, and Backspace is the plain one.  A departure: a
        tab counts as indentation by its width, where DN had expanded tabs on
        loading and met only spaces.
        """
        if not self.back_indent or self.line == 0:
            return False
        text = self._text()
        index, past = self._index()
        before = text[:min(index, len(text))]
        blank_line = not text.strip(" \t")
        if before.strip(" \t"):
            return False
        if not blank_line and (past or index >= len(text) or text[index] in " \t"):
            return False
        if not past and columns.column_of(text, index, self.tab_size) != self.col:
            return False
        target = None
        for line in range(self.line - 1, -1, -1):
            above = self._text(line)
            if above.strip(" \t"):
                indent = columns.width(above[:len(above) - len(above.lstrip(" \t"))], self.tab_size)
                if indent < self.col:
                    target = indent
                    break
        if target is None:
            return False
        self._begin("back")
        cut = min(index, len(text))
        if cut:
            self.buffer.delete(Pos(self.line, 0), Pos(self.line, cut))
        if target and not blank_line:
            blanks = columns.fill(0, target, self.tab_size) if self.insert_tabs else " " * target
            self.buffer.insert(Pos(self.line, 0), blanks)
        self._go_column(self.line, target)
        self._end()
        return True

    async def on_delete_back(self, event: DeleteBack) -> bool:
        """``MakeBack``: the character before the cursor, or the line break.

        In the line's leading blanks, under the Editor setup's *Backspace
        unindents*, :meth:`_unindent` instead.  With the cursor in the block,
        the block alone (:meth:`_cursor_in_block`, a departure); elsewhere it
        is not taken, and with *Persistent blocks* off only goes (``BlockOff;
        MakeBack``).
        """
        if self._cursor_in_block():
            self._delete_block()
            return True
        # ``cmDelBackChar: BlockOff; MakeBack``: Backspace never takes the block.
        self._block_off()
        if self._unindent():
            return True
        index, past = self._index()
        if past:
            self._moved()
            self._go_column(self.line, self.col - 1)
            return True
        if self.overwrite:
            self._overwrite_back(index)
            return True
        text = self._text()
        at_boundary = columns.column_of(text, index, self.tab_size) == self.col
        if at_boundary and index == 0:
            if self.line == 0:
                return True
            self._begin("back")
            previous = Pos(self.line - 1, len(self._text(self.line - 1)))
            self.buffer.delete(previous, Pos(self.line, 0))
            self._go(previous)
            self._end()
            return True
        start = index - 1 if at_boundary else index
        self._begin("back")
        self.buffer.delete(Pos(self.line, start), Pos(self.line, start + 1))
        self._go(Pos(self.line, start))
        self._end()
        return True

    def _overwrite_back(self, index: int) -> None:
        """``MakeBack`` in overwrite: at column 0 nothing -- no join -- and
        otherwise the character before the cursor made blanks as wide as it
        (``udReplaceChar``), the cursor a column left.  A tab is blank already:
        the cursor alone moves."""
        if self.col == 0:
            return
        text = self._text()
        at_boundary = columns.column_of(text, index, self.tab_size) == self.col
        start = index - 1 if at_boundary else index
        char = text[start] if 0 <= start < len(text) else " "
        if char in " \t":
            self._moved()
            self._go_column(self.line, self.col - 1)
            return
        wide = columns.advance(char, columns.column_of(text, start, self.tab_size), self.tab_size)
        self._begin("back")
        self.buffer.delete(Pos(self.line, start), Pos(self.line, start + 1))
        self.buffer.insert(Pos(self.line, start), " " * wide)
        self._end()
        self._go_column(self.line, columns.column_of(self._text(), start, self.tab_size))

    async def on_delete_char(self, event: DeleteChar) -> bool:
        """``MakeDel``: the character under the cursor, or join the next line.

        With *Overwrite blocks* on and *Persistent blocks* off, a marked block alone.
        """
        if self._deleting_block():
            return True
        index, past = self._index()
        text = self._text()
        if index < len(text) and not past:
            self._begin("del")
            self.buffer.delete(Pos(self.line, index), Pos(self.line, index + 1))
            self._end()
            return True
        if self.line + 1 >= len(self.document):
            return True
        self._begin("del")
        self._join_next()
        self._end()
        return True

    def _join_next(self) -> None:
        """``MakeDel`` at a line's end: the next line joined on, blanks written up to the cursor first."""
        at = self._pad()
        self.buffer.delete(at, Pos(self.line + 1, 0))

    async def on_delete_word_left(self, event: DeleteWordLeft) -> bool:
        """``cmDelWordLeft`` (``MICROED.PAS:3160``): blanks, then the word before them, on this line alone.

        At column 0, after punctuation, or on an empty line it is Backspace (``MakeBack``), so it joins
        only at the line's start and takes one ``.`` at a time: ``foo. |`` keeps ``foo.``.
        """
        index, past = self._index()
        text = self._text()
        if past:
            if not text:
                return await self.on_delete_back(DeleteBack())
            index = len(text)
        if index == 0 or (text[index - 1] in BREAK_CHARS and text[index - 1] != " "):
            return await self.on_delete_back(DeleteBack())
        start = index
        while start > 0 and text[start - 1] == " ":
            start -= 1
        while start > 0 and text[start - 1] not in BREAK_CHARS:
            start -= 1
        self._begin()
        self.buffer.delete(Pos(self.line, start), Pos(self.line, index))
        self._go(Pos(self.line, start))
        self._end()
        return True

    async def on_delete_word_right(self, event: DeleteWordRight) -> bool:
        """``cmDelWordRight``: the word and the blanks after it, or the line break.

        At a line's end (``MICROED.PAS:3140``) the next line is joined on and its leading blanks
        go with the break -- and an empty line joined leaves the end there, so the next is joined too.
        """
        index, past = self._index()
        text = self._text()
        if past or index >= len(text):
            if self.line + 1 >= len(self.document):
                return True
            self._begin()
            self._join_next()
            while True:
                index, _ = self._index()
                text = self._text()
                if index >= len(text) and self.line + 1 < len(self.document):
                    self._join_next()
                elif index < len(text) and text[index] == " ":
                    self.buffer.delete(Pos(self.line, index), Pos(self.line, index + 1))
                else:
                    break
            self._end()
            return True
        stop = index
        if text[stop] in BREAK_CHARS and text[stop] != " ":
            stop += 1
        else:
            while stop < len(text) and text[stop] not in BREAK_CHARS:
                stop += 1
            while stop < len(text) and text[stop] == " ":
                stop += 1
        self._begin()
        self.buffer.delete(Pos(self.line, index), Pos(self.line, stop))
        self._end()
        return True

    async def on_delete_line(self, event: DeleteLine) -> bool:
        """``cmDeleteLine`` (DN's ``DeleteLine``, ``MICROED.PAS:2389``): the line and its break, the
        cursor to its start; the last line is only emptied.  Presses on one line are one undo step,
        as ``udDelLine`` gathered them."""
        last = len(self.document) - 1
        if self.line < last:
            self._begin(f"delline:{self.line}")
            self.buffer.delete(Pos(self.line, 0), Pos(self.line + 1, 0))
        else:
            self._begin()
            self.buffer.delete(Pos(self.line, 0), Pos(self.line, len(self._text())))
        self._go_column(self.line, 0)
        self._end()
        return True

    async def on_delete_to_end(self, event: DeleteToEnd) -> bool:
        index, past = self._index()
        text = self._text()
        if past or index >= len(text):
            return True
        self._begin()
        self.buffer.delete(Pos(self.line, index), Pos(self.line, len(text)))
        self._end()
        return True

    async def on_undo(self, event: Undo) -> bool:
        self._edit_here()
        before = self.buffer.undo()
        if before is not None:
            self.revision += 1
            self._go_column(*before)
        return True

    async def on_redo(self, event: Redo) -> bool:
        """The cursor where the group redone ended, as other editors leave it."""
        self._edit_here()
        after = self.buffer.redo()
        if after is not None:
            self.revision += 1
            self._go(after)
        return True

    async def on_select_all(self, event: SelectAll) -> bool:
        """The whole text as the block -- a departure: DN's editor had no
        *Select all*, and the context menu offers it as every editor's does.
        A column block, while vertical blocks are on, as wide as the widest
        line."""
        self._unmark()
        lines = self.document.lines
        last = len(lines) - 1
        if self.vertical_blocks:
            width = max(columns.width(text, self.tab_size) for text in lines)
            if width:
                self.column_block = ((0, 0), (last, width))
        else:
            self._set_block(Pos(0, 0), Pos(last, len(lines[last])))
        return True

    # -- keys the table cannot name ------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if event.is_printable:
            self.type_text(event.char)
            return True
        if event.matches("escape") and self.highlight_query is not None and self.application is not None:
            # Esc puts the Find bar away while its matches are lit, before the
            # window's Esc closes the window.  Not a key of this table: it
            # would shadow the window's.
            return await commands.run(self.application, CloseFindBar, self)
        return False

    async def on_paste(self, event: PasteEvent) -> bool:
        if event.text:
            self.insert_text(event.text)
        return True
