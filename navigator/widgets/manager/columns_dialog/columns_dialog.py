"""What *Columns Setup* answers: the columns ticked, *Brief*, or *Full*."""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navml.widgets.dialog.dialog import Dialog

#: The boxes' columns, in their order (``Panel.DETAIL_ORDER``).
COLUMNS = ("size", "attributes", "owner", "date", "path")


class ColumnsDialog(Dialog):
    """``CM_SetShowParms``'s dialog for one panel: ``("columns", set)``,
    ``("brief",)`` or ``("full",)``."""

    def __init__(self, columns: frozenset[str] = frozenset(COLUMNS), listing: bool = False,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        #: Whether the panel shows a *Find:* listing: only then is *Path* a box.
        self.keys_shown = COLUMNS if listing else COLUMNS[:-1]
        self.show.items = list(self.show.items)[: len(self.keys_shown)]
        self.show.value = sum(1 << index for index, key in enumerate(self.keys_shown) if key in columns)
        self._kept = frozenset(columns) - set(self.keys_shown)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.brief, self.full)

    def accept(self) -> tuple[str, frozenset[str]]:
        ticked = {key for index, key in enumerate(self.keys_shown) if self.show.value & (1 << index)}
        return "columns", frozenset(ticked) | self._kept

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True

    async def on_brief_click(self, event: Event) -> bool:
        self.close(("brief",))
        return True

    async def on_full_click(self, event: Event) -> bool:
        self.close(("full",))
        return True
