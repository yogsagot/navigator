"""The handlers behind ``file_history_dialog.nml``: what the buttons do.

``ViewHistoryMenu``/``EditHistoryMenu`` ran the dialog and opened the record
under the cursor on ``cmOK``.  Here the answer is that record's path, and the
caller opens it.  *Delete record* stays in the dialog, as its ``cmYes``
broadcast did; the last record going ends it, since an empty history was never
shown at all.  Cancel needs no handler: ``Dialog.on_click`` dismisses for any
button nobody claimed.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event

from navml.widgets.dialog.dialog import Dialog


class FileHistoryDialog(Dialog):
    """The records of *model* -- ``ViewRecord`` or ``EditRecord`` -- newest first."""

    def __init__(self, model: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.records.show(model)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        """This dialog's own buttons, which the tab order puts after the list."""
        return (self.pick, self.drop, self.abandon)

    def accept(self) -> Any:
        """The path of the record under the cursor."""
        record = self.records.selected
        return None if record is None else record.path

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True

    async def on_records_chosen(self, event: Any) -> bool:
        """Enter in the list is Open."""
        self.close(self.accept())
        return True

    async def on_drop_click(self, event: Event) -> bool:
        self.records.delete_selected()
        if not self.records.items:
            self.close(None)
            return True
        self.records.focus()
        return True
