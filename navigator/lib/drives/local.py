"""The local disk as a drive: DN's ``TDrive`` itself, ``dtDisk``.

Each method is the very call the code it stands in for made before drives
existed -- ``os.lstat``, ``os.scandir``, ``os.replace`` -- on the
:class:`~pathlib.Path` the location holds, so a panel or a copy on the disk
does what it always did.  :data:`LOCAL` is the one instance.
"""

from __future__ import annotations

import errno
import os
import shutil
from collections.abc import Callable
from typing import IO, Any

from navigator.lib.drives.base import EVERYTHING, Child, Drive
from navigator.lib.drives.location import LOCAL_SITE, Location


class LocalDrive(Drive):
    site = LOCAL_SITE
    capabilities = EVERYTHING

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        # Here, not at the top: the listing's entries name owners through
        # ``fileattr``, which is a file operation, which reads drives.
        from navigator.lib.drives import listing

        return listing.read_listing(location.local, show_hidden, sort, free=free, **options)

    def stat(self, location: Location) -> os.stat_result:
        return os.stat(location.local)

    def lstat(self, location: Location) -> os.stat_result:
        return os.lstat(location.local)

    def lexists(self, location: Location) -> bool:
        return os.path.lexists(location.local)

    def exists(self, location: Location) -> bool:
        return location.local.exists()

    def is_dir(self, location: Location) -> bool:
        return location.local.is_dir()

    def is_link(self, location: Location) -> bool:
        return location.local.is_symlink()

    def children(self, location: Location) -> list[Child]:
        found: list[Child] = []
        with os.scandir(location.local) as entries:
            for entry in entries:
                try:
                    found.append((entry.name, entry.stat(follow_symlinks=False)))
                except OSError as error:
                    found.append((entry.name, error))
        return found

    def names(self, location: Location) -> list[str]:
        with os.scandir(location.local) as entries:
            return [entry.name for entry in entries]

    def readlink(self, location: Location) -> str:
        return os.readlink(location.local)

    def realpath(self, location: Location) -> Location:
        return Location.of(location.local.resolve())

    def same_file(self, a: Location, b: Location) -> bool:
        if not (a.is_local and b.is_local):
            return False
        try:
            return os.path.samefile(a.local, b.local)
        except OSError:
            return False

    def writable(self, location: Location, st: Any) -> bool:
        return os.access(location.local, os.W_OK)

    def free_bytes(self, location: Location) -> int | None:
        try:
            fs = os.statvfs(location.local)
        except OSError:
            return None
        return fs.f_bavail * fs.f_frsize

    def open_read(self, location: Location) -> IO[bytes]:
        return open(location.local, "rb")

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if append else os.O_TRUNC)
        return os.fdopen(os.open(location.local, flags, mode), "wb")

    def sync(self, handle: IO[bytes]) -> None:
        """``fsync``; a write-back error raises, as a failed write would.

        A file system that cannot sync at all (``EINVAL``, ``ENOTSUP``) has
        nothing to flush, which is not a failure of the copy.
        """
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError as error:
            if error.errno not in (errno.EINVAL, errno.ENOTSUP):
                raise

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        os.mkdir(location.local, mode)

    def makedirs(self, location: Location) -> None:
        location.local.mkdir(parents=True, exist_ok=True)

    def rmdir(self, location: Location) -> None:
        os.rmdir(location.local)

    def unlink(self, location: Location) -> None:
        os.unlink(location.local)

    def rename(self, source: Location, dest: Location) -> None:
        os.rename(source.local, dest.local)

    def replace(self, source: Location, dest: Location) -> None:
        os.replace(source.local, dest.local)

    def symlink(self, target: str, location: Location) -> None:
        os.symlink(target, location.local)

    def chmod(self, location: Location, mode: int) -> None:
        os.chmod(location.local, mode)

    def chown(self, location: Location, uid: int, gid: int, *, follow: bool = True) -> None:
        if follow:
            os.chown(location.local, uid, gid)
        else:
            os.lchown(location.local, uid, gid)

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        os.utime(location.local, ns=(atime_ns, mtime_ns), follow_symlinks=follow)

    def copy_attributes(self, source_drive: Drive, source: Location, dest: Location, st: Any, *,
                        follow: bool) -> None:
        if not isinstance(source_drive, LocalDrive):
            super().copy_attributes(source_drive, source, dest, st, follow=follow)
            return
        try:
            shutil.copystat(source.local, dest.local, follow_symlinks=follow)
        except OSError:
            pass

    def watch(self, location: Location, notify: Callable[[], None]) -> Any:
        from navigator.lib.system import dirwatch

        return dirwatch.watch(location.local.absolute(), notify)


#: The disk.
LOCAL = LocalDrive()


__all__ = ["LOCAL", "LocalDrive"]
