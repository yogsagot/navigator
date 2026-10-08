"""What *Press a key* answers: the key caught, as a key table spells it."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class KeyCaptureDialog(Dialog):
    """The box over a :class:`KeyCatcher`; its answer is the spec, or None."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.catcher.done = self.close

    def accept(self) -> str | None:
        return self.catcher.spec or None
