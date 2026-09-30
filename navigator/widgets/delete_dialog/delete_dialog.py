"""The handlers behind ``delete_dialog.nml``: what it asks, and what *Yes* means.

*Recursive delete* is remembered for the session, as Copy's mode and options
and Create symlink's *Relative link* are, and starts unticked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from navkit.reactive import unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.fileerase import EraseRequest

#: The *Recursive delete* box as the last accepted dialog left it.
_session = {"recursive": False}

#: The check box's bit.
RECURSIVE = 0x01

#: DN's ``Cut(S, 40)``: a longer name loses its middle.
NAME_WIDTH = 40


def cut(name: str, width: int = NAME_WIDTH) -> str:
    """*name*, its middle given up to ``...`` if it is wider than *width*."""
    if len(name) <= width:
        return name
    head = (width - 3) // 2
    return name[:head] + "..." + name[len(name) - (width - 3 - head) :]


def prompt_for(entries: Sequence[Any]) -> str:
    """``file ~NAME~?``, ``directory ~NAME~?``, ``these ~3 files~?``."""
    if len(entries) == 1:
        entry = entries[0]
        kind = "directory" if entry.is_dir else "file"
        return f"{kind} ~{escape_caption(cut(entry.name))}~?"
    return f"these ~{len(entries)} files~?"


class DeleteDialog(Dialog):
    """*Delete* (F8, Del): whether, and whether into non-empty directories."""

    def __init__(
        self,
        entries: Sequence[Any] = (),
        here: Path | None = None,
        **kwargs: Any,
    ) -> None:
        """*entries* are the panel's selection in *here*."""
        super().__init__(**kwargs)
        self._entries = list(entries)
        self._here = Path(here) if here is not None else Path.cwd()
        self.message.visible = False
        # ``mfYesNoConfirm``: Yes and No, where No is Cancel's answer.
        unbind(self.ok, Button.text)
        self.ok.text = "~Y~es"
        unbind(self.cancel, Button.text)
        self.cancel.text = "~N~o"
        self.prompt_caption.text = prompt_for(self._entries)
        self.options.value = RECURSIVE if _session["recursive"] else 0

    def focusable(self) -> list[Any]:
        """*Yes* first, as the message box's focus was, and the box after the buttons."""
        order = super().focusable()
        return [w for w in order if w is not self.options] + [self.options]

    def accept(self) -> EraseRequest:
        recursive = bool(self.options.value & RECURSIVE)
        _session["recursive"] = recursive
        return EraseRequest(
            sources=[self._here / entry.name for entry in self._entries],
            recursive=recursive,
        )
