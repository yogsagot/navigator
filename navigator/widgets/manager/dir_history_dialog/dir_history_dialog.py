"""What *Directories History* answers: the directory to go to, or nothing.

*Delete record* takes the one at the cursor out of the history
(``HISTORY``'s ``directories`` list) there and then, and the dialog stays.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navml.history import HISTORY
from navml.widgets.dialog.dialog import Dialog

#: The history list visited directories go into.
HISTORY_ID = "directories"


class DirHistoryDialog(Dialog):
    """``DirHistoryMenu``'s box."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.places.items = HISTORY.entries(HISTORY_ID)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.drop, self.abandon)

    def accept(self) -> str | None:
        return self.places.selected

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True

    async def on_places_chosen(self, event: Event) -> bool:
        self.close(self.accept())
        return True

    async def on_drop_click(self, event: Event) -> bool:
        place = self.places.selected
        if place is not None:
            HISTORY.remove(HISTORY_ID, place)
            self.places.items = HISTORY.entries(HISTORY_ID)
            self.places.focus()
        return True
