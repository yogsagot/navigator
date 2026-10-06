"""The directories the history holds, newest first; a double click goes."""

from __future__ import annotations

from typing import Any

from navkit.events import Event

from navml.widgets.dialog.list_viewer import ListViewer


class Chosen(Event):
    """A directory double-clicked, or Enter on it."""


class DirList(ListViewer):
    """``dlgDirectoryHistory``'s list."""

    emits = (Chosen,)

    async def choose(self) -> bool:
        if self.selected is None:
            return False
        await self.emit(Chosen())
        return True
