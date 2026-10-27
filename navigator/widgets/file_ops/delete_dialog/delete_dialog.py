"""The handlers behind ``delete_dialog.nml``: what it asks, and what *Yes* means.

*Recursive delete* is remembered for the session, as Copy's mode and options
and Create symlink's *Relative link* are, and starts unticked.

*Move to Trash* is a second box, not DN's: offered (and ticked) only when
File Manager Setup's *F8 moves to Trash* is on and every entry is on the
disk.  Unticked, the entries are erased for good, as DN erased them; the
first line says which of the two *Yes* does.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from navkit.i18n import tr, tr_n
from navkit.reactive import bind, unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location
from navigator.lib.file_ops.filecopy import shown
from navigator.lib.file_ops.fileerase import EraseRequest

#: The *Recursive delete* box as the last accepted dialog left it.
_session = {"recursive": False}

#: The check boxes' bits.
RECURSIVE = 0x01
TRASH = 0x02

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
        name = escape_caption(cut(entry.name))
        if entry.is_dir:
            return tr("directory ~{name}~?").format(name=name)
        return tr("file ~{name}~?").format(name=name)
    return tr_n("these ~{n} file~?", "these ~{n} files~?", len(entries))


class DeleteDialog(Dialog):
    """*Delete* (F8, Del): whether, and whether into non-empty directories."""

    def __init__(
        self,
        entries: Sequence[Any] = (),
        here: Path | None = None,
        trash: bool = False,
        **kwargs: Any,
    ) -> None:
        """*entries* are the panel's selection in *here*; *trash* offers *Move to Trash*."""
        super().__init__(**kwargs)
        self._entries = list(entries)
        self._here = Location.of(here if here is not None else Path.cwd())
        self.message.visible = False
        # ``mfYesNoConfirm``: Yes and No, where No is Cancel's answer.
        unbind(self.ok, Button.text)
        self.ok.text = tr("~Y~es")
        unbind(self.cancel, Button.text)
        self.cancel.text = tr("~N~o")
        self.prompt_caption.text = prompt_for(self._entries)
        self.options.value = RECURSIVE if _session["recursive"] else 0
        if trash:
            self.options.items = [tr("~R~ecursive delete"), tr("Move to ~T~rash")]
            self.options.height = 2
            # A row more, so the buttons keep their distance from the boxes.
            self.modal_height += 1
            self.options.value |= TRASH
            options = self.options
            self.prompt_head.text = bind(
                lambda o: tr("Do you wish to move to the Trash") if options.value & TRASH
                else tr("Do you wish to delete"))

    def focusable(self) -> list[Any]:
        """*Yes* first, as the message box's focus was, and the box after the buttons."""
        order = super().focusable()
        return [w for w in order if w is not self.options] + [self.options]

    def accept(self) -> EraseRequest:
        recursive = bool(self.options.value & RECURSIVE)
        _session["recursive"] = recursive
        return EraseRequest(
            sources=[shown(entry.path_in(self._here)) for entry in self._entries],
            recursive=recursive,
            trash=bool(self.options.value & TRASH),
        )
