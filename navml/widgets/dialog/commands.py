"""The dialog group's commands: what ``Dialog`` and ``TreeView`` handle.

Turbo Vision's ``cmCancel`` and ``cmDefault``, and Tab and Shift+Tab, which
are commands here where Turbo Vision had ``TGroup`` select the next view
directly: as commands they are rebindable, and a dialog that wants Tab for
itself can take the key without overriding a method.  And the quick search
every list of names shares -- a file panel's and a tree's alike.
"""

from __future__ import annotations

from navkit.commands import Command


class Cancel(Command):
    """Dismiss a dialog without an answer."""

    title = "Cancel"


class Default(Command):
    """Press a dialog's default button, wherever the focus is."""

    title = "OK"


class SelectNext(Command):
    """Move the keyboard to the next control."""


class SelectPrevious(Command):
    """Move the keyboard to the previous control."""


class QuickSearch(Command):
    """Ctrl+S: type the start of a name and the cursor jumps to it.

    Midnight Commander's key and its rules -- a file panel's and a tree's
    alike, which is why it is the library's.  DOS Navigator 1.51's panel quick
    search -- the *Quick search* choice in ``dlgPanelSetup``, started by an
    Alt+letter -- has no handler in the published source to follow; its tree's
    does (``TREE.PAS``), and the tree follows it.
    """

    title = "Search"


__all__ = [
    "Cancel",
    "Default",
    "QuickSearch",
    "SelectNext",
    "SelectPrevious",
]
