"""The handlers behind ``calculate_checksums_dialog.nml``: what it opens on,
and what OK means.

It opens on the digest and the way of writing last accepted, kept in
``navigator.ini``'s ``[checksum]``, and on a list named after the panel's
directory; the name's extension follows the digest chosen.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navkit.reactive import effect

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops.checksum import default_list_name, with_extension
from navigator.settings import SETTINGS, ChecksumData


class CalculateChecksumsDialog(Dialog):
    """*Calculate Checksums*: which digest, one list or a list per file, and
    the one list's name."""

    def __init__(self, directory_name: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        section = SETTINGS.checksum
        self.algorithm.value = self.algorithm.sel = ChecksumData.ALGORITHMS.index(section.algorithm)
        self.mode.value = self.mode.sel = ChecksumData.MODES.index(section.mode)
        self.list_name.value = default_list_name(directory_name, section.algorithm)
        self.list_name.entry.select_all()
        self._named = section.algorithm

    def mounted(self) -> None:
        super().mounted()
        effect(self, CalculateChecksumsDialog._follow_algorithm)

    def _follow_algorithm(self) -> None:
        """The list's extension changed with the digest."""
        algorithm = ChecksumData.ALGORITHMS[self.algorithm.value]
        if algorithm != self._named:
            self._named = algorithm
            name = self.list_name.value.strip()
            if name:
                self.list_name.value = with_extension(name, algorithm)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon)

    def accept(self) -> dict[str, str] | None:
        """``{"algorithm", "mode", "name"}``; None for one list with no name."""
        mode = ChecksumData.MODES[self.mode.value]
        name = self.list_name.value.strip()
        if mode == "combined" and not name:
            return None
        return {"algorithm": ChecksumData.ALGORITHMS[self.algorithm.value], "mode": mode, "name": name}

    async def on_pick_click(self, event: Event) -> bool:
        if ChecksumData.MODES[self.mode.value] == "combined":
            self.record_history()
        self.close(self.accept())
        return True
