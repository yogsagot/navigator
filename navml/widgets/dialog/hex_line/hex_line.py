"""DOS Navigator's ``THexLine`` (``DIALOGS.PAS``): the bytes of the text in
the :class:`~navml.widgets.dialog.input_line.InputLine` it is linked to, as
hex pairs, edited as hex -- the viewer's *Find* box puts one under *Search
for*.  Written in Python alone, as :class:`Control` is: it has nothing a
document would lay out.

**Its keys are DN's**: ``0-9``/``A-F`` set the high nibble, then the low one,
then step on (a byte past the end is added as ``00`` first); Left and Right
step a nibble; Backspace deletes the byte before (the one under, on its low
nibble), Del the one under; Up is Shift+Tab; any other printable key is
swallowed.  Tab, Enter and Escape are the dialog's.

**The bytes are its own.**  In DN a character was a byte, so the two lines
were one string.  Here the text is Unicode and the bytes are it in
:attr:`HexLine.encoding`, so a hex edit can make bytes that are no text in it
(``FF`` in UTF-8): :attr:`HexLine.data` keeps them, and the text line shows
them decoded, ``U+FFFD`` for what will not decode.  Typing in the text line
makes :attr:`data` the text's bytes again -- a character the encoding has no
byte for gives none.

**The two cursors follow each other**, as DN's ``Draw`` made them: while the
text line has the keyboard the hex cursor is on the first byte of the
character the text cursor is before, and while this line has it the text
cursor is on the character holding the byte.

**Left to right on a mirrored screen** too, as the viewer's hex rows are:
hex is numbers.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent
from navkit.reactive import effect, peek, reactive
from navkit.screen import Surface

from navml.widgets.dialog.control import Control

_DIGITS = "0123456789ABCDEF"


class HexLine(Control):
    """The linked line's bytes as hex pairs, edited as hex."""

    #: The :class:`InputLine` whose text this shows -- in markup, an ``id``
    #: from the same document (``what.entry``), as a ``Label``'s ``link``.
    link: Any = reactive(None)

    #: What the text is in bytes.
    encoding: str = reactive("utf-8")

    #: The bytes, replaced whole on every edit.
    data: bytes = reactive(b"")

    #: The byte the cursor is on (DN's ``CurX``) and whether it is on its low
    #: nibble (``Sec``).
    cursor: int = reactive(0)
    low: bool = reactive(False)

    #: The first byte shown (``DeltaX``).
    first: int = reactive(0)

    mirrors = False

    #: The text this line last wrote into the link, so the effect reading
    #: the link's value can tell its own write from typing.
    _wrote: str | None = None

    def mounted(self) -> None:
        super().mounted()
        effect(self, HexLine._follow_text)
        effect(self, HexLine._follow_cursor)

    # -- the link ------------------------------------------------------------

    def _encode(self, text: str) -> bytes:
        return text.encode(self.encoding, errors="ignore")

    def _decode(self, data: bytes) -> str:
        return data.decode(self.encoding, errors="replace")

    def _follow_text(self) -> None:
        """Typing in the text line: the bytes are the text's again; and the
        hex cursor where the text cursor is while the text line is focused."""
        link = self.link
        if link is None:
            return
        value, text_cursor = link.value, link.cursor
        if value != self._wrote:
            self._wrote = None
            self.data = self._encode(value)
        if link.focused:
            self.cursor = len(self._encode(value[:text_cursor]))
            self.low = False

    def set_data(self, data: bytes) -> None:
        """Show *data*, and its text in the linked line."""
        self.data = data
        self.cursor = min(peek(self, HexLine.cursor), len(data))
        self._write_link()

    def _write_link(self) -> None:
        link = self.link
        if link is None:
            return
        text = self._decode(self.data)
        self._wrote = text
        link.value = text
        # The text cursor on the character holding the hex cursor's byte.
        link.cursor = len(self._decode(self.data[:self.cursor]))

    # -- scrolling -----------------------------------------------------------

    @property
    def room(self) -> int:
        """Bytes that fit: three columns each, one clear at either end."""
        return max(1, (self.width - 2) // 3)

    def _follow_cursor(self) -> None:
        cursor, room = self.cursor, self.room
        first = peek(self, HexLine.first)
        if cursor < first:
            self.first = cursor
        elif cursor >= first + room:
            self.first = cursor - room + 1

    # -- keys ----------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        data, cursor, low = self.data, self.cursor, self.low
        if event.matches("backspace"):
            if low:
                self.low = False
                self.set_data(data[:cursor] + data[cursor + 1:])
            elif cursor > 0:
                self.cursor = cursor - 1
                self.set_data(data[:cursor - 1] + data[cursor:])
        elif event.matches("delete"):
            if cursor < len(data):
                self.low = False
                self.set_data(data[:cursor] + data[cursor + 1:])
        elif event.matches("left"):
            if low:
                self.low = False
            elif cursor > 0:
                self.cursor, self.low = cursor - 1, True
            self._write_link()
        elif event.matches("right"):
            if low and cursor < len(data):
                self.cursor, self.low = cursor + 1, False
            else:
                self.low = True
            self._write_link()
        elif event.matches("up"):
            self.application.focus_next(reverse=True)
        elif event.matches("tab", "shift+tab", "escape", "enter"):
            return False
        elif event.is_printable and event.char:
            digit = _DIGITS.find(event.char.upper())
            if digit < 0 or len(event.char) != 1:
                return True  # swallowed, as DN's
            limit = getattr(self.link, "max_length", 0)
            if limit and cursor == limit - 1 and low:
                return True
            padded = data + b"\0" if cursor >= len(data) else data
            byte = padded[cursor]
            byte = (byte & 0xF0) | digit if low else (byte & 0x0F) | digit << 4
            new = padded[:cursor] + bytes((byte,)) + padded[cursor + 1:]
            if limit:
                new = new[:limit]
            if low:
                self.cursor, self.low = cursor + 1, False
            else:
                self.low = True
            self.set_data(new)
        else:
            return False
        return True

    # -- painting ------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        return 1 + 3 * (self.cursor - self.first) + int(self.low), 0

    def render(self, surface: Surface) -> None:
        if self.width < 1 or self.height < 1:
            return
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        shown = self.data[self.first:self.first + self.room]
        pairs = " ".join(f"{byte:02X}" for byte in shown)
        surface.draw_text(1, 0, pairs[:max(0, self.width - 2)], style)
