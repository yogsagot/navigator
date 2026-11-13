"""What OK means in *Goto Line*: a line number, or nothing."""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navml.widgets.dialog.dialog import Dialog

#: What was last typed, which the next *Goto Line* opens with: ``GotoLine``'s
#: ``const S``, kept from one call to the next.
_last = {"text": ""}


class GotoLineDialog(Dialog):
    """Alt+G: the line to go to, counted from 1."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.number.value = _last["text"]
        self.number.entry.select_all()

    async def on_pick_click(self, event: Event) -> bool:
        """OK, in this dialog's own row: what ``Dialog``'s ``ok`` does --
        the history recorded, then the answer."""
        return await self.on_ok_click(event)

    def accept(self) -> Any:
        """The line as an int above 0, or ``None``: ``Val`` failing, or 0 and less,
        did nothing in DN, and ``None`` is what Cancel says too."""
        text = self.number.value.strip()
        _last["text"] = text
        try:
            number = int(text)
        except ValueError:
            return None
        return number if number > 0 else None
