"""A separator between two groups of entries, Turbo Vision's ``MenuLine``."""

from __future__ import annotations

from navml.widgets.menu.menu_item.menu_item import MenuNode


class MenuLine(MenuNode):
    """A rule across a menu box.  Never selected, never chosen."""
