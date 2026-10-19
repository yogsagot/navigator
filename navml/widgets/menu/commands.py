"""The menu group's commands: what whoever holds a ``MenuBar`` handles."""

from __future__ import annotations

from navkit.commands import Command


class OpenMenu(Command):
    """Highlight the menu bar's first entry and give it the keyboard: ``cmMenu``.

    Handled by whoever holds the bar, since a bar is nowhere near the focus.
    """

    title = "Menu"


class ShowContextMenu(Command):
    """Open the context menu of the widget holding the keyboard: the Menu key,
    Shift+F10.

    Not DOS Navigator's, which had no context menu.  Handled by the nearest
    :class:`~navml.widgets.menu.context_menu.ContextMenuHost` on the focus
    path, so the key bubbles from an input line to the dialog and stops at
    the first widget with a menu to show.  No title, so it takes no room on
    the key bar: DN's Shift row left F10 empty.
    """


__all__ = [
    "OpenMenu",
    "ShowContextMenu",
]
