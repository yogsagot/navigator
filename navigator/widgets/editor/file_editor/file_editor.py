"""F4's text: DOS Navigator's ``TFileEditor``, editing what ``navigator.editor`` holds.

**Written in Python alone**, as ``FileViewer`` is: everything it shows is
painted, and the window around it, ``EditWindow``, is the half with markup.

**Its state is the cursor, the view and one counter.**  ``line`` and ``col``
are the cursor -- a line, and a *column* on screen, which may lie past the
line's end as it could in DN -- and ``top`` and ``left`` are the first line
and column shown.  The text itself is a great deal of mutable state that
changes together, so ``revision`` stands in for all of it, the way
``Console.revision`` stands for a console's screen: every edit bumps it, and
everything painted from the text reads it.

**Every key is a command**, bound in :attr:`FileEditor.keys` from ``DN.DNR``'s
``EDITOR COMMANDS`` table and handled here under DN's own name.  The table
is the editor's rather than the window's because DN's was too: ``LoadCommands``
filled ``TFileEditor``'s, and the window's status line only captioned some.
What is left to :meth:`on_key` is what the table could not name -- a
printable character.
"""

from __future__ import annotations

import functools
import re
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Awaitable, Callable

from navkit.capabilities import GLYPHS_UNICODE
from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent, PasteEvent
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navml.widgets.dialog.static_text import StaticText

from navigator.widgets.editor.commands import (
    DuplicateLine,
    SwitchDrawMode,
    SwitchBack,
    SwitchIndent,
    SwitchBrackets,
    SwitchSave,
    SwitchWrap,
    FCenter,
    FJustify,
    FLeft,
    FRight,
    Replace,
    ReverseSearch,
    StartSearch,
    AsciiTable,
    GotoLineNumber,
    BracketPair,
    PrintBlock,
    CalcBlock,
    SortBlock,
    GotoMarker,
    PlaceMarker,
    BlockRead,
    BlockWrite,
    InsertDate,
    InsertTime,
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
    Clear,
    ClipboardCopy,
    ClipboardCut,
    ClipboardPaste,
    DeleteBack,
    DeleteChar,
    DeleteLine,
    DeleteToEnd,
    DeleteWordLeft,
    DeleteWordRight,
    InsertLine,
    LineEnd,
    LineStart,
    MoveDown,
    MoveLeft,
    MoveRight,
    MoveUp,
    NewLine,
    PageDown,
    PageUp,
    ScreenBottom,
    ScreenTop,
    ScrollDown,
    ScrollUp,
    SwitchInsert,
    TabKey,
    TextEnd,
    TextStart,
    Undo,
    SwitchBlock,
    WordLeft,
    WordRight,
)
from navigator.editor import columns
from navigator.editor.buffer import EditBuffer
from navigator.editor.document import BREAK, NEWLINES, Document, Pos, shifted
from navigator.editor.save import write_file
from navigator.editor import search
from navigator.editor.search import BREAK_CHARS, SearchData
from navigator.fileattr import DATE_FORMAT, TIME_FORMAT
from navigator.settings import SETTINGS


#: How many lines one wheel notch moves the view.
WHEEL_ROWS = 3

#: The text of the last column block copied, with the padded pieces it was
#: copied from: a paste of exactly that text goes in as a rectangle.  Shared
#: by every editor, as the clipboard is, and holding only the newest copy.
_COLUMN_CLIP: dict[str, list[str]] = {}


def _wordstar(prefix: str, letters: dict[str, Any]) -> dict[str, Any]:
    """*prefix* then each key, and then each letter with Ctrl held too, as WordStar took them."""
    table = {}
    for key, command in letters.items():
        table[f"{prefix} {key}"] = command
        if len(key) == 1 and key.isalpha():
            table[f"{prefix} ctrl+{key}"] = command
    return table


def _now() -> time.struct_time:
    """The time ^Q D and ^Q T write; a function so a test can fix it."""
    return time.localtime()


#: What Pascal's ``Val`` reads as a real: a sign, digits with a point, an exponent.
_NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


def block_sum(pieces: list[str]) -> str:
    """``CalcBlock``'s sum of *pieces*, each with its blanks removed (``DelSpaces``).

    A piece that is not a number counts as nothing, as ``Val``'s failure left
    0.  Written as ``Str(R:0:20)`` was, its trailing zeros and point cut --
    but added exactly, where DN's 6-byte ``Real`` would print 0.1 + 0.2 with
    its binary error.
    """
    total = Decimal(0)
    for piece in pieces:
        text = piece.replace(" ", "")
        if _NUMBER.fullmatch(text):
            try:
                total += Decimal(text)
            except InvalidOperation:
                pass
    written = format(total, "f")
    if "." in written:
        written = written.rstrip("0").rstrip(".")
    return "0" if written in ("", "-0") else written


#: A word, for Capitalize: letters and digits, not the underscore.
_WORD = re.compile(r"[^\W_]+")


def _marking(
    handler: Callable[[Any, Any], Awaitable[bool]],
) -> Callable[[Any, Any], Awaitable[bool]]:
    """A movement that, with its command's *extend* (Shift), drags the block along.

    The block grows from wherever the cursor stood unless that was one of the
    block's ends, in which case the other end stays put: Shift+Right then
    Shift+Left takes back what the first marked.  Without Shift, and with the
    Editor setup's *Persistent blocks* off, the block goes.
    """

    @functools.wraps(handler)
    async def moving(self: Any, event: Any) -> bool:
        before = self._here()
        done = await handler(self, event)
        if getattr(event, "extend", False):
            self._extend_block(before)
        elif not SETTINGS.editor.persistent_blocks:
            self._unmark()
        return done

    return moving


class FileEditor(Widget):
    """The inside of an editor window: a text, its cursor, and the keys that edit it."""

    #: ``CFileEditor``'s ten colours, by what they paint.  Only *selected*
    #: is drawn yet; the rest are named so a sheet can carry them.
    parts = (
        "selected",
        "comment",
        "symbol",
        "string",
        "number",
        "current_line",
        "current_line_selected",
        "current_line_comment",
        "current_column",
    )

    #: ``EDITOR COMMANDS``, the keys that need no second one.  A binding with
    #: Shift is the same movement dragging a block along.
    keys = {
        "left": MoveLeft,
        "ctrl+s": MoveLeft,
        "shift+left": MoveLeft(extend=True),
        "right": MoveRight,
        "ctrl+d": MoveRight,
        "shift+right": MoveRight(extend=True),
        "up": MoveUp,
        "ctrl+e": MoveUp,
        "shift+up": MoveUp(extend=True),
        "down": MoveDown,
        "ctrl+x": MoveDown,
        "shift+down": MoveDown(extend=True),
        "ctrl+left": WordLeft,
        "ctrl+a": WordLeft,
        "ctrl+shift+left": WordLeft(extend=True),
        "ctrl+right": WordRight,
        "ctrl+f": WordRight,
        "ctrl+shift+right": WordRight(extend=True),
        "home": LineStart,
        "shift+home": LineStart(extend=True),
        "end": LineEnd,
        "shift+end": LineEnd(extend=True),
        "pageup": PageUp,
        "ctrl+r": PageUp,
        "shift+pageup": PageUp(extend=True),
        "pagedown": PageDown,
        "ctrl+c": PageDown,
        "shift+pagedown": PageDown(extend=True),
        "ctrl+home": ScreenTop,
        "ctrl+shift+home": ScreenTop(extend=True),
        "ctrl+end": ScreenBottom,
        "ctrl+shift+end": ScreenBottom(extend=True),
        "ctrl+pageup": TextStart,
        "ctrl+shift+pageup": TextStart(extend=True),
        "ctrl+pagedown": TextEnd,
        "ctrl+shift+pagedown": TextEnd(extend=True),
        "ctrl+w": ScrollUp,
        "ctrl+z": ScrollDown,
        "enter": NewLine,
        "ctrl+enter": NewLine,
        "ctrl+m": NewLine,
        "ctrl+n": InsertLine,
        "tab": TabKey,
        "ctrl+i": TabKey,
        "backspace": DeleteBack,
        "ctrl+h": DeleteBack,
        "delete": DeleteChar,
        "ctrl+g": DeleteChar,
        "ctrl+backspace": DeleteWordLeft,
        "ctrl+t": DeleteWordRight,
        "ctrl+y": DeleteLine,
        "insert": SwitchInsert,
        "ctrl+v": SwitchInsert,
        "alt+backspace": Undo,
        # ``cmCut``, ``cmCopy``, ``cmPaste`` and ``cmClear``: Turbo Vision's
        # keys, since Ctrl+C and Ctrl+V are WordStar's here.
        "shift+delete": ClipboardCut,
        "ctrl+insert": ClipboardCopy,
        "shift+insert": ClipboardPaste,
        "ctrl+delete": Clear,
        "alt+h": HideBlock,
        "alt+t": SortBlock,
        "alt+insert": CalcBlock,
        "alt+g": GotoLineNumber,
        "f4": SwitchDrawMode,
        "f6": DuplicateLine,
        "ctrl+p": AsciiTable,
        "alt+left": BracketPair,
        "alt+right": BracketPair,
        "alt+j": FJustify,
        "alt+r": FRight,
        "alt+l": FLeft,
        "alt+c": FCenter,
        **_wordstar("ctrl+b", {
            "v": SwitchBlock,
            "j": FJustify,
            "r": FRight,
            "l": FLeft,
            "c": FCenter,
        }),
        # ``EDITOR COMMANDS``' two-key half: WordStar's Ctrl+K and Ctrl+Q.
        **_wordstar("ctrl+k", {
            "b": BlockStart,
            "k": BlockEnd,
            "h": HideBlock,
            "c": CopyBlock,
            "v": MoveBlock,
            "y": Clear,
            "i": IndentBlock,
            "u": UnindentBlock,
            "[": UpcaseBlock,
            "]": LowcaseBlock,
            "\\": CapitalizeBlock,
            "t": MarkWord,
            "l": MarkLine,
            "s": SortBlock,
            "p": PrintBlock,
            "r": BlockRead,
            "w": BlockWrite,
            # ``^K'1'`` to ``^K'9'``: the digit alone, as the table has it.
            **{str(n): PlaceMarker(n) for n in range(1, 10)},
        }),
        **_wordstar("ctrl+q", {
            "b": MoveBlockStart,
            "k": MoveBlockEnd,
            "y": DeleteToEnd,
            "l": Undo,
            "d": InsertDate,
            "t": InsertTime,
            "f": StartSearch,
            "a": Replace,
            "r": ReverseSearch,
            # ``^Q'['`` and ``^Q^]``, as the table has them, neither with the other's form.
            "[": BracketPair,
            **{str(n): GotoMarker(n) for n in range(1, 10)},
            "m": SwitchDrawMode,
            # ``^Q^M``: Ctrl+M is Enter on a terminal that cannot tell them apart.
            "enter": SwitchDrawMode,
        }),
        "ctrl+q ctrl+]": BracketPair,
    }

    #: What typing reaches: the command line's Enter, Home, End and Tab step
    #: aside while this holds the keyboard.  See ``Shell.enables``.
    edits_text = True

    #: The file, or None for a text never saved.
    path: Path | None = reactive(None)

    #: One counter standing for the whole text.
    revision: int = reactive(0)

    #: The cursor: a line, and a column on screen.
    line: int = reactive(0)
    col: int = reactive(0)

    #: The first line and column shown.
    top: int = reactive(0)
    left: int = reactive(0)

    #: Overwrite rather than insert: the ``:overwrite`` state, which gives the
    #: caret DN's ``BlockCursor``.
    overwrite: bool = reactive(False)

    #: Column blocks rather than stream ones: DN's ``VertBlock``.
    vertical_blocks: bool = reactive(False)

    #: ``AutoWrap``: a line typed past the right margin wraps; ``AutoJustify``:
    #: the line it leaves is widened to the margin.  Seeded from the Editor
    #: setup, switched for this editor alone from Editor > Options.
    autowrap: bool = reactive(False)
    justify_on_wrap: bool = reactive(False)

    #: ``AutoBrackets``: an opening bracket typed with its partner after it.
    auto_brackets: bool = reactive(False)

    #: ``AutoIndent``: Enter indents the new line; ``BackIndent``: Backspace on
    #: a line's first character goes back to an indent above.  Seeded from the
    #: Editor setup, switched for this editor alone from Editor > Options.
    auto_indent: bool = reactive(True)
    back_indent: bool = reactive(True)

    #: ``DrawMode``: 0 off, 1 single lines, 2 double.  While on, the arrows
    #: draw (with Shift), erase (with Ctrl) or only move (:meth:`_draw_key`).
    draw_mode: int = reactive(0)

    #: The marked stream block, its start before its end, or None: from one
    #: place in the text to another.  It stays when the cursor moves, as
    #: DN's *Persistent blocks* kept it, and follows the edits made around it
    #: (:meth:`_follow_edit`).
    block: tuple[Pos, Pos] | None = reactive(None)

    #: The marked column block, or None: two opposite corners as screen
    #: cells ``(line, col)``, the one marking started from first.  Columns,
    #: not string indices, because a rectangle runs past short lines' ends
    #: and across tabs; :attr:`rectangle` is what it covers.  Only one of the
    #: two blocks is ever marked, the one :attr:`vertical_blocks` says.
    column_block: tuple[tuple[int, int], tuple[int, int]] | None = reactive(None)

    #: ``not BlockVisible``: the block marked but hidden by ^K H / Alt+H.  It is
    #: neither painted nor acted on, follows the edits all the same, and shows
    #: again at a second ^K H or as soon as anything marks.
    block_hidden: bool = reactive(False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._use(EditBuffer())
        #: Where a Tab stops, and how far a tab character reaches.
        self.tab_size = SETTINGS.editor.tab_size
        self.vertical_blocks = SETTINGS.editor.vertical_blocks
        self.autowrap = SETTINGS.editor.autowrap
        self.auto_brackets = SETTINGS.editor.auto_brackets
        self.auto_indent = SETTINGS.editor.auto_indent
        self.back_indent = SETTINGS.editor.backspace_unindents
        self.justify_on_wrap = SETTINGS.editor.justify_on_wrap
        #: ``LeftSide``, ``RightSide`` and ``InSide``: this editor's margins and
        #: paragraph indent, seeded from the Editor setup and changed by
        #: *Format Margins* for this editor alone, as ``SetFormat`` did.
        self.margins = (
            SETTINGS.editor.left_margin, SETTINGS.editor.right_margin, SETTINGS.editor.paragraph,
        )
        # In __init__, not the class body: a plain class attribute would
        # shadow the reactive descriptor, as `Console` learned.
        self.can_focus = True
        #: The match the last search showed, and the cursor and text it was shown
        #: for: ``SearchActive``'s highlight lasts only while both stand.
        self._found: tuple[Pos, Pos] | None = None
        self._found_for: tuple[int, int, int] | None = None
        #: The block indicator's and the line:column's places in the info line,
        #: set as it is written.
        self._block_at = (0, 0)
        self._place_at = (0, 0)
        self._code_at = (0, 0)
        #: The block's fixed end while the left button drags, else None: a
        #: ``Pos``, or a ``(line, col)`` cell for a column block.
        self._drag_from: Any = None
        #: ``LastDir``: where the pen came into the cell it is on, or None.
        self._pen: int | None = None
        #: DN's ``MarkPos``: markers 1 to 9, each a ``(line, col)`` or None.
        #: Fixed places, as DN's were -- an edit above one does not move it.
        self.markers: list[tuple[int, int] | None] = [None] * 9
        #: ^K B or ^K K pressed with no block marked: the end it set, and
        #: whether it was the start, waiting for the other.  Any edit drops it.
        self._half_mark: tuple[Any, bool] | None = None

    # -- the file ----------------------------------------------------------------

    def open(self, path: Path | str, *, new: bool = False) -> None:
        """Edit *path* from its start.  Raises ``OSError`` if it cannot be read.

        With *new*, a file that does not exist is an empty text that saving
        will create -- Shift+F4's *Edit new file*.  A text with no line break
        to follow, new or not, breaks lines as the Editor setup's *Line
        divisor* says.
        """
        path = Path(path)
        try:
            document = Document.load(path)
        except FileNotFoundError:
            if not new:
                raise
            document = Document()
        self.use_document(path, document)

    def use_document(self, path: Path | str, document: Document) -> None:
        """Edit *document*, already read from *path*, from its start.

        What :meth:`open` does once the file is read -- for a caller that read
        it on a thread (``navigator.widgets.editor.loading``).
        """
        path = Path(path)
        if not any(document.endings):
            document.newline = NEWLINES[SETTINGS.editor.line_divisor]
        self._use(EditBuffer(document))
        self._unmark()
        self.markers = [None] * 9
        self.path = path
        self.line = self.col = self.top = self.left = 0
        self.revision += 1

    def _use(self, buffer: EditBuffer) -> None:
        self.buffer = buffer
        buffer.listeners.append(self._follow_edit)

    def save(self) -> None:
        """Write the text to :attr:`path`, here and now.  Raises ``OSError``.

        The window writes on a thread instead (``EditWindow._write``), through
        :meth:`snapshot` and :meth:`saved`.
        """
        if self.path is None:
            raise OSError("no file name")
        write_file(self.path, self.buffer.document.encode())
        self.buffer.mark_saved()
        self.revision += 1

    def snapshot(self) -> tuple[list[str], list[str], object]:
        """The text as it is now, for a thread to write: lines, endings, and
        the point :meth:`saved` is to be given once it is written.

        Copies of the two lists, which edits change in place; the strings in
        them never change, so the copies are the text whatever is typed next.
        """
        document = self.buffer.document
        return list(document.lines), list(document.endings), self.buffer.save_point()

    def saved(self, point: object) -> None:
        """The text as :meth:`snapshot` took it is on disk now."""
        self.buffer.mark_saved(point)
        self.revision += 1

    @computed
    def modified(self) -> bool:
        self.revision
        return self.buffer.modified

    @property
    def document(self) -> Document:
        return self.buffer.document

    @computed
    def line_count(self) -> int:
        self.revision
        return len(self.buffer.document)

    # -- the cursor --------------------------------------------------------------

    def _text(self, line: int | None = None) -> str:
        return self.document.lines[self.line if line is None else line]

    def _index(self) -> tuple[int, int]:
        """The cursor as a string index, and the blanks it lies past the end."""
        return columns.index_at(self._text(), self.col, self.tab_size)

    def _pos(self) -> Pos:
        return Pos(self.line, self._index()[0])

    def _column(self, pos: Pos) -> int:
        return columns.column_of(self.document.lines[pos.line], pos.index, self.tab_size)

    def _go(self, pos: Pos) -> None:
        """Put the cursor on *pos*, a string index, and bring it into view."""
        self.line = pos.line
        self.col = self._column(pos)
        self._follow()

    def _go_column(self, line: int, col: int) -> None:
        self.line = max(0, min(line, len(self.document) - 1))
        self.col = max(0, col)
        self._follow()

    def _follow(self) -> None:
        """Scroll so the cursor is on screen: DN's ``ScrollTo``."""
        rows, cols = max(1, self.height), max(1, self.width)
        if self.line < self.top:
            self.top = self.line
        elif self.line >= self.top + rows:
            self.top = self.line - rows + 1
        if self.col < self.left:
            self.left = self.col
        elif self.col >= self.left + cols:
            self.left = self.col - cols + 1

    def layout(self, width: int, height: int) -> None:
        super().layout(width, height)
        self._follow()

    def _moved(self) -> None:
        """A movement ends the typing run an undo would take back together."""
        self.buffer.seal()

    # -- movements ---------------------------------------------------------------

    @_marking
    async def on_move_left(self, event: MoveLeft) -> bool:
        """One column left; over a tab or a wide character, to its start."""
        self._moved()
        index, past = self._index()
        text = self._text()
        if past or index >= len(text):
            self._go_column(self.line, self.col - 1)
        elif columns.column_of(text, index, self.tab_size) < self.col:
            self._go(Pos(self.line, index))
        elif index > 0:
            self._go(Pos(self.line, index - 1))
        return True

    @_marking
    async def on_move_right(self, event: MoveRight) -> bool:
        self._moved()
        index, past = self._index()
        text = self._text()
        if past or index >= len(text):
            self._go_column(self.line, self.col + 1)
        else:
            self._go(Pos(self.line, index + 1))
        return True

    @_marking
    async def on_move_up(self, event: MoveUp) -> bool:
        self._moved()
        self._go_column(self.line - 1, self.col)
        return True

    @_marking
    async def on_move_down(self, event: MoveDown) -> bool:
        self._moved()
        self._go_column(self.line + 1, self.col)
        return True

    @_marking
    async def on_line_start(self, event: LineStart) -> bool:
        self._moved()
        self._go_column(self.line, 0)
        return True

    @_marking
    async def on_line_end(self, event: LineEnd) -> bool:
        """``cmEnd``: after the last character that is not a blank."""
        self._moved()
        text = self._text()
        self._go(Pos(self.line, len(text.rstrip(" "))))
        return True

    @_marking
    async def on_page_up(self, event: PageUp) -> bool:
        self._moved()
        rows = max(1, self.height)
        self.top = max(0, self.top - rows)
        self._go_column(self.line - rows, self.col)
        return True

    @_marking
    async def on_page_down(self, event: PageDown) -> bool:
        self._moved()
        rows = max(1, self.height)
        last = len(self.document) - 1
        self.top = max(0, min(self.top + rows, last - rows + 1))
        self._go_column(self.line + rows, self.col)
        return True

    @_marking
    async def on_screen_top(self, event: ScreenTop) -> bool:
        self._moved()
        self._go_column(self.top, self.col)
        return True

    @_marking
    async def on_screen_bottom(self, event: ScreenBottom) -> bool:
        self._moved()
        self._go_column(self.top + max(1, self.height) - 1, self.col)
        return True

    @_marking
    async def on_text_start(self, event: TextStart) -> bool:
        self._moved()
        self._go_column(0, 0)
        return True

    @_marking
    async def on_text_end(self, event: TextEnd) -> bool:
        self._moved()
        self._go(self.document.end)
        return True

    async def on_scroll_up(self, event: ScrollUp) -> bool:
        """``cmScrollUp``: the view a line up; the cursor moves only to stay on it."""
        if self.top > 0:
            self._moved()
            self.top -= 1
            if self.line >= self.top + max(1, self.height):
                self.line -= 1
        return True

    async def on_scroll_down(self, event: ScrollDown) -> bool:
        if self.top < len(self.document) - 1:
            self._moved()
            self.top += 1
            if self.line < self.top:
                self.line = self.top
        return True

    def _word_left(self, pos: Pos) -> Pos:
        """DN's ``WordLeft``: to the start of this word or the one before."""
        lines = self.document.lines
        line, index = pos.line, min(pos.index, len(lines[pos.line]))
        while True:
            text = lines[line]
            if index > 0:
                while index > 0 and text[index - 1] in BREAK_CHARS:
                    index -= 1
                while index > 0 and text[index - 1] not in BREAK_CHARS:
                    index -= 1
                if index < len(text) and text[index] not in BREAK_CHARS:
                    return Pos(line, index)
            if line == 0:
                return Pos(0, 0)
            line -= 1
            index = len(lines[line])

    def _word_right(self, pos: Pos) -> Pos:
        """DN's ``WordRight``: to the start of the next word."""
        lines = self.document.lines
        line, index = pos.line, pos.index
        text = lines[line]
        started_inside = index < len(text)
        while index < len(text) and text[index] not in BREAK_CHARS:
            index += 1
        while index < len(text) and text[index] in BREAK_CHARS:
            index += 1
        if index < len(text) or (started_inside and index == len(text)):
            return Pos(line, index)
        while line + 1 < len(lines):
            line += 1
            text = lines[line]
            index = 0
            if text and text[0] not in BREAK_CHARS:
                return Pos(line, 0)
            while index < len(text) and text[index] in BREAK_CHARS:
                index += 1
            if index < len(text):
                return Pos(line, index)
        return Pos(line, len(text))

    @_marking
    async def on_word_left(self, event: WordLeft) -> bool:
        self._moved()
        self._go(self._word_left(self._pos()))
        return True

    @_marking
    async def on_word_right(self, event: WordRight) -> bool:
        self._moved()
        self._go(self._word_right(self._pos()))
        return True

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
        """The cursor as an end of the kind of block in force."""
        return (self.line, self.col) if self.vertical_blocks else self._mark_pos()

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
        block = self.block
        if block is not None:
            first = shifted(block[0], kind, start, end)
            last = shifted(block[1], kind, start, end, stay=True)
            self.block = (first, last) if first < last else None
        corners = self.column_block
        if corners is not None and end.line != start.line:
            def moved(cell: tuple[int, int]) -> tuple[int, int]:
                line, col = cell
                # A break typed at a line's very start pushes it down, block and all.
                return shifted(Pos(line, 0), kind, start, end).line, col
            self.column_block = (moved(corners[0]), moved(corners[1]))

    def _column_pieces(self) -> list[str]:
        """Each line's part of the column block, padded out to its width."""
        top, left, bottom, right = self.rectangle
        pieces = []
        for number in range(top, bottom + 1):
            text = self.document.lines[number] if number < len(self.document) else ""
            i, j = columns.span(text, left, right, self.tab_size)
            piece = text[i:j]
            shown = columns.column_of(text, j, self.tab_size) - columns.column_of(text, i, self.tab_size)
            pieces.append(piece + " " * max(0, (right - left) - shown))
        return pieces

    @property
    def block_text(self) -> str:
        """What the block holds, its line breaks plain ``\\n``: what a copy hands out.

        A column block's lines lose the blanks that only padded them out.
        """
        if self.column_block is not None:
            return "\n".join(piece.rstrip(" ") for piece in self._column_pieces())
        if self.block is None:
            return ""
        return BREAK.sub("\n", self.document.text(*self.block))

    def _take_block(self) -> None:
        """Delete the block inside an open group; the cursor to where it began."""
        if self.column_block is not None:
            top, left, bottom, right = self.rectangle
            for number in range(top, min(bottom, len(self.document) - 1) + 1):
                i, j = columns.span(self.document.lines[number], left, right, self.tab_size)
                self.buffer.delete(Pos(number, i), Pos(number, j))
            self.column_block = None
            self._go_column(top, left)
            return
        block = self.block
        if block is not None:
            self.buffer.delete(*block)
            self._go(block[0])

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
            self.column_block = ((line, col), (line + len(pieces) - 1, col + width))
            self._go_column(line, col)
        else:
            text = self.document.text(*self.block)
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
            if top <= line <= bottom and left <= col < right:
                return True
            pieces = self._column_pieces()
            self._moved()
            self._begin()
            self._take_block()
            if top <= line <= bottom and col >= right:
                col -= right - left
            self._put_rectangle(pieces, line, col)
            self.column_block = ((line, col), (line + len(pieces) - 1, col + right - left))
            self._go_column(line, col)
            self._end()
            return True
        start, end = self.block
        if start < self._mark_pos() < end:
            return True
        self._moved()
        self._begin()
        at = self._pad()
        start, end = self.block  # padding the cursor's line may have moved it
        text = self.buffer.delete(start, end)
        at = shifted(at, "delete", start, end)
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
        """^K I: a blank before each line of the block -- at its left column, for a column block."""
        left = self.rectangle[1] if self.column_block is not None else 0
        block = self.block
        self._moved()
        self._begin()
        for number in self._block_lines():
            text = self.document.lines[number]
            index, past = columns.index_at(text, left, self.tab_size)
            if not past and index < len(text):
                self.buffer.insert(Pos(number, index), " ")
        if block is not None and block[0].index == 0:
            # The blank went before the block's first character, and into it.
            self.block = (Pos(block[0].line, 0), self.block[1])
        self._end()
        return True

    async def on_unindent_block(self, event: UnindentBlock) -> bool:
        """^K U: one blank out of each line of the block where one stands there; a
        leading tab gives way to one column fewer of spaces."""
        left = self.rectangle[1] if self.column_block is not None else 0
        self._moved()
        self._begin()
        for number in self._block_lines():
            text = self.document.lines[number]
            index, past = columns.index_at(text, left, self.tab_size)
            if past or index >= len(text) or text[index] not in " \t":
                continue
            width = columns.advance(text[index], columns.column_of(text, index, self.tab_size),
                                    self.tab_size)
            self.buffer.delete(Pos(number, index), Pos(number, index + 1))
            if width > 1:
                self.buffer.insert(Pos(number, index), " " * (width - 1))
        self._end()
        return True

    def _recase(self, change: Callable[[str], str]) -> None:
        """The block's text through *change*, the block kept where it is."""
        self._moved()
        self._begin()
        if self.column_block is not None:
            top, left, bottom, right = self.rectangle
            corners = self.column_block
            for number in self._block_lines():
                text = self.document.lines[number]
                i, j = columns.span(text, left, right, self.tab_size)
                new = change(text[i:j])
                if new != text[i:j]:
                    self.buffer.delete(Pos(number, i), Pos(number, j))
                    self.buffer.insert(Pos(number, i), new)
            self.column_block = corners
        else:
            start, end = self.block
            old = self.document.text(start, end)
            new = change(old)
            if new != old:
                self.buffer.delete(start, end)
                end = self.buffer.insert(start, new)
                self.block = (start, end)
        self._end()

    #: ``dlED_VertNeed``, word for word.
    VERTICAL_NEEDED = "Vertical blocks need for this operation"

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
                self.spawn(Dialog(title="Error", prompt=self.VERTICAL_NEEDED, buttons="ok").execute(app))
            return True
        top, left, bottom, right = self.rectangle
        lines = self.document.lines
        bottom = min(bottom, len(lines) - 1)
        if bottom <= top:
            return True
        tab = self.tab_size

        def key(text: str) -> str:
            i, j = columns.span(text, left, right, tab)
            return text[i:j]

        old = lines[top:bottom + 1]
        new = sorted(old, key=key)
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
                self.spawn(Dialog(title="Error", prompt=self.VERTICAL_NEEDED, buttons="ok").execute(app))
            return True
        top, left, bottom, right = self.rectangle
        lines = self.document.lines
        pieces = []
        for number in range(top, min(bottom, len(lines) - 1) + 1):
            i, j = columns.span(lines[number], left, right, self.tab_size)
            pieces.append(lines[number][i:j])
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
        self._recase(lambda text: _WORD.sub(lambda m: m[0][:1].upper() + m[0][1:].lower(), text))
        return True

    # -- ^Q[: the bracket pair ---------------------------------------------------------

    #: What opens, mapped to what closes it: ``SearchFwd``'s three pairs.
    BRACKETS = {"(": ")", "[": "]", "{": "}"}

    def bracket_pair(self) -> Pos | None:
        """Where the bracket under the cursor is answered, or None.

        DN's ``SearchFwd`` and ``SearchBwd``: an opening bracket looks forward
        and a closing one back, line after line, counting only brackets of its
        own kind -- strings and comments are not told apart, as they were not.
        """
        index, past = self._index()
        text = self._text()
        if past or index >= len(text):
            return None
        char = text[index]
        lines = self.document.lines
        if char in self.BRACKETS:
            opener, closer, step = char, self.BRACKETS[char], 1
        elif char in self.BRACKETS.values():
            closer = char
            opener = next(o for o, c in self.BRACKETS.items() if c == char)
            step = -1
        else:
            return None
        depth = 0
        line, at = self.line, index
        while 0 <= line < len(lines):
            row = lines[line]
            while 0 <= at < len(row):
                if row[at] == opener:
                    depth += step
                elif row[at] == closer:
                    depth -= step
                if depth == 0:
                    return Pos(line, at)
                at += step
            line += step
            if 0 <= line < len(lines):
                at = 0 if step > 0 else len(lines[line]) - 1
        return None

    async def on_bracket_pair(self, event: BracketPair) -> bool:
        """``cmBracketPair``: the cursor to the bracket's pair, if it has one."""
        found = self.bracket_pair()
        if found is not None:
            self._moved()
            self._go(found)
        return True

    # -- F4: line drawing ---------------------------------------------------------------

    #: The keys ``DrawLine`` answered, and the direction each goes.
    DRAW_KEYS = {"up": 0, "right": 1, "down": 2, "left": 3, "e": 0, "d": 1, "x": 2, "s": 3}

    async def on_switch_draw_mode(self, event: SwitchDrawMode) -> bool:
        """``cmSwitchDrawMode``: off, single, double, off; the pen lifted."""
        self.draw_mode = (self.draw_mode + 1) % 3
        self._pen = None
        return True

    async def _run_key(self, event: KeyEvent) -> bool:
        """While drawing, the arrows (and ^E ^D ^X ^S) are ``DrawLine``'s before any
        command they are bound to: a key table hands a command on without the
        Shift or Ctrl that decide here between drawing, erasing and moving."""
        if self.draw_mode and self._draw_key(event):
            return True
        return await super()._run_key(event)

    def _draw_key(self, event: KeyEvent) -> bool:
        key = event.key
        direction = self.DRAW_KEYS.get(key)
        if direction is None or event.alt or (len(key) == 1 and not event.ctrl):
            return False
        if event.shift:
            how = "draw"
        elif event.ctrl:
            how = "erase"
        else:
            how = "move"
        self.draw_line(direction, how)
        return True

    def _cell(self, line: int, col: int) -> str:
        """The character in a cell, a blank past a line's end or outside the text."""
        if not 0 <= line < len(self.document) or col < 0:
            return " "
        text = self.document.lines[line]
        index, past = columns.index_at(text, col, self.tab_size)
        return " " if past or index >= len(text) else text[index]

    def _put(self, line: int, col: int, char: str) -> None:
        """*char* into a cell, the line padded out to it with blanks if short."""
        text = self.document.lines[line]
        index, past = columns.index_at(text, col, self.tab_size)
        if past or index >= len(text):
            self.buffer.insert(Pos(line, len(text)), " " * past + char)
        elif text[index] != char:
            self.buffer.delete(Pos(line, index), Pos(line, index + 1))
            self.buffer.insert(Pos(line, index), char)

    def draw_line(self, direction: int, how: str) -> None:
        """``DrawLine``: draw, erase or only move one cell *direction* (0 up, 1 right,
        2 down, 3 left).

        Drawing or erasing is skipped going straight back the way the pen came;
        either way the cursor then moves, a line added below the last, and the
        pen remembers the side it came in by.
        """
        from navigator.editor import linedraw

        line, col = self.line, self.col
        double = self.draw_mode == 2
        if how != "move" and self._pen != direction:
            up, down = self._cell(line - 1, col), self._cell(line + 1, col)
            left, right = self._cell(line, col - 1), self._cell(line, col + 1)
            self._moved()
            self._begin()
            if how == "draw":
                self._put(line, col, linedraw.drawn(
                    up, right, down, left, double=double, direction=direction, came=self._pen,
                ))
            else:
                for (y, x, char, arm) in ((line - 1, col, up, 4), (line + 1, col, down, 1),
                                         (line, col - 1, left, 2)):
                    new = linedraw.without_arm(char, arm) if 0 <= y < len(self.document) and x >= 0 else None
                    if new is not None:
                        self._put(y, x, new)
                self._put(line, col, " ")
                text = self.document.lines[line]
                if columns.width(text, self.tab_size) > col + 1:
                    new = linedraw.without_arm(right, 8)
                    if new is not None:
                        self._put(line, col + 1, new)
            self._end()
        self._moved()
        if direction == 0:
            self._go_column(line - 1, col)
        elif direction == 2:
            if line == len(self.document) - 1:
                self._begin()
                self.buffer.insert(self.document.end, self.document.newline)
                self._end()
            self._go_column(line + 1, col)
        elif direction == 1:
            self._go_column(line, col + 1)
        else:
            self._go_column(line, max(0, col - 1))
        if how != "move":
            self._pen = (direction + 2) % 4

    # -- ^K1-9 and ^Q1-9 -----------------------------------------------------------

    async def on_place_marker(self, event: PlaceMarker) -> bool:
        """``cmPlaceMarker``: the cursor's place, kept."""
        self.markers[event.marker - 1] = (self.line, self.col)
        return True

    @_marking
    async def on_goto_marker(self, event: GotoMarker) -> bool:
        """``cmGotoMarker``: the cursor to a marker that is set, in the middle of the
        window (``Pos := Delta - Size div 2``, then ``CenterScreen``).  A marker
        past a text that has since got shorter lands on its last line."""
        place = self.markers[event.marker - 1]
        if place is None:
            return True
        self._moved()
        line, col = place
        self._go_column(line, col)
        rows, cols = max(1, self.height), max(1, self.width)
        self.top = max(0, min(self.line - rows // 2, len(self.document) - 1))
        self.left = max(0, self.col - cols // 2)
        return True

    def markers_text(self) -> str:
        """The markers as the edit history keeps them: ``line:col`` nine times, empty where unset."""
        return ",".join("" if m is None else f"{m[0]}:{m[1]}" for m in self.markers)

    def restore_markers(self, text: str) -> None:
        """:meth:`markers_text`'s form read back; anything unreadable is unset."""
        markers: list[tuple[int, int] | None] = [None] * 9
        for index, part in enumerate(text.split(",")[:9]):
            line, _, col = part.partition(":")
            if line.isdigit() and col.isdigit():
                markers[index] = (int(line), int(col))
        self.markers = markers

    # -- ^K R and ^K W: the window asks for the file; these are the text ------

    def block_file_text(self) -> str:
        """The block as ^K W writes it: DN's ``BlockWrite``.

        Lines joined by the Editor setup's *Line divisor*, the file's own breaks
        notwithstanding, and none after the last.  A column block -- or a stream
        block on one line, which is the same thing -- gives each line's columns
        as they stand, cut short where a line is, never padded.
        """
        return NEWLINES[SETTINGS.editor.line_divisor].join(self.block_lines())

    def block_lines(self) -> list[str]:
        """The block line by line, DN's ``GetSelection``: a stream block's lines from
        its start to its end, a column block's columns of each line, unpadded."""
        if self.column_block is not None:
            top, left, bottom, right = self.rectangle
            lines = []
            for number in range(top, bottom + 1):
                text = self.document.lines[number] if number < len(self.document) else ""
                i, j = columns.span(text, left, right, self.tab_size)
                lines.append(text[i:j])
            return lines
        if self.block is None:
            return []
        return BREAK.split(self.document.text(*self.block))

    def read_block(self, text: str) -> None:
        """^K R's text at the cursor: DN's ``BlockRead``, which turned column blocks
        off (``VertBlock := Off``) and marked what it put in (``InsertBlock``).

        In the file's own line breaks; the cursor stays at the start.
        """
        text = BREAK.sub(self.document.newline, text)
        self._moved()
        self._begin_replacing()
        self.column_block = None
        self.vertical_blocks = False
        self.block_hidden = False
        at = self._pad()
        end = self.buffer.insert(at, text)
        self.block = (at, end) if at < end else None
        self._go(at)
        self._end()

    # -- ^Q D and ^Q T -------------------------------------------------------------

    def _insert_now(self, format: str) -> None:
        """The date or time in DN's ``Date (D-M-Y)``/``Time (H:M:S)`` form -- the
        attributes dialog's -- inserted at the cursor, never typed over what is
        there even in overwrite; with *Persistent blocks* off it replaces the block."""
        self._moved()
        self._begin_replacing()
        end = self.buffer.insert(self._pad(), time.strftime(format, _now()))
        self._go(end)
        self._end()

    async def on_insert_date(self, event: InsertDate) -> bool:
        self._insert_now(DATE_FORMAT)
        return True

    async def on_insert_time(self, event: InsertTime) -> bool:
        self._insert_now(TIME_FORMAT)
        return True

    async def on_switch_indent(self, event: SwitchIndent) -> bool:
        """``cmSwitchIndent``: ``AutoIndent := not AutoIndent``."""
        self.auto_indent = not self.auto_indent
        return True

    async def on_switch_back(self, event: SwitchBack) -> bool:
        """``cmSwitchBack``: ``BackIndent := not BackIndent``."""
        self.back_indent = not self.back_indent
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
            first = (start.line, columns.column_of(lines[start.line], start.index, tab))
            last = (end.line, columns.column_of(lines[end.line], end.index, tab))
            self.block = None
            self.column_block = (first, last) if first[1] != last[1] else None
        elif self.column_block is not None:
            top, left, bottom, right = self.rectangle
            bottom = min(bottom, len(lines) - 1)

            def place(line: int, col: int) -> Pos:
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

    # -- edits -------------------------------------------------------------------

    def _begin(self, merge: str | None = None) -> None:
        self.buffer.begin((self.line, self.col), merge)

    def _begin_replacing(self, merge: str | None = None) -> None:
        """:meth:`_begin` an edit that, with *Persistent blocks* off, replaces the block.

        The block goes in the same undo group as what replaces it, and starts
        a group of its own rather than joining a run of typing before it.
        """
        if SETTINGS.editor.persistent_blocks or not self.has_block:
            self._begin(merge)
            return
        self._moved()
        self._begin(merge)
        self._take_block()

    def _deleting_block(self) -> bool:
        """Backspace and Del with *Persistent blocks* off: the block, if any, and nothing else."""
        if SETTINGS.editor.persistent_blocks or not self.has_block:
            return False
        self._delete_block()
        return True

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
        self._begin_replacing("type")
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
        from navigator.editor.paragraph import wrap_line

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
        """A paste: line breaks become the file's own.

        Text a column block was copied as goes back in as a rectangle
        (:meth:`_insert_rectangle`).
        """
        pieces = _COLUMN_CLIP.get(BREAK.sub("\n", text))
        if pieces is not None:
            self._insert_rectangle(pieces)
            return
        text = BREAK.sub(self.document.newline, text)
        self._begin_replacing()
        end = self.buffer.insert(self._pad(), text)
        self._go(end)
        self._end()

    def _insert_rectangle(self, pieces: list[str]) -> None:
        """Each piece at the cursor's column, one line under another.

        Short lines are padded out to the column and lines are added past the
        text's end; a piece with nothing after it loses its padding.  The
        cursor stays at the top-left corner.
        """
        self._begin_replacing()
        line, col = self.line, self.col
        self._put_rectangle(pieces, line, col)
        self._go_column(line, col)
        self._end()

    def _put_rectangle(self, pieces: list[str], line: int, col: int) -> None:
        """:meth:`_insert_rectangle`'s edits, inside a group the caller opened."""
        for offset, piece in enumerate(pieces):
            number = line + offset
            if number >= len(self.document):
                self.buffer.insert(self.document.end, self.document.newline)
            text = self.document.lines[number]
            index, past = columns.index_at(text, col, self.tab_size)
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
        the cursor waiting at the indent, as DN's trimmed it once left.
        """
        if self.overwrite:
            self._moved()
            if self.line == len(self.document) - 1:
                self._begin()
                self.buffer.insert(self.document.end, self.document.newline)
                self._end()
            self._go_column(self.line + 1, 0)
            return True
        self._begin_replacing()
        index, _ = self._index()
        text = self._text()
        line = self.line
        at = min(index, len(text))
        kept = text[:at].rstrip(" ")
        moved = text[at:].rstrip(" ")
        indent = ""
        lead = 0
        if self.auto_indent:
            lead = len(moved) - len(moved.lstrip(" \t"))
            moved = moved[lead:]
            source = kept if kept.strip(" \t") else text
            indent = source[:len(source) - len(source.lstrip(" \t"))]
        # Right to left, so each edit leaves the places of the next alone.
        end = len(text.rstrip(" "))
        if end > at:
            self.buffer.delete(Pos(line, end), Pos(line, len(text)))
        else:
            self.buffer.delete(Pos(line, at), Pos(line, len(text)))
        if lead:
            self.buffer.delete(Pos(line, at), Pos(line, at + lead))
        self.buffer.insert(Pos(line, at), self.document.newline + (indent if moved else ""))
        if len(kept) < at:
            self.buffer.delete(Pos(line, len(kept)), Pos(line, at))
        self._go_column(line + 1, columns.width(indent, self.tab_size))
        self._end()
        return True

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
        """``cmInsLine``: a break after the cursor, which stays where it was."""
        line, col = self.line, self.col
        self._begin()
        index, _ = self._index()
        at = Pos(self.line, min(index, len(self._text())))
        self.buffer.insert(at, self.document.newline)
        self._end()
        self._go_column(line, col)
        return True

    async def on_tab_key(self, event: TabKey) -> bool:
        """``MakeTab``: blanks to the next stop, or over them in overwrite."""
        stop = (self.col // self.tab_size + 1) * self.tab_size
        if self.overwrite:
            self._moved()
            self._go_column(self.line, stop)
            return True
        self._begin_replacing("type")
        # Again: a block replaced has moved the cursor to where it began.
        stop = (self.col // self.tab_size + 1) * self.tab_size
        at = self._pad()
        self.buffer.insert(at, " " * (stop - self.col))
        self._go_column(self.line, stop)
        self._end()
        return True

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
            self.buffer.insert(Pos(self.line, 0), " " * target)
        self._go_column(self.line, target)
        self._end()
        return True

    async def on_delete_back(self, event: DeleteBack) -> bool:
        """``MakeBack``: the character before the cursor, or the line break.

        In the line's leading blanks, under the Editor setup's *Backspace
        unindents*, :meth:`_unindent` instead; with *Persistent blocks* off
        and a block marked, the block alone.
        """
        if self._deleting_block() or self._unindent():
            return True
        index, past = self._index()
        if past:
            self._moved()
            self._go_column(self.line, self.col - 1)
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

    async def on_delete_char(self, event: DeleteChar) -> bool:
        """``MakeDel``: the character under the cursor, or join the next line.

        With *Persistent blocks* off and a block marked, the block alone.
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
        at = self._pad()
        self.buffer.delete(at, Pos(self.line + 1, 0))
        self._end()
        return True

    async def on_delete_word_left(self, event: DeleteWordLeft) -> bool:
        index, past = self._index()
        if past:
            index = len(self._text())
        start = self._word_left(Pos(self.line, index))
        if start == Pos(self.line, index):
            return await self.on_delete_back(DeleteBack())
        self._begin()
        self.buffer.delete(start, Pos(self.line, index))
        self._go(start)
        self._end()
        return True

    async def on_delete_word_right(self, event: DeleteWordRight) -> bool:
        """``cmDelWordRight``: the word and the blanks after it, or the line break."""
        index, past = self._index()
        text = self._text()
        if past or index >= len(text):
            return await self.on_delete_char(DeleteChar())
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
        """``cmDeleteLine``: the whole line, and the cursor to its start."""
        self._begin()
        last = len(self.document) - 1
        if self.line < last:
            self.buffer.delete(Pos(self.line, 0), Pos(self.line + 1, 0))
        elif self.line > 0:
            self.buffer.delete(Pos(self.line - 1, len(self._text(self.line - 1))),
                               Pos(self.line, len(self._text())))
            self.line -= 1
        else:
            self.buffer.delete(Pos(0, 0), Pos(0, len(self._text())))
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

    async def on_switch_insert(self, event: SwitchInsert) -> bool:
        self.overwrite = not self.overwrite
        return True

    def enables(self, command: Any) -> bool:
        if isinstance(command, Undo):
            self.revision
            return self.buffer.can_undo
        if isinstance(command, HideBlock):
            return self.marked
        if isinstance(command, (FJustify, FRight, FLeft, FCenter)):
            # ``not (ValidBlock and BlockVisible) or VertBlock``: a stream block only.
            return self.block is not None and not self.block_hidden
        if isinstance(command, (
            ClipboardCut, ClipboardCopy, Clear, CopyBlock, MoveBlock,
            IndentBlock, UnindentBlock, UpcaseBlock, LowcaseBlock, CapitalizeBlock, SortBlock,
            CalcBlock,
            MoveBlockStart, MoveBlockEnd,
        )):
            return self.has_block
        return super().enables(command)

    def checks(self, command: Any) -> bool | None:
        """Editor > Options ticks *Vertical blocks*, *Auto wrap*, *Justify on wrap* and
        *AutoBrackets* while they are on (``SetM``)."""
        if isinstance(command, SwitchBlock):
            return self.vertical_blocks
        if isinstance(command, SwitchSave):
            return self.autowrap
        if isinstance(command, SwitchBrackets):
            return self.auto_brackets
        if isinstance(command, SwitchIndent):
            return self.auto_indent
        if isinstance(command, SwitchBack):
            return self.back_indent
        if isinstance(command, SwitchWrap):
            return self.justify_on_wrap
        return super().checks(command)

    async def on_undo(self, event: Undo) -> bool:
        before = self.buffer.undo()
        if before is not None:
            self.revision += 1
            self._go_column(*before)
        return True

    # -- keys the table cannot name ------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if event.is_printable:
            self.type_text(event.char)
            return True
        return False

    async def on_paste(self, event: PasteEvent) -> bool:
        if event.text:
            self.insert_text(event.text)
        return True

    # -- the mouse -----------------------------------------------------------------

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.is_wheel:
            if event.button in ("wheel_up", "wheel_down"):
                step = -WHEEL_ROWS if event.button == "wheel_up" else WHEEL_ROWS
                last = max(0, len(self.document) - 1)
                self.top = max(0, min(self.top + step, last))
                return True
            return False
        app = self.application
        if event.button == "middle" and event.action == "press":
            # The primary selection, as the console and the input lines paste it.
            if app is not None:
                app.request_clipboard(primary=True)
            return True
        if event.button != "left":
            return False
        if event.action == "press":
            self.focus()
            self._moved()
            before = self._here()
            self._point(event)
            here = self._here()
            if event.shift:
                # Shift+click: the block's far end stays, as Shift+movement keeps it.
                self._extend_block(before)
                ends = self._block_ends()
                self._drag_from = here if ends is None else (ends[0] if here == ends[1] else ends[1])
            else:
                self._unmark()
                self._drag_from = here
            if app is not None:
                app.capture_mouse(self)
        elif event.action == "move" and self._drag_from is not None:
            # Past the top or bottom row the text scrolls a line at a time.
            if event.y < 0 and self.top > 0:
                self.top -= 1
            elif event.y >= self.height and self.top < len(self.document) - 1:
                self.top += 1
            self._point(event)
            self._mark_to(self._drag_from)
        elif event.action == "release" and self._drag_from is not None:
            self._drag_from = None
            self._copy_primary()
        else:
            return False
        return True

    def _point(self, event: MouseClickEvent) -> None:
        """The cursor to the cell under *event*, held inside the text's rows."""
        y = min(max(event.y, 0), max(0, self.height - 1))
        self._go_column(self.top + y, self.left + max(0, event.x))

    def _mark_to(self, anchor: Any) -> None:
        self._set_block(anchor, self._here())

    def _copy_primary(self) -> None:
        """A block marked by the mouse is the primary selection, as a drag elsewhere is."""
        self._copy_block(primary=True)

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        """The word under the pointer, marked: the run between two ``BREAK_CHARS``."""
        if event.button != "left":
            return False
        self._drag_from = None
        self._point(event)
        if self._mark_word():
            self._copy_primary()
        return True

    def _mark_word(self) -> bool:
        """Mark the word at the cursor, the run between two ``BREAK_CHARS``; False on none."""
        at = self._mark_pos()
        text = self._text()
        if at.index >= len(text) or text[at.index] in BREAK_CHARS:
            return False
        start, stop = at.index, at.index
        while start and text[start - 1] not in BREAK_CHARS:
            start -= 1
        while stop < len(text) and text[stop] not in BREAK_CHARS:
            stop += 1
        if self.vertical_blocks:
            tab = self.tab_size
            self.column_block = ((self.line, columns.column_of(text, start, tab)),
                                 (self.line, columns.column_of(text, stop, tab)))
        else:
            self.block = (Pos(self.line, start), Pos(self.line, stop))
        self._go(Pos(self.line, stop))
        return True

    # -- the info line -------------------------------------------------------------

    @computed
    def info_text(self) -> str:
        """``TInfoLine``: modified mark, line:column, the code under the cursor, block mode, a pending chord.

        ``☼══12:34 [065] (↔)``.  The code is the character's own number, which
        was a byte in DN and is a code point here -- three digits until it
        needs more -- and a byte that was not UTF-8 gives the byte.
        """
        self.revision
        unicode = self.glyphs >= GLYPHS_UNICODE
        bar = "═" if unicode else "="
        mark = ("☼" if unicode else "*") if self.modified else bar
        text = self.document.lines[self.line] if self.line < len(self.document) else ""
        index, past = columns.index_at(text, self.col, self.tab_size)
        code = 0
        if not past and index < len(text):
            char = text[index]
            code = ord(char) - 0xDC00 if columns.is_escaped(char) else ord(char)
        block = ("(↕)" if unicode else "(|)") if self.vertical_blocks else ("(↔)" if unicode else "(-)")
        if self.draw_mode:
            # ``{┼}``/``{╬}``: the pen's weight, where the block's kind was.
            block = ("{┼}", "{╬}")[self.draw_mode - 1] if unicode else ("{+}", "{#}")[self.draw_mode - 1]
        # A departure: the keys of a chord still waiting for its last, WordStar's
        # ``^K``, so a key about to be swallowed is not a surprise.
        app = self.application
        pending = ""
        if app is not None and app.chord:
            pending = " " + " ".join(
                f"^{key[5:].upper()}" if key.startswith("ctrl+") else key for key in app.chord.split()
            )
        place = f"{self.line + 1}:{self.col + 1}"
        head = f"{mark}{bar}{bar}{place} [{code:03d}] "
        self._block_at = (len(head), len(head) + len(block))
        self._place_at = (3, 3 + len(place))
        code_start = 3 + len(place) + 1
        self._code_at = (code_start, code_start + len(f"[{code:03d}]"))
        return f"{head}{block}{pending}"

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

    def _search_bounds(self, number: int) -> tuple[int, int] | None:
        """The part of line *number* the block covers, as indices -- *Selected text*."""
        text = self.document.lines[number]
        if self.column_block is not None:
            top, left, bottom, right = self.rectangle
            if not top <= number <= bottom:
                return None
            return columns.span(text, left, right, self.tab_size)
        if self.block is None:
            return None
        start, end = self.block
        if not start.line <= number <= end.line:
            return None
        return (start.index if number == start.line else 0,
                end.index if number == end.line else len(text))

    def find(self, at: Pos, data: SearchData, *, backward: bool) -> tuple[Pos, Pos] | None:
        """The next match of *data* from *at*: the whole text, or the block's part of it."""
        bounds = self._search_bounds if data.selected else None
        return search.find(self.document.lines, at, data, backward=backward, bounds=bounds)

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

    def replace_found(self, found: tuple[Pos, Pos], new: str) -> Pos:
        """One replacement, an undo step of its own as DN's ``udReplace``; where it ends."""
        self._moved()
        self._begin()
        self.buffer.delete(*found)
        end = self.buffer.insert(found[0], new)
        self._end()
        return end

    def _found_columns(self, number: int) -> tuple[int, int] | None:
        found, mark = self._found, self._found_for
        if found is None or mark != (self.line, self.col, self.revision) or found[0].line != number:
            return None
        text, tab = self.document.lines[number], self.tab_size
        return columns.column_of(text, found[0].index, tab), columns.column_of(text, found[1].index, tab)

    # -- paragraph formatting -------------------------------------------------------------

    #: Which ``FormatBlock`` each command asks for.
    FORMATS = {FJustify: "justify", FRight: "right", FLeft: "left", FCenter: "center"}

    def format_block(self, mode: str) -> None:
        """``FormatBlock``: the stream block's whole lines as one paragraph, laid out
        between this editor's margins (:mod:`navigator.editor.paragraph`).

        The lines go in one undo step; the block then covers the new lines,
        from the start of the first to the start of the line after them, and
        the cursor is at its start.
        """
        from navigator.editor.paragraph import format_lines

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

    def go_to_line(self, number: int) -> None:
        """``ScrollTo(Delta.X, I-1)``: line *number*, counted from 1, at the same
        column; past the end, the last line."""
        self._moved()
        self._go_column(number - 1, self.col)

    def block_indicator(self) -> tuple[int, int]:
        """Where ``(↔)``/``(↕)`` stands in :attr:`info_text`, end exclusive: what a
        click switches -- ``TInfoLine``'s ``Length(S)+7 .. Length(S)+9``, worked out
        from the text itself because the code before it may be longer than three."""
        _ = self.info_text
        return self._block_at

    # -- painting ------------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        x, y = self.col - self.left, self.line - self.top
        if 0 <= x < self.width and 0 <= y < self.height:
            return x, y
        return None

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

    def render(self, surface: Surface) -> None:
        self.revision
        style = self.style
        selected = self.part_style("selected")
        surface.fill(0, 0, self.width, self.height, " ", style)
        lines = self.document.lines
        left, width = self.left, self.width
        for y in range(self.height):
            number = self.top + y
            if number >= len(lines):
                break
            span = self._block_columns(number) or self._found_columns(number)
            if span is not None:
                start, stop = max(span[0], left), min(span[1], left + width)
                if start < stop:
                    surface.fill(start - left, y, stop - start, 1, " ", selected)
            row = columns.cells(lines[number], self.tab_size, limit=left + width)
            for x in range(width):
                column = x + left
                if column >= len(row):
                    break
                cell = selected if span is not None and span[0] <= column < span[1] else style
                char, _ = row[column]
                if char == "":
                    if x == 0:
                        surface.set_cell(x, y, " ", cell)
                    continue
                if x == width - 1 and column + 1 < len(row) and row[column + 1][0] == "":
                    surface.set_cell(x, y, " ", cell)
                    continue
                surface.set_cell(x, y, char, cell)


class InfoLine(StaticText):
    """``TInfoLine``: the editor's line over the bottom frame, and what a click on it asks.

    DN gave it three places to click: the line and column (``cmGotoLineNumber``),
    the character's code (``cmSpecChar``, *ASCII Chart*) and the block indicator
    (``cmSwitchBlock``).  A press anywhere on the line is the line's, as
    ``ClearEvent`` made it, so it never reaches the frame beneath.
    """

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.action != "press":
            return True
        editor = getattr(self.parent, "editor", None)
        if event.button == "left" and isinstance(editor, FileEditor):
            start, end = editor.block_indicator()
            if start <= event.x < end:
                await editor.emit(SwitchBlock())
            start, end = editor.place_indicator()
            if start <= event.x < end:
                await editor.emit(GotoLineNumber())
            start, end = editor.code_indicator()
            if start <= event.x < end:
                await editor.emit(AsciiTable())
        return True
