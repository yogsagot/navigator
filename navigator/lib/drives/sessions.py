"""Connections to other drives: opening one, and what happens when it ends.

DN's Navigator Link had one cable and one PC on the other end of it; here a
connection is per :class:`~navigator.lib.drives.location.Site`, and
:data:`SESSIONS` keeps them.  :meth:`SessionManager.connect` opens one --
blocking, so a thread runs it -- and mounts its drive, so that
:func:`~navigator.lib.drives.drive_of` finds it; when it cannot go on
without the user it raises what it needs (:class:`NeedPassword`,
:class:`NeedPassphrase`, :class:`UnknownHostKey`), and the caller asks on
the loop and tries again with the :class:`Answers`.

**Closing is DN's** ``cmCloseLinked``: every listener hears the site and why
(``"closed"`` or ``"lost"``), and the shell sends each panel that was on it
back to the disk.  Listeners are called on whatever thread closed it.

Which protocol a scheme is, is :data:`SCHEMES`' business: each names the
module that speaks it, imported only when a connection is made, so a
missing optional package (``navigator-fm[sftp]``) costs nothing until then
and says so through :func:`available`.
"""

from __future__ import annotations

import importlib
import threading
import time
import weakref
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from navigator.lib.drives import Drive, DriveGone, mount, mounted, unmount
from navigator.lib.drives.location import Site

#: The schemes a connection can be made to, and the module that makes it.
#: Each module has ``available() -> str | None`` (why not, or None) and
#: ``connect(site, answers) -> Drive``.
SCHEMES: dict[str, str] = {
    "sftp": "navigator.lib.drives.sftp",
    "ftp": "navigator.lib.drives.ftp",
    "ftps": "navigator.lib.drives.ftp",
    "smb": "navigator.lib.drives.smb",
    "s3": "navigator.lib.drives.s3",
    "s3+http": "navigator.lib.drives.s3",
}

#: The module of every scheme GVfs reaches (:data:`navigator.lib.system.gio.GVFS_SCHEMES`):
#: not in :data:`SCHEMES`, which are Navigator's own, but found by
#: :func:`module_name` all the same.
GVFS = "navigator.lib.drives.gvfs"
#: The module of every scheme KIO reaches (:data:`navigator.lib.system.kio.KIO_SCHEMES`),
#: where the desktop's plumbing is KDE's.
KIO = "navigator.lib.drives.kio"

#: What a menu says beside a scheme that is not there: the extra to install.
EXTRA_HINT: dict[str, str] = {
    "sftp": "navigator-fm[sftp]",
    "smb": "navigator-fm[smb]",
}

#: What each scheme is called wherever a connection is named -- the menu, the
#: boxes, the panel's title -- so it is never in doubt what is on the wire.
#: The *sign* is DN's archive and link drives' ``GetSign`` (``ZIP:``,
#: ``LINK:``), in front of the place in a panel's title.  Proper names, not
#: translated.
PROTOCOLS: dict[str, tuple[str, str]] = {
    "sftp": ("SFTP", "SFTP (SSH)"),
    "ftp": ("FTP", "FTP"),
    "ftps": ("FTPS", "FTPS (FTP over TLS)"),
    "smb": ("SMB", "SMB (Windows share)"),
    "s3": ("S3", "S3 (Amazon S3 and compatible)"),
    "s3+http": ("S3", "S3 over plain HTTP"),
    # GVfs's (navigator.lib.drives.gvfs).
    "mtp": ("MTP", "MTP (phone or player)"),
    "gphoto2": ("PTP", "PTP (camera)"),
    "afc": ("AFC", "AFC (iPhone, iPad)"),
    "dav": ("DAV", "WebDAV"),
    "davs": ("DAVS", "WebDAV over TLS"),
    "afp": ("AFP", "AFP (Apple share)"),
    "nfs": ("NFS", "NFS"),
    "google-drive": ("GDRIVE", "Google Drive"),
    "onedrive": ("ONEDRIVE", "OneDrive"),
    "cdda": ("CDDA", "Audio CD"),
    # KIO's (navigator.lib.drives.kio), beside the ones it shares with GVfs.
    "webdav": ("DAV", "WebDAV"),
    "webdavs": ("DAVS", "WebDAV over TLS"),
    "fish": ("FISH", "FISH (files over SSH)"),
    "gdrive": ("GDRIVE", "Google Drive"),
    "kdeconnect": ("KDECONNECT", "KDE Connect"),
}


def protocol_sign(scheme: str) -> str:
    """``SFTP``: what a panel's title puts in front of the place."""
    return PROTOCOLS.get(scheme, (scheme.upper(), ""))[0]


def protocol_name(scheme: str) -> str:
    """``SFTP (SSH)``: what the boxes call the protocol."""
    sign, name = PROTOCOLS.get(scheme, (scheme.upper(), scheme.upper()))
    return name or sign


#: Each question below has a *hop*: None when the server asked it, or the
#: ``(host, port)`` of the ``ProxyJump`` host on the way that did -- whose
#: answer goes in ``Answers.for_hop``.
Hop = tuple[str, int] | None


class NeedPassword(Exception):
    """The server wants a password, and none that was tried was right."""

    def __init__(self, site: Site, user: str, host: str, *, wrong: bool = False, hop: Hop = None) -> None:
        super().__init__(f"password needed for {user}@{host}")
        self.site, self.user, self.host, self.wrong, self.hop = site, user, host, wrong, hop


class NeedPassphrase(Exception):
    """A private key is locked, and its passphrase was not given (or was wrong)."""

    def __init__(self, key_file: str, *, wrong: bool = False, hop: Hop = None) -> None:
        super().__init__(f"passphrase needed for {key_file}")
        self.key_file, self.wrong, self.hop = key_file, wrong, hop


class UnknownHostKey(Exception):
    """The server's host key is in no ``known_hosts``: accept it, or not."""

    def __init__(self, hostname: str, port: int, key_type: str, fingerprint: str, key: Any,
                 *, hop: Hop = None) -> None:
        super().__init__(f"unknown host key for {hostname}")
        self.hostname, self.port, self.key_type, self.fingerprint, self.key, self.hop = (
            hostname, port, key_type, fingerprint, key, hop)


class HostKeyChanged(OSError):
    """The server's host key is not the one ``known_hosts`` has for it."""


@dataclass
class Answers:
    """What the user said so far, for one connection being made."""

    password: str | None = None
    passphrase: str | None = None
    #: The host key: ``"once"`` for this connection, ``"save"`` into
    #: ``known_hosts`` too, None not asked yet.
    host_key: str | None = None
    #: *Save in keyring* ticked: the password is kept once it has worked.
    save_password: bool = False
    #: Whether the keyring's password has been tried already.
    tried_keyring: bool = False
    #: Where on the drive the connection is being made to: the path of the
    #: location asked for -- SMB's first name in it is the share.
    start: str = ""
    #: What answers a server's own questions mid-login (SSH's
    #: keyboard-interactive: a one-time code, say): called on the connecting
    #: thread with ``(title, instructions, [(prompt, echo), ...])``, it waits
    #: for the user and answers the replies, or None to give up.
    interactive: Any = None
    #: What was said for each ``ProxyJump`` host on the way, by ``(host, port)``.
    hops: dict[tuple[str, int], Answers] = field(default_factory=dict)

    def for_hop(self, hop: Hop) -> Answers:
        """The answers for *hop* -- these, for None (the server itself)."""
        if hop is None:
            return self
        answers = self.hops.get(hop)
        if answers is None:
            answers = self.hops[hop] = Answers(interactive=self.interactive)
        return answers


def module_name(scheme: str) -> str | None:
    """The module that speaks *scheme*: Navigator's own, else the desktop's
    -- KIO's where its plumbing is KDE's and KIO reaches it, else GVfs's
    for a scheme GVfs reaches, else KIO's for one only KIO does; None for
    one nothing does.  A scheme both reach (``mtp``) goes to the one in use."""
    if scheme in SCHEMES:
        return SCHEMES[scheme]
    from navigator.lib.system import desktop, kio
    from navigator.lib.system.gio import GVFS_SCHEMES

    if scheme in kio.KIO_SCHEMES and (scheme not in GVFS_SCHEMES or desktop.backend() is kio):
        return KIO
    return GVFS if scheme in GVFS_SCHEMES else None


def is_connection(scheme: str) -> bool:
    """Whether a drive on *scheme* is a connection Disconnect (Alt+H) closes."""
    return module_name(scheme) is not None


def scheme_module(scheme: str) -> Any:
    name = module_name(scheme)
    if name is None:
        raise DriveGone(scheme, f"No drive speaks {scheme}://")
    return importlib.import_module(name)


def available(scheme: str) -> str | None:
    """Why *scheme* cannot be connected to here, or None if it can."""
    name = module_name(scheme)
    if name is None:
        return f"{scheme}:// is not supported"
    try:
        module = importlib.import_module(name)
    except ImportError as error:
        return str(error)
    return module.available()


Listener = Callable[[Site, str], None]


class SessionManager:
    """Every connection open, by site."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._listeners: list[Listener] = []
        #: When each site's drive was last asked anything.
        self._used: dict[Site, float] = {}

    # -- listening -----------------------------------------------------------------------------

    def add_listener(self, listener: Listener) -> None:
        """*listener* told of each connection closed.  A bound method is held
        weakly: :data:`SESSIONS` outlives every widget, and must not keep one
        -- and the application it is in -- alive (a shell that is never
        unmounted, in a process that runs many)."""
        held: Any = weakref.WeakMethod(listener) if hasattr(listener, "__self__") else (lambda: listener)
        with self._lock:
            self._listeners.append(held)

    def remove_listener(self, listener: Listener) -> None:
        with self._lock:
            self._listeners = [each for each in self._listeners if each() not in (None, listener)]

    def _tell(self, site: Site, why: str) -> None:
        with self._lock:
            listeners = [listener for listener in (each() for each in self._listeners) if listener is not None]
        for listener in listeners:
            try:
                listener(site, why)
            except Exception:
                pass

    # -- connecting ------------------------------------------------------------------------------

    def is_open(self, site: Site) -> bool:
        return any(drive.site == site for drive in mounted())

    def connect(self, site: Site, answers: Answers | None = None) -> Drive:
        """*site*'s drive, connected now if it is not already.  Blocks."""
        for drive in mounted():
            if drive.site == site:
                return drive
        drive = scheme_module(site.scheme).connect(site, answers or Answers())
        drive.on_lost = lambda: self.close(site, "lost")
        self.touch(site)
        return mount(drive)

    def touch(self, site: Site) -> None:
        self._used[site] = time.monotonic()

    def close(self, site: Site, why: str = "closed") -> bool:
        """*site*'s connection closed, and everyone told; False if none was open."""
        drive = unmount(site)
        if drive is None:
            return False
        self._used.pop(site, None)
        try:
            drive.close()
        except Exception:
            pass
        self._tell(site, why)
        return True

    def close_all(self) -> None:
        for drive in mounted():
            self.close(drive.site)

    def reap(self, in_use: set[Site], idle: float) -> list[Site]:
        """The connections nothing uses, idle for *idle* seconds, closed:
        *Communications*' *Close an idle connection after*.  Answers them."""
        if idle <= 0:
            return []
        now = time.monotonic()
        closed = []
        for drive in mounted():
            site = drive.site
            if site in in_use:
                self.touch(site)
                continue
            if now - self._used.get(site, now) >= idle and self.close(site):
                closed.append(site)
        return closed


#: The connections.
SESSIONS = SessionManager()


__all__ = [
    "Answers", "GVFS", "HostKeyChanged", "KIO", "NeedPassphrase", "NeedPassword", "SCHEMES", "SESSIONS",
    "SessionManager", "UnknownHostKey", "available", "is_connection", "module_name", "scheme_module",
]
