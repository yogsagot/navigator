"""What the delete's *Confirm* box says, and what each of its buttons answers.

The answer is :data:`~navigator.fileerase.NO`, ``YES`` or ``ALL``, or ``None``
for Cancel and Esc, which stops the whole delete as DN's ``Abort`` did.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.fileerase import ALL, NO, YES, NotEmpty, ReadOnly
from navigator.widgets.file_ops.delete_dialog.delete_dialog import cut

#: Each button's width, and the columns between two.
BUTTON, GAP = 11, 2


def describe(question: NotEmpty | ReadOnly) -> str:
    """``dlEraseDirNotEmpty`` or ``dlEraseRO``, after the name."""
    name = escape_caption(cut(question.path.name))
    if isinstance(question, ReadOnly):
        return tr("File {name}\nis write-protected.\nOK to delete it?").format(name=name)
    return tr("Directory {name}\nis not empty.\nDo you wish to delete it?").format(name=name)


class EraseQuery(Dialog):
    """*Confirm*: No, Yes, All or Cancel for a directory; Yes, No, All for a file."""

    def __init__(self, question: NotEmpty | ReadOnly | None = None, **kwargs: Any) -> None:
        if isinstance(question, ReadOnly):
            kwargs.setdefault("kind", "read-only")
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        if question is not None:
            self.details.text = describe(question)

    def slot(self, index: int) -> int:
        """The column of the *index*-th button of the row, which is centred."""
        count = 4 if self.kind == "not-empty" else 3
        wide = count * BUTTON + (count - 1) * GAP
        return max(0, (self.width - wide) // 2) + index * (BUTTON + GAP)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        if self.kind == "not-empty":
            return (self.refuse, self.agree, self.every, self.abandon)
        return (self.agree, self.refuse, self.every)

    async def on_refuse_click(self, event: Event) -> bool:
        self.close(NO)
        return True

    async def on_agree_click(self, event: Event) -> bool:
        self.close(YES)
        return True

    async def on_every_click(self, event: Event) -> bool:
        self.close(ALL)
        return True
