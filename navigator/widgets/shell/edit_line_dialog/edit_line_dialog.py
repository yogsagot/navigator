"""What OK means in the box: the line as typed."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class EditLineDialog(Dialog):
    """One line, seeded with *text*; no longer than *max_length* when one is
    given, as ``InputBox``'s ``Limit`` held it."""

    def __init__(self, text: str = "", *, history: str = "", max_length: int = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if history:
            self.line.history_id = history
        if max_length:
            self.line.entry.max_length = max_length
            text = text[:max_length]
        self.line.value = text
        self.line.entry.select_all()

    def accept(self) -> Any:
        return self.line.value
