"""What *ASCII Chart* answers: ``TASCIIChart.Execute``.

Esc cancels; Enter, Ctrl+B and Ctrl+P take the character under the cursor;
**any other character typed is taken at once**, as ``Execute`` did with
``SetData(Event.CharCode)`` -- a key that is in code page 437 picks itself.
A double click in the table is Enter.  The answer is the code, 0 to 255, or
None.  The chart opens on the character last taken, which starts as ``p``
(``const C: Char = #112``).

A departure: DN opened the window where it was last left (``T :=
P^.Origin``); a navml dialog is centred.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.shell.char_table.char_table import glyph

#: The code last taken: ``ASCIITable``'s ``const C``, kept between calls.
_last = {"code": 112}


def code_of(char: str) -> int | None:
    """The code-page-437 code a typed *char* stands for, or None if it has none."""
    if len(char) != 1:
        return None
    if " " <= char <= "~":
        return ord(char)
    for code in range(256):
        if glyph(code) == char and code != 0:
            return code
    return None


class AsciiChart(Dialog):
    """*ASCII Chart*: a code from 0 to 255, picked or typed."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.table.code = _last["code"]

    def mounted(self) -> None:
        super().mounted()
        effect(self, AsciiChart._report)

    def _report(self) -> None:
        """``TReport.Draw``: ``'  Char: %c Decimal: %0#%3d Hex: %0#%02x  '``."""
        code = self.table.code
        self.report.text = "  " + tr("Char: {char} Decimal: {decimal:3d} Hex: {hex:02x}").format(
            char=glyph(code), decimal=code, hex=code)

    def accept(self) -> int:
        _last["code"] = self.table.code
        return self.table.code

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("enter") or event.matches("ctrl+b") or event.matches("ctrl+p"):
            self.close(self.accept())
            return True
        if event.is_printable and event.char and not event.ctrl and not event.alt:
            code = code_of(event.char)
            if code is not None:
                self.table.code = code
                self.close(self.accept())
            return True
        return await super().on_key(event)

    async def on_table_chosen(self, event: Any) -> bool:
        """A double click on a character: Enter."""
        self.close(self.accept())
        return True
