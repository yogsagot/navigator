"""The handlers behind ``tree_window.nml``.

What the window says for itself is little: where it opens, and that Ctrl+R
re-reads its tree.  **Enter is not handled here.**  The tree emits
``ChosenEvent``, this window's generated stub declines it, and it walks on up
to the screen, which is the one thing that knows where the file manager is.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navml.widgets.window import Window

from navigator.commands import Rescan


class TreeWindow(Window):
    """A directory tree in a window of its own, opened on *start*."""

    def __init__(self, start: Path | None = None, hidden: bool = True, **kwargs: Any) -> None:
        """*hidden* is the panel's ``show_hidden``: whether dot-directories are listed."""
        super().__init__(**kwargs)
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
