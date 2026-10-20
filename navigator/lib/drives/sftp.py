"""A server's files over SSH: the SFTP drive, ``sftp://user@host:port/path``.

The heir of DN's ``TLinkDrive`` (``NAVYLINK.PAS``), whose other PC was at
the end of a serial cable: the panel reads a directory there, a copy goes
across, and :meth:`SftpDrive.get_dir` is ``host:/path`` where DN's said
``LINK:C:\\...``.  It needs `paramiko <https://www.paramiko.org/>`_, the
``navigator-fm[sftp]`` extra; without it :func:`available` says so and
nothing here is imported.

**One SSH connection per site, several SFTP channels on it.**  paramiko's
``SFTPClient`` is not for two threads at once, and a panel's read should not
wait behind a copy's megabytes, so each operation checks a channel out of a
small pool (:data:`CHANNELS`) for itself -- a file opened keeps its channel
until it is closed.  A connection that dropped is made again once, silently,
with what proved it the first time (kept in memory, never on disk); if that
fails the drive is lost, and :data:`~navigator.lib.drives.sessions.SESSIONS`
sends its panels home.

Copies are fast only with paramiko's two tricks: reads ``prefetch`` the file
ahead of the copy, and writes are *pipelined* -- each request sent without
waiting for the one before to be answered.
"""

from __future__ import annotations

import contextlib
import errno
import importlib.util
import os
import queue
import socket
import stat
import threading
from pathlib import PurePosixPath
from typing import IO, Any, Iterator

from navigator.lib.drives.base import CHMOD, CHOWN, RENAME, SYMLINK, WRITE, Child, Drive, DriveGone, FileStat
from navigator.lib.drives.location import Location, Site
from navigator.lib.drives.sessions import (
    Answers, HostKeyChanged, NeedPassphrase, NeedPassword, UnknownHostKey,
)

#: How many SFTP channels one connection may have open at once.
CHANNELS = 4

#: What the drive cannot be without.
EXTRA = "navigator-fm[sftp]"


def available() -> str | None:
    """Why SFTP cannot be used here -- paramiko missing -- or None."""
    if importlib.util.find_spec("paramiko") is None:
        return f"SFTP needs paramiko: pip install {EXTRA}"
    return None


def _umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


#: Read once, on import: a file made on the server is given the local umask,
#: as a copy made on the disk would be.
_UMASK = _umask()


def _stat_of(attributes: Any) -> FileStat:
    return FileStat(attributes.st_mode or 0, attributes.st_size or 0, float(attributes.st_mtime or 0),
                    float(attributes.st_atime or 0), attributes.st_uid or 0, attributes.st_gid or 0)


def _owner_of(attributes: Any) -> str | None:
    """``user:group`` from ``ls -l``'s line the server sent, where it sent one."""
    words = (getattr(attributes, "longname", None) or "").split()
    if len(words) >= 4:
        return f"{words[2]}:{words[3]}"
    return None


class _Connection:
    """One SSH connection and its pool of SFTP channels."""

    def __init__(self, site: Site, answers: Answers) -> None:
        self.site = site
        self.answers = answers
        self.client: Any = None
        self.transport: Any = None
        #: The ``ProxyJump`` hosts' clients, first first, the server's
        #: connection carried by the last's.
        self.chain: list[Any] = []
        self.hostname = site.host
        self.port = site.port or 22
        self.user = site.user
        self._pool: queue.LifoQueue[Any] = queue.LifoQueue()
        self._made = 0
        self._lock = threading.Lock()
        #: Set by :meth:`close`: an end that is meant, not one to mend.
        self._closing = False
        #: Called, on a thread of its own, once the connection is gone and
        #: could not be made again: the drive's, which tells the sessions.
        self.on_lost: Any = None
        self.open()

    # -- connecting ------------------------------------------------------------------------------

    def open(self) -> None:
        import paramiko

        from navigator.lib.drives import credentials
        from navigator.settings import SETTINGS

        site, answers = self.site, self.answers
        config = credentials.host_config(site)
        self.hostname, self.port, self.user = config.hostname, config.port, config.user
        # ``ProxyJump``: each host on the way logged into in turn, the next
        # one reached over a ``direct-tcpip`` channel of the one before --
        # ``ssh -J``'s chain, its questions asked as the server's are.  The
        # first may have a ``ProxyCommand`` of its own; a jump host's own
        # ``ProxyJump`` is not followed.
        hops = [credentials.host_config(jump) for jump in config.jumps]
        first = hops[0] if hops else config
        sock = paramiko.ProxyCommand(first.proxy_command) if first.proxy_command else None
        chain: list[Any] = []
        try:
            for number, (jump, hop_config) in enumerate(zip(config.jumps, hops)):
                hop = (hop_config.hostname, hop_config.port)
                client = self._login(jump, hop_config, answers.for_hop(hop), sock, hop)
                chain.append(client)
                following = hops[number + 1] if number + 1 < len(hops) else config
                sock = self._forward(client, hop_config.hostname, following.hostname, following.port)
            client = self._login(site, config, answers, sock, None)
        except BaseException:
            for each in reversed(chain):
                each.close()
            raise
        transport = client.get_transport()
        if SETTINGS.remote.keepalive > 0:
            for each in (*chain, client):
                each.get_transport().set_keepalive(SETTINGS.remote.keepalive)
        self.client, self.transport, self.chain = client, transport, chain
        self._pool = queue.LifoQueue()
        self._made = 0
        threading.Thread(target=self._watch, args=(transport,), daemon=True,
                         name=f"nav-sftp-watch-{config.hostname}").start()

    def _login(self, site: Site, config: Any, answers: Answers, sock: Any, hop: Any) -> Any:
        """An SSH client logged into *config*'s host -- the server, or the
        jump host *hop* on the way to it -- over *sock*, or raising what the
        user must answer."""
        import paramiko

        from navigator.lib.drives import credentials
        from navigator.settings import SETTINGS

        if answers.password is None and not answers.tried_keyring:
            answers.tried_keyring = True
            answers.password = credentials.saved_password(site)
        client = paramiko.SSHClient()
        try:
            client.load_system_host_keys()
        except (OSError, paramiko.SSHException):
            pass
        client.set_missing_host_key_policy(_AskPolicy(config.hostname, config.port, answers, hop))
        timeout = max(1, SETTINGS.remote.timeout)
        try:
            client.connect(
                config.hostname, config.port, username=config.user, password=answers.password,
                key_filename=config.identity_files or None, passphrase=answers.passphrase,
                allow_agent=True, look_for_keys=True, sock=sock,
                timeout=timeout, banner_timeout=timeout, auth_timeout=timeout,
                transport_factory=self._transport_factory(),
            )
        except UnknownHostKey:
            client.close()
            raise
        except paramiko.BadHostKeyException as error:
            client.close()
            raise HostKeyChanged(errno.EACCES, f"The host key for {config.hostname} has changed: "
                                 "it may be an impostor, or the server was reinstalled. "
                                 "Remove the old key from known_hosts to connect.") from error
        except paramiko.PasswordRequiredException as error:
            client.close()
            raise NeedPassphrase(str(error) or "private key", wrong=answers.passphrase is not None,
                                 hop=hop) from error
        except paramiko.AuthenticationException as error:
            if not self._interactively(client, config.user, error):
                client.close()
                raise NeedPassword(site, config.user, config.hostname, wrong=answers.password is not None,
                                   hop=hop) from error
        except paramiko.SSHException as error:
            if answers.password is None and "authentication methods" in str(error):
                # No key, no agent and no password to try: the server's own
                # questions where it asks them, else a password.
                if not self._interactively(client, config.user, error):
                    client.close()
                    raise NeedPassword(site, config.user, config.hostname, hop=hop) from error
            else:
                client.close()
                raise DriveGone(config.hostname, f"Cannot connect to {config.hostname}: {error}") from error
        except (OSError, EOFError) as error:
            client.close()
            reason = getattr(error, "strerror", None) or str(error) or type(error).__name__
            raise DriveGone(config.hostname, f"Cannot connect to {config.hostname}: {reason}") from error
        if answers.save_password and answers.password and hop is not None:
            # A jump host's password is kept once it worked; the server's is
            # kept by :func:`connect`, once the drive answers.
            credentials.save_password(site, answers.password)
        return client

    @staticmethod
    def _forward(client: Any, via: str, hostname: str, port: int) -> Any:
        """A channel from the jump host *client* is logged into on to
        *hostname*:*port*: the socket the next connection is made over."""
        import paramiko

        from navigator.settings import SETTINGS

        try:
            return client.get_transport().open_channel(
                "direct-tcpip", (hostname, port), ("127.0.0.1", 0), timeout=max(1, SETTINGS.remote.timeout))
        except (paramiko.SSHException, OSError, EOFError) as error:
            client.close()
            reason = getattr(error, "strerror", None) or str(error) or type(error).__name__
            raise DriveGone(hostname, f"Cannot reach {hostname} through {via}: {reason}") from error

    def _watch(self, transport: Any) -> None:
        """Wait for *transport* to end -- paramiko's is a thread -- and then
        make the connection again at once, or say it is lost: a panel on a
        server that went away goes home without waiting to be read."""
        transport.join()
        if self._closing:
            return
        with self._lock:
            if self.transport is not transport or self._closing:
                return  # made again already, by a take()
            self.close(meant=False)
            try:
                self.open()
                return
            except Exception:
                pass
        lost = self.on_lost
        if lost is not None:
            lost()

    def _transport_factory(self) -> Any:
        """paramiko's ``Transport``, less one thing: the second factor it asks
        for after a key (``auth_interactive_dumb``) is asked through
        ``Answers.interactive`` -- a box -- not on the terminal's stdin, which
        is Navigator's screen."""
        import paramiko

        connection = self

        class _Transport(paramiko.Transport):
            def auth_interactive_dumb(self, username: str, handler: Any = None, submethods: str = "") -> Any:
                ask = connection.answers.interactive
                if ask is None:
                    raise paramiko.AuthenticationException("keyboard-interactive needs someone to answer")
                return self.auth_interactive(username, _handler(ask), submethods)

        return lambda sock, **kwargs: _Transport(sock, **kwargs)

    def _interactively(self, client: Any, user: str, error: Exception) -> bool:
        """SSH's keyboard-interactive, where the server allows it and something
        is there to answer its prompts (``Answers.interactive``): its questions
        -- a password, a one-time code -- put to the user as they come.  True
        once logged in; a refusal to answer is :class:`DriveGone`."""
        import paramiko

        allowed = getattr(error, "allowed_types", None)
        if allowed is not None and "keyboard-interactive" not in allowed:
            return False
        ask = self.answers.interactive
        transport = client.get_transport()
        if ask is None or transport is None or not transport.is_active():
            return False

        try:
            transport.auth_interactive(user, _handler(ask))
        except _Refused:
            client.close()
            raise DriveGone(self.hostname, "Cancelled") from error
        except (paramiko.AuthenticationException, paramiko.SSHException):
            return False
        return transport.is_authenticated()

    @property
    def alive(self) -> bool:
        return self.transport is not None and self.transport.is_active()

    def close(self, *, meant: bool = True) -> None:
        if meant:
            self._closing = True
        client, self.client, self.transport = self.client, None, None
        chain, self.chain = self.chain, []
        for each in (client, *reversed(chain)):
            if each is not None:
                try:
                    each.close()
                except Exception:
                    pass

    # -- channels ----------------------------------------------------------------------------------

    def take(self) -> Any:
        """A channel this thread alone may use until :meth:`give` back."""
        import paramiko

        with self._lock:
            if self._closing:
                raise DriveGone(self.hostname)
            if not self.alive:
                # Dropped -- the network, a server's timeout: once more,
                # with what worked before.
                self.close(meant=False)
                try:
                    self.open()
                except Exception as error:
                    raise DriveGone(self.hostname) from error
            try:
                return self._pool.get_nowait()
            except queue.Empty:
                pass
            if self._made < CHANNELS:
                try:
                    channel = paramiko.SFTPClient.from_transport(self.transport)
                except (paramiko.SSHException, OSError, EOFError) as error:
                    raise DriveGone(self.hostname) from error
                if channel is None:
                    raise DriveGone(self.hostname)
                self._made += 1
                return channel
        return self._pool.get()

    def give(self, channel: Any, *, broken: bool = False) -> None:
        """*channel* back in the pool -- unless it is broken, or of a
        connection since made again, which it would never work on."""
        try:
            current = channel.get_channel().get_transport() is self.transport
        except Exception:
            current = False
        if broken or not current:
            with self._lock:
                if current:
                    self._made -= 1
            try:
                channel.close()
            except Exception:
                pass
            return
        self._pool.put(channel)


class _Refused(Exception):
    """The user would not answer a server's question."""


def _handler(ask: Any) -> Any:
    """paramiko's keyboard-interactive handler, over ``Answers.interactive``."""
    def handler(title: str, instructions: str, prompts: list[tuple[str, bool]]) -> list[str]:
        if not prompts:
            return []
        replies = ask(title, instructions, list(prompts))
        if replies is None:
            raise _Refused()
        return list(replies)
    return handler


class _AskPolicy:
    """paramiko's question about a host key it does not know, put to the user."""

    def __init__(self, hostname: str, port: int, answers: Answers, hop: Any) -> None:
        self.hostname, self.port, self.answers, self.hop = hostname, port, answers, hop

    def missing_host_key(self, client: Any, hostname: str, key: Any) -> None:
        from navigator.lib.drives import credentials

        choice = self.answers.host_key
        if choice is None:
            raise UnknownHostKey(self.hostname, self.port, key.get_name(),
                                 credentials.fingerprint(key), key, hop=self.hop)
        client.get_host_keys().add(hostname, key.get_name(), key)
        if choice == "save":
            try:
                credentials.save_host_key(self.hostname, self.port, key)
            except OSError:
                pass


class _HeldFile:
    """A file on the server, holding its channel until it is closed."""

    def __init__(self, drive: SftpDrive, channel: Any, file: Any) -> None:
        self._drive, self._channel, self._file = drive, channel, file

    def read(self, size: int = -1) -> bytes:
        with self._drive._failing():
            return self._file.read(size)

    def seek(self, offset: int) -> None:
        with self._drive._failing():
            self._file.seek(offset)

    def write(self, data: bytes) -> int:
        with self._drive._failing():
            self._file.write(data)
        return len(data)

    def flush(self) -> None:
        with self._drive._failing():
            self._file.flush()

    def close(self) -> None:
        file, self._file = self._file, None
        if file is None:
            return
        broken = False
        try:
            with self._drive._failing():
                file.close()
        except OSError:
            broken = not self._drive.connection.alive
            raise
        finally:
            self._drive.connection.give(self._channel, broken=broken)

    def __enter__(self) -> _HeldFile:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class SftpDrive(Drive):
    """A server's files, over one SSH connection."""

    seekable = True

    capabilities = frozenset((WRITE, RENAME, SYMLINK, CHMOD, CHOWN))
    #: No server says when a directory changed: *Auto refresh* looks again.
    polled = True

    def __init__(self, site: Site, connection: _Connection) -> None:
        self.site = site
        self.connection = connection
        #: Called when the connection is gone for good:
        #: :class:`~navigator.lib.drives.sessions.SessionManager` sets it.
        self.on_lost: Any = None
        self.home = PurePosixPath("/")
        connection.on_lost = self._lost

    # -- channels ----------------------------------------------------------------------------------

    @contextlib.contextmanager
    def _failing(self) -> Iterator[None]:
        """paramiko's failures as :class:`OSError` -- a dead connection's as
        :class:`DriveGone`, after telling whoever closes it."""
        import paramiko

        try:
            yield
        except (EOFError, socket.error, paramiko.SSHException) as error:
            if isinstance(error, OSError) and error.errno is not None and self.connection.alive:
                raise
            if not self.connection.alive:
                self._lost()
                raise DriveGone(self.connection.hostname) from error
            raise OSError(errno.EIO, str(error) or type(error).__name__) from error

    def _lost(self) -> None:
        """Tell whoever closes the drive that it is gone -- on a thread of its
        own, so a listener closing it does not wait on this one's channel."""
        lost = self.on_lost
        if lost is not None:
            threading.Thread(target=lost, daemon=True).start()

    def _take(self) -> Any:
        """A channel; :class:`DriveGone`, and the drive closed, when the
        connection is gone and will not come back."""
        try:
            return self.connection.take()
        except DriveGone:
            self._lost()
            raise

    @contextlib.contextmanager
    def _channel(self) -> Iterator[Any]:
        connection = self.connection
        channel = self._take()
        broken = False
        try:
            with self._failing():
                yield channel
        except DriveGone:
            broken = True
            raise
        finally:
            connection.give(channel, broken=broken)

    @staticmethod
    def _path(location: Location) -> str:
        return str(location.path)

    # -- names -------------------------------------------------------------------------------------

    def get_dir(self, location: Location) -> str:
        """``SFTP:host:/path``: the protocol's sign first, as DN's link drive
        said ``LINK:`` and the drive, so a panel never hides what it is reading over."""
        from navigator.lib.drives.sessions import protocol_sign

        return f"{protocol_sign(self.site.scheme)}:{self.site.host}:{location.path}"

    # -- reading -----------------------------------------------------------------------------------

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.appearance import filetypes
        from navigator.lib.drives.listing import DirEntry, order_entries

        mask = options.get("mask", filetypes.ALL_FILES)
        filtered = mask.strip() not in ("", filetypes.ALL_FILES)
        entries: list[DirEntry] = []
        error: str | None = None
        path = self._path(location)
        with self._channel() as sftp:
            if not location.is_root:
                try:
                    up = sftp.stat(str(location.path.parent))
                    entries.append(DirEntry("..", True, 0, up.st_mode or stat.S_IFDIR, float(up.st_mtime or 0)))
                except OSError:
                    entries.append(DirEntry("..", True, 0, stat.S_IFDIR | 0o755))
            try:
                listed = sftp.listdir_attr(path)
            except OSError as failure:
                error = failure.strerror or str(failure)
                listed = []
            for attributes in listed:
                name = attributes.filename
                if not show_hidden and name.startswith("."):
                    continue
                mode = attributes.st_mode or 0
                is_link = stat.S_ISLNK(mode)
                target_text = None
                facts = attributes
                if is_link:
                    child = f"{path.rstrip('/')}/{name}"
                    try:
                        target_text = sftp.readlink(child)
                    except OSError:
                        pass
                    try:
                        facts = sftp.stat(child)
                    except OSError:
                        facts = attributes  # pointing nowhere: the link's own
                mode = facts.st_mode or 0
                is_dir = stat.S_ISDIR(mode)
                if filtered and not is_dir and not filetypes.in_filter(name, mask):
                    continue
                entry = DirEntry(name, is_dir, 0 if is_dir else facts.st_size or 0, mode,
                                 float(facts.st_mtime or 0), is_link, target_text,
                                 attributes.st_uid, attributes.st_gid)
                entry.owner = _owner_of(attributes)
                entries.append(entry)
        order = {key: options[key] for key in ("executables_first", "archives_first", "reverse")
                 if key in options}
        return order_entries(entries, sort, **order), error, None

    def stat(self, location: Location) -> FileStat:
        with self._channel() as sftp:
            return _stat_of(sftp.stat(self._path(location)))

    def lstat(self, location: Location) -> FileStat:
        with self._channel() as sftp:
            return _stat_of(sftp.lstat(self._path(location)))

    def children(self, location: Location) -> list[Child]:
        with self._channel() as sftp:
            return [(item.filename, _stat_of(item)) for item in sftp.listdir_attr(self._path(location))]

    def names(self, location: Location) -> list[str]:
        with self._channel() as sftp:
            return sftp.listdir(self._path(location))

    def readlink(self, location: Location) -> str:
        with self._channel() as sftp:
            target = sftp.readlink(self._path(location))
        if target is None:
            raise OSError(errno.EINVAL, os.strerror(errno.EINVAL), str(location))
        return target

    def realpath(self, location: Location) -> Location:
        with self._channel() as sftp:
            try:
                resolved = sftp.normalize(self._path(location))
            except FileNotFoundError:
                return location.normalized()
        return Location(self.site, PurePosixPath(resolved), location.outer)

    def open_random(self, location: Location) -> Any:
        """A file held open on a channel of its own, read where asked -- no
        ``prefetch``, which would fetch the whole of it."""
        from navigator.lib.drives.base import SeekingReader

        return SeekingReader(self.open_read(location, whole=False))

    def open_read(self, location: Location, *, whole: bool = True) -> IO[bytes]:
        connection = self.connection
        channel = self._take()
        try:
            with self._failing():
                file = channel.open(self._path(location), "rb")
                if whole:
                    file.prefetch()
        except BaseException:
            connection.give(channel, broken=not connection.alive)
            raise
        return _HeldFile(self, channel, file)  # type: ignore[return-value]

    # -- writing -----------------------------------------------------------------------------------

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        connection = self.connection
        channel = self._take()
        path = self._path(location)
        try:
            with self._failing():
                try:
                    channel.lstat(path)
                    new = False
                except FileNotFoundError:
                    new = True
                file = channel.open(path, "ab" if append else "wb")
                file.set_pipelined(True)
                if new:
                    try:
                        channel.chmod(path, mode & 0o7777 & ~_UMASK)
                    except OSError:
                        pass
        except BaseException:
            connection.give(channel, broken=not connection.alive)
            raise
        return _HeldFile(self, channel, file)  # type: ignore[return-value]

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        with self._channel() as sftp:
            try:
                sftp.mkdir(self._path(location), mode & 0o7777 & ~_UMASK)
            except OSError as error:
                # SFTP version 3 says only *Failure* for a name taken: ask.
                try:
                    sftp.lstat(self._path(location))
                except OSError:
                    raise error from None
                raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(location)) from None

    def rmdir(self, location: Location) -> None:
        with self._channel() as sftp:
            sftp.rmdir(self._path(location))

    def unlink(self, location: Location) -> None:
        with self._channel() as sftp:
            sftp.remove(self._path(location))

    def rename(self, source: Location, dest: Location) -> None:
        with self._channel() as sftp:
            sftp.rename(self._path(source), self._path(dest))

    def replace(self, source: Location, dest: Location) -> None:
        """``posix-rename@openssh.com`` where the server has it -- one step,
        the old file there until the new one is -- else remove and rename."""
        with self._channel() as sftp:
            try:
                sftp.posix_rename(self._path(source), self._path(dest))
                return
            except IOError as error:
                if getattr(error, "errno", None) not in (None, errno.EIO, errno.ENOTSUP, errno.EOPNOTSUPP):
                    raise
            try:
                sftp.remove(self._path(dest))
            except FileNotFoundError:
                pass
            sftp.rename(self._path(source), self._path(dest))

    def symlink(self, target: str, location: Location) -> None:
        with self._channel() as sftp:
            sftp.symlink(target, self._path(location))

    def chmod(self, location: Location, mode: int) -> None:
        with self._channel() as sftp:
            sftp.chmod(self._path(location), mode & 0o7777)

    def chown(self, location: Location, uid: int, gid: int, *, follow: bool = True) -> None:
        if not follow:
            raise OSError(errno.ENOTSUP, os.strerror(errno.ENOTSUP), str(location))
        with self._channel() as sftp:
            sftp.chown(self._path(location), uid, gid)

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        if not follow and self.is_link(location):
            # SFTP sets a link's target's times, never the link's own.
            raise OSError(errno.ENOTSUP, os.strerror(errno.ENOTSUP), str(location))
        with self._channel() as sftp:
            sftp.utime(self._path(location), (atime_ns / 1e9, mtime_ns / 1e9))

    # -- the rest ----------------------------------------------------------------------------------

    def describe(self) -> list[tuple[str, str]]:
        """What the info panel says of the connection: who, where, how."""
        transport = self.connection.transport
        lines = [("Server", f"{self.connection.user}@{self.connection.hostname}:{self.connection.port}")]
        if transport is not None:
            key = transport.get_remote_server_key()
            from navigator.lib.drives.credentials import fingerprint

            lines.append(("Host key", f"{key.get_name()} {fingerprint(key)}"))
            lines.append(("Software", transport.remote_version or ""))
            cipher = getattr(transport, "remote_cipher", "") or ""
            if cipher:
                lines.append(("Cipher", cipher))
        return lines

    def close(self) -> None:
        self.connection.close()


def connect(site: Site, answers: Answers) -> SftpDrive:
    """*site* connected: blocks, and raises what the user must answer."""
    connection = _Connection(site, answers)
    drive = SftpDrive(site, connection)
    try:
        with drive._channel() as sftp:
            drive.home = PurePosixPath(sftp.normalize("."))
    except OSError:
        pass
    if answers.save_password and answers.password:
        from navigator.lib.drives.credentials import save_password

        save_password(site, answers.password)
    return drive


__all__ = ["CHANNELS", "EXTRA", "SftpDrive", "available", "connect"]
