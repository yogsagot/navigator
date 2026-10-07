"""A heading and lines to scroll through, and OK."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class DBListDialog(Dialog):
    """*Structure of* or *Memo view*."""

    def __init__(self, heading: str = "", lines: list[str] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        self.heading.text = heading
        self.lines.items = list(lines or [])
