"""What the *Confirm* query says, and what each of its buttons answers.

The answer is a :class:`~navigator.lib.file_ops.filecopy.OverwriteAnswer`, or ``None`` for
Cancel, which stops the whole copy as DN's ``cmCancel`` did.  *Rename* asks
for the new name in a second box before it answers -- DN's ``InputBox``,
``Rename file`` / ``~N~ew name``, opened on the whole destination path, so
the file may go elsewhere -- and a rename abandoned there, or left empty,
skips the file, as DN's ``DoSkip`` did.
"""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.config import country
from navigator.lib.file_ops.filecopy import Overwrite, OverwriteAnswer


def stamp(mtime: float) -> str:
    """``MakeDate`` as the query showed it, ``DATE (hh:mm)``, in *Country
    support*'s format -- with the four-digit year the panels have, where
    DN's was ``YY``."""
    return f"{country.date_text(mtime)} ({country.time_text(mtime, file=True)})"


def describe(question: Overwrite, width: int = 40) -> str:
    """``File NAME`` and ``dlFCOver``: the sizes right-aligned to one width.
    NAME is the whole destination, its middle given up to fit *width*, as
    DN's ``Cut(NName, 40)``."""
    from navigator.widgets.file_ops.delete_dialog.delete_dialog import cut

    name = cut(str(question.dest), width)
    sizes = [f"{question.source_size:,}", f"{question.dest_size:,}"]
    wide = max(len(s) for s in sizes)
    return "\n".join((
        tr("File {name}\nalready exists in destination directory").format(name=escape_caption(name)),
        "",
        tr_n("  Source:  {date}  {size} byte", "  Source:  {date}  {size} bytes", question.source_size,
             date=stamp(question.source_mtime), size=f"{sizes[0]:>{wide}}"),
        tr_n("Existing:  {date}  {size} byte", "Existing:  {date}  {size} bytes", question.dest_size,
             date=stamp(question.dest_mtime), size=f"{sizes[1]:>{wide}}"),
    ))


class OverwriteQuery(Dialog):
    """*Confirm*: overwrite, append, rename, skip, or stop."""

    def __init__(self, question: Overwrite | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._question = question
        if question is not None:
            self.details.text = describe(question)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.overwrite, self.append, self.rename, self.skip, self.abandon)

    def _answer(self, action: str, name: str = "") -> None:
        self.close(OverwriteAnswer(action, all=bool(self.for_all.value & 1), name=name))

    async def ask_name(self) -> None:
        """DN's ``InputBox('Rename file', '~N~ew name')``, opened on the whole
        destination (``P^.NewName``), all of it selected so a bare name typed
        replaces it.  Abandoned or left empty, the file is skipped (DN's
        ``DoSkip``) -- this file only, whatever *for all* says."""
        from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

        box = MkdirDialog()
        box.title = tr("Rename file")
        if self._question is not None:
            box.entry.value = str(self._question.dest)
            box.entry.entry.select_all()
        box.entry.label_text = tr("~N~ew name")
        box.entry.label_width = 10
        box.entry.history_id = ""
        name = await box.execute(self.application)
        if name and name.strip():
            self._answer("rename", name.strip())
        else:
            self.close(OverwriteAnswer("skip"))
