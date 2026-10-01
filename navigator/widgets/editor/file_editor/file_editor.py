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

from pathlib import Path
from typing import Any

from navkit.capabilities import GLYPHS_UNICODE
from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent, PasteEvent
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navigator.widgets.editor.commands import (
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
    WordLeft,
    WordRight,
)
from navigator.editor import columns
from navigator.editor.buffer import EditBuffer
from navigator.editor.document import BREAK, Document, Pos
from navigator.editor.save import write_file

#: DN's ``BreakChars`` (``ADVANCE.PAS``): what ends a word for Ctrl+Left,
#: Ctrl+Right and the word deletes.
BREAK_CHARS = frozenset(", []{}():;.^&*!#$/\\'\"%><-+=|?\r\n\t\x1a\x0c")

#: How many lines one wheel notch moves the view.
WHEEL_ROWS = 3


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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.buffer = EditBuffer()
        #: Where a Tab stops, and how far a tab character reaches.
        self.tab_size = columns.TAB
        # In __init__, not the class body: a plain class attribute would
        # shadow the reactive descriptor, as `Console` learned.
        self.can_focus = True

    # -- the file ----------------------------------------------------------------

    def open(self, path: Path | str, *, new: bool = False) -> None:
        """Edit *path* from its start.  Raises ``OSError`` if it cannot be read.

        With *new*, a file that does not exist is an empty text that saving
        will create -- Shift+F4's *Edit new file*.
        """
        path = Path(path)
        try:
            document = Document.load(path)
        except FileNotFoundError:
            if not new:
                raise
            document = Document()
        self.buffer = EditBuffer(document)
        self.path = path
        self.line = self.col = self.top = self.left = 0
        self.revision += 1

    def save(self) -> None:
        """Write the text to :attr:`path`.  Raises ``OSError``."""
        if self.path is None:
            raise OSError("no file name")
        write_file(self.path, self.buffer.document.encode())
        self.buffer.mark_saved()
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

    async def on_move_right(self, event: MoveRight) -> bool:
        self._moved()
        index, past = self._index()
        text = self._text()
        if past or index >= len(text):
            self._go_column(self.line, self.col + 1)
        else:
            self._go(Pos(self.line, index + 1))
        return True

    async def on_move_up(self, event: MoveUp) -> bool:
        self._moved()
        self._go_column(self.line - 1, self.col)
        return True

    async def on_move_down(self, event: MoveDown) -> bool:
        self._moved()
        self._go_column(self.line + 1, self.col)
        return True

    async def on_line_start(self, event: LineStart) -> bool:
        self._moved()
        self._go_column(self.line, 0)
        return True

    async def on_line_end(self, event: LineEnd) -> bool:
        """``cmEnd``: after the last character that is not a blank."""
        self._moved()
        text = self._text()
        self._go(Pos(self.line, len(text.rstrip(" "))))
        return True

    async def on_page_up(self, event: PageUp) -> bool:
        self._moved()
        rows = max(1, self.height)
        self.top = max(0, self.top - rows)
        self._go_column(self.line - rows, self.col)
        return True

    async def on_page_down(self, event: PageDown) -> bool:
        self._moved()
        rows = max(1, self.height)
        last = len(self.document) - 1
        self.top = max(0, min(self.top + rows, last - rows + 1))
        self._go_column(self.line + rows, self.col)
        return True

    async def on_screen_top(self, event: ScreenTop) -> bool:
        self._moved()
        self._go_column(self.top, self.col)
        return True

    async def on_screen_bottom(self, event: ScreenBottom) -> bool:
        self._moved()
        self._go_column(self.top + max(1, self.height) - 1, self.col)
        return True

    async def on_text_start(self, event: TextStart) -> bool:
        self._moved()
        self._go_column(0, 0)
        return True

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

    async def on_word_left(self, event: WordLeft) -> bool:
        self._moved()
        self._go(self._word_left(self._pos()))
        return True

    async def on_word_right(self, event: WordRight) -> bool:
        self._moved()
        self._go(self._word_right(self._pos()))
        return True

    # -- edits -------------------------------------------------------------------

    def _begin(self, merge: str | None = None) -> None:
        self.buffer.begin((self.line, self.col), merge)

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
        """Characters typed at the cursor, inserted or over what is there."""
        self._begin("type")
        at = self._pad()
        if self.overwrite:
            line = self._text()
            stop = min(len(line), at.index + len(text))
            self.buffer.delete(at, Pos(at.line, stop))
        end = self.buffer.insert(at, text)
        self._go(end)
        self._end()

    def insert_text(self, text: str) -> None:
        """A paste: line breaks become the file's own."""
        text = BREAK.sub(self.document.newline, text)
        self._begin()
        end = self.buffer.insert(self._pad(), text)
        self._go(end)
        self._end()

    async def on_new_line(self, event: NewLine) -> bool:
        """``MakeEnter``: split the line, and indent the new one as this one is."""
        self._begin()
        index, _ = self._index()
        text = self._text()
        at = Pos(self.line, min(index, len(text)))
        indent = text[:len(text) - len(text.lstrip(" \t"))]
        tail = text[at.index:]
        if at.index <= len(indent):
            indent = ""
        end = self.buffer.insert(at, self.document.newline + (indent if tail.strip() else ""))
        self._go(end)
        if not tail.strip() and indent:
            # Nothing follows: the new line stays empty and the cursor waits
            # at the indent, as DN's did, rather than leaving blanks behind.
            self.col = columns.width(indent, self.tab_size)
            self._follow()
        self._end()
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
        self._begin("type")
        at = self._pad()
        self.buffer.insert(at, " " * (stop - self.col))
        self._go_column(self.line, stop)
        self._end()
        return True

    async def on_delete_back(self, event: DeleteBack) -> bool:
        """``MakeBack``: the character before the cursor, or the line break."""
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
        """``MakeDel``: the character under the cursor, or join the next line."""
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
        return super().enables(command)

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
        if event.action != "press" or event.button != "left":
            return False
        self.focus()
        self._moved()
        self._go_column(self.top + event.y, self.left + event.x)
        return True

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        return False

    # -- the info line -------------------------------------------------------------

    @computed
    def info_text(self) -> str:
        """``TInfoLine``: modified mark, line:column, the code under the cursor, block mode.

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
        return f"{mark}{bar}{bar}{self.line + 1}:{self.col + 1} [{code:03d}] {block}"

    # -- painting ------------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        x, y = self.col - self.left, self.line - self.top
        if 0 <= x < self.width and 0 <= y < self.height:
            return x, y
        return None

    def render(self, surface: Surface) -> None:
        self.revision
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        lines = self.document.lines
        left, width = self.left, self.width
        for y in range(self.height):
            number = self.top + y
            if number >= len(lines):
                break
            row = columns.cells(lines[number], self.tab_size, limit=left + width)
            for x in range(width):
                column = x + left
                if column >= len(row):
                    break
                char, _ = row[column]
                if char == "":
                    if x == 0:
                        surface.set_cell(x, y, " ", style)
                    continue
                if x == width - 1 and column + 1 < len(row) and row[column + 1][0] == "":
                    surface.set_cell(x, y, " ", style)
                    continue
                surface.set_cell(x, y, char, style)
