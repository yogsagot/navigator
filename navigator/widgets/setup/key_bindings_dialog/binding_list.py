"""The commands of one key table and their keys, a row each.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` over ``(entry, keys)``
pairs: the command's title on the left, its keys on the right as a menu
writes them, a divider between, and a ``*`` before a command whose keys are
not its defaults.
"""

from __future__ import annotations

from typing import Any

from navkit.commands import key_label
from navkit.screen import Surface
from navml.widgets.dialog.list_viewer import ListViewer


def keys_text(keys: tuple[str, ...]) -> str:
    """*keys* as a menu shows them, ``Ctrl-K B, F5``; a dash for none."""
    return ", ".join(key_label(key) for key in keys) or "-"


class BindingList(ListViewer):
    """``(entry, keys)`` rows: :class:`navigator.keybindings.Entry` and its keys."""

    def keys_width(self) -> int:
        """The right column's width: half the row."""
        return max(0, (self.inner_width - 1) // 2)

    def row_text(self, index: int, item: Any) -> str:
        entry, keys = item
        mark = " " if keys == entry.defaults else "*"
        return f"{mark}{entry.title}"

    def render_row(self, surface: Surface, y: int, index: int, item: Any) -> None:
        _, keys = item
        style = self.row_style(index, item)
        right = self.keys_width()
        left = max(0, self.inner_width - right - 1)
        surface.draw_text(self.inset, y, self.row_text(index, item), style, left)
        surface.draw_text(self.inset + left, y, "│", self.part_style("divider"), 1)
        surface.draw_text(self.inset + left + 1, y, keys_text(keys), style, right)
