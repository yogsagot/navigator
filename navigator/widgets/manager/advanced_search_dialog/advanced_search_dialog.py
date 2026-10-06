"""What OK means in *Advanced search*: its lines as typed, and the kinds as bits."""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navml.widgets.dialog.dialog import Dialog

LINES = ("after", "before", "greater", "less")


class AdvancedSearchDialog(Dialog):
    """DN's ``AdvanceSearchData``: dates, sizes and kinds a match keeps within."""

    def __init__(self, limits: dict[str, Any] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        limits = limits or {}
        for name in LINES:
            getattr(self, name).value = limits.get(name, "")
        self.kinds.value = limits.get("kinds", 0)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.clear, self.abandon)

    def accept(self) -> dict[str, Any]:
        return {**{name: getattr(self, name).value.strip() for name in LINES},
                "kinds": self.kinds.value}

    async def on_pick_click(self, event: Event) -> bool:
        self.record_history()
        self.close(self.accept())
        return True

    async def on_clear_click(self, event: Event) -> bool:
        """*Clear all*: every line emptied, every kind unticked."""
        for name in LINES:
            getattr(self, name).value = ""
        self.kinds.value = 0
        return True
