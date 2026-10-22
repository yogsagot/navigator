"""What *Yes* means in Del's question: delete the bookmark, and perhaps never ask again."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

#: The *Don't ask again* box's bit.
DONT_ASK = 0x01


class DeleteBookmarkDialog(Dialog):
    """Del's question: *Yes* answers ``{"ask_again": bool}``, *No* False, Esc None."""

    def __init__(self, name: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The tail of a path too long for the line: its end is what tells one from another.
        # Three dots, not an ellipsis, which the ASCII tier has no glyph for.
        room = max(4, self.prompt_tail.width or 46)
        shown = name if len(name) <= room else "..." + name[-(room - 3):]
        self.prompt_tail.text = escape_caption(shown)

    def focusable(self) -> list[Any]:
        """*Yes* first, as Alt+X's question has it, and the box after the buttons."""
        order = super().focusable()
        return [w for w in order if w is not self.options] + [self.options]

    def accept(self) -> dict[str, bool]:
        return {"ask_again": not self.options.value & DONT_ASK}
