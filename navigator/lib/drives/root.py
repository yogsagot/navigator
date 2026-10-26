"""The disk as root: :class:`LocalDrive`'s steps done by the root helper.

What a worker turns to once the user has answered *As root* to a refusal
(:mod:`navigator.lib.system.elevate`).  Each method is
:class:`~navigator.lib.drives.local.LocalDrive`'s own, run in the helper
(:mod:`navigator.lib.system.roothelper`) instead of here, so a copy or an erase
reads the same with either drive.  Blocking, like every drive: on a thread.
"""

from __future__ import annotations

import io
import os
from collections.abc import Iterable
from pathlib import Path
from typing import IO, Any

from navigator.lib.drives.base import Child, Drive
from navigator.lib.drives.local import LocalDrive
from navigator.lib.drives.location import Location
from navigator.lib.system.elevate import ELEVATION
from navigator.lib.system.roothelper import unpack_stat

#: How much one request reads or writes.
CHUNK = 1 << 20


def _path(location: Location | Path) -> str:
    return str(location.local if isinstance(location, Location) else location)


class _RootFile(io.RawIOBase):
    """A file the helper has open, read or written a request at a time."""

    def __init__(self, handle: int, *, writing: bool) -> None:
        self.handle = handle
        self._writing = writing

    def readable(self) -> bool:
        return not self._writing

    def writable(self) -> bool:
        return self._writing

    def readinto(self, buffer: Any) -> int:
        _, data = ELEVATION.call_data("read", handle=self.handle, count=min(len(buffer), CHUNK))
        buffer[:len(data)] = data
        return len(data)

    def write(self, data: Any) -> int:
        data = bytes(data)
        for start in range(0, len(data), CHUNK):
            ELEVATION.call("write", data[start:start + CHUNK], handle=self.handle)
        return len(data)

    def sync(self) -> None:
        ELEVATION.call("sync", handle=self.handle)

    def close(self) -> None:
        if not self.closed:
            try:
                ELEVATION.call("close", handle=self.handle)
            finally:
                super().close()


class _RootRandom:
    """F3's handle on a file read as root (``Drive.open_random``): it holds
    the helper open (:meth:`~navigator.lib.system.elevate.Elevation.hold`)
    until closed, and lets it go then as an operation's end would."""

    def __init__(self, handle: int) -> None:
        self.handle = handle
        ELEVATION.hold()
        self._open = True

    def read_at(self, offset: int, count: int) -> bytes:
        _, data = ELEVATION.call_data("read_at", handle=self.handle, offset=offset, count=count)
        return data

    def close(self) -> None:
        if not self._open:
            return
        self._open = False
        try:
            ELEVATION.call("close", handle=self.handle)
        except OSError:
            pass  # the helper is gone already, and the file with it
        finally:
            ELEVATION.unhold()
            ELEVATION.release()


class RootDrive(LocalDrive):
    """The disk, every step taken as root."""

    def stat(self, location: Location) -> os.stat_result:
        return unpack_stat(ELEVATION.call("stat", path=_path(location)))

    def lstat(self, location: Location) -> os.stat_result:
        return unpack_stat(ELEVATION.call("lstat", path=_path(location)))

    def lexists(self, location: Location) -> bool:
        return ELEVATION.call("lexists", path=_path(location))

    def exists(self, location: Location) -> bool:
        return ELEVATION.call("exists", path=_path(location))

    def is_dir(self, location: Location) -> bool:
        return ELEVATION.call("is_dir", path=_path(location))

    def is_link(self, location: Location) -> bool:
        return ELEVATION.call("is_link", path=_path(location))

    def children(self, location: Location) -> list[Child]:
        found: list[Child] = []
        for name, value in ELEVATION.call("children", path=_path(location)):
            found.append((name, OSError(value["errno"], value["strerror"]) if isinstance(value, dict)
                          else unpack_stat(value)))
        return found

    def names(self, location: Location) -> list[str]:
        return ELEVATION.call("names", path=_path(location))

    def readlink(self, location: Location) -> str:
        return ELEVATION.call("readlink", path=_path(location))

    def realpath(self, location: Location) -> Location:
        return Location.of(Path(ELEVATION.call("realpath", path=_path(location))))

    def writable(self, location: Location, st: Any) -> bool:
        return ELEVATION.call("writable", path=_path(location))

    def open_read(self, location: Location) -> IO[bytes]:
        handle = ELEVATION.call("open_read", path=_path(location))
        return io.BufferedReader(_RootFile(handle, writing=False), CHUNK)  # type: ignore[return-value]

    def open_random(self, location: Location) -> _RootRandom:
        return _RootRandom(ELEVATION.call("open_read", path=_path(location)))

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        handle = ELEVATION.call("open_write", path=_path(location), append=append, mode=mode)
        return io.BufferedWriter(_RootFile(handle, writing=True), CHUNK)  # type: ignore[return-value]

    def sync(self, handle: IO[bytes]) -> None:
        handle.flush()
        raw = getattr(handle, "raw", handle)
        if isinstance(raw, _RootFile):
            raw.sync()
        else:
            super().sync(handle)

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        ELEVATION.call("mkdir", path=_path(location), mode=mode)

    def makedirs(self, location: Location) -> None:
        ELEVATION.call("makedirs", path=_path(location))

    def rmdir(self, location: Location) -> None:
        ELEVATION.call("rmdir", path=_path(location))

    def unlink(self, location: Location) -> None:
        ELEVATION.call("unlink", path=_path(location))

    def rename(self, source: Location, dest: Location) -> None:
        ELEVATION.call("rename", source=_path(source), dest=_path(dest))

    def replace(self, source: Location, dest: Location) -> None:
        ELEVATION.call("replace", source=_path(source), dest=_path(dest))

    def symlink(self, target: str, location: Location) -> None:
        ELEVATION.call("symlink", target=target, path=_path(location))

    def chmod(self, location: Location, mode: int) -> None:
        ELEVATION.call("chmod", path=_path(location), mode=mode)

    def chown(self, location: Location, uid: int, gid: int, *, follow: bool = True) -> None:
        ELEVATION.call("chown", path=_path(location), uid=uid, gid=gid, follow=follow)

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        ELEVATION.call("utime", path=_path(location), atime_ns=atime_ns, mtime_ns=mtime_ns, follow=follow)

    def copy_attributes(self, source_drive: Drive, source: Location, dest: Location, st: Any, *,
                        follow: bool) -> None:
        if not isinstance(source_drive, LocalDrive):
            Drive.copy_attributes(self, source_drive, source, dest, st, follow=follow)
            return
        ELEVATION.call("copystat", source=_path(source), dest=_path(dest), follow=follow)

    def write_file(self, path: Path, chunks: Iterable[bytes], job: Any = None, backup: bool = False) -> None:
        """The editor's :func:`~navigator.lib.editor.save.write_file`, as root.

        The text is sent first and written once it is all there, so the
        write itself is the editor's, in one rename; not stoppable part way.
        """
        from navigator.lib.editor.lock import refuse_if_locked
        from navigator.lib.editor.save import resolve

        # Here, where this Navigator's own locks are known.
        refuse_if_locked(resolve(path))
        if job is not None:
            job.cancellable = False
        handle = ELEVATION.call("begin_text", path=str(path))
        try:
            for chunk in chunks:
                for start in range(0, len(chunk), CHUNK):
                    ELEVATION.call("write", bytes(chunk[start:start + CHUNK]), handle=handle)
        except BaseException:
            ELEVATION.call("close", handle=handle)
            raise
        ELEVATION.call("write_text", handle=handle, backup=backup)


    @staticmethod
    def release() -> None:
        """A use of it over: :meth:`~navigator.lib.system.elevate.Elevation.release`."""
        ELEVATION.release()


#: The disk as root.
ROOT_DRIVE = RootDrive()


__all__ = ["ROOT_DRIVE", "RootDrive"]
