"""The handlers behind ``link_dialog.nml``: what it opens on, and what OK means.

Seeded as the Copy dialog is -- the other panel's directory, a single file's
name after it, that directory in the history -- because a link is most often
wanted where a copy would have gone.  *Relative link* is remembered for the
session, as Copy's mode and options are.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from navkit.events import Event

from navml.history import HISTORY
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.file_ops.commands import ChooseTarget
from navigator.filelink import LinkRequest
from navigator.widgets.file_ops.copy_dialog.copy_dialog import choose_target_line, target_for

#: The *Relative link* box as the last accepted dialog left it.
_session = {"relative": False}

#: The check box's bit.
RELATIVE = 0x01


def prompt_for(entries: Sequence[Any]) -> str:
    """``Create symlink to file NAME in``, ``… Directory NAME …``, ``… 3 files …``."""
    if len(entries) == 1:
        entry = entries[0]
        kind = "Directory" if entry.is_dir else "file"
        what = f"{kind} ~{escape_caption(entry.name)}~"
    else:
        what = f"~{len(entries)} files~"
    return f"Create ~s~ymlink to {what} in"


class LinkDialog(Dialog):
    """*Create symlink* (Shift+F5): where the links go, and what they hold."""

    def __init__(
        self,
        entries: Sequence[Any] = (),
        here: Path | None = None,
        other: Path | None = None,
        hidden: bool = True,
        **kwargs: Any,
    ) -> None:
        """*entries* are the panel's selection in *here*; *other* is the passive panel's directory."""
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self._entries = list(entries)
        self._here = Path(here) if here is not None else Path.cwd()
        self._hidden = hidden
        self.prompt_caption.text = prompt_for(self._entries)
        if other is not None and Path(other) != self._here:
            HISTORY.add("link", str(other).rstrip("/") + "/")
        self.target.value = target_for(self._entries, self._here, other, move=False)
        self.target.entry.select_all()
        self.options.value = RELATIVE if _session["relative"] else 0

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.tree, self.help)

    def accept(self) -> LinkRequest | None:
        """The request, or ``None`` for an empty line -- what Cancel says."""
        target = self.target.value.strip()
        if not target:
            return None
        relative = bool(self.options.value & RELATIVE)
        _session["relative"] = relative
        return LinkRequest(
            sources=[self._here / entry.name for entry in self._entries],
            target=target,
            relative=relative,
        )

    # -- the buttons -----------------------------------------------------------

    async def on_pick_click(self, event: Event) -> bool:
        self.record_history()
        self.close(self.accept())
        return True

    async def on_tree_click(self, event: Event) -> bool:
        self.spawn(choose_target_line(self, self._here, self._hidden))
        return True

    async def on_choose_target(self, event: ChooseTarget) -> bool:
        self.spawn(choose_target_line(self, self._here, self._hidden))
        return True
