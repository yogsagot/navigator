"""What OK means in *Goto Address*: an offset, or nothing."""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navml.widgets.dialog.dialog import Dialog


class GotoDialog(Dialog):
    """F5 in a hex viewer: the address to go to."""

    def accept(self) -> Any:
        """The address as an int, or ``None`` if the line is not hex.

        ``None`` is also what Cancel says, and DN did nothing about either: a
        ``Val`` that failed left the viewer where it was.
        """
        text = self.address.value.strip().lower().removeprefix("$").removeprefix("0x")
        try:
            return int(text, 16) if text else None
        except ValueError:
            return None

    async def on_pick_click(self, event: Event) -> bool:
        """OK, in this dialog's own row: what ``Dialog``'s ``ok`` does --
        the histories recorded, then the answer."""
        return await self.on_ok_click(event)
