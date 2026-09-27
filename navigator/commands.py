"""What the user can ask Navigator for, by name rather than by key.

The ten key bar commands carry DOS Navigator's own captions as their titles,
because the key bar is where they are read.  Most of them have no handler yet
-- View, Edit, Copy and the rest are the file operations still to be written
-- and a command nobody handles is a disabled one, so the key bar shows them
in the status line's *Disabled* colour until they exist.  That is the original
behaving as it did whenever a command was unavailable, not a placeholder look.

Where each is bound says whose it is: the panel commands on ``Manager``, since
they act on a panel; Help, the pull-down menu and the ways out on the
application, since they mean the same wherever the focus is.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command


class Help(Command):
    title = "Help"


class UserMenu(Command):
    title = "Menu"


class View(Command):
    title = "View"


class Edit(Command):
    title = "Edit"


class Copy(Command):
    title = "Copy"


class RenameMove(Command):
    title = "RenMov"


class MakeDirectory(Command):
    title = "Mkdir"


class Delete(Command):
    title = "Delete"


class PullDown(Command):
    title = "PullDn"


@dataclass(frozen=True, slots=True)
class Quit(Command):
    """Leave Navigator.

    *desktop* marks the Alt+X binding, which quits only while the desktop is
    what the user is looking at: with Ctrl+O's console over the windows, Meta+X
    belongs to the program in it.  One command with a field rather than two
    commands, because both mean *quit* and a key bar shows them as one.
    """

    title = "Quit"

    desktop: bool = False


class ToggleConsole(Command):
    """Ctrl+O: put the windows away to show the console, or bring them back."""


class SwitchPanel(Command):
    """Tab: move the keyboard to the other panel."""


class Rescan(Command):
    """Ctrl+R: read the active panel's directory again."""


__all__ = [
    "Copy",
    "Delete",
    "Edit",
    "Help",
    "MakeDirectory",
    "PullDown",
    "Quit",
    "RenameMove",
    "Rescan",
    "SwitchPanel",
    "ToggleConsole",
    "UserMenu",
    "View",
]
