"""The list inside *File View History* and *File Edit History*: DN's ``TTHistList``.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` over a history model's
records, newest first.  A row is the record's flag and its path, the flag
painted ``■`` for a pinned record as ``TTHistList.GetText`` painted it.  The
keys are ``TTHistList.HandleEvent``'s:

* **Space** (and Insert) pins or unpins the record under the cursor:
  ``SelectItem`` flipping the ``'+'``.
* **Delete** forgets it, unless it is pinned -- DN beeped, here nothing happens.
* **Shift+Up / Shift+Down** move it a row, trading places with its neighbour.
* **Left / Right** jump to the previous or next pinned record.
* **Enter** and a double click open it -- the dialog's default *Open*.

Every change goes to the table at once, and the rows are read back from it.
"""

from __future__ import annotations

from typing import Any

from navkit.capabilities import GLYPHS_UNICODE
from navkit.events import KeyEvent
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent


class FileRecordList(ListViewer):
    """The records of one history model, newest first."""

    emits = (ChosenEvent,)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: The model the rows come from: ``ViewRecord`` or ``EditRecord``.
        self.model: Any = None

    def show(self, model: Any) -> None:
        """List *model*'s records."""
        self.model = model
        self.refresh()

    def refresh(self) -> None:
        """Read the records again; a new list, so the change counts."""
        self.items = [] if self.model is None else self.model.ordered()

    def row_text(self, index: int, item: Any) -> str:
        mark = ("■" if self.glyphs >= GLYPHS_UNICODE else "+") if item.pinned else " "
        return f"{mark}{item.path}"

    async def choose(self) -> bool:
        if self.selected is None:
            return False
        await self.emit(ChosenEvent(self.selected))
        return True

    # -- TTHistList's keys -------------------------------------------------------

    def toggle_pin(self) -> None:
        record = self.selected
        if record is not None:
            self.model.toggle_pin(record.path)
            self.refresh()

    def delete_selected(self) -> bool:
        """Forget the record under the cursor; a pinned one stays.  Whether it went."""
        record = self.selected
        if record is None or not self.model.forget(record.path):
            return False
        self.refresh()
        return True

    def move_selected(self, delta: int) -> None:
        """Trade the record under the cursor with the one *delta* rows away."""
        other = self.cursor + delta
        record = self.selected
        if record is None or not 0 <= other < len(self.items):
            return
        self.model.swap(record.path, self.items[other].path)
        self.refresh()
        self.cursor = other

    def jump_pinned(self, step: int) -> None:
        """``ScanMarked``: the nearest pinned record that way, if there is one."""
        index = self.cursor + step
        while 0 <= index < len(self.items):
            if self.items[index].pinned:
                self.cursor = index
                return
            index += step

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        if event.matches("space") or event.matches("insert"):
            self.toggle_pin()
        elif event.matches("delete"):
            self.delete_selected()
        elif event.matches("shift+up"):
            self.move_selected(-1)
        elif event.matches("shift+down"):
            self.move_selected(1)
        elif event.matches("left"):
            self.jump_pinned(-1)
        elif event.matches("right"):
            self.jump_pinned(1)
        else:
            return await super().on_key(event)
        return True
