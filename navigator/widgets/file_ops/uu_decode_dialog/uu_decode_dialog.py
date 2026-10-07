"""The handlers behind ``uu_decode_dialog.nml``: what it opens on, and what OK means.

``UuDecode``'s part around ``ExecResource(dlgUUDecode)``: the line opens on
the other panel's directory when there is one (``cmPushFirstName``), else
empty -- which is the file's own -- and the boxes on ``UUDecodeOptions``,
kept in ``navigator.ini``'s ``[uucode]``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.events import Event

from navml.history import HISTORY
from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS, UUCodeData
from navigator.widgets.file_ops.commands import ChooseTarget


class UUDecodeDialog(Dialog):
    """*UU Decode*: into which directory, and how."""

    def __init__(self, here: Path | None = None, other: Path | None = None,
                 hidden: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self._here = Path(here) if here is not None else Path.cwd()
        self._hidden = hidden
        if other is not None and Path(other) != self._here:
            HISTORY.add("uudecode", str(other).rstrip("/") + "/")
            self.target.value = str(other).rstrip("/") + "/"
        self.target.entry.select_all()
        self.options.value = SETTINGS.uucode.to_bits(UUCodeData.DECODE)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.tree)

    def accept(self) -> dict[str, Any]:
        """``{"target": text, "uucode": {...}}``: an empty line is the file's
        own directory, as DN took ``.\\``."""
        return {
            "target": self.target.value.strip(),
            "uucode": UUCodeData.from_bits(UUCodeData.DECODE, self.options.value),
        }

    async def on_pick_click(self, event: Event) -> bool:
        self.record_history()
        self.close(self.accept())
        return True

    async def on_tree_click(self, event: Event) -> bool:
        self.spawn(self.choose_target())
        return True

    async def on_choose_target(self, event: ChooseTarget) -> bool:
        self.spawn(self.choose_target())
        return True

    async def choose_target(self) -> None:
        from navigator.widgets.file_ops.copy_dialog.copy_dialog import choose_target_line

        await choose_target_line(self, self._here, self._hidden)
