"""The menu group's commands: what whoever holds a ``MenuBar`` handles."""

from __future__ import annotations

from navkit.commands import Command


class OpenMenu(Command):
    """Highlight the menu bar's first entry and give it the keyboard: ``cmMenu``.

    Handled by whoever holds the bar, since a bar is nowhere near the focus.
    """

    title = "Menu"


__all__ = [
    "OpenMenu",
]
