"""rclone's remotes as a drive: ``rclone://REMOTE/path``.

`rclone <https://rclone.org/>`_ speaks to some seventy storage services --
Google Drive, OneDrive, Dropbox, Box, pCloud, Mega, B2, Swift, WebDAV... --
each set up once with ``rclone config``.  Any remote set up there is a place
a panel can be, with no Python client for any of them: Navigator speaks to
rclone and rclone to the service.  DOS had no cloud; this is a departure,
asked for, as the containers were.

**One daemon a connection.**  ``rclone rcd`` is started for the drive on a
Unix socket of its own in a directory of this user's alone -- the runtime
directory, else :func:`~navigator.lib.system.tempdir.private_dir`, whichever
gives a path short enough to bind -- and ``--rc-no-auth``: that directory is
the guard, and every step is a JSON call to its remote control
(``operations/list``, ``stat``, ``mkdir``, ``movefile``...).  So rclone reads
its configuration and logs in to the service once, and keeps its tokens and
caches warm, where a process a step (as the containers' drive runs) would log
in again for every listing.  Its ``--rc-serve`` gives each object at
``/[REMOTE:]/path``, with ranges: a file is read as it streams, and F3 reads
one a chunk at a time.  A file is written as a streamed multipart POST to
``operations/uploadfile``, which rclone hands to the service as it comes.

**The host is the remote's name**, case-sensitive and as written
(``location.AS_WRITTEN``); the path is from the remote's own root
(``REMOTE:``) -- an sftp or local-backend remote's root is where its
configuration says, its home by default.  Remotes made on the fly
(``:s3,provider=...:``) are not reached.

**A configuration encrypted** by ``rclone config`` wants its password: it
is asked as a password is (:class:`NeedPassword`), given to the daemon in its
environment (``RCLONE_CONFIG_PASS``, which only this user can read in
``/proc``), never on its command line, and kept in the keyring if asked.

No modes, owners, links or times to set: what a service keeps of those is
rclone's business, and an object's time is its upload's.  A directory is
renamed on the server where the backend can (``DirMove``), else ``EXDEV``
and the copier copies it.

**An rclone before 1.63** (Ubuntu 24.04's is 1.60) cannot serve the remote
control on a Unix socket.  When it says so the daemon is started again on
``127.0.0.1``, on a port the system picks (read back from its *Serving remote
control on* line), with a user and a random password of its own given in its
environment (``RCLONE_RC_USER``/``RCLONE_RC_PASS``, never its command line)
and sent with every request.  What was learnt is kept for the next daemon.
"""

from __future__ import annotations

import errno
import http.client
import base64
import io
import json
import os
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import IO, Any
from urllib.parse import quote

from navigator.lib.drives.base import (
    FREE_SPACE,
    RENAME,
    WRITE,
    Child,
    Drive,
    DriveGone,
    FileStat,
)
from navigator.lib.drives.location import Location, Site
from navigator.lib.drives.sessions import Answers, NeedPassword
from navigator.lib.system.which import which as _which

#: The command spoken through.
PROGRAM = "rclone"

#: The directories' mode, and the files': rclone keeps none.
DIR_MODE = stat.S_IFDIR | 0o755
FILE_MODE = stat.S_IFREG | 0o644

#: How long the daemon may take to put its socket up.
START_TIMEOUT = 20.0

#: What rclone says of a configuration it cannot read without a password,
#: or with the one it was given.
_CONFIG_PASSWORD = ("rclone_config_pass", "configuration password", "decrypt configuration",
                    "couldn't decrypt", "unable to decrypt")

#: rclone's error words, and the errno each is.
_WORDS = (
    ("not found", errno.ENOENT),
    ("doesn't exist", errno.ENOENT),
    ("does not exist", errno.ENOENT),
    ("directory not empty", errno.ENOTEMPTY),
    ("not empty", errno.ENOTEMPTY),
    ("already exists", errno.EEXIST),
    ("permission denied", errno.EACCES),
    ("access denied", errno.EACCES),
    ("forbidden", errno.EACCES),
    ("is a directory", errno.EISDIR),
    ("not a directory", errno.ENOTDIR),
    ("quota", errno.EDQUOT),
)
_STATUS = {404: errno.ENOENT, 403: errno.EACCES, 401: errno.EACCES, 409: errno.EEXIST,
           507: errno.ENOSPC, 416: errno.EINVAL}
_KINDS = {errno.ENOENT: FileNotFoundError, errno.EEXIST: FileExistsError, errno.EACCES: PermissionError,
          errno.EISDIR: IsADirectoryError, errno.ENOTDIR: NotADirectoryError}


def program() -> str | None:
    """Where ``rclone`` is, or None."""
    return _which(PROGRAM)


def available() -> str | None:
    if program() is None:
        return "rclone remotes need the rclone command"
    return None


def os_error(text: str, where: Any = None, status: int = 0) -> OSError:
    """The ``OSError`` rclone's error *text* (and its HTTP *status*) is."""
    lower = text.lower()
    number = next((each for words, each in _WORDS if words in lower), _STATUS.get(status, errno.EIO))
    return _KINDS.get(number, OSError)(number, " ".join(text.split()) or os.strerror(number),
                                       None if where is None else str(where))


def _error(number: int, where: Any, message: str | None = None) -> OSError:
    return _KINDS.get(number, OSError)(number, message or os.strerror(number), None if where is None else str(where))


def wants_password(text: str) -> bool:
    """Whether rclone's *text* says its configuration needs a password (or a right one)."""
    lower = text.lower()
    return any(words in lower for words in _CONFIG_PASSWORD)


def moment(text: str) -> float:
    """``ModTime``'s RFC 3339 -- nanoseconds and all -- as seconds; 0 when unreadable."""
    if not text:
        return 0.0
    text = text.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    head, dot, rest = text.partition(".")
    fraction = ""
    if dot:
        digits = len(rest) - len(rest.lstrip("0123456789"))
        fraction, rest = rest[:digits], rest[digits:]
    try:
        whole = datetime.fromisoformat(head + rest).timestamp()
    except ValueError:
        return 0.0
    return whole + (float(f"0.{fraction}") if fraction else 0.0)


def facts(item: dict[str, Any]) -> FileStat:
    """A ``FileStat`` for one of ``operations/list``'s items."""
    when = moment(str(item.get("ModTime") or ""))
    if item.get("IsDir"):
        return FileStat(DIR_MODE, 0, when, when)
    size = item.get("Size")
    return FileStat(FILE_MODE, max(0, int(size)) if isinstance(size, int) else 0, when, when)


@dataclass(frozen=True)
class Remote:
    """One remote ``rclone config`` has: its name and its backend."""

    name: str
    kind: str = ""


def parse_listremotes(text: str) -> list[Remote]:
    """``rclone listremotes --long``: ``name:   type`` a line (a name may hold spaces)."""
    found = []
    for line in text.splitlines():
        if not line.strip():
            continue
        name, colon, kind = line.rstrip().rpartition(":")
        if not colon:
            name, kind = line.strip().rstrip(":"), ""
        elif not name:
            continue
        found.append(Remote(name.strip(), kind.strip()))
    return found


def config_env(password: str | None = None) -> dict[str, str]:
    """The environment rclone runs in: ours, with the configuration's password when given."""
    env = dict(os.environ)
    if password is not None:
        env["RCLONE_CONFIG_PASS"] = password
    return env


def list_remotes(password: str | None = None) -> list[Remote]:
    """The remotes ``rclone config`` has: blocks, so a thread asks.  Raises
    ``OSError`` with rclone's words."""
    found = program()
    if found is None:
        raise OSError(errno.ENOENT, "rclone: command not found")
    try:
        done = subprocess.run([found, "listremotes", "--long", "--ask-password=false"], capture_output=True,
                              stdin=subprocess.DEVNULL, timeout=30, env=config_env(password))
    except subprocess.TimeoutExpired as error:
        raise OSError(errno.ETIMEDOUT, "rclone listremotes did not answer") from error
    if done.returncode != 0:
        text = done.stderr.decode("utf-8", "replace")
        if wants_password(text):
            raise PermissionError(errno.EACCES, "rclone's configuration is encrypted: connect to a remote "
                                                "to give its password")
        raise os_error(text or f"rclone listremotes exited {done.returncode}")
    return parse_listremotes(done.stdout.decode("utf-8", "replace"))


def configure_command() -> list[str]:
    """What *Configure...* runs in a window: rclone's own interactive setup."""
    return [program() or PROGRAM, "config"]


# -- the daemon -----------------------------------------------------------------------------------


class _UnixConnection(http.client.HTTPConnection):
    """HTTP over the daemon's Unix socket."""

    def __init__(self, path: str, timeout: float) -> None:
        super().__init__("localhost", timeout=timeout)
        self._path = path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect(self._path)
        except BaseException:
            sock.close()
            raise
        self.sock = sock


class _TcpConnection(http.client.HTTPConnection):
    """HTTP to a daemon on ``127.0.0.1``, its user and password with every request."""

    def __init__(self, port: int, authorization: str, timeout: float) -> None:
        super().__init__("127.0.0.1", port, timeout=timeout)
        self._authorization = authorization

    def putrequest(self, method: str, url: str, *args: Any, **kwargs: Any) -> None:
        super().putrequest(method, url, *args, **kwargs)
        self.putheader("Authorization", self._authorization)


class _Unreachable(Exception):
    """The daemon did not answer: gone, or never there."""


_counter = 0
_counter_lock = threading.Lock()

#: Whether this rclone was found not to serve on a Unix socket (before 1.63):
#: the next daemon goes to TCP at once.
_tcp_only = False

#: What an rclone before 1.63 says of ``--rc-addr=unix://...``: it took the
#: whole as a host and port.
_NO_UNIX = ("unknown port", "lookup tcp", "missing port", "too many colons")

#: Where the daemon says it serves, when on TCP.
_SERVING = re.compile(r"Serving remote control on https?://[^\s/]*:(\d+)/")


#: The longest a socket's path may be (``sun_path`` is 108 bytes, its end a NUL).
_SOCKET_LIMIT = 100


def _private(directory: str) -> bool:
    """Whether *directory* is this user's alone."""
    try:
        info = os.lstat(directory)
    except OSError:
        return False
    return stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077


def _socket_path() -> str:
    """A new socket's path in a directory of this user's alone, short enough
    to bind: the runtime directory's, else the private one's, else one made
    under the system's temporary directory."""
    import tempfile

    from navigator.lib.system.tempdir import private_dir

    global _counter
    with _counter_lock:
        _counter += 1
        number = _counter
    name = f"rclone-{os.getpid()}-{number}.sock"
    candidates = []
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    if runtime and _private(runtime):
        candidates.append(runtime)
    try:
        candidates.append(str(private_dir()))
    except OSError:
        pass
    for directory in candidates:
        if len(os.path.join(directory, name)) <= _SOCKET_LIMIT:
            return os.path.join(directory, name)
    return os.path.join(tempfile.mkdtemp(prefix="nav-rc-"), name)


class Daemon:
    """One ``rclone rcd``: started, asked, stopped."""

    def __init__(self, password: str | None = None) -> None:
        self.password = password
        self.path = ""
        self.port = 0
        self.tcp = False
        self._authorization = ""
        self.process: subprocess.Popen[bytes] | None = None
        self.version = ""

    def argv(self) -> list[str]:
        if self.tcp:
            return [program() or PROGRAM, "rcd", "--rc-addr=127.0.0.1:0", "--rc-serve", "--ask-password=false"]
        return [program() or PROGRAM, "rcd", f"--rc-addr=unix://{self.path}", "--rc-serve", "--rc-no-auth",
                "--ask-password=false"]

    def start(self) -> None:
        """Up and answering, on a Unix socket or else on TCP: raises
        :class:`_StartFailed` with rclone's words when it ended first."""
        global _tcp_only
        if not _tcp_only:
            try:
                self._start(tcp=False)
                return
            except _StartFailed as error:
                if not any(words in str(error).lower() for words in _NO_UNIX):
                    raise
                _tcp_only = True
        self._start(tcp=True)

    def _start(self, *, tcp: bool) -> None:
        self.tcp = tcp
        env = config_env(self.password)
        if tcp:
            self.path = ""
            user, password = "navigator", secrets.token_urlsafe(24)
            env["RCLONE_RC_USER"], env["RCLONE_RC_PASS"] = user, password
            self._authorization = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
        else:
            self.path = _socket_path()
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass
        self.port = 0
        try:
            self.process = subprocess.Popen(self.argv(), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.PIPE, env=env, start_new_session=True)
        except FileNotFoundError as error:
            raise OSError(errno.ENOENT, "rclone: command not found") from error
        # Its standard error is read throughout, so a chatty daemon never blocks
        # on it: the start's lines kept (the port, or why it ended), the rest dropped.
        log = _Log()
        reader = threading.Thread(target=log.read, args=(self.process.stderr,), daemon=True, name="nav-rclone-log")
        reader.start()
        deadline = time.monotonic() + START_TIMEOUT
        while True:
            if self.process.poll() is not None:
                reader.join(timeout=2)
                self.process = None
                raise _StartFailed(log.text().strip() or "rclone rcd ended at once")
            if tcp and not self.port:
                self.port = log.port
            if self.port if tcp else os.path.exists(self.path):
                try:
                    self.version = str(self.call("core/version", timeout=5).get("version", ""))
                    break
                except _Unreachable:
                    pass
            if time.monotonic() > deadline:
                self.stop()
                raise OSError(errno.ETIMEDOUT, "rclone rcd did not start")
            time.sleep(0.05)
        log.done()

    @property
    def alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def connection(self, timeout: float) -> http.client.HTTPConnection:
        if self.tcp:
            return _TcpConnection(self.port, self._authorization, timeout)
        return _UnixConnection(self.path, timeout)

    def call(self, method: str, timeout: float = 60.0, **params: Any) -> dict[str, Any]:
        """``method`` called with *params*: its answer.  Raises :class:`RcError`
        for rclone's refusal, :class:`_Unreachable` when nothing answered."""
        body = json.dumps(params).encode()
        connection = self.connection(timeout)
        try:
            try:
                connection.request("POST", f"/{method}", body, {"Content-Type": "application/json"})
                response = connection.getresponse()
                data = response.read()
            except (ConnectionError, FileNotFoundError, socket.timeout, http.client.HTTPException, OSError) as error:
                if isinstance(error, socket.timeout) and self.alive:
                    raise OSError(errno.ETIMEDOUT, f"rclone did not answer {method}") from error
                raise _Unreachable(str(error)) from error
        finally:
            connection.close()
        return _answer(response.status, data)

    def stop(self) -> None:
        process, self.process = self.process, None
        if process is not None and process.poll() is None:
            try:
                self.call_quietly("core/quit")
                process.wait(timeout=3)
            except Exception:
                pass
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=3)
                except Exception:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except Exception:
                        pass
        if self.path:
            try:
                os.unlink(self.path)
            except OSError:
                pass
            if os.path.basename(os.path.dirname(self.path)).startswith("nav-rc-"):
                try:
                    os.rmdir(os.path.dirname(self.path))
                except OSError:
                    pass

    def call_quietly(self, method: str) -> None:
        try:
            connection = self.connection(2)
            connection.request("POST", f"/{method}", b"{}", {"Content-Type": "application/json"})
            connection.getresponse().read()
            connection.close()
        except Exception:
            pass


class _StartFailed(Exception):
    """The daemon ended before its socket was up: rclone's words."""


class RcError(Exception):
    """rclone refused a call: its words and HTTP status."""

    def __init__(self, text: str, status: int) -> None:
        super().__init__(text)
        self.text, self.status = text, status


class _Log:
    """The daemon's standard error: its lines kept until it is up, then dropped."""

    LIMIT = 65536

    def __init__(self) -> None:
        self._lines: list[str] = []
        self._size = 0
        self._keeping = True
        self.port = 0

    def read(self, stream: Any) -> None:
        try:
            for raw in stream:
                if not self._keeping:
                    continue
                line = raw.decode("utf-8", "replace")
                found = _SERVING.search(line)
                if found and not self.port:
                    self.port = int(found.group(1))
                if self._size < self.LIMIT:
                    self._lines.append(line)
                    self._size += len(line)
        except Exception:
            pass

    def text(self) -> str:
        return "".join(self._lines)

    def done(self) -> None:
        self._keeping = False
        self._lines = []


def _answer(status: int, data: bytes) -> dict[str, Any]:
    try:
        answer = json.loads(data or b"{}")
    except ValueError:
        answer = {"error": data.decode("utf-8", "replace")}
    if not isinstance(answer, dict):
        answer = {}
    if status != 200:
        raise RcError(str(answer.get("error") or f"HTTP {status}"), int(answer.get("status") or status))
    return answer


# -- the drive ------------------------------------------------------------------------------------


class RcloneDrive(Drive):
    """A remote ``rclone config`` has, through one ``rclone rcd``."""

    #: No service says when a directory changed: *Auto refresh* looks again.
    polled = True
    seekable = False

    def __init__(self, site: Site, daemon: Daemon) -> None:
        self.site = site
        self.daemon = daemon
        self.on_lost: Any = None
        self.home = PurePosixPath("/")
        self.kind = ""
        self.info: dict[str, Any] = {}
        self.capabilities = frozenset((WRITE, RENAME))
        self._lock = threading.Lock()
        self._closed = False

    # -- speaking ---------------------------------------------------------------------------

    @property
    def fs(self) -> str:
        """The remote's root as rclone names it: ``REMOTE:``."""
        return f"{self.site.host}:"

    @staticmethod
    def remote_of(location: Location) -> str:
        """*location*'s path from the remote's root, as rclone's ``remote`` takes it."""
        return "/".join(part for part in location.path.parts if part not in ("/", "."))

    @property
    def _timeout(self) -> float:
        from navigator.settings import SETTINGS

        return float(max(30, SETTINGS.remote.timeout))

    def _gone(self, reason: str) -> DriveGone:
        lost = self.on_lost
        if lost is not None and not self._closed:
            threading.Thread(target=lost, daemon=True).start()
        return DriveGone(self.site.host, reason)

    def _revive(self) -> bool:
        """The daemon started again once, after it went: the one silent reconnect."""
        with self._lock:
            if self._closed:
                return False
            if self.daemon.alive:
                return True
            self.daemon.stop()
            try:
                self.daemon.start()
            except Exception:
                return False
            return True

    def call(self, method: str, where: Any = None, **params: Any) -> dict[str, Any]:
        """*method* asked of the daemon, its refusal an ``OSError``."""
        for attempt in (0, 1):
            try:
                return self.daemon.call(method, timeout=self._timeout, **params)
            except RcError as error:
                raise os_error(error.text, where, error.status) from error
            except _Unreachable as error:
                if attempt == 0 and self._revive():
                    continue
                raise self._gone(f"rclone for {self.site.host} is not running: {error}") from error
        raise AssertionError("unreachable")

    def _open(self, method: str, url: str, headers: dict[str, str], where: Any) -> tuple[Any, Any]:
        """A request whose answer is read as it streams: ``(connection, response)``."""
        for attempt in (0, 1):
            connection = self.daemon.connection(self._timeout)
            try:
                connection.request(method, url, headers=headers)
                response = connection.getresponse()
            except (ConnectionError, FileNotFoundError, http.client.HTTPException, OSError) as error:
                connection.close()
                if attempt == 0 and self._revive():
                    continue
                raise self._gone(f"rclone for {self.site.host} is not running: {error}") from error
            if response.status not in (200, 206):
                data = response.read()
                connection.close()
                try:
                    _answer(response.status, data)
                except RcError as error:
                    raise os_error(error.text, where, error.status) from error
                raise _error(errno.EIO, where, f"HTTP {response.status}")
            return connection, response
        raise AssertionError("unreachable")

    def object_url(self, location: Location) -> str:
        """Where ``--rc-serve`` gives *location*: ``/[REMOTE:]/a/b``."""
        name = quote(self.fs, safe="")
        return f"/[{name}]/" + "/".join(quote(part, safe="") for part in self.remote_of(location).split("/"))

    # -- names ------------------------------------------------------------------------------

    def get_dir(self, location: Location) -> str:
        from navigator.lib.drives.sessions import protocol_sign

        return f"{protocol_sign(self.site.scheme)}:{self.site.host}:{location.path}"

    # -- reading ----------------------------------------------------------------------------

    def _list(self, location: Location) -> list[Child]:
        answer = self.call("operations/list", location, fs=self.fs, remote=self.remote_of(location),
                           opt={"noMimeType": True})
        found: dict[str, FileStat] = {}
        for item in answer.get("list") or []:
            name = str(item.get("Name") or str(item.get("Path") or "").rpartition("/")[2])
            if name and name not in found:
                found[name] = facts(item)
        return sorted(found.items())

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.appearance import filetypes
        from navigator.lib.drives.listing import DirEntry, order_entries

        mask = options.get("mask", filetypes.ALL_FILES)
        filtered = mask.strip() not in ("", filetypes.ALL_FILES)
        entries = [] if location.is_root else [DirEntry("..", True, 0, DIR_MODE)]
        try:
            listed = self._list(location)
        except DriveGone:
            raise
        except OSError as error:
            return entries, error.strerror or str(error), None
        for name, st in listed:
            if not show_hidden and name.startswith("."):
                continue
            is_dir = stat.S_ISDIR(st.st_mode)
            if filtered and not is_dir and not filetypes.in_filter(name, mask):
                continue
            entries.append(DirEntry(name, is_dir, st.st_size, st.st_mode, st.st_mtime))
        space = None
        if free and FREE_SPACE in self.capabilities:
            left = self.free_bytes(location)
            if left is not None:
                space = (left, self.site.host)
        order = {key: options[key] for key in ("executables_first", "archives_first", "reverse")
                 if key in options}
        return order_entries(entries, sort, **order), None, space

    def children(self, location: Location) -> list[Child]:
        return self._list(location)

    def names(self, location: Location) -> list[str]:
        return [name for name, _ in self._list(location)]

    def stat(self, location: Location) -> FileStat:
        remote = self.remote_of(location)
        if not remote:
            return FileStat(DIR_MODE)
        answer = self.call("operations/stat", location, fs=self.fs, remote=remote, opt={"noMimeType": True})
        item = answer.get("item")
        if not item:
            raise _error(errno.ENOENT, location)
        return facts(item)

    def lstat(self, location: Location) -> FileStat:
        return self.stat(location)

    def free_bytes(self, location: Location) -> int | None:
        try:
            answer = self.call("operations/about", location, fs=self.fs)
        except DriveGone:
            raise
        except OSError:
            return None
        if isinstance(answer.get("free"), int):
            return answer["free"]
        if isinstance(answer.get("total"), int) and isinstance(answer.get("used"), int):
            return max(0, answer["total"] - answer["used"])
        return None

    def open_read(self, location: Location) -> IO[bytes]:
        if not self.remote_of(location):
            raise _error(errno.EISDIR, location)
        connection, response = self._open("GET", self.object_url(location), {}, location)
        return io.BufferedReader(_Body(connection, response), 1 << 16)  # type: ignore[return-value]

    def open_random(self, location: Location) -> Any:
        """Ranged ``GET``s: F3 reads a file a chunk at a time."""
        if not self.remote_of(location):
            raise _error(errno.EISDIR, location)
        return _RangeReader(self, location)

    # -- writing ----------------------------------------------------------------------------

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        remote = self.remote_of(location)
        if not remote:
            raise _error(errno.EISDIR, location)
        if append:
            raise _error(errno.ENOTSUP, location, "rclone cannot append to a file")
        return _Upload(self, location)  # type: ignore[return-value]

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        remote = self.remote_of(location)
        if not remote or self.lexists(location):
            raise _error(errno.EEXIST, location)
        self.call("operations/mkdir", location, fs=self.fs, remote=remote)

    def rmdir(self, location: Location) -> None:
        remote = self.remote_of(location)
        if not remote:
            raise _error(errno.EBUSY, location)
        if self._list(location):
            raise _error(errno.ENOTEMPTY, location)
        self.call("operations/rmdir", location, fs=self.fs, remote=remote)

    def unlink(self, location: Location) -> None:
        remote = self.remote_of(location)
        if not remote:
            raise _error(errno.EISDIR, location)
        if stat.S_ISDIR(self.stat(location).st_mode):
            raise _error(errno.EISDIR, location)
        self.call("operations/deletefile", location, fs=self.fs, remote=remote)

    def _move(self, source: Location, dest: Location, *, replace: bool) -> None:
        if source.site != self.site or dest.site != self.site:
            raise _error(errno.EXDEV, source)
        old, new = self.remote_of(source), self.remote_of(dest)
        if not old or not new:
            raise _error(errno.EBUSY, source)
        is_dir = stat.S_ISDIR(self.stat(source).st_mode)
        there = None
        try:
            there = self.stat(dest)
        except FileNotFoundError:
            pass
        if there is not None and (not replace or stat.S_ISDIR(there.st_mode)):
            raise _error(errno.EEXIST, dest)
        if is_dir:
            if not self.info.get("Features", {}).get("DirMove"):
                raise _error(errno.EXDEV, source, f"{self.kind or 'this remote'} cannot rename a directory")
            self.call("sync/move", source, srcFs=f"{self.fs}{old}", dstFs=f"{self.fs}{new}",
                      createEmptySrcDirs=True, deleteEmptySrcDirs=True)
            return
        self.call("operations/movefile", source, srcFs=self.fs, srcRemote=old, dstFs=self.fs, dstRemote=new)

    def rename(self, source: Location, dest: Location) -> None:
        self._move(source, dest, replace=False)

    def replace(self, source: Location, dest: Location) -> None:
        self._move(source, dest, replace=True)

    def copy_attributes(self, source_drive: Drive, source: Location, dest: Location, st: Any, *,
                        follow: bool) -> None:
        """Nothing to set: a file's time on a service is its upload's."""

    # -- the rest ---------------------------------------------------------------------------

    def describe(self) -> list[tuple[str, str]]:
        lines = [("Remote", self.site.host)]
        if self.kind:
            lines.append(("Backend", self.kind))
        if self.daemon.version:
            lines.append(("Software", f"rclone {self.daemon.version}"))
        hashes = self.info.get("Hashes")
        if hashes:
            lines.append(("Hashes", ", ".join(str(each) for each in hashes)))
        return lines

    def close(self) -> None:
        with self._lock:
            self._closed = True
        self.daemon.stop()


class _Body(io.RawIOBase):
    """A served object's body, as it streams."""

    def __init__(self, connection: Any, response: Any) -> None:
        super().__init__()
        self._connection, self._response = connection, response

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        try:
            return self._response.readinto(buffer)
        except (http.client.IncompleteRead, ConnectionError) as error:
            raise OSError(errno.EIO, f"rclone stopped sending: {error}") from error

    def close(self) -> None:
        if not self.closed:
            try:
                self._connection.close()
            except Exception:
                pass
        super().close()


class _RangeReader:
    """``read_at`` as a ranged ``GET``."""

    def __init__(self, drive: RcloneDrive, where: Location) -> None:
        self._drive, self._where = drive, where
        self._url = drive.object_url(where)

    def read_at(self, offset: int, count: int) -> bytes:
        if count <= 0:
            return b""
        try:
            connection, response = self._drive._open(
                "GET", self._url, {"Range": f"bytes={offset}-{offset + count - 1}"}, self._where)
        except OSError as error:
            if error.errno == errno.EINVAL:  # 416: past the end
                return b""
            raise
        try:
            data = response.read()
        finally:
            connection.close()
        # A server that answered the whole file (200) for a range.
        return data[offset:offset + count] if response.status == 200 else data[:count]

    def close(self) -> None:
        pass


class _Upload(io.RawIOBase):
    """A file being written: one multipart POST to ``operations/uploadfile``,
    its body sent chunk by chunk as the bytes come, so rclone passes them on
    as they arrive.  Its answer is read on close; an exception in the
    ``with`` it is written in cuts the request off, and the copier removes
    what may be left."""

    BOUNDARY = "navigator-rclone-upload-boundary-7f3a9c"

    def __init__(self, drive: RcloneDrive, where: Location) -> None:
        super().__init__()
        self._drive, self._where = drive, where
        remote = drive.remote_of(where)
        parent, _, name = remote.rpartition("/")
        query = f"fs={quote(drive.fs, safe='')}&remote={quote(parent, safe='')}"
        self._connection = drive.daemon.connection(drive._timeout)
        try:
            self._connection.putrequest("POST", f"/operations/uploadfile?{query}")
            self._connection.putheader("Content-Type", f"multipart/form-data; boundary={self.BOUNDARY}")
            self._connection.putheader("Transfer-Encoding", "chunked")
            self._connection.endheaders()
            quoted = quote(name, safe="")
            ascii_name = name.encode("ascii", "replace").decode().replace('"', "_").replace("?", "_")
            head = (f"--{self.BOUNDARY}\r\n"
                    f"Content-Disposition: form-data; name=\"file0\"; filename=\"{ascii_name}\"; "
                    f"filename*=UTF-8''{quoted}\r\n"
                    "Content-Type: application/octet-stream\r\n\r\n").encode()
            self._chunk(head)
        except (ConnectionError, FileNotFoundError, OSError) as error:
            self._connection.close()
            raise drive._gone(f"rclone for {drive.site.host} is not running: {error}") from error

    def _chunk(self, data: bytes) -> None:
        if data:
            self._connection.send(b"%x\r\n" % len(data) + data + b"\r\n")

    def writable(self) -> bool:
        return True

    def write(self, data: Any) -> int:
        if self.closed:
            raise ValueError("write to a closed upload")
        data = bytes(data)
        try:
            self._chunk(data)
        except OSError as error:
            self.abort()
            raise _error(errno.EIO, self._where, f"rclone stopped taking the file: {error}") from error
        return len(data)

    def abort(self) -> None:
        """Nothing completed: the request cut off."""
        try:
            self._connection.close()
        except Exception:
            pass
        super().close()

    def close(self) -> None:
        if self.closed:
            return
        try:
            self._chunk(f"\r\n--{self.BOUNDARY}--\r\n".encode())
            self._connection.send(b"0\r\n\r\n")
            response = self._connection.getresponse()
            data = response.read()
        except (OSError, http.client.HTTPException) as error:
            self.abort()
            raise _error(errno.EIO, self._where, f"rclone did not take the file: {error}") from error
        self._connection.close()
        super().close()
        try:
            _answer(response.status, data)
        except RcError as error:
            raise os_error(error.text, self._where, error.status) from error

    def __exit__(self, kind: Any, value: Any, traceback: Any) -> None:
        if kind is not None:
            self.abort()
        else:
            self.close()


def _environment_type(name: str) -> str:
    """The backend of a remote set up in the environment, as rclone names its
    variable: ``RCLONE_CONFIG_`` and the name upper-cased, ``-`` as ``_``."""
    key = "RCLONE_CONFIG_" + name.upper().replace("-", "_") + "_TYPE"
    return os.environ.get(key, "")


def connect(site: Site, answers: Answers) -> RcloneDrive:
    """*site*'s remote, its daemon up: blocks, and raises what the user must answer."""
    from navigator.lib.drives import credentials

    if not site.host:
        raise DriveGone("rclone", "Name a remote: rclone://REMOTE/path")
    keyring_site = Site("rclone")
    if answers.password is None and not answers.tried_keyring:
        answers.tried_keyring = True
        answers.password = credentials.saved_password(keyring_site)
    daemon = Daemon(answers.password)
    try:
        daemon.start()
    except _StartFailed as error:
        text = str(error)
        if wants_password(text):
            raise NeedPassword(site, "rclone", "rclone's configuration", wrong=answers.password is not None) \
                from error
        raise os_error(text, site.host) from error
    drive = RcloneDrive(site, daemon)
    try:
        # Not config/listremotes: it leaves out a remote set up in the
        # environment (RCLONE_CONFIG_NAME_TYPE=...), which fsinfo reaches.
        try:
            drive.info = drive.call("operations/fsinfo", fs=drive.fs)
        except OSError as error:
            words = error.strerror or ""
            if wants_password(words):
                raise NeedPassword(site, "rclone", "rclone's configuration",
                                   wrong=answers.password is not None) from error
            if "find section in config" in words:
                raise DriveGone(site.host, f"rclone has no remote called {site.host}") from error
            raise
        try:
            drive.kind = str(drive.call("config/get", name=site.host).get("type") or "")
        except OSError:
            pass
        drive.kind = drive.kind or _environment_type(site.host)
        if drive.info.get("Features", {}).get("About"):
            drive.capabilities = drive.capabilities | {FREE_SPACE}
    except BaseException:
        drive.close()
        raise
    if answers.save_password and answers.password:
        answers.keyring_refused = credentials.save_password(keyring_site, answers.password) or ""
    return drive


__all__ = ["Daemon", "PROGRAM", "Remote", "RcloneDrive", "available", "configure_command", "connect",
           "list_remotes", "moment", "os_error", "parse_listremotes", "program", "wants_password"]
