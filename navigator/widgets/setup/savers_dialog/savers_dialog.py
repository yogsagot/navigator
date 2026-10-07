"""What *Screen Saver Setup* opens on and what OK means: ``TSaversDialog``'s
``Awaken`` and ``GetData``.

The available savers are DN's four, then the programs in ``savers/``
(:func:`navigator.savers.external`, read once as the dialog opens -- one
directory's names, as DN's ``FindFirst`` read ``SSAVERS``).  *Add* puts the
one at the available list's cursor among the selected, once; *Remove* takes
the one at the selected list's cursor out.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event

from navml.widgets.dialog.dialog import Dialog

from navigator import savers
from navigator.settings import SETTINGS, SaversData


class SaversDialog(Dialog):
    """Which savers take turns, after how long, and the mouse's corners."""

    def __init__(self, section: SaversData | None = None, available: list[str] | None = None,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.savers
        names = [name for name, _ in savers.BUILT_IN] + (savers.external() if available is None else available)
        self.offered.items = [savers.caption(name) for name in names]
        self.chosen.items = [savers.caption(name) for name in self.section.names()]
        self.time.value = self.time.sel = SaversData.TIMES.index(self.section.time)
        self.mouse.value = 1 if self.section.mouse else 0

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.join, self.drop, *super().buttons_row)

    async def on_join_click(self, event: Event) -> bool:
        picked = self.offered.selected
        if picked is not None and picked not in self.chosen.items:
            self.chosen.items = [*self.chosen.items, picked]
        return True

    async def on_drop_click(self, event: Event) -> bool:
        items = list(self.chosen.items)
        cursor = self.chosen.cursor
        if 0 <= cursor < len(items):
            del items[cursor]
            self.chosen.items = items
            self.chosen.cursor = min(cursor, max(0, len(items) - 1))
        return True

    def accept(self) -> dict[str, Any]:
        return {
            "selected": ",".join(savers.name_of(text) for text in self.chosen.items),
            "time": SaversData.TIMES[self.time.value],
            "mouse": bool(self.mouse.value & 1),
        }
