"""The drives' dialogs' commands: what *Saved links* and the SSH connection manager handle."""

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


class NewSshLink(Command):
    """Ins in the SSH connection manager (``SshLinkDialog``): a new connection,
    kept at once and chosen -- empty under a placeholder name, or the one-off
    lines typed."""


class SaveSshLink(Command):
    """F2 in the SSH connection manager: the chosen connection made what the lines say."""


class DeleteSshLink(Command):
    """Del in the SSH connection manager's list: the chosen connection, once asked."""


__all__ = ["AddLink", "DeleteLink", "DeleteSshLink", "EditLink", "MoveLinkDown", "MoveLinkUp", "NewSshLink",
           "SaveSshLink"]
