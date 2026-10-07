"""What the Top Ten's name box answers: the name, *Anonymous* for none."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.tetris import ANONYMOUS


class WinnerDialog(Dialog):
    """*You have entered Top Ten!*"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        self.player.value = ANONYMOUS
        self.player.entry.select_all()

    def accept(self) -> str:
        return self.player.value.strip()[:30] or ANONYMOUS
