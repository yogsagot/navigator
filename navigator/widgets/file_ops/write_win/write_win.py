"""What the reading and writing box's one button means."""

from __future__ import annotations

from typing import Any

from navkit.reactive import bind, unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.commands import Cancel, Default
from navml.widgets.dialog.dialog import Dialog


class WriteWin(Dialog):
    """*Reading file* or *Writing file*: a spinner, a gauge, and *Cancel*."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        unbind(self.ok, Button.text)
        self.ok.text = "~C~ancel"
        self.ok.visible = bind(lambda ok: self.cancellable)

    def accept(self) -> Any:
        """*Cancel* answers what Esc does: nothing, which stops the work."""
        return None

    async def on_cancel(self, event: Cancel) -> bool:
        if not self.cancellable:
            return True
        return await super().on_cancel(event)

    async def on_default(self, event: Default) -> bool:
        if not self.cancellable:
            return True
        return await super().on_default(event)
