"""What *Replace this occurence?* answers: ``"yes"``, ``"all"``, ``"no"`` or None for Cancel.

DN placed the box above or below the line found so as not to hide it; a navml
dialog is centred.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event

from navml.widgets.dialog.dialog import Dialog


class ReplaceQuery(Dialog):
    """``MessageBoxRect(dlQueryReplace, mfYesButton + mfAllButton + mfNoButton + mfCancelButton)``."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.every, self.skip, self.abandon)

    async def on_pick_click(self, event: Event) -> bool:
        self.close("yes")
        return True

    async def on_every_click(self, event: Event) -> bool:
        self.close("all")
        return True

    async def on_skip_click(self, event: Event) -> bool:
        self.close("no")
        return True
