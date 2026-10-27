"""The process that does a refused step as root: run under ``sudo``/``pkexec``.

Not DN's -- DOS had no one to be refused by.  :mod:`navigator.lib.system.elevate`
starts it and is the only thing that talks to it, over its stdin and stdout:
each message is a 4-byte big-endian length and that much JSON, followed by
``size`` raw bytes when the JSON says so.  A request names one *op* from
:data:`OPS`, a closed list of the disk's own steps
(:class:`~navigator.lib.drives.local.LocalDrive`'s methods, so the work is the
very code an unrefused step runs); the answer is ``{"ok": value}`` or
``{"errno", "strerror", "filename"}`` for an ``OSError``.  It says
:data:`READY` once, and ends at the end of its input.

**A step that changes the disk follows no symbolic link another user owns**
(:meth:`_Helper._pinned`): only root's and the asking user's.  The kernel's
``fs.protected_symlinks`` says as much for sticky world-writable directories
(``/tmp``); here it holds everywhere, so a user who may write where root is
working -- a shared directory, their own home being erased -- cannot swap a
directory for a link between two steps and send root's next write, chmod or
unlink somewhere else.  Every directory on the way is held open (``O_PATH``)
and the step is done through ``/proc/self/fd``, so what was checked is what
is changed.  Reads are left alone: the user has root already.
"""

from __future__ import annotations

import errno
import json
import os
import shutil
import stat
import struct
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any

#: Written on stdout, alone on its line, once the helper is listening.
READY = b"NAVROOT1\n"

#: The stat fields beyond the ten a tuple of one holds.
STAT_EXTRA = ("st_atime", "st_mtime", "st_ctime", "st_atime_ns", "st_mtime_ns", "st_ctime_ns",
              "st_blksize", "st_blocks", "st_rdev")


#: Whether steps can be pinned to the directories they were checked in:
#: Linux's ``O_PATH`` and ``/proc/self/fd``.  Elsewhere they go by name.
PINNABLE = hasattr(os, "O_PATH") and os.path.isdir("/proc/self/fd")
#: How many links one path may go through, as the kernel's ``MAXSYMLINKS``.
MAX_LINKS = 40


def asker() -> int:
    """The user who asked for root: sudo's ``SUDO_UID``, pkexec's
    ``PKEXEC_UID``, else whoever runs this (the tests' unprivileged helper)."""
    for name in ("SUDO_UID", "PKEXEC_UID"):
        value = os.environ.get(name, "")
        if value.isdigit():
            return int(value)
    return os.getuid()


def pack_stat(st: os.stat_result) -> list[Any]:
    return [list(st), {name: getattr(st, name) for name in STAT_EXTRA if hasattr(st, name)}]


def unpack_stat(value: list[Any]) -> os.stat_result:
    return os.stat_result(tuple(value[0]), value[1])


def send(stream: IO[bytes], message: dict[str, Any], payload: bytes = b"") -> None:
    if payload:
        message = {**message, "size": len(payload)}
    body = json.dumps(message).encode()
    view = memoryview(struct.pack(">I", len(body)) + body + payload)
    while view:
        written = stream.write(view)
        view = view[len(view) if written is None else written:]
    stream.flush()


def _exact(stream: IO[bytes], count: int) -> bytes:
    data = b""
    while len(data) < count:
        piece = stream.read(count - len(data))
        if not piece:
            raise EOFError
        data += piece
    return data


def receive(stream: IO[bytes]) -> tuple[dict[str, Any], bytes]:
    """One message and its payload; ``EOFError`` at the end."""
    (length,) = struct.unpack(">I", _exact(stream, 4))
    message = json.loads(_exact(stream, length))
    size = message.get("size", 0)
    return message, _exact(stream, size) if size else b""


class _Helper:
    def __init__(self, trusted: frozenset[int] | None = None) -> None:
        from navigator.lib.drives.local import LOCAL

        self.drive = LOCAL
        #: Whose symbolic links a step that changes the disk may follow.
        self.trusted = frozenset({0, asker()}) if trusted is None else trusted
        #: Open files, by the number the client knows them by.
        self.files: dict[int, IO[bytes]] = {}
        self.next = 1
        #: ``write_file``'s text, gathered before it is written.
        self.pending: dict[int, tuple[IO[bytes], str]] = {}

    @staticmethod
    def _where(path: str) -> Any:
        from navigator.lib.drives.location import Location

        return Location.of(Path(path))

    @contextmanager
    def _pinned(self, path: str, follow: bool = False) -> Iterator[str]:
        """*path* as a name to change it by, every directory on the way held
        open and reached through no link but a trusted one.  *follow* goes
        through a link at the end too, so the last name is never a link
        followed.  Raises ``ELOOP`` for another user's link."""
        if not PINNABLE:
            yield path
            return
        if not os.path.isabs(path):
            raise OSError(errno.EINVAL, "Not an absolute path", path)
        held = [os.open("/", os.O_PATH | os.O_DIRECTORY)]
        try:
            pending = [part for part in path.split("/") if part not in ("", ".")]
            links = 0
            name = "."
            while pending:
                part = pending.pop(0)
                if part == "..":
                    if len(held) > 1:
                        os.close(held.pop())
                    name = "."
                    continue
                last = not pending
                try:
                    fd = os.open(part, os.O_PATH | os.O_NOFOLLOW, dir_fd=held[-1])
                except FileNotFoundError:
                    if last:
                        name = part
                        break
                    raise
                st = os.fstat(fd)
                if stat.S_ISLNK(st.st_mode) and (follow or not last):
                    os.close(fd)
                    if st.st_uid not in self.trusted:
                        raise OSError(errno.ELOOP, "Not following a symbolic link another user owns", path)
                    links += 1
                    if links > MAX_LINKS:
                        raise OSError(errno.ELOOP, os.strerror(errno.ELOOP), path)
                    target = os.readlink(part, dir_fd=held[-1])
                    if target.startswith("/"):
                        while len(held) > 1:
                            os.close(held.pop())
                    pending[:0] = [piece for piece in target.split("/") if piece not in ("", ".")]
                    name = "."
                    continue
                if last:
                    os.close(fd)
                    name = part
                    break
                held.append(fd)
                name = "."
            yield f"/proc/self/fd/{held[-1]}/{name}"
        finally:
            for fd in held:
                os.close(fd)

    def _keep(self, handle: IO[bytes]) -> int:
        number, self.next = self.next, self.next + 1
        self.files[number] = handle
        return number

    # -- the ops -----------------------------------------------------------------

    def stat(self, path: str) -> Any:
        return pack_stat(self.drive.stat(self._where(path)))

    def lstat(self, path: str) -> Any:
        return pack_stat(self.drive.lstat(self._where(path)))

    def lexists(self, path: str) -> bool:
        return os.path.lexists(path)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def is_dir(self, path: str) -> bool:
        return os.path.isdir(path)

    def is_link(self, path: str) -> bool:
        return os.path.islink(path)

    def names(self, path: str) -> list[str]:
        return self.drive.names(self._where(path))

    def children(self, path: str) -> list[Any]:
        return [[name, pack_stat(st) if isinstance(st, os.stat_result)
                 else {"errno": st.errno, "strerror": st.strerror}]
                for name, st in self.drive.children(self._where(path))]

    def readlink(self, path: str) -> str:
        return os.readlink(path)

    def listing(self, path: str, show_hidden: bool, sort: str, free: bool, options: dict[str, Any]) -> Any:
        """A panel's read of *path*, as the disk's own (``listing.read_listing``),
        its entries packed: a panel browsing as root (``RootSiteDrive.scan``)."""
        from navigator.lib.drives.listing import read_listing

        entries, error, space = read_listing(Path(path), show_hidden, sort, free=free, **options)
        # A list, not a tuple: a tuple answered is ``(value, payload)``.
        return [[[entry.name, entry.is_dir, entry.size, entry.mode, entry.mtime, entry.is_link,
                 entry.link_target, entry.uid, entry.gid, entry.counted] for entry in entries], error, space]

    def realpath(self, path: str) -> str:
        return str(Path(path).resolve())

    def writable(self, path: str) -> bool:
        return os.access(path, os.W_OK)

    def mkdir(self, path: str, mode: int) -> None:
        with self._pinned(path) as there:
            os.mkdir(there, mode)

    def makedirs(self, path: str) -> None:
        parts = [part for part in path.split("/") if part]
        for count in range(1, len(parts) + 1):
            with self._pinned("/" + "/".join(parts[:count])) as there:
                try:
                    os.mkdir(there)
                except FileExistsError:
                    if not os.path.isdir(there):
                        raise

    def rmdir(self, path: str) -> None:
        with self._pinned(path) as there:
            os.rmdir(there)

    def unlink(self, path: str) -> None:
        with self._pinned(path) as there:
            os.unlink(there)

    def rename(self, source: str, dest: str) -> None:
        with self._pinned(source) as old, self._pinned(dest) as new:
            os.rename(old, new)

    def replace(self, source: str, dest: str) -> None:
        with self._pinned(source) as old, self._pinned(dest) as new:
            os.replace(old, new)

    def symlink(self, target: str, path: str) -> None:
        with self._pinned(path) as there:
            os.symlink(target, there)

    def chmod(self, path: str, mode: int) -> None:
        # No lchmod on Linux: the file itself held open, so a link put in
        # its place after the check is not what is changed.
        with self._pinned(path, follow=True) as there:
            if not PINNABLE:
                os.chmod(there, mode)
                return
            fd = os.open(there, os.O_PATH | os.O_NOFOLLOW)
            try:
                if stat.S_ISLNK(os.fstat(fd).st_mode):
                    raise OSError(errno.ELOOP, os.strerror(errno.ELOOP), path)
                os.chmod(f"/proc/self/fd/{fd}", mode)
            finally:
                os.close(fd)

    def chown(self, path: str, uid: int, gid: int, follow: bool) -> None:
        # Followed here, the end is never a link: changed as named.
        with self._pinned(path, follow=follow) as there:
            os.chown(there, uid, gid, follow_symlinks=not PINNABLE and follow)

    def utime(self, path: str, atime_ns: int, mtime_ns: int, follow: bool) -> None:
        with self._pinned(path, follow=follow) as there:
            os.utime(there, ns=(atime_ns, mtime_ns), follow_symlinks=not PINNABLE and follow)

    # Extended attributes (and the ACLs in them) and inode flags, Alt+E's:
    # each on the name _pinned gives, whose end is never a link followed.

    def listxattr(self, path: str, follow: bool) -> list[str]:
        with self._pinned(path, follow=follow) as there:
            return os.listxattr(there, follow_symlinks=not PINNABLE and follow)

    def getxattr(self, path: str, name: str, follow: bool) -> tuple[None, bytes]:
        with self._pinned(path, follow=follow) as there:
            return None, os.getxattr(there, name, follow_symlinks=not PINNABLE and follow)

    def setxattr(self, path: str, name: str, follow: bool, data: bytes = b"") -> None:
        with self._pinned(path, follow=follow) as there:
            os.setxattr(there, name, data, follow_symlinks=not PINNABLE and follow)

    def removexattr(self, path: str, name: str, follow: bool) -> None:
        with self._pinned(path, follow=follow) as there:
            os.removexattr(there, name, follow_symlinks=not PINNABLE and follow)

    def get_flags(self, path: str, follow: bool) -> int:
        from navigator.lib.file_ops import fsflags

        with self._pinned(path, follow=follow) as there:
            return fsflags.get_flags(there, follow=not PINNABLE and follow)

    def set_flags(self, path: str, flags: int, follow: bool) -> None:
        from navigator.lib.file_ops import fsflags

        with self._pinned(path, follow=follow) as there:
            fsflags.set_flags(there, flags, follow=not PINNABLE and follow)

    def copystat(self, source: str, dest: str, follow: bool) -> None:
        try:
            with self._pinned(dest, follow=follow) as there:
                shutil.copystat(source, there, follow_symlinks=follow)
        except OSError:
            pass

    def open_read(self, path: str) -> int:
        return self._keep(open(path, "rb"))

    def open_write(self, path: str, append: bool, mode: int) -> int:
        # LocalDrive's flags, the end not a link: a trusted one is followed
        # by _pinned, and one put there since is refused (O_NOFOLLOW).
        with self._pinned(path, follow=True) as there:
            flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if append else os.O_TRUNC)
            if PINNABLE:
                flags |= os.O_NOFOLLOW
            return self._keep(os.fdopen(os.open(there, flags, mode), "wb"))

    def read(self, handle: int, count: int) -> tuple[None, bytes]:
        return None, self.files[handle].read(count)

    def read_at(self, handle: int, offset: int, count: int) -> tuple[None, bytes]:
        """*count* bytes at *offset*, the file's position untouched: F3's chunks."""
        return None, os.pread(self.files[handle].fileno(), count, offset)

    def write(self, handle: int, data: bytes) -> int:
        return self.files[handle].write(data)

    def sync(self, handle: int) -> None:
        self.drive.sync(self.files[handle])

    def close(self, handle: int) -> None:
        file = self.files.pop(handle, None)
        self.pending.pop(handle, None)
        if file is not None:
            file.close()

    def begin_text(self, path: str) -> int:
        """``write_file``'s first half: somewhere private to gather the text in."""
        handle = tempfile.TemporaryFile()
        number = self._keep(handle)
        self.pending[number] = (handle, path)
        return number

    def write_text(self, handle: int, backup: bool, check_lock: bool = False) -> None:
        """``write_file``'s second half: the text gathered put in its file, as
        the editor writes one -- in a single rename, owner and mode kept.
        *check_lock* where the asking Navigator could not look itself."""
        from navigator.lib.editor.save import write_file

        file, path = self.pending.pop(handle)
        self.files.pop(handle, None)
        try:
            file.seek(0)
            # Locks were asked about by the Navigator asking, where it could:
            # the lock it holds itself would refuse this process.  Its links
            # resolved here, through trusted ones only, not by write_file.
            with self._pinned(path, follow=True) as there:
                write_file(Path(there), iter(lambda: file.read(1 << 20), b""), None, backup,
                           check_lock=check_lock, follow=not PINNABLE)
        finally:
            file.close()


#: What a client may ask for: the names of :class:`_Helper`'s ops.
OPS = frozenset(
    name for name, value in vars(_Helper).items()
    if not name.startswith("_") and callable(value)
)


def serve(reader: IO[bytes], writer: IO[bytes]) -> None:
    helper = _Helper()
    writer.write(READY)
    writer.flush()
    while True:
        try:
            message, payload = receive(reader)
        except EOFError:
            return
        op = message.get("op")
        args = message.get("args", {})
        if payload:
            args["data"] = payload
        method: Callable[..., Any] | None = getattr(helper, op, None) if op in OPS else None
        try:
            if method is None:
                raise OSError(22, f"unknown request {op!r}")
            value = method(**args)
        except OSError as error:
            send(writer, {"errno": error.errno, "strerror": error.strerror or str(error),
                          "filename": error.filename and str(error.filename)})
            continue
        except Exception as error:  # noqa: BLE001 - said to the client, never lost
            send(writer, {"errno": 5, "strerror": f"{type(error).__name__}: {error}", "filename": None})
            continue
        if isinstance(value, tuple):
            send(writer, {"ok": value[0]}, value[1])
        else:
            send(writer, {"ok": value})


def main() -> None:
    serve(sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    main()
