"""^K R and ^K W's text, ^Q D and ^Q T, the editor's switches (indent, highlight, wrap, tabs...)
and the clipboard.

A mixin of :class:`FileEditor` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``file_editor.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from navigator.widgets.editor.commands import (
    SwitchHiColumn,
    SwitchHiLine,
    SwitchHighLight,
    SwitchHiddenChars,
    SwitchFill,
    SwitchTabs,
    SwitchLineNumbers,
    SwitchSoftWrap,
    SwitchBack,
    SwitchIndent,
    IndentOn,
    IndentOff,
    SwitchBrackets,
    SwitchSave,
    SwitchWrap,
    InsertDate,
    InsertTime,
    Clear,
    ClipboardCopy,
    ClipboardCut,
    ClipboardPaste,
    SwitchInsert,
    InsertOn,
    InsertOff,
    SwitchBlock,
)
from navigator.lib.editor import columns
from navigator.lib.editor.document import BREAK, NEWLINES, Pos
from navigator.lib.config import country
from navigator.settings import SETTINGS
from navigator.widgets.editor.file_editor.helpers import _now

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navigator.widgets.editor.file_editor.file_editor_surface import FileEditor as _Base
else:
    from navkit.widget import Mixin as _Base


class Switches(_Base):
    """^K R and ^K W's text, ^Q D and ^Q T, the editor's switches (indent, highlight, wrap, tabs...)"""

    # -- ^K R and ^K W: the window asks for the file; these are the text ------

    def block_file_text(self) -> str:
        """The block as ^K W writes it: DN's ``BlockWrite``.

        Lines joined by the Editor setup's *Line divisor*, the file's own breaks
        notwithstanding, and none after the last.  A column block -- or a stream
        block on one line, which is the same thing -- gives each line's columns
        as they stand, cut short where a line is, never padded.
        """
        return NEWLINES[SETTINGS.editor.line_divisor].join(self.filled(self.block_lines()))

    def block_lines(self) -> list[str]:
        """The block line by line, DN's ``GetSelection``: a stream block's lines from
        its start to its end, a column block's columns of each line, unpadded."""
        if self.column_block is not None:
            top, left, bottom, right = self.rectangle
            lines = []
            for number in range(top, bottom + 1):
                text = self.document.lines[number] if number < len(self.document) else ""
                lines.append("".join(text[i:j] for i, j in self._rect_spans(number, left, right)[0]))
            return lines
        if self.block is None:
            return []
        return BREAK.split(self._block_raw())

    def read_block(self, text: str) -> None:
        """^K R's text at the cursor: DN's ``BlockRead``, which turned column blocks
        off (``VertBlock := Off``) and marked what it put in (``InsertBlock``).

        In the file's own line breaks; the cursor stays at the start.
        """
        text = BREAK.sub(self.document.newline, text)
        self._moved()
        self._begin()
        self.column_block = None
        self.vertical_blocks = False
        self.block_hidden = False
        at = self._pad()
        end = self.buffer.insert(at, text)
        self.block = (at, end) if at < end else None
        self._go(at)
        self._end()

    # -- ^Q D and ^Q T -------------------------------------------------------------

    def _insert_now(self, text: str) -> None:
        """The date or the time in *Country support*'s format (a custom date
        included; the time with its seconds, DN's ``Time (H:M:S)``), inserted
        at the cursor, never typed over what is there even in overwrite, and
        the block left alone, as ``InsertDateTime`` left it."""
        self._moved()
        self._begin()
        end = self.buffer.insert(self._pad(), text)
        self._go(end)
        self._end()

    async def on_insert_date(self, event: InsertDate) -> bool:
        self._insert_now(country.format_date(_now()))
        return True

    async def on_insert_time(self, event: InsertTime) -> bool:
        self._insert_now(country.format_time(_now(), seconds=True))
        return True

    async def on_switch_indent(self, event: SwitchIndent) -> bool:
        """``cmSwitchIndent``: ``AutoIndent := not AutoIndent``."""
        self.auto_indent = not self.auto_indent
        return True

    async def on_indent_on(self, event: IndentOn) -> bool:
        """``cmIndentOn``: ``AutoIndent := On`` -- a macro's, set whatever it was."""
        self.auto_indent = True
        return True

    async def on_indent_off(self, event: IndentOff) -> bool:
        """``cmIndentOff``: ``AutoIndent := Off``."""
        self.auto_indent = False
        return True

    async def on_switch_back(self, event: SwitchBack) -> bool:
        """``cmSwitchBack``: ``BackIndent := not BackIndent``."""
        self.back_indent = not self.back_indent
        return True

    async def on_switch_hi_line(self, event: SwitchHiLine) -> bool:
        """``cmSwitchHiLine``: ``HiliteLine := not HiliteLine``."""
        self.highlight_line = not self.highlight_line
        return True

    async def on_switch_hi_column(self, event: SwitchHiColumn) -> bool:
        """``cmSwitchHiColumn``: ``HiliteColumn := not HiliteColumn``."""
        self.highlight_column = not self.highlight_column
        return True

    async def on_switch_high_light(self, event: SwitchHighLight) -> bool:
        """``cmSwitchHighLight``: ``HiLite := not HiLite``."""
        self.syntax_highlight = not self.syntax_highlight
        return True

    async def on_switch_hidden_chars(self, event: SwitchHiddenChars) -> bool:
        """Editor > Options > *Show hidden characters*: a departure."""
        self.show_hidden = not self.show_hidden
        return True

    async def on_switch_soft_wrap(self, event: SwitchSoftWrap) -> bool:
        """*Soft wrap* (not DN's): long lines on as many rows as they need, or
        back to one row a line and sideways scrolling.  Refused under column
        blocks (:meth:`refusal`)."""
        if self.vertical_blocks:
            return True
        self.soft_wrap = not self.soft_wrap
        self.left = 0
        self.top_row = 0
        self._goal = None
        self._follow()
        return True

    async def on_switch_line_numbers(self, event: SwitchLineNumbers) -> bool:
        """*Line numbers* (not DN's): the gutter shown or hidden for this editor."""
        self.line_numbers = not self.line_numbers
        return True

    async def on_switch_tabs(self, event: SwitchTabs) -> bool:
        """*Tab characters* (not DN's): ``insert_tabs`` switched for this editor."""
        self.insert_tabs = not self.insert_tabs
        return True

    async def on_switch_fill(self, event: SwitchFill) -> bool:
        """``cmSwitchFill``: ``OptimalFill := not OptimalFill``."""
        self.optimal_fill = not self.optimal_fill
        return True

    async def on_switch_brackets(self, event: SwitchBrackets) -> bool:
        """``cmSwitchBrackets``: ``AutoBrackets := not AutoBrackets``."""
        self.auto_brackets = not self.auto_brackets
        return True

    async def on_switch_save(self, event: SwitchSave) -> bool:
        """``cmSwitchSave``: ``AutoWrap := not AutoWrap``."""
        self.autowrap = not self.autowrap
        return True

    async def on_switch_wrap(self, event: SwitchWrap) -> bool:
        """``cmSwitchWrap``: ``AutoJustify := not AutoJustify``."""
        self.justify_on_wrap = not self.justify_on_wrap
        return True

    async def on_switch_block(self, event: SwitchBlock) -> bool:
        """``cmSwitchBlock``: ``VertBlock := not VertBlock``.

        DN's block was two points whichever kind it was, so the one marked
        stays and is read the other way: a stream block becomes the rectangle
        between its ends, a rectangle the stream from its top-left to its
        bottom-right.  One that would enclose nothing goes.  Hidden stays hidden.
        """
        tab = self.tab_size
        lines = self.document.lines
        if self.block is not None:
            start, end = self.block
            first = (start.line, self._painted_column(start))
            last = (end.line, self._painted_column(end))
            self.block = None
            self.column_block = (first, last) if first[1] != last[1] else None
        elif self.column_block is not None:
            top, left, bottom, right = self.rectangle
            bottom = min(bottom, len(lines) - 1)

            def place(line: int, col: int) -> Pos:
                col = self._logical_column(line, col)
                return Pos(line, min(columns.index_at(lines[line], col, tab)[0], len(lines[line])))

            start, end = place(min(top, bottom), left), place(bottom, right)
            self.column_block = None
            self.block = (start, end) if start < end else None
        if not self.marked:
            self.block_hidden = False
        self.vertical_blocks = not self.vertical_blocks
        return True

    async def on_clipboard_copy(self, event: ClipboardCopy) -> bool:
        self._copy_block()
        return True

    async def on_clipboard_cut(self, event: ClipboardCut) -> bool:
        await self.on_clipboard_copy(ClipboardCopy())
        self._delete_block()
        return True

    async def on_clear(self, event: Clear) -> bool:
        self._delete_block()
        return True

    async def on_clipboard_paste(self, event: ClipboardPaste) -> bool:
        """Ask for the clipboard; it arrives as a paste, which :meth:`on_paste` types."""
        app = self.application
        if app is not None:
            app.request_clipboard()
        return True

    async def on_switch_insert(self, event: SwitchInsert) -> bool:
        self.overwrite = not self.overwrite
        return True

    async def on_insert_on(self, event: InsertOn) -> bool:
        """``cmInsertOn``: ``InsertMode := On`` -- a macro's, set whatever it was."""
        self.overwrite = False
        return True

    async def on_insert_off(self, event: InsertOff) -> bool:
        """``cmInsertOff``: ``InsertMode := Off``."""
        self.overwrite = True
        return True
