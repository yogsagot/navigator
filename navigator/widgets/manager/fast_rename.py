"""Alt+F6: the name at the cursor edited where it stands -- DN's ``CM_RenameSingle``.

DOS Navigator laid a ``TInputFName`` (SWE.PAS) over the name in the panel
and renamed the file when it ended.  ``TInputString`` ended on Enter, Esc,
Up, Down, Left at the line's start and Right at its end; whatever ended it
other than Enter was handed back to the panel afterwards, so Down renames
and moves on.  Here Esc cancels: DN renamed even then, which a key that
reads as *never mind* everywhere else should not do.

``TInputFName`` was laid out as an 8.3 name, its dot fixed in the ninth
cell; a POSIX name has no such shape, and the line is as wide as the name
column.  DN's filter kept DOS's forbidden characters out; here only ``/``
cannot be in a name, and is not typed.
"""

from __future__ import annotations

import asyncio
from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import bind

from navml.widgets.dialog.input_line import InputLine


class FastRenameLine(InputLine):
    """An input line over a panel's name, run like a dialog."""

    #: The keys that end it and are then the panel's (``TInputString``).
    PASSED_ON = ("up", "down")

    def __init__(self, name: str, x: int, y: int, width: int, **kwargs: Any) -> None:
        """Over the name whose first cell is *x*, *y*, *width* cells wide: one
        cell further left, where the line keeps its scroll arrow, so the text
        stays where the name was."""
        super().__init__(**kwargs)
        x, width = max(0, x - 1), width + 1
        self.modal = True
        self.dims_behind = False
        self.x = bind(lambda o: x)
        self.y = bind(lambda o: y)
        self.width = bind(lambda o: width)
        self.height = bind(lambda o: 1)
        self.value = name
        # ``SetData`` selected it all, the cursor at the end.
        self.select_all()
        self._answer: asyncio.Future[Any] | None = None

    async def execute(self, app: Any) -> tuple[str | None, KeyEvent | None]:
        """Show it; ``(name, key)`` once it ends -- name None for Esc, key the
        one to hand back to the panel, if any."""
        self._answer = asyncio.get_running_loop().create_future()
        app.overlay(self)
        self.focus()
        try:
            return await self._answer
        finally:
            if self.parent is not None:
                self.parent.remove(self)

    def _end(self, name: str | None, key: KeyEvent | None = None) -> None:
        if self._answer is not None and not self._answer.done():
            self._answer.set_result((name, key))

    async def on_key(self, event: KeyEvent) -> bool:
        start, end = self.selection
        selected = start != end
        if event.matches("escape"):
            self._end(None)
        elif event.matches("enter"):
            self._end(self.value)
        elif event.matches(*self.PASSED_ON):
            self._end(self.value, event)
        elif event.matches("left") and self.cursor == 0 and not selected:
            self._end(self.value, event)
        elif event.matches("right") and self.cursor == len(self.value) and not selected:
            self._end(self.value, event)
        elif event.char == "/":
            return True
        else:
            await super().on_key(event)
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if 0 <= event.x < self.width and event.y == 0:
            return await super().on_mouse_click(event)
        if event.action == "press":
            self._end(None)
        return True
