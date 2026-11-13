"""What the Top Ten's name box answers: the name, *Anonymous* for none."""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navkit.i18n import tr
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.utilities.tetris import ANONYMOUS


class WinnerDialog(Dialog):
    """*You have entered Top Ten!*"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.player.value = tr("Anonymous")
        self.player.entry.select_all()

    async def on_pick_click(self, event: Event) -> bool:
        """OK, in this dialog's own row: what ``Dialog``'s ``ok`` does --
        the history recorded, then the answer."""
        return await self.on_ok_click(event)

    def accept(self) -> str:
        return self.player.value.strip()[:30] or ANONYMOUS
