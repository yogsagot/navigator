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
"""

from __future__ import annotations

import json
import os
import shutil
import struct
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import IO, Any

#: Written on stdout, alone on its line, once the helper is listening.
READY = b"NAVROOT1\n"

#: The stat fields beyond the ten a tuple of one holds.
STAT_EXTRA = ("st_atime", "st_mtime", "st_ctime", "st_atime_ns", "st_mtime_ns", "st_ctime_ns",
              "st_blksize", "st_blocks", "st_rdev")


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
    def __init__(self) -> None:
        from navigator.lib.drives.local import LOCAL

        self.drive = LOCAL
        #: Open files, by the number the client knows them by.
        self.files: dict[int, IO[bytes]] = {}
        self.next = 1
        #: ``write_file``'s text, gathered before it is written.
        self.pending: dict[int, tuple[IO[bytes], str]] = {}

    @staticmethod
    def _where(path: str) -> Any:
        from navigator.lib.drives.location import Location

        return Location.of(Path(path))

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

    def realpath(self, path: str) -> str:
        return str(Path(path).resolve())

    def writable(self, path: str) -> bool:
        return os.access(path, os.W_OK)

    def mkdir(self, path: str, mode: int) -> None:
        os.mkdir(path, mode)

    def makedirs(self, path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def rmdir(self, path: str) -> None:
        os.rmdir(path)

    def unlink(self, path: str) -> None:
        os.unlink(path)

    def rename(self, source: str, dest: str) -> None:
        os.rename(source, dest)

    def replace(self, source: str, dest: str) -> None:
        os.replace(source, dest)

    def symlink(self, target: str, path: str) -> None:
        os.symlink(target, path)

    def chmod(self, path: str, mode: int) -> None:
        os.chmod(path, mode)

    def chown(self, path: str, uid: int, gid: int, follow: bool) -> None:
        os.chown(path, uid, gid, follow_symlinks=follow)

    def utime(self, path: str, atime_ns: int, mtime_ns: int, follow: bool) -> None:
        os.utime(path, ns=(atime_ns, mtime_ns), follow_symlinks=follow)

    def copystat(self, source: str, dest: str, follow: bool) -> None:
        try:
            shutil.copystat(source, dest, follow_symlinks=follow)
        except OSError:
            pass

    def open_read(self, path: str) -> int:
        return self._keep(open(path, "rb"))

    def open_write(self, path: str, append: bool, mode: int) -> int:
        return self._keep(self.drive.open_write(self._where(path), append=append, mode=mode))

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

    def write_text(self, handle: int, backup: bool) -> None:
        """``write_file``'s second half: the text gathered put in its file, as
        the editor writes one -- in a single rename, owner and mode kept."""
        from navigator.lib.editor.save import write_file

        file, path = self.pending.pop(handle)
        self.files.pop(handle, None)
        try:
            file.seek(0)
            # Locks were asked about by the Navigator asking: the lock it
            # holds itself would refuse this process.
            write_file(Path(path), iter(lambda: file.read(1 << 20), b""), None, backup, check_lock=False)
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
