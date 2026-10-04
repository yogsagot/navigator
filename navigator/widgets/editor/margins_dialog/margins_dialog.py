"""What OK means in *Format Margins*: ``SetFormat``.

The three numbers as they stand, each one that does not read as a number
left as it was (``Val`` failing kept the old value), then put right as
:func:`navigator.editor.paragraph.fix_margins` says.  The answer is
``(left, right, indent)``, or None for Cancel.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event

from navml.widgets.dialog.dialog import Dialog

from navigator.editor.paragraph import fix_margins


class MarginsDialog(Dialog):
    """*Format Margins*: the margins of one editor."""

    def __init__(self, margins: tuple[int, int, int] = (0, 78, 5), **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.margins = margins
        for field, value in zip((self.left, self.right, self.indent), margins):
            field.value = str(value)
        self.left.entry.select_all()

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.helper)

    def accept(self) -> tuple[int, int, int]:
        values = []
        for field, old in zip((self.left, self.right, self.indent), self.margins):
            try:
                values.append(int(field.value.strip()))
            except ValueError:
                values.append(old)
        return fix_margins(*values)

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True
