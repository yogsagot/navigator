"""What Replace in files' *Replace* box says, and what each of its buttons answers.

The answer is :data:`~navigator.lib.file_ops.filereplace.YES`, ``ALL`` or
``SKIP``, or ``None`` for Cancel and Esc, which stops the whole replace.
"""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops.filereplace import ALL, SKIP, YES, ReplaceQuestion
from navigator.widgets.file_ops.delete_dialog.delete_dialog import cut
from navigator.widgets.file_ops.replace_query.change_list import rows_of


def describe(question: ReplaceQuestion) -> str:
    """The file's name, and how many replacements -- and changed lines past
    what the list holds."""
    text = tr_n("File {name}: {count} replacement", "File {name}: {count} replacements", question.count,
                name=escape_caption(cut(question.path.name)), count=question.count)
    if question.more:
        text += "\n" + tr_n("{count} more change is not listed", "{count} more changes are not listed",
                            question.more, count=question.more)
    return text


class ReplaceQuery(Dialog):
    """*Replace*: Yes, All, Skip or Cancel, over the lines that change."""

    def __init__(self, question: ReplaceQuestion | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if question is not None:
            self.details.text = describe(question)
            self.changes.items = rows_of(question.changes)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.agree, self.every, self.skip, self.abandon)

