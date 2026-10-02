"""What *Yes* means in the exit question: quit, and perhaps never ask again."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

#: The *Don't ask again* box's bit.
DONT_ASK = 0x01


class ExitDialog(Dialog):
    """Alt+X's question: *Yes* answers ``{"ask_again": bool}``, *No* False, Esc None."""

    def focusable(self) -> list[Any]:
        """*Yes* first, as the message box's focus was, and the box after the buttons."""
        order = super().focusable()
        return [w for w in order if w is not self.options] + [self.options]

    def accept(self) -> dict[str, bool]:
        return {"ask_again": not self.options.value & DONT_ASK}
