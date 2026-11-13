"""The keys, as FVIEWER.PAS's HandleEvent had them in each mode, and editing bytes in hex.

A mixin of :class:`FileViewer` (``navkit.widget.Mixin``): methods only; its state,
keys and the file are in ``file_viewer.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from navkit.events import KeyEvent
from navigator.widgets.viewer.file_viewer.helpers import BIG_STEP, _when_here

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navigator.widgets.viewer.file_viewer.file_viewer_surface import FileViewer as _Base
else:
    from navkit.widget import Mixin as _Base


class KeyHandling(_Base):
    """The keys, as FVIEWER.PAS's HandleEvent had them in each mode, and editing bytes in hex."""

    # -- keys ------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.source is None:
            return False
        name = event.name
        rows = max(1, self.height - 1)
        if self.filtering:
            return self._lines_key(name, rows)
        if name in ("ctrl+pageup",):
            self.to_start()
        elif name in ("ctrl+pagedown",):
            self.to_end()
        elif self.rendering:
            return self._rendered_key(name, rows)
        elif self.mode == "text":
            return self._text_key(name, rows)
        elif self.mode == "dump":
            return self._dump_key(name, rows)
        elif self.editable and self._edit_key(event):
            return True
        else:
            return self._hex_key(name, rows)
        return True

    def _text_key(self, name: str, rows: int) -> bool:
        if name == "up":
            self.scroll_rows(-1)
        elif name == "down":
            self.scroll_rows(1)
        elif name == "pageup":
            self.scroll_rows(-rows)
        elif name == "pagedown":
            self.scroll_rows(rows)
        elif name == "ctrl+home":
            self.to_start()
        elif name == "ctrl+end":
            self.to_end()
        elif self.wrap and name in ("left", "right", "ctrl+left", "ctrl+right", "home", "end"):
            # Nothing is off the side of a wrapped row.
            pass
        elif name == "left":
            self.x_delta = max(0, self.x_delta - 1)
        elif name == "right":
            self.x_delta += 1
        elif name == "ctrl+left":
            self.x_delta = max(0, self.x_delta - BIG_STEP)
        elif name == "ctrl+right":
            self.x_delta += BIG_STEP
        elif name == "home":
            self.x_delta = 0
        elif name == "end":
            self._to_longest_end()
        else:
            return False
        return True

    def _rendered_key(self, name: str, rows: int) -> bool:
        """The rendering's keys: rows up and down; nothing is off its side."""
        moves = {"up": -1, "down": 1, "pageup": -rows, "pagedown": rows}
        if name in moves:
            self.scroll_rows(moves[name])
        elif name in ("ctrl+home", "home"):
            self.to_start()
        elif name in ("ctrl+end", "end"):
            self.to_end()
        elif name not in ("left", "right", "ctrl+left", "ctrl+right"):
            return False
        return True

    @_when_here
    def _to_longest_end(self) -> None:
        """CM_END: far enough to show the end of the longest row showing."""
        longest = max((len(r.cells) for r in self._text_rows(self.height)), default=0)
        self.x_delta = max(0, longest - self.width)

    def _dump_key(self, name: str, rows: int) -> bool:
        """Dump, DN's ``ViewMode = 2``: no cursor, so the arrows scroll as in
        text, Ctrl+Home/Ctrl+End go to the file's ends (``Goto 1/2``) and
        Ctrl+Left/Right shift the rows a byte as in hex.  Home, End, Left,
        Right and Tab only moved DN's ``XDelta`` or hex ``Cur`` there, so they
        do nothing -- but are still the viewer's.  ``cursor`` stays on the
        view's first byte, where a search starts (DN's ``FilePos+BufPos``)."""
        if name in ("up", "down"):
            self.scroll_rows(-1 if name == "up" else 1)
        elif name in ("pageup", "pagedown"):
            self.scroll_rows(-rows if name == "pageup" else rows)
        elif name == "ctrl+home":
            self.to_start()
        elif name == "ctrl+end":
            self.to_end()
        elif name in ("ctrl+left", "ctrl+right"):
            self._shift_rows(-1 if name == "ctrl+left" else 1)
        elif name not in ("home", "end", "left", "right", "tab"):
            return False
        self.cursor = self.top
        return True

    def _shift_rows(self, step: int) -> None:
        """Ctrl+Left/Right in hex and dump: the rows' start a byte back or on,
        as DN's ``Dec(BufPos)``/``Inc(BufPos)``."""
        if step < 0 and self.top > 0:
            self.top -= 1
        elif step > 0 and self.top + 1 < self.size:
            self.top += 1
        self._keep_cursor()

    def _hex_key(self, name: str, rows: int) -> bool:
        per = self.row_bytes()
        if name == "up":
            if self.cursor >= per:
                self.move_cursor(-per)
        elif name == "down":
            if self.cursor + per < self.size:
                self.move_cursor(per)
        elif name == "pageup":
            self.scroll_rows(-rows)
            if self.cursor >= rows * per:
                self.move_cursor(-rows * per)
            self._keep_cursor()
        elif name == "pagedown":
            self.scroll_rows(rows)
            self.move_cursor(rows * per)
            self._keep_cursor()
        elif name == "left":
            self.move_cursor(-1)
        elif name == "right":
            self.move_cursor(1)
        elif name == "ctrl+left":
            self._shift_rows(-1)
        elif name == "ctrl+right":
            self._shift_rows(1)
        elif name == "home":
            self.cursor = self.cursor - (self.cursor - self.top) % per
        elif name == "end":
            self.cursor = min(self.size - 1, self.cursor - (self.cursor - self.top) % per + per - 1)
        elif name == "ctrl+home":
            self.cursor = self.top + (self.cursor - self.top) % per
        elif name == "ctrl+end":
            column = (self.cursor - self.top) % per
            last_row = self.top + (max(1, self.height) - 1) * per
            while last_row + column >= self.size and last_row > self.top:
                last_row -= per
            self.cursor = min(self.size - 1, last_row + column)
        else:
            return False
        return True

    # -- hex editing -----------------------------------------------------------
    #
    # ``FVIEWER.PAS``'s ``HandleEvent`` in ``ViewMode = 1``: in the pairs
    # (``HexEdit``) Left and Right step a nibble and 0-9/A-F replace it; in
    # the characters (Tab) they step a byte and a character replaces it; each
    # typed moves on, as DN's ``Message(kbRight)`` did.  The bytes are the
    # source's overlay until Shift+F2 stores them (``FileWindow.store``).

    @property
    def editable(self) -> bool:
        """Whether a key typed here types over a byte: the F3 window's hex
        view of a file that has a size to write back to."""
        return (self.hex_editing and self.mode == "hex" and self.source is not None
                and self.source.editable)

    def _edit_key(self, event: KeyEvent) -> bool:
        name = event.name
        pairs = not self.in_chars
        if name == "tab":
            self.in_chars = not self.in_chars
            self.nibble = 0
        elif name == "left" and pairs:
            if self.nibble:
                self.nibble = 0
            elif self.cursor > 0:
                self.move_cursor(-1)
                self.nibble = 1
        elif name == "right" and pairs:
            self._step_nibble()
        elif name == "home" and pairs:
            self.cursor = self.cursor - (self.cursor - self.top) % self.row_bytes()
            self.nibble = 0
        elif name == "end" and pairs:
            per = self.row_bytes()
            self.cursor = min(self.size - 1, self.cursor - (self.cursor - self.top) % per + per - 1)
            self.nibble = 1
        elif name == "ctrl+z":
            self.undo_edit()
        elif name == "backspace":
            # A departure, as Ctrl+Z: a step back, the file's own byte put back there.
            if self.cursor > 0:
                self.move_cursor(-1)
            self.nibble = 0
            if self.source.revert(self.cursor):
                self._edits_changed()
        elif event.char and not (event.ctrl or event.alt or event.super_) and event.char.isprintable():
            self._type(event.char)
        else:
            return False
        return True

    def _step_nibble(self) -> None:
        """Right in the pairs: the low nibble, or the next byte's high one."""
        if self.nibble == 0:
            self.nibble = 1
        elif self.cursor + 1 < self.size:
            self.move_cursor(1)
            self.nibble = 0

    def _type(self, char: str) -> None:
        """*char* typed over the byte at the cursor: a hex digit into its
        nibble in the pairs, the character's byte in the characters.  Anything
        else is swallowed, as DN cleared it."""
        source = self.source
        current = source.peek(self.cursor)
        if current is None:
            return
        if not self.in_chars:
            digit = "0123456789ABCDEF".find(char.upper())
            if digit < 0 or len(char) != 1:
                return
            byte = (current & 0x0F) | (digit << 4) if self.nibble == 0 else (current & 0xF0) | digit
            if source.patch(self.cursor, byte):
                self._edits_changed()
            self._step_nibble()
            return
        byte = self._byte_of(char)
        if byte is None:
            return
        if source.patch(self.cursor, byte):
            self._edits_changed()
        if self.cursor + 1 < self.size:
            self.move_cursor(1)

    def _byte_of(self, char: str) -> int | None:
        """The one byte *char* is in the code page the file is read in
        (File > Encoding), or in ASCII under UTF-8; None if there is none."""
        table = self.source.table
        if table is not None:
            try:
                return table.index(char)
            except ValueError:
                return None
        return ord(char) if ord(char) < 0x80 else None

    def undo_edit(self) -> None:
        """Ctrl+Z: the last byte typed taken back, the cursor on it."""
        offset = self.source.undo() if self.source is not None else None
        if offset is None:
            return
        self.cursor = offset
        self.nibble = 0
        self.follow_cursor()
        self._edits_changed()

    def _edits_changed(self) -> None:
        self.edited = self.source.edited
        self.invalidate()

    def edits_stored(self, written: dict[int, int]) -> None:
        """Shift+F2 done: the file holds the bytes *written* now; highlighting
        and a rendering are made again from it."""
        if self.source is None:
            return
        self.source.stored(written)
        self.edited = self.source.edited
        self.rehighlight()
        self._forget_layout()
        self.invalidate()
