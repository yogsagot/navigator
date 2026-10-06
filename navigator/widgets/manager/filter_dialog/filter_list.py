"""The *Filter* box's list: DN's ``TSelectList``, masks one marks."""

from __future__ import annotations

from typing import Any

from navkit import glyphs as glyphs_module
from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import reactive

from navml.widgets.dialog.list_viewer import ListViewer


class FilterList(ListViewer):
    """Masks, each marked or not: Space or Insert marks the one at the cursor
    and steps down, ``+`` marks every one, ``-`` none, ``*`` turns each
    over, and a right click marks the one clicked (``TSelectList``)."""

    #: The indices marked.
    marks: frozenset[int] = reactive(frozenset())

    def row_text(self, index: int, item: Any) -> str:
        sign = "■" if self.glyphs > glyphs_module.GLYPHS_ASCII else "*"
        return f"{sign if index in self.marks else ' '} {item}"

    def toggle(self, index: int) -> None:
        if 0 <= index < len(self.items):
            self.marks = self.marks ^ {index}

    async def on_key(self, event: KeyEvent) -> bool:
        if not self.inert:
            if event.matches("space", "insert"):
                self.toggle(self.cursor)
                self.move_cursor(1)
                return True
            if event.char in ("+", "-", "*"):
                every = frozenset(range(len(self.items)))
                self.marks = {"+": every, "-": frozenset(), "*": every - self.marks}[event.char]
                return True
        return await super().on_key(event)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.button == "right" and event.action == "press" and not self.inert:
            index = self.index_at(event.x, event.y)
            if index is not None:
                self.cursor = index
                self.toggle(index)
            return True
        return await super().on_mouse_click(event)
