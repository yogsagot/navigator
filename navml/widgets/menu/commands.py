"""The menu group's commands: what whoever holds a ``MenuBar`` handles."""

from __future__ import annotations

from navkit.commands import Command


class OpenMenu(Command):
    """Highlight the menu bar's first entry and give it the keyboard: ``cmMenu``.

    Handled by whoever holds the bar, since a bar is nowhere near the focus.
    """

    title = "Menu"


class MainMenu(Command):
    """Highlight the main bar's first entry: ``cmMainMenu``.

    DOS Navigator's editor window had a menu bar of its own, which F10's
    ``cmMenu`` reached first; its *File > Main menu* went to the
    application's bar instead.  Here a window's own menu is an entry of the
    one bar (a window's ``f10_menu``), and this is the way back to the bar's
    start.  Handled by whoever holds the bar, as :class:`OpenMenu` is.
    """


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
    "MainMenu",
    "OpenMenu",
    "ShowContextMenu",
]
