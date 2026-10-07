"""The handlers behind ``uu_encode_dialog.nml``: what it opens on, and what OK means.

``UuEncode``'s part before and after ``ExecResource(dlgUUEncode)``: the line
opens on the file's name with ``.uue``, in the other panel's directory when
there is one (``cmPushFirstName``), and the rest on what was last accepted --
``UUEncodeData``, kept in ``navigator.ini``'s ``[uucode]``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.events import Event

from navml.history import HISTORY
from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS, UUCodeData
from navigator.widgets.file_ops.commands import ChooseTarget


class UUEncodeDialog(Dialog):
    """*UU Encode*: where to, and how."""

    def __init__(self, source: Path | None = None, other: Path | None = None,
                 hidden: bool = True, **kwargs: Any) -> None:
        """*source* is the file; *other* the passive panel's directory, where
        the line puts the encoded file when it is somewhere else."""
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self._source = Path(source) if source is not None else Path.cwd() / "file"
        self._here = self._source.parent
        self._hidden = hidden
        name = self._source.stem + ".uue"
        if other is not None and Path(other) != self._here:
            HISTORY.add("uuencode", str(other).rstrip("/") + "/")
            self.target.value = str(Path(other) / name)
        else:
            self.target.value = name
        self.target.entry.select_all()
        section = SETTINGS.uucode
        self.prefixes.value = section.to_bits(UUCodeData.PREFIXES)
        self.checksum.value = self.checksum.sel = UUCodeData.CHECKSUMS.index(section.checksum)
        self.lines.value = f"{section.lines_per_section:4d}"
        self.format.value = self.format.sel = UUCodeData.LINE_ENDS.index(section.line_ends)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.tree)

    def accept(self) -> dict[str, Any] | None:
        """``{"target": text, "uucode": {...}}``, or None for an empty line.

        *Lines per section* that is not a number is DN's 900, and fewer than
        ten is ten (``NLines``).
        """
        target = self.target.value.strip()
        if not target:
            return None
        text = self.lines.value.strip()
        lines = max(10, int(text)) if text.isdigit() else 900
        return {
            "target": target,
            "uucode": {
                **UUCodeData.from_bits(UUCodeData.PREFIXES, self.prefixes.value),
                "checksum": UUCodeData.CHECKSUMS[self.checksum.value],
                "lines_per_section": lines,
                "line_ends": UUCodeData.LINE_ENDS[self.format.value],
            },
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
