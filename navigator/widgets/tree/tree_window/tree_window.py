"""The handlers behind ``tree_window.nml``.

What the window says for itself is little: where it opens, that Ctrl+R
re-reads its tree, and that the tree's quick search shows on its bottom
frame -- the tree has no frame of its own to put it on.  **Enter is not
handled here.**  The tree emits ``ChosenEvent``, this window's generated stub
declines it, and it walks on up to the screen, which is the one thing that
knows where the file manager is.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.screen import Surface

from navml.widgets.window import Window

from navigator.widgets.manager.commands import Rescan


class TreeWindow(Window):
    """A directory tree in a window of its own, opened on *start*."""

    def __init__(self, start: Path | None = None, hidden: bool = True, **kwargs: Any) -> None:
        """*hidden* is the panel's ``show_hidden``: whether dot-directories are listed."""
        super().__init__(**kwargs)
        # The search shows on this window's frame, and its caret with it.
        self.tree.caret_on_name = False
        self.tree.set_show_hidden(hidden)
        self.tree.show(start if start is not None else Path.cwd())

    def take_keyboard(self) -> None:
        # Not from ``mounted()``: that runs inside ``Desktop.open``'s ``add()``,
        # before ``activate`` has saved which panel the window below had, so
        # closing this one would hand the keyboard to the left panel.
        self.tree.focus()

    async def on_rescan(self, event: Rescan) -> bool:
        self.tree.reload()
        return True

    def _search_label(self) -> tuple[int, str] | None:
        """Where the tree's search label sits on the bottom frame, and its text.

        Centred as the Ctrl+T tree's footer is, and kept clear of the resize
        grip in the corner.  None while there is no search, or no frame.
        """
        label = self.tree.search_label()
        if not label or not self.framed or self.height < 2:
            return None
        label = label[: max(0, self.width - 4)]
        return max(1, (self.width - len(label)) // 2), label

    def render(self, surface: Surface) -> None:
        """The frame, and over its bottom edge what the tree's search has typed,
        in the title's colours."""
        super().render(surface)
        placed = self._search_label()
        if placed is not None:
            x, label = placed
            surface.draw_text(x, self.height - 1, label, self.part_style("title"))

    def cursor_position(self) -> tuple[int, int] | None:
        """While the tree searches, the caret after what it has typed, on the frame."""
        placed = self._search_label()
        if placed is None:
            return None
        x, label = placed
        # Before the label's closing blank, as the panel's caret is.
        return min(x + len(label) - 1, self.width - 3), self.height - 1
