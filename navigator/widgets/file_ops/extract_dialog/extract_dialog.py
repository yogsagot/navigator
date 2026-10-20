"""The handlers behind ``extract_dialog.nml``: what it opens on, and what OK means.

``TArcDrive.CopyFiles``' part around ``ExecResource(dlgExtract)``: the line
opens on the other panel's directory (``cmPushFirstName``), *Extract with
path names* ticked (``DT.W := 1``).  An empty line is the archive's own
directory, as DN took an empty ``ExtrDir``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.events import Event

from navml.history import HISTORY
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location
from navigator.widgets.file_ops.commands import ChooseTarget

#: The boxes' bits.
WITH_PATHS, TEST_ONLY = 1, 2


class ExtractDialog(Dialog):
    """*Extract files*: where to, and how."""

    def __init__(self, here: Path | Location | None = None, other: str | None = None,
                 hidden: bool = True, test_only: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self._here = here if here is not None else Path.cwd()
        self._hidden = hidden
        if other:
            line = other.rstrip("/") + "/"
            HISTORY.add("copy", line)
            self.target.value = line
        self.target.entry.select_all()
        self.options.value = WITH_PATHS | (TEST_ONLY if test_only else 0)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.tree)

    def accept(self) -> dict[str, Any]:
        """``{"target": text, "paths": bool, "test": bool}``."""
        return {
            "target": self.target.value.strip(),
            "paths": bool(self.options.value & WITH_PATHS),
            "test": bool(self.options.value & TEST_ONLY),
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
