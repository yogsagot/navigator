"""What ``ExistsQuery`` says, and what each button answers: ``"yes"``,
``"no"``, ``"all"``, or None for Cancel and Esc."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.events import Event

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.file_ops.delete_dialog.delete_dialog import cut

#: Each button's width, and the columns between two.
BUTTON, GAP = 11, 2


class ExistsQuery(Dialog):
    """*Confirm*: File NAME already exists.  Overwrite?"""

    def __init__(self, path: Path | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        if path is not None:
            self.details.text = f"File {escape_caption(cut(str(path)))} already exists.\nOverwrite?"

    def slot(self, index: int) -> int:
        """The column of the *index*-th button of the centred row."""
        wide = 4 * BUTTON + 3 * GAP
        return max(0, (self.width - wide) // 2) + index * (BUTTON + GAP)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.agree, self.refuse, self.every, self.abandon)

    async def on_agree_click(self, event: Event) -> bool:
        self.close("yes")
        return True

    async def on_refuse_click(self, event: Event) -> bool:
        self.close("no")
        return True

    async def on_every_click(self, event: Event) -> bool:
        self.close("all")
        return True
