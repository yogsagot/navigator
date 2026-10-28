"""The commands of one key table and their keys, a row each.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` over ``(entry, keys)``
pairs: the command's title on the left, its keys on the right as a menu
writes them, a divider between, and a ``*`` before a command whose keys are
not its defaults.
"""

from __future__ import annotations

from typing import Any

from navkit.commands import key_label
from navkit.i18n import tr
from navkit.screen import Surface
from navkit.tooltip import lines
from navml.widgets.dialog.control import parse_shortcut
from navml.widgets.dialog.list_viewer import ListViewer


def keys_text(keys: tuple[str, ...]) -> str:
    """*keys* as a menu shows them, ``Ctrl-K B, F5``; a dash for none."""
    return ", ".join(key_label(key) for key in keys) or "-"


class BindingList(ListViewer):
    """``(entry, keys)`` rows: :class:`navigator.lib.config.keybindings.Entry` and its keys."""

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

    def tooltip_at(self, x: int, y: int) -> str:
        """Over the title, where the command is in the menus and what its item
        says of it; over the keys, all of them where cut.  Either way, the
        defaults where the keys are not they."""
        inside = self.inset <= x < self.inset + self.inner_width
        index = self.index_at(x, y) if inside else None
        if index is None:
            return super().tooltip_at(x, y)
        entry, keys = self.items[index]
        right = self.keys_width()
        left = max(0, self.inner_width - right - 1)
        changed = ""
        if keys != entry.defaults:
            changed = tr("Its keys by default: {keys}").format(keys=keys_text(entry.defaults))
        if x < self.inset + left:
            return lines(*self.describe(entry), changed)
        shown = keys_text(keys)
        return lines(shown if len(shown) > right else "", changed)

    def describe(self, entry: Any) -> list[str]:
        """Where *entry*'s command is in the main menu, ``File > Make
        directory``, and that item's tooltip; nothing for a command in no menu."""
        app = self.application
        menu = getattr(getattr(app, "shell", None), "menu", None)
        path = menu.path_to(entry.binding) if menu is not None else []
        if not path:
            return []
        names = " > ".join(parse_shortcut(node.text)[0].rstrip(".…").rstrip() for node in path)
        return [names, path[-1].tooltip]
