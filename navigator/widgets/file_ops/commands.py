"""The file operations' commands: what their dialogs handle."""

from __future__ import annotations

from navkit.commands import Command


class ChooseTarget(Command):
    """F10 in the Copy dialog: pick where the files go from a tree.

    DOS Navigator's ``cmTree``, which ``StatusDef hcCopyDialog`` put on F10
    and the dialog's *Tree* button sent too.
    """

    title = "Tree"


__all__ = [
    "ChooseTarget",
]
