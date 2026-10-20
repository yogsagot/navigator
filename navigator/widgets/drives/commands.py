"""The drives' dialogs' commands: what *Saved links* handles."""

from __future__ import annotations

from navkit.commands import Command


class AddLink(Command):
    """Ins in *Saved links*: a new link, its protocol chosen first."""


class EditLink(Command):
    """F2 in *Saved links*: the focused link in its protocol's box -- the
    *Link* list's own key for it."""


class DeleteLink(Command):
    """Del in *Saved links*: the focused link, once asked."""


class MoveLinkUp(Command):
    """Ctrl+Up in *Saved links*: the focused link one place up, as in the *Link* list."""


class MoveLinkDown(Command):
    """Ctrl+Down in *Saved links*: the focused link one place down."""


__all__ = ["AddLink", "DeleteLink", "EditLink", "MoveLinkDown", "MoveLinkUp"]
