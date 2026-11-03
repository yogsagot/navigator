"""The SSH connection manager's list: a ``ListViewer`` that says when a row is
chosen -- clicked, even the one already under the cursor, or Space on it --
which a cursor that did not move cannot say for itself, and when one is
double-clicked, which connects to it.  Enter stays the dialog's, *Connect*."""

from __future__ import annotations

from typing import Any, Callable

from navkit.events import KeyEvent, MouseClickEvent

from navml.widgets.dialog.list_viewer import ListViewer


class SavedList(ListViewer):
    """The kept connections, one a row."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: Called with a row's index when that row is chosen.
        self.on_choose: Callable[[int], Any] | None = None
        #: Called with a row's index when that row is double-clicked.
        self.on_activate: Callable[[int], Any] | None = None

    def _chose(self, index: int | None) -> None:
        if index is not None and 0 <= index < len(self.items) and self.on_choose is not None:
            self.on_choose(index)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        handled = await super().on_mouse_click(event)
        if handled and not event.is_wheel and event.action == "press" and event.button == "left":
            self._chose(self.index_at(event.x, event.y))
        return handled

    async def on_double_click(self, event: MouseClickEvent) -> bool:
        """The row connected to.  navkit delivers the press that completed the
        double click as well, and that press has already chosen it."""
        index = self.index_at(event.x, event.y)
        if event.button != "left" or index is None:
            return False
        if self.on_activate is not None:
            self.on_activate(index)
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        if event.key == " " and not (event.ctrl or event.alt):
            self._chose(self.cursor)
            return True
        return await super().on_key(event)


__all__ = ["SavedList"]
