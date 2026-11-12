"""The handlers behind ``split_dialog.nml``: what it opens on, and what OK means.

``LongCopy``'s ``CopyDialog`` for a split: the label names the file
(``'~'+GetName(fn1)+'~'+dlSplit_To``), and the line opens on the other
panel's directory when there is one (``cmPushFirstName``), else on the
history's last -- empty, which is the file's own directory, when there is
none.  The part size and the box are ``[split]``'s.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.events import Event
from navkit.i18n import tr
from navkit.text import escape_caption

from navml.history import HISTORY
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location
from navigator.lib.file_ops.splitfile import SplitError, parse_size
from navigator.settings import SETTINGS


def opening_target(other: Path | None, here: Path | Location) -> str:
    """What Split's and Combine's line opens on, as DN's ``LongCopy``: the
    other panel's directory (``cmPushFirstName``), put in the history --
    else the history's last (``HistoryStr(hsFBBCopy, 1)``), else empty, the
    file's own directory."""
    if other is not None and Path(other) != here:
        text = str(other).rstrip("/") + "/"
        HISTORY.add("splitfile", text)
        return text
    used = HISTORY.entries("splitfile")
    return used[0] if used else ""


class SplitDialog(Dialog):
    """*Split file*: where to, and in parts how large."""

    def __init__(self, name: str = "", here: Path | Location | None = None, other: Path | None = None,
                 hidden: bool = True, **kwargs: Any) -> None:
        """*name* is the file's; *here* its directory; *other* the passive
        panel's directory, which the line opens on when it is somewhere else."""
        super().__init__(**kwargs)
        self._here = here if here is not None else Path.cwd()
        self._hidden = hidden
        if name:
            self.target_caption.text = tr("~S~plit {name} to").format(name=escape_caption(name))
        self.target.value = opening_target(other, self._here)
        self.target.entry.select_all()
        self.size.value = SETTINGS.split.size
        self.options.value = 1 if SETTINGS.split.checksum else 0

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.tree)

    def valid(self) -> bool:
        try:
            parse_size(self.size.value)
        except SplitError as error:
            if self.application is not None:
                box = Dialog(title=tr("Error"), prompt=escape_caption(str(error)), buttons="ok")
                self.spawn(box.execute(self.application))
            return False
        return True

    def accept(self) -> dict[str, Any]:
        """``{"target": text, "size": bytes, "split": {...}}``: an empty
        line is the file's own directory."""
        return {
            "target": self.target.value.strip(),
            "size": parse_size(self.size.value),
            "split": {"size": self.size.value.strip(), "checksum": bool(self.options.value & 1)},
        }

    async def on_pick_click(self, event: Event) -> bool:
        if not self.valid():
            self.size.entry.focus()
            return True
        self.record_history()
        self.close(self.accept())
        return True

    async def choose_target(self) -> None:
        from navigator.widgets.file_ops.copy_dialog.copy_dialog import choose_target_line

        await choose_target_line(self, self._here, self._hidden)
