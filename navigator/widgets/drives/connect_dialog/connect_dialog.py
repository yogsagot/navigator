"""What OK answers: a :class:`ConnectRequest`, or None for an empty host."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog


@dataclass
class ConnectRequest:
    """Where to connect, and whether to keep it as a profile."""

    scheme: str
    host: str
    user: str = ""
    port: int = 0
    path: str = ""
    name: str = ""
    keep: bool = False


def split_host(text: str) -> tuple[str, str, int]:
    """``user@host:port`` -- either end left out -- as its three parts."""
    user, _, rest = text.strip().rpartition("@")
    host, port = rest, 0
    if rest.startswith("["):
        bracket = rest.find("]")
        host, after = rest[1:bracket], rest[bracket + 1:]
        if after.startswith(":") and after[1:].isdigit():
            port = int(after[1:])
    elif rest.count(":") == 1:
        head, _, tail = rest.partition(":")
        if tail.isdigit():
            host, port = head, int(tail)
    return user, host, port


def titles(scheme: str) -> tuple[str, str]:
    """The box's title for *scheme*, connecting and editing: always the
    protocol, never in doubt."""
    family = "ftp" if scheme in ("ftp", "ftps") else scheme
    return {
        "sftp": (tr("SSH link (SFTP)"), tr("Edit SSH link (SFTP)")),
        "ftp": (tr("FTP link"), tr("Edit FTP link")),
        "smb": (tr("SMB link (Windows share)"), tr("Edit SMB link (Windows share)")),
    }.get(family, (scheme.upper(), scheme.upper()))


class ConnectDialog(Dialog):
    """Utilities > *SSH link*, *FTP link*, *SMB link*: a server to connect to."""

    def __init__(self, request: ConnectRequest | None = None, *, missing: str | None = None,
                 recent: list[Any] = (), editing: bool = False, scheme: str = "sftp", **kwargs: Any) -> None:
        """*request* fills the lines in (a profile being opened again);
        *missing* says why SFTP cannot be used, and OK then does nothing.
        *recent* are the connections made before
        (:func:`navigator.lib.drives.recent.recent`), newest first: the Host
        line's list, each filling host, login, port and directory at once.

        *editing* is F2 on a profile in the *Link* list: the same lines, kept
        under the name and nothing connected -- so *Keep* is not asked, and
        OK needs a name.  *scheme* is the protocol, a *request*'s if given:
        FTP's box has *Encrypt with TLS*, SMB's directory starts with the share."""
        super().__init__(**kwargs)
        self.editing = editing
        if request is not None:
            scheme = request.scheme
        self.scheme = scheme
        connect_title, edit_title = titles(scheme)
        self.title = edit_title if editing else connect_title
        if editing:
            self.keep.visible = False
        if scheme in ("ftp", "ftps"):
            self.secure.visible = True
            self.secure.value = 1 if scheme == "ftps" else 0
        if scheme == "smb":
            self.directory.label_text = tr("~S~hare/dir")
        self._recent = list(recent)
        self.host.choices = [link.text() for link in self._recent]
        # The list's choice fills the one line it drops from; a connection is
        # every line, so the button's ``choose`` is this dialog's.
        self.host.history.choose = self._choose_recent
        if request is not None:
            self.host.value = request.host
            self.user.value = request.user
            self.port.value = str(request.port) if request.port else ""
            self.directory.value = request.path
            self.label.value = request.name
            self.keep.value = 1 if request.keep else 0
        self._missing = missing
        self.missing.text = missing or ""

    def _choose_recent(self, text: str) -> None:
        link = next((each for each in self._recent if each.text() == text), None)
        if link is None:
            return
        self.host.value = link.host
        self.user.value = link.user
        self.port.value = str(link.port) if link.port else ""
        self.directory.value = link.path
        if self.secure.visible:
            self.secure.value = 1 if link.scheme == "ftps" else 0
        self.host.entry.select_all()
        self.host.entry.focus()

    def accept(self) -> ConnectRequest | None:
        if self._missing:
            return None
        user, host, port = split_host(self.host.value)
        if not host:
            return None
        typed_port = self.port.value.strip()
        if typed_port.isdigit():
            port = int(typed_port)
        name = self.label.value.strip()
        keep = bool(self.keep.value & 1) or self.editing
        if self.editing and not name:
            name = host
        scheme = self.scheme
        if scheme in ("ftp", "ftps"):
            scheme = "ftps" if self.secure.value & 1 else "ftp"
        directory = self.directory.value.strip()
        if scheme == "smb" and directory and not directory.startswith("/"):
            directory = "/" + directory  # the share is the first name
        return ConnectRequest(
            scheme, host, self.user.value.strip() or user, port, directory,
            name or (host if keep else ""), keep,
        )
