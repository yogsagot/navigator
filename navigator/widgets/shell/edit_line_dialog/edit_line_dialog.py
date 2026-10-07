"""What OK means in the box: the line as typed."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class EditLineDialog(Dialog):
    """One line, seeded with *text*."""

    def __init__(self, text: str = "", *, history: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if history:
            self.line.history_id = history
        self.line.value = text
        self.line.entry.select_all()

    def accept(self) -> Any:
        return self.line.value
