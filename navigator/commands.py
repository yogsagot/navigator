"""What the user can ask Navigator for, by name rather than by key.

The key bar commands carry DOS Navigator's own captions as their titles --
the file panel's status line, ``StatusDef hcFilePanel`` in ``DN.DNR`` --
because the key bar is where they are read.  Most of them have no handler yet
-- View, Edit, Copy and the rest are the file operations still to be written
-- and a command nobody handles is a disabled one, so the key bar shows them
in the status line's *Disabled* colour until they exist.  That is the original
behaving as it did whenever a command was unavailable, not a placeholder look.

Where each is bound says whose it is: the panel commands on ``Manager``, since
they act on a panel; Help, the menu and the way out on the application, since
they mean the same wherever the focus is.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command


class Help(Command):
    title = "Help"


class UserMenu(Command):
    title = "User"


class View(Command):
    title = "View"


class Edit(Command):
    title = "Edit"


class Copy(Command):
    title = "Copy"


class RenameMove(Command):
    title = "Ren"


class MakeDirectory(Command):
    title = "MkDir"


class Delete(Command):
    title = "Del"


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


class SwitchPanel(Command):
    """Tab: move the keyboard to the other panel."""


class Rescan(Command):
    """Ctrl+R: read the active panel's directory again."""


class ChangeDirectory(Command):
    """Alt+T: choose a directory from a tree, and send the active panel there.

    DOS Navigator's ``cmChangeDir``, Panel > Change directory.
    """

    title = "ChDir"


class NewManager(Command):
    """Ctrl+F3: another file manager window, the size of the desktop.

    DOS Navigator's ``cmCreatePanel``, Manager > New.
    """

    title = "New"


class OpenTreeWindow(Command):
    """Disk > Directory tree: a *Directory Tree* window on the desktop.

    DOS Navigator's ``cmCreateTree`` -- here opening the ``TTreeWindow`` that
    1.51 defined and never used.
    """

    title = "Tree"


class ToggleTree(Command):
    """Ctrl+T: the passive panel becomes a directory tree, or a panel again.

    DOS Navigator's ``cmDirTree``, Manager > Directory tree.
    """

    title = "Tree"


__all__ = [
    "ChangeDirectory",
    "Copy",
    "Delete",
    "Edit",
    "Help",
    "MakeDirectory",
    "NewManager",
    "OpenTreeWindow",
    "Quit",
    "RenameMove",
    "Rescan",
    "SwitchPanel",
    "ToggleConsole",
    "ToggleTree",
    "UserMenu",
    "View",
]
