"""The application's own commands: what ``Navigator`` (``__main__.py``) handles.

Help, the way out and Ctrl+O mean the same wherever the focus is, so they are
the application's, bound on its key table.  Every other command lives with the
widgets that handle it, one ``commands.py`` per group of
``navigator/widgets/`` -- ``shell``, ``manager``, ``viewer``, ``editor`` and
``file_ops`` -- and a command nobody handles yet lives where its key table
binds it.  A command is only a name; its code is the ``on_*`` handler.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command


class Help(Command):
    title = "Help"


@dataclass(frozen=True, slots=True)
class Quit(Command):
    """Leave Navigator.

    *desktop* marks the Alt+X binding, which quits only while the desktop is
    what the user is looking at: with Ctrl+O's console over the windows, Meta+X
    belongs to the program in it.  One command with a field rather than two
    commands, because both mean *quit* and a key bar shows them as one.
    """

    title = "Exit"

    desktop: bool = False


class ToggleConsole(Command):
    """Ctrl+O: put the windows away to show the console, or bring them back."""


__all__ = [
    "Help",
    "Quit",
    "ToggleConsole",
]
