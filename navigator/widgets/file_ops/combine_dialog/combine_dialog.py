"""The handlers behind ``combine_dialog.nml``: what it opens on, and what OK means.

``LongCopy``'s ``CopyDialog`` for a combine: the label names the part, and
the line opens on the other panel's directory when there is one
(``cmPushFirstName``), else on the history's last (DN's ``HistoryStr(hsFBBCopy,
1)``), else empty -- the parts' own directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.events import Event
from navkit.i18n import tr
from navkit.text import escape_caption

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location


class CombineDialog(Dialog):
    """*Combine file*: where the set goes back together."""

    def __init__(self, name: str = "", here: Path | Location | None = None, other: Path | None = None,
                 hidden: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._here = here if here is not None else Path.cwd()
        self._hidden = hidden
        if name:
            self.target_caption.text = tr("~C~ombine {name} to").format(name=escape_caption(name))
        from navigator.widgets.file_ops.split_dialog.split_dialog import opening_target

        self.target.value = opening_target(other, self._here)
        self.target.entry.select_all()

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.tree)

    def accept(self) -> dict[str, Any]:
        """``{"target": text}``: an empty line is the parts' own directory."""
        return {"target": self.target.value.strip()}

    async def on_pick_click(self, event: Event) -> bool:
        self.record_history()
        self.close(self.accept())
        return True

    async def choose_target(self) -> None:
        from navigator.widgets.file_ops.copy_dialog.copy_dialog import choose_target_line

        await choose_target_line(self, self._here, self._hidden)
