"""What the *Filter* box answers: show or hide, the masks, and where it was."""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navml.widgets.dialog.dialog import Dialog


class FilterDialog(Dialog):
    """``GetMaskSelection``'s box: ``(show, masks, cursor)``, or None for Close."""

    def __init__(self, masks: list[str] | None = None, cursor: int = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.masks.items = list(masks or [])
        self.masks.cursor = min(cursor, max(0, len(self.masks.items) - 1))

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.show, self.hide, self.abandon)

    def chosen(self) -> list[str]:
        """The marked masks, or the one at the cursor with none marked (DN's ``FItem``)."""
        items = self.masks.items
        if self.masks.marks:
            return [items[index] for index in sorted(self.masks.marks) if index < len(items)]
        return [items[self.masks.cursor]] if items else []

    def _answer(self, show: bool) -> None:
        self.close((show, self.chosen(), self.masks.cursor))

    async def on_show_click(self, event: Event) -> bool:
        self._answer(True)
        return True

    async def on_hide_click(self, event: Event) -> bool:
        self._answer(False)
        return True
