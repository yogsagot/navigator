"""The list inside *Windows Manager*: DOS Navigator's ``TWindowList``.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` whose items are the
windows themselves, so what the cursor is on is the window to act on and no
parallel list has to be kept in step.  A row is the window's
:meth:`~navml.widgets.window.Window.list_name`, as ``TWindowList.GetText``
asked each window for its ``cmGetName``, after the window's number: DOS
Navigator showed none, and Win+1 .. Win+9 need one to be seen somewhere.
A digit typed in the list chooses that window outright, as Enter would --
Alt+0 then 2 is Win+2 for a terminal that sends neither Super nor
Alt+Shift+F2.

**The names are read once, when a window enters the list.**  A file manager
names itself after its active panel, and which panel is active is a question
the focus answers -- and while this list is up the focus is in the dialog.
Asked while painting, every file manager would answer with its left panel.
"""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent

from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent


class WindowList(ListViewer):
    """The windows of a desktop, top first."""

    #: Enter or a double click, carrying the window as its ``node``.  The
    #: tree's event rather than one of its own: a list row was chosen, and
    #: that is all ``ChosenEvent`` says.
    emits = (ChosenEvent,)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._names: dict[int, str] = {}

    def show(self, windows: list[Any]) -> None:
        """List *windows*, naming the ones not seen before.

        A new list every time, because the reactive layer counts a change
        only when the collection is replaced.
        """
        for window in windows:
            if id(window) not in self._names:
                self._names[id(window)] = window.list_name()
        self.items = [window for window in windows if self._names[id(window)]]

    def row_text(self, index: int, item: Any) -> str:
        number = str(item.number) if item.number else " "
        return f" {number} {self._names.get(id(item), '')}"

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches(*"123456789"):
            number = int(event.key)
            index = next((i for i, w in enumerate(self.items) if w.number == number), None)
            if index is None:
                return True  # no such window: swallowed, not typed anywhere
            self.cursor = index
            return await self.choose()
        return await super().on_key(event)

    async def choose(self) -> bool:
        if self.selected is None:
            return False
        await self.emit(ChosenEvent(self.selected))
        return True
