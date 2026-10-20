"""A Windows share -- or Samba's -- as a drive: ``smb://user@host/share/path``.

Through `smbprotocol <https://github.com/jborean93/smbprotocol>`_'s
``smbclient``, the ``navigator-fm[smb]`` extra, whose functions are
:mod:`os`'s over ``\\\\host\\share\\path`` names; without it
:func:`available` says what to install.

**The first name of a path is the share.**  SMB has no listing of a server's
shares to ask for without RPC, so the drive's root lists the ones it has been
told -- the share the connection opened on, and any reached since -- and the
link box asks for the share as the start of its *Directory*.

Each drive keeps its own connection cache, so two drives on one server with
two users do not share a session.  ``smbclient`` is imported lazily, and
can be swapped for a stand-in (:data:`CLIENT`) in tests: no SMB server is
written in Python to test against.
"""

from __future__ import annotations

import errno
import importlib
import importlib.util
import os
import stat
import threading
from pathlib import PurePosixPath
from typing import IO, Any

from navigator.lib.drives.base import RENAME, WRITE, Child, Drive, DriveGone, FileStat
from navigator.lib.drives.location import Location, Site
from navigator.lib.drives.sessions import Answers, NeedPassword

#: What the drive cannot be without.
EXTRA = "navigator-fm[smb]"

#: The ``smbclient`` module to speak through: imported at the first
#: connection, unless a test has put its own here.
CLIENT: Any = None


def available() -> str | None:
    if CLIENT is None and importlib.util.find_spec("smbclient") is None:
        return f"SMB needs smbprotocol: pip install {EXTRA}"
    return None


def _client() -> Any:
    global CLIENT
    if CLIENT is None:
        CLIENT = importlib.import_module("smbclient")
    return CLIENT


def _error(code: int, where: Any) -> OSError:
    kind = {errno.ENOENT: FileNotFoundError, errno.ENOTDIR: NotADirectoryError}.get(code, OSError)
    return kind(code, os.strerror(code), str(where))


def _stat_of(info: Any) -> FileStat:
    return FileStat(info.st_mode, info.st_size, float(info.st_mtime), float(info.st_atime))


class SmbDrive(Drive):
    """A server's shares, through ``smbclient``."""

    capabilities = frozenset((WRITE, RENAME))
    seekable = True
    #: No server says when a directory changed: *Auto refresh* looks again.
    polled = True

    def __init__(self, site: Site, *, user: str, password: str | None, share: str) -> None:
        self.site = site
        self.user = user
        self._password = password
        self.port = site.port or 445
        #: This drive's sessions, apart from any other's.
        self._cache: dict[str, Any] = {}
        #: The shares the root lists: the one opened on, and those reached since.
        self.shares: list[str] = [share] if share else []
        self._lock = threading.Lock()
        self.on_lost: Any = None
        self.home = PurePosixPath(f"/{share}") if share else PurePosixPath("/")

    # -- names ----------------------------------------------------------------------------------

    def _unc(self, location: Location) -> str:
        parts = [part for part in location.path.parts if part != "/"]
        if not parts:
            raise _error(errno.EISDIR, location)
        with self._lock:
            if parts[0] not in self.shares:
                self.shares.append(parts[0])
        return "\\\\" + self.site.host + "\\" + "\\".join(parts)

    def _kw(self) -> dict[str, Any]:
        return {"port": self.port, "connection_cache": self._cache, "username": self.user or None,
                "password": self._password}

    def _call(self, name: str, location: Location, *args: Any, **kwargs: Any) -> Any:
        client = _client()
        try:
            return getattr(client, name)(self._unc(location), *args, **self._kw(), **kwargs)
        except OSError:
            raise
        except Exception as error:
            # The connection's own failures: not a file's.
            raise DriveGone(self.site.host, f"{self.site.host}: {error}") from error

    def get_dir(self, location: Location) -> str:
        from navigator.lib.drives.sessions import protocol_sign

        return f"{protocol_sign(self.site.scheme)}:{self.site.host}:{location.path}"

    # -- reading --------------------------------------------------------------------------------

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.appearance import filetypes
        from navigator.lib.drives.listing import DirEntry, order_entries

        mask = options.get("mask", filetypes.ALL_FILES)
        filtered = mask.strip() not in ("", filetypes.ALL_FILES)
        entries: list[DirEntry] = []
        if location.is_root:
            # The shares known: SMB keeps its list of them behind RPC.
            for share in list(self.shares):
                entries.append(DirEntry(share, True, 0, stat.S_IFDIR | 0o755))
            return order_entries(entries, sort), None, None
        entries.append(DirEntry("..", True, 0, stat.S_IFDIR | 0o755))
        try:
            listed = list(self._call("scandir", location))
        except OSError as error:
            if isinstance(error, DriveGone):
                raise
            return entries, error.strerror or str(error), None
        for item in listed:
            name = item.name
            if name in (".", ".."):
                continue
            if not show_hidden and name.startswith("."):
                continue
            try:
                info = item.stat()
            except OSError:
                entries.append(DirEntry(name, False, 0))
                continue
            is_dir = stat.S_ISDIR(info.st_mode)
            if filtered and not is_dir and not filetypes.in_filter(name, mask):
                continue
            is_link = item.is_symlink() if hasattr(item, "is_symlink") else False
            entries.append(DirEntry(name, is_dir, 0 if is_dir else info.st_size, info.st_mode,
                                    float(info.st_mtime), is_link))
        order = {key: options[key] for key in ("executables_first", "archives_first", "reverse")
                 if key in options}
        return order_entries(entries, sort, **order), None, None

    def stat(self, location: Location) -> FileStat:
        if location.is_root:
            return FileStat(stat.S_IFDIR | 0o755)
        return _stat_of(self._call("stat", location))

    def lstat(self, location: Location) -> FileStat:
        if location.is_root:
            return FileStat(stat.S_IFDIR | 0o755)
        return _stat_of(self._call("lstat", location))

    def children(self, location: Location) -> list[Child]:
        if location.is_root:
            return [(share, FileStat(stat.S_IFDIR | 0o755)) for share in self.shares]
        found: list[Child] = []
        for item in self._call("scandir", location):
            if item.name in (".", ".."):
                continue
            try:
                found.append((item.name, _stat_of(item.stat(follow_symlinks=False))))
            except OSError as error:
                found.append((item.name, error))
        return found

    def names(self, location: Location) -> list[str]:
        return [name for name, _ in self.children(location)]

    def readlink(self, location: Location) -> str:
        return self._call("readlink", location)

    def open_read(self, location: Location) -> IO[bytes]:
        return self._call("open_file", location, mode="rb")

    # -- writing --------------------------------------------------------------------------------

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        return self._call("open_file", location, mode="ab" if append else "wb")

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        self._call("mkdir", location)

    def rmdir(self, location: Location) -> None:
        self._call("rmdir", location)

    def unlink(self, location: Location) -> None:
        self._call("remove", location)

    def rename(self, source: Location, dest: Location) -> None:
        self._call("rename", source, self._unc(dest))

    def replace(self, source: Location, dest: Location) -> None:
        self._call("replace", source, self._unc(dest))

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        self._call("utime", location, ns=(atime_ns, mtime_ns), follow_symlinks=follow)

    def describe(self) -> list[tuple[str, str]]:
        return [("Server", f"{self.user or '(guest)'}@{self.site.host}:{self.port}"),
                ("Shares", ", ".join(self.shares))]

    def close(self) -> None:
        try:
            _client().reset_connection_cache(fail_on_error=False, connection_cache=self._cache)
        except Exception:
            pass


def connect(site: Site, answers: Answers) -> SmbDrive:
    """A session with *site*'s server: blocks, and raises what the user must answer.

    The share is the first name of the place asked for (``answers.start``);
    the session is proved by opening it.  No user is the guest, or Kerberos
    where a ticket is held.
    """
    parts = [part for part in PurePosixPath(answers.start or "/").parts if part not in ("/", ".")]
    share = parts[0] if parts else ""
    from navigator.lib.drives import credentials
    from navigator.settings import SETTINGS

    client = _client()
    user = site.user
    if answers.password is None and not answers.tried_keyring and user:
        answers.tried_keyring = True
        answers.password = credentials.saved_password(site)
    drive = SmbDrive(site, user=user, password=answers.password, share=share)
    try:
        client.register_session(site.host, username=user or None, password=answers.password,
                                port=drive.port, connection_timeout=max(1, SETTINGS.remote.timeout),
                                connection_cache=drive._cache)
        if share:
            drive.stat(drive_root(site, share))
    except Exception as error:
        drive.close()
        name = type(error).__name__
        if name in ("LogonFailure", "AccessDenied", "SpnegoError", "BadPassword") or "logon" in str(error).lower():
            raise NeedPassword(site, user or "guest", site.host, wrong=answers.password is not None) from error
        if isinstance(error, OSError) and not isinstance(error, DriveGone):
            raise DriveGone(site.host, f"{site.host}: {error.strerror or error}") from error
        if isinstance(error, DriveGone):
            raise
        raise DriveGone(site.host, f"Cannot connect to {site.host}: {error}") from error
    if answers.save_password and answers.password and user:
        credentials.save_password(site, answers.password)
    return drive


def drive_root(site: Site, share: str) -> Location:
    return Location(site, PurePosixPath(f"/{share}"))


__all__ = ["CLIENT", "EXTRA", "SmbDrive", "available", "connect"]
