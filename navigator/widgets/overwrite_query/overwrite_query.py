"""What the *Confirm* query says, and what each of its buttons answers.

The answer is a :class:`~navigator.filecopy.OverwriteAnswer`, or ``None`` for
Cancel, which stops the whole copy as DN's ``cmCancel`` did.  *Rename* asks
for the new name in a second box before it answers -- DN's ``InputBox``,
``Rename file`` / ``~N~ew name`` -- and a rename abandoned there puts this
query back rather than skipping the file.
"""

from __future__ import annotations

import time
from typing import Any

from navkit.events import Event

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.filecopy import Overwrite, OverwriteAnswer


def stamp(mtime: float) -> str:
    """``MakeDate`` as the query showed it: ``DD-MM-YY (hh:mm)``."""
    return time.strftime("%d-%m-%y (%H:%M)", time.localtime(mtime))


def describe(question: Overwrite, width: int = 40) -> str:
    """``File NAME`` and ``dlFCOver``: the sizes right-aligned to one width."""
    name = question.dest.name
    if len(name) > width:
        name = name[: width - 3] + "..."
    sizes = [f"{question.source_size:,}", f"{question.dest_size:,}"]
    wide = max(len(s) for s in sizes)
    return "\n".join((
        f"File {escape_caption(name)}",
        "already exists in destination directory",
        "",
        f"  Source:  {stamp(question.source_mtime)}  {sizes[0]:>{wide}} bytes",
        f"Existing:  {stamp(question.dest_mtime)}  {sizes[1]:>{wide}} bytes",
    ))


class OverwriteQuery(Dialog):
    """*Confirm*: overwrite, append, rename, skip, or stop."""

    def __init__(self, question: Overwrite | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self._question = question
        if question is not None:
            self.details.text = describe(question)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.overwrite, self.append, self.rename, self.skip, self.abandon)

    def _answer(self, action: str, name: str = "") -> None:
        self.close(OverwriteAnswer(action, all=bool(self.for_all.value & 1), name=name))

    async def on_overwrite_click(self, event: Event) -> bool:
        self._answer("overwrite")
        return True

    async def on_append_click(self, event: Event) -> bool:
        self._answer("append")
        return True

    async def on_skip_click(self, event: Event) -> bool:
        self._answer("skip")
        return True

    async def on_rename_click(self, event: Event) -> bool:
        self.spawn(self.ask_name())
        return True

    async def ask_name(self) -> None:
        """DN's ``InputBox('Rename file', '~N~ew name')``, opened on the old name."""
        from navigator.widgets.mkdir_dialog import MkdirDialog

        box = MkdirDialog()
        box.title = "Rename file"
        if self._question is not None:
            box.entry.value = self._question.dest.name
            box.entry.entry.select_all()
        box.entry.label_text = "~N~ew name"
        box.entry.label_width = 10
        box.entry.history_id = ""
        name = await box.execute(self.application)
        if name:
            self._answer("rename", name)
