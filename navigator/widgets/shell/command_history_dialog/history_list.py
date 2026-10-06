"""The commands, oldest at the top: DN's ``TTHistList`` with ``CommandHistory`` on."""

from __future__ import annotations

from typing import Any

from navkit import glyphs as glyphs_module
from navkit.events import Event, KeyEvent
from navkit.reactive import reactive

from navml.widgets.dialog.list_viewer import ListViewer


class Chosen(Event):
    """Enter, or a double click, on a command."""


class Killed(Event):
    """Del on a command (``kbDel``, *Kill*)."""


class HistoryList(ListViewer):
    """A ``■`` beside each command kept from *Kill* (DN's ``+`` flag, navml's
    pinned).  Space marks and unmarks one; Left and Right go to the marked
    one before or after; Del kills."""

    emits = (Chosen, Killed)

    #: The commands marked.
    kept: frozenset[str] = reactive(frozenset())

    def row_text(self, index: int, item: Any) -> str:
        sign = "■" if self.glyphs > glyphs_module.GLYPHS_ASCII else "+"
        return f"{sign if item in self.kept else ' '}{item}"

    async def choose(self) -> bool:
        if self.selected is None:
            return False
        await self.emit(Chosen())
        return True

    def _to_kept(self, step: int) -> None:
        """``ScanMarked``: the next marked command that way."""
        index = self.cursor + step
        while 0 <= index < len(self.items):
            if self.items[index] in self.kept:
                self.cursor = index
                return
            index += step

    async def on_key(self, event: KeyEvent) -> bool:
        if not self.inert:
            if event.matches("space"):
                if self.selected is not None:
                    self.kept = self.kept ^ {self.selected}
                return True
            if event.matches("delete"):
                await self.emit(Killed())
                return True
            if event.matches("left", "right"):
                self._to_kept(-1 if event.key == "left" else 1)
                return True
        return await super().on_key(event)
