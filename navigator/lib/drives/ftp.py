"""A server's files over FTP: ``ftp://user@host:port/path``, and ``ftps://``
for FTP over TLS.

Python's own :mod:`ftplib`, so it needs nothing installed.  A directory is
read with ``MLSD`` where the server has it -- one line a file, its facts
named -- and with ``LIST`` where it has not, whose ``ls -l`` lines are
parsed as Midnight Commander parses them, as well as they can be.

**A pool of control connections**, as SFTP has of channels: FTP does one
thing at a time on each, so a panel's read does not wait for a copy's
megabytes.  A file being read or written holds its connection until it is
closed.  A connection the server dropped -- FTP servers drop idle ones -- is
made again, once, silently; when that fails the drive is lost and its panels
go home (``SESSIONS``).

FTPS is explicit TLS (``AUTH TLS``) with the data channel protected too
(``PROT P``), and the server's certificate checked against the system's.
"""

from __future__ import annotations

import calendar
import contextlib
import errno
import ftplib
import os
import queue
import re
import socket
import ssl
import stat
import threading
import time
from pathlib import PurePosixPath
from typing import IO, Any, Iterator

from navigator.lib.drives.base import CHMOD, RENAME, WRITE, Child, Drive, DriveGone, FileStat
from navigator.lib.drives.location import Location, Site
from navigator.lib.drives.sessions import Answers, NeedPassword

#: How many control connections one drive may have open at once.
CONNECTIONS = 3


def available() -> str | None:
    return None  # the standard library's


def _error(code: int, where: Any, text: str = "") -> OSError:
    kind = {errno.ENOENT: FileNotFoundError, errno.EACCES: PermissionError,
            errno.EEXIST: FileExistsError, errno.ENOTDIR: NotADirectoryError,
            errno.EISDIR: IsADirectoryError}.get(code, OSError)
    return kind(code, text or os.strerror(code), str(where))


def _os_error(error: ftplib.Error, where: Any) -> OSError:
    """An FTP reply as the ``OSError`` a disk would have raised."""
    text = str(error)
    code = text[:3]
    lower = text.lower()
    if code == "530" or "permission" in lower or "denied" in lower:
        return _error(errno.EACCES, where, text)
    if code in ("550", "450") and ("exist" in lower and "not" not in lower):
        return _error(errno.EEXIST, where, text)
    if code in ("550", "450", "553"):
        return _error(errno.ENOENT, where, text)
    return _error(errno.EIO, where, text)


# -- reading a listing ------------------------------------------------------------------------------


def _mlsd_stat(facts: dict[str, str]) -> FileStat:
    kind = facts.get("type", "file").lower()
    perms = facts.get("unix.mode")
    mode = int(perms, 8) if perms and perms.isdigit() else 0
    if kind in ("dir", "cdir", "pdir"):
        mode = stat.S_IFDIR | (mode or 0o755)
    elif kind.startswith("os.unix=symlink") or kind == "os.unix=slink":
        mode = stat.S_IFLNK | (mode or 0o777)
    else:
        mode = stat.S_IFREG | (mode or 0o644)
    modify = facts.get("modify", "")
    mtime = 0.0
    if len(modify) >= 14:
        try:
            mtime = calendar.timegm(time.strptime(modify[:14], "%Y%m%d%H%M%S"))
        except ValueError:
            pass
    size = int(facts.get("size", "0") or 0) if facts.get("size", "0").isdigit() else 0
    return FileStat(mode, size, float(mtime), float(mtime))


#: ``ls -l``'s line, as most servers send it to ``LIST``.
_LS = re.compile(
    r"^(?P<mode>[-dlbcps][-rwxsStT]{9})[.+@]?\s+\d+\s+(?P<owner>\S+)\s+(?P<group>\S+)\s+(?P<size>\d+)\s+"
    r"(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<when>\d{1,2}:\d{2}|\d{4})\s(?P<name>.+)$")

_MONTHS = {name: number for number, name in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}


def _parse_list(line: str) -> tuple[str, FileStat, str | None, str | None] | None:
    """``(name, stat, link target, owner)`` from a ``LIST`` line, or None."""
    match = _LS.match(line)
    if match is None:
        return None
    letters = match["mode"]
    kind = {"d": stat.S_IFDIR, "l": stat.S_IFLNK}.get(letters[0], stat.S_IFREG)
    bits = 0
    for index, letter in enumerate(letters[1:]):
        if letter not in "-ST":
            bits |= 1 << (8 - index)
    name, target = match["name"], None
    if kind == stat.S_IFLNK and " -> " in name:
        name, target = name.split(" -> ", 1)
    month = _MONTHS.get(match["month"].lower(), 1)
    when = match["when"]
    now = time.gmtime()
    if ":" in when:
        hour, minute = (int(part) for part in when.split(":"))
        year = now.tm_year
        moment = calendar.timegm((year, month, int(match["day"]), hour, minute, 0))
        if moment > time.time() + 86400:
            moment = calendar.timegm((year - 1, month, int(match["day"]), hour, minute, 0))
    else:
        moment = calendar.timegm((int(when), month, int(match["day"]), 0, 0, 0))
    st = FileStat(kind | bits, int(match["size"]), float(moment), float(moment))
    return name, st, target, f"{match['owner']}:{match['group']}"


# -- the connections ---------------------------------------------------------------------------------


class _Pool:
    """Up to :data:`CONNECTIONS` logged-in control connections to one server."""

    def __init__(self, site: Site, answers: Answers) -> None:
        self.site = site
        self.answers = answers
        self.secure = site.scheme == "ftps"
        self.host = site.host
        self.port = site.port or 21
        self.user = site.user or "anonymous"
        self._free: queue.LifoQueue[ftplib.FTP] = queue.LifoQueue()
        self._made = 0
        self._lock = threading.Lock()
        self.closing = False
        #: Whether the server answers ``MLSD``, and whether its ``LIST`` takes
        #: ``-a``; each learnt at the first listing that asks.
        self.mlsd: bool | None = None
        self.list_a: bool | None = None
        self._free.put(self._login())
        self._made = 1

    def _login(self) -> ftplib.FTP:
        from navigator.lib.drives import credentials
        from navigator.settings import SETTINGS

        answers = self.answers
        if answers.password is None and not answers.tried_keyring and self.site.user:
            answers.tried_keyring = True
            answers.password = credentials.saved_password(self.site)
        timeout = max(1, SETTINGS.remote.timeout)
        if self.secure:
            client: ftplib.FTP = ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=timeout)
        else:
            client = ftplib.FTP(timeout=timeout)
        try:
            client.connect(self.host, self.port)
            if self.secure:
                client.auth()
            password = answers.password
            if password is None:
                password = "" if not self.site.user else None
            if password is None:
                raise NeedPassword(self.site, self.user, self.host)
            client.login(self.user, password)
            if self.secure:
                client.prot_p()
        except NeedPassword:
            _quietly_close(client)
            raise
        except ftplib.error_perm as error:
            _quietly_close(client)
            if str(error)[:3] in ("530", "331", "332"):
                raise NeedPassword(self.site, self.user, self.host, wrong=answers.password is not None) from error
            raise DriveGone(self.host, f"Cannot connect to {self.host}: {error}") from error
        except (ftplib.Error, OSError, EOFError, ssl.SSLError) as error:
            _quietly_close(client)
            reason = getattr(error, "strerror", None) or str(error) or type(error).__name__
            raise DriveGone(self.host, f"Cannot connect to {self.host}: {reason}") from error
        return client

    def take(self) -> ftplib.FTP:
        if self.closing:
            raise DriveGone(self.host)
        try:
            return self._free.get_nowait()
        except queue.Empty:
            pass
        with self._lock:
            if self._made < CONNECTIONS:
                self._made += 1
                try:
                    return self._login()
                except BaseException:
                    self._made -= 1
                    raise
        return self._free.get()

    def give(self, client: ftplib.FTP, *, broken: bool = False) -> None:
        if broken or self.closing:
            _quietly_close(client)
            with self._lock:
                self._made -= 1
            return
        self._free.put(client)

    def remake(self) -> ftplib.FTP:
        """A connection in place of one the server dropped: once."""
        try:
            return self._login()
        except Exception as error:
            raise DriveGone(self.host) from error

    def close(self) -> None:
        self.closing = True
        while True:
            try:
                client = self._free.get_nowait()
            except queue.Empty:
                return
            try:
                client.quit()
            except Exception:
                _quietly_close(client)


def _quietly_close(client: ftplib.FTP) -> None:
    try:
        client.close()
    except Exception:
        pass


class _Transfer:
    """A file being read or written: a data connection, its control
    connection held until the transfer's reply is in."""

    def __init__(self, drive: FtpDrive, client: ftplib.FTP, sock: socket.socket, mode: str) -> None:
        self._drive, self._client, self._sock = drive, client, sock
        self._file = sock.makefile(mode)
        self.after: Any = None

    def read(self, size: int = -1) -> bytes:
        return self._file.read(size)

    def write(self, data: bytes) -> int:
        self._file.write(data)
        return len(data)

    def flush(self) -> None:
        self._file.flush()

    def close(self) -> None:
        file, self._file = self._file, None
        if file is None:
            return
        broken = False
        try:
            file.close()
            # As ``ftplib`` ends a TLS transfer, read or written.
            unwrap = getattr(self._sock, "unwrap", None)
            if unwrap is not None:
                with contextlib.suppress(OSError, ValueError):
                    unwrap()
            self._sock.close()
            self._client.voidresp()
            if self.after is not None:
                self.after(self._client)
        except ftplib.Error as error:
            raise _os_error(error, "") from error
        except (OSError, EOFError) as error:
            broken = True
            raise _error(errno.EIO, "", str(error)) from error
        finally:
            self._drive.pool.give(self._client, broken=broken)

    def __enter__(self) -> _Transfer:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class _RestReader:
    """``read_at`` over FTP: a transfer from *offset*, abandoned after *count*."""

    def __init__(self, drive: FtpDrive, location: Location) -> None:
        self._drive, self._path = drive, str(location.path)

    def read_at(self, offset: int, count: int) -> bytes:
        drive = self._drive
        client = drive._take()
        broken = False
        try:
            client.voidcmd("TYPE I")
            sock = client.transfercmd(f"RETR {self._path}", rest=offset or None)
            parts, left = [], count
            try:
                while left > 0:
                    data = sock.recv(min(left, 1 << 16))
                    if not data:
                        break
                    parts.append(data)
                    left -= len(data)
            finally:
                sock.close()
            try:
                if left > 0:
                    client.voidresp()  # the whole of it came: 226
                else:
                    client.abort()  # cut short: ABOR, and its 426/226 read
            except ftplib.Error:
                pass
            return b"".join(parts)
        except ftplib.Error as error:
            raise _os_error(error, self._path) from error
        except (OSError, EOFError) as error:
            broken = True
            raise _error(errno.EIO, self._path, str(error)) from error
        finally:
            drive.pool.give(client, broken=broken)

    def close(self) -> None:
        pass


class FtpDrive(Drive):
    """A server's files, over a pool of FTP control connections."""

    capabilities = frozenset((WRITE, RENAME, CHMOD))
    #: No server says when a directory changed: *Auto refresh* looks again.
    polled = True

    def __init__(self, site: Site, pool: _Pool) -> None:
        self.site = site
        self.pool = pool
        self.on_lost: Any = None
        self.home = PurePosixPath("/")

    # -- connections ----------------------------------------------------------------------------

    @contextlib.contextmanager
    def _client(self, where: Any = "") -> Iterator[ftplib.FTP]:
        """A connection for one step, made again once if the server dropped it."""
        pool = self.pool
        client = self._take()
        try:
            yield client
        except (EOFError, ConnectionError, socket.timeout, ftplib.error_temp) as error:
            if isinstance(error, ftplib.error_temp) and not str(error).startswith("421"):
                pool.give(client)
                raise _os_error(error, where) from error
            pool.give(client, broken=True)
            raise _error(errno.EIO, where, "The server closed the connection; try again") from error
        except ftplib.Error as error:
            pool.give(client)
            raise _os_error(error, where) from error
        except BaseException:
            pool.give(client)
            raise
        else:
            pool.give(client)

    def _take(self) -> ftplib.FTP:
        pool = self.pool
        try:
            client = pool.take()
        except DriveGone:
            self._lost()
            raise
        try:
            client.voidcmd("NOOP")
            return client
        except (ftplib.Error, OSError, EOFError):
            pool.give(client, broken=True)
        try:
            client = pool.remake()
        except DriveGone:
            self._lost()
            raise
        with pool._lock:
            pool._made += 1
        return client

    def _lost(self) -> None:
        lost = self.on_lost
        if lost is not None:
            threading.Thread(target=lost, daemon=True).start()

    @staticmethod
    def _path(location: Location) -> str:
        return str(location.path)

    # -- names ----------------------------------------------------------------------------------

    def get_dir(self, location: Location) -> str:
        from navigator.lib.drives.sessions import protocol_sign

        return f"{protocol_sign(self.site.scheme)}:{self.site.host}:{location.path}"

    # -- reading --------------------------------------------------------------------------------

    def _list(self, client: ftplib.FTP, path: str) -> list[tuple[str, FileStat, str | None, str | None]]:
        """``(name, stat, link target, owner)`` for *path*'s entries."""
        pool = self.pool
        if pool.mlsd is not False:
            try:
                found = []
                for name, facts in client.mlsd(path, facts=["type", "size", "modify", "unix.mode",
                                                             "unix.owner", "unix.group"]):
                    if facts.get("type", "").lower() in ("cdir", "pdir") or name in (".", ".."):
                        continue
                    owner = None
                    if "unix.owner" in facts:
                        owner = f"{facts['unix.owner']}:{facts.get('unix.group', '')}"
                    found.append((name, _mlsd_stat(facts), None, owner))
                pool.mlsd = True
                return found
            except ftplib.error_perm as error:
                if str(error)[:3] not in ("500", "501", "502", "504"):
                    raise
                pool.mlsd = False
        lines: list[str] = []
        if pool.list_a is not False:
            # ``-a`` for the dot-files, where the server takes options at all.
            try:
                client.retrlines(f"LIST -a {path}", lines.append)
                pool.list_a = True
            except ftplib.error_perm:
                if pool.list_a:
                    raise
                pool.list_a = False
                lines = []
        if pool.list_a is False:
            client.retrlines(f"LIST {path}", lines.append)
        found = []
        for line in lines:
            parsed = _parse_list(line)
            if parsed is not None and parsed[0] not in (".", ".."):
                found.append(parsed)
        return found

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.appearance import filetypes
        from navigator.lib.drives.listing import DirEntry, order_entries

        mask = options.get("mask", filetypes.ALL_FILES)
        filtered = mask.strip() not in ("", filetypes.ALL_FILES)
        entries: list[DirEntry] = []
        if not location.is_root:
            entries.append(DirEntry("..", True, 0, stat.S_IFDIR | 0o755))
        error = None
        try:
            with self._client(location) as client:
                listed = self._list(client, self._path(location))
        except OSError as failure:
            if isinstance(failure, DriveGone):
                raise
            return entries, failure.strerror or str(failure), None
        for name, st, target, owner in listed:
            if not show_hidden and name.startswith("."):
                continue
            is_link = stat.S_ISLNK(st.st_mode)
            if is_link:
                # Where the server says nothing of its target, a link to a
                # directory is the likelier one to be entered.
                st = FileStat(stat.S_IFDIR | 0o755 if target is None or target.endswith("/") else
                              stat.S_IFREG | 0o644, st.st_size, st.st_mtime, st.st_atime)
            is_dir = stat.S_ISDIR(st.st_mode)
            if filtered and not is_dir and not filetypes.in_filter(name, mask):
                continue
            entry = DirEntry(name, is_dir, 0 if is_dir else st.st_size, st.st_mode, st.st_mtime, is_link, target)
            entry.owner = owner
            entries.append(entry)
        order = {key: options[key] for key in ("executables_first", "archives_first", "reverse")
                 if key in options}
        return order_entries(entries, sort, **order), error, None

    def stat(self, location: Location) -> FileStat:
        if location.is_root:
            return FileStat(stat.S_IFDIR | 0o755)
        with self._client(location) as client:
            if self.pool.mlsd is not False:
                try:
                    reply = client.sendcmd(f"MLST {self._path(location)}")
                    for line in reply.splitlines()[1:]:
                        line = line.strip()
                        if ";" in line:
                            text, _, _ = line.partition(" ")
                            facts = dict(part.split("=", 1) for part in text.split(";") if "=" in part)
                            return _mlsd_stat({key.lower(): value for key, value in facts.items()})
                except ftplib.error_perm as error:
                    if str(error)[:3] not in ("500", "501", "502", "504"):
                        raise _os_error(error, location) from error
            for name, st, _, _ in self._list(client, self._path(location.parent)):
                if name == location.name:
                    return st
        raise _error(errno.ENOENT, location)

    def lstat(self, location: Location) -> FileStat:
        return self.stat(location)

    def children(self, location: Location) -> list[Child]:
        with self._client(location) as client:
            return [(name, st) for name, st, _, _ in self._list(client, self._path(location))]

    def names(self, location: Location) -> list[str]:
        return [name for name, _ in self.children(location)]

    def open_read(self, location: Location) -> IO[bytes]:
        client = self._take()
        try:
            client.voidcmd("TYPE I")
            sock = client.transfercmd(f"RETR {self._path(location)}")
        except ftplib.Error as error:
            self.pool.give(client)
            raise _os_error(error, location) from error
        except BaseException:
            self.pool.give(client, broken=True)
            raise
        return _Transfer(self, client, sock, "rb")  # type: ignore[return-value]

    def open_random(self, location: Location) -> Any:
        """``REST`` and ``RETR`` for each read, the transfer cut off once it
        has what was asked: FTP has no seek, but a server may start a file
        anywhere."""
        return _RestReader(self, location)

    # -- writing --------------------------------------------------------------------------------

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        client = self._take()
        path = self._path(location)
        try:
            client.voidcmd("TYPE I")
            sock = client.transfercmd(f"{'APPE' if append else 'STOR'} {path}")
        except ftplib.Error as error:
            self.pool.give(client)
            raise _os_error(error, location) from error
        except BaseException:
            self.pool.give(client, broken=True)
            raise
        transfer = _Transfer(self, client, sock, "wb")
        if not append:
            def chmod(after: ftplib.FTP) -> None:
                with contextlib.suppress(ftplib.Error):
                    after.voidcmd(f"SITE CHMOD {mode & 0o777 & ~_UMASK:o} {path}")
            transfer.after = chmod
        return transfer  # type: ignore[return-value]

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        with self._client(location) as client:
            try:
                client.mkd(self._path(location))
            except ftplib.error_perm as error:
                if self._exists(client, location):
                    raise _error(errno.EEXIST, location) from error
                raise

    def _exists(self, client: ftplib.FTP, location: Location) -> bool:
        try:
            return any(name == location.name for name, _, _, _ in self._list(client, self._path(location.parent)))
        except ftplib.Error:
            return False

    def rmdir(self, location: Location) -> None:
        with self._client(location) as client:
            client.rmd(self._path(location))

    def unlink(self, location: Location) -> None:
        with self._client(location) as client:
            client.delete(self._path(location))

    def rename(self, source: Location, dest: Location) -> None:
        with self._client(source) as client:
            if self._exists(client, dest):
                raise _error(errno.EEXIST, dest)
            client.rename(self._path(source), self._path(dest))

    def replace(self, source: Location, dest: Location) -> None:
        with self._client(source) as client:
            try:
                client.rename(self._path(source), self._path(dest))
            except ftplib.error_perm:
                # A server that will not rename over a file: out of the way first.
                client.delete(self._path(dest))
                client.rename(self._path(source), self._path(dest))

    def chmod(self, location: Location, mode: int) -> None:
        with self._client(location) as client:
            client.voidcmd(f"SITE CHMOD {mode & 0o7777:o} {self._path(location)}")

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        stamp = time.strftime("%Y%m%d%H%M%S", time.gmtime(mtime_ns / 1e9))
        with self._client(location) as client:
            client.voidcmd(f"MFMT {stamp} {self._path(location)}")

    def describe(self) -> list[tuple[str, str]]:
        lines = [("Server", f"{self.pool.user}@{self.pool.host}:{self.pool.port}")]
        if self.pool.secure:
            lines.append(("Security", "TLS (FTPS)"))
        return lines

    def close(self) -> None:
        self.pool.close()


def _read_umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


_UMASK = _read_umask()


def connect(site: Site, answers: Answers) -> FtpDrive:
    """*site* logged into: blocks, and raises what the user must answer."""
    pool = _Pool(site, answers)
    drive = FtpDrive(site, pool)
    try:
        with drive._client() as client:
            drive.home = PurePosixPath(client.pwd() or "/")
    except OSError:
        pass
    if answers.save_password and answers.password and site.user:
        from navigator.lib.drives.credentials import save_password

        save_password(site, answers.password)
    return drive


__all__ = ["CONNECTIONS", "FtpDrive", "available", "connect"]
