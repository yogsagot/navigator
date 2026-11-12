"""What *Screen Saver Setup* opens on and what OK means: ``TSaversDialog``'s
``Awaken`` and ``GetData``.

The available savers are DN's four, then the programs in ``savers/``
(:func:`navigator.lib.appearance.savers.external`, read once as the dialog opens -- one
directory's names, as DN's ``FindFirst`` read ``SSAVERS``).  *Add* puts the
one at the available list's cursor among the selected, once; *Remove* takes
the one at the selected list's cursor out.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navkit.i18n import tr


from navigator.lib.appearance import savers
from navigator.widgets.setup.settings_page import SettingsPage


class SaversPage(SettingsPage):
    """Which savers take turns, after how long, and the mouse's corners."""

    def __init__(self, available: list[str] | None = None, **kwargs: Any) -> None:
        # *Time* and *Mouse* say what they edit (``key:``); the two lists are
        # made here.
        super().__init__(**kwargs)
        names = list(savers.BUILT_IN) + (savers.external() if available is None else available)
        self.offered.items = [savers.caption(name) for name in names]
        self.chosen.items = [savers.caption(name) for name in self.section.names()]
        self.chosen.tooltip = tr("The savers that take turns when the screen rests; Remove takes the one at the cursor out")
        self.offered.tooltip = tr("Every saver there is; Add puts the one at the cursor among the selected")

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
            **super().accept(),
            "selected": ",".join(savers.name_of(text) for text in self.chosen.items),
        }
