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
from pathlib import Path, PurePosixPath
from typing import IO, Any

from navigator.lib.drives.base import CHMOD, CHOWN, RENAME, SYMLINK, WRITE, Child, Drive
from navigator.lib.drives.local import LocalDrive
from navigator.lib.drives.location import LOCAL_SITE, Location, Site
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

        # Here, where this Navigator's own locks are known -- unless the user
        # may not even reach the file (a directory only root may enter): then
        # no lock of this Navigator's can be on it, and the helper asks.
        try:
            refuse_if_locked(resolve(path))
            helper_checks = False
        except PermissionError:
            helper_checks = True
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
        ELEVATION.call("write_text", handle=handle, backup=backup, check_lock=helper_checks)


    @staticmethod
    def release() -> None:
        """A use of it over: :meth:`~navigator.lib.system.elevate.Elevation.release`."""
        ELEVATION.release()


#: The disk as root.
ROOT_DRIVE = RootDrive()


# -- browsing as root ---------------------------------------------------------------

#: Where a panel is that lists and works as root: the disk's paths, on a site
#: of their own (``root:///etc/...``), so every step is a drive's -- as on a
#: server -- and nothing mistakes it for the disk itself.
ROOT_SITE = Site("root")

#: Seconds between a ``root:`` panel's looks for *Auto refresh*: the disk's
#: own watcher cannot see into what the user may not read, and this is the
#: disk, not a server -- so not ``[remote] refresh``, which is off by default.
POLL_INTERVAL = 2.0


def root_location(path: Path | str | Location) -> Location:
    """*path* on the disk, as root sees it."""
    if isinstance(path, Location):
        path = path.path
    return Location(ROOT_SITE, PurePosixPath(str(path)))


def on_disk(location: Location) -> Location:
    """A ``root:`` location's own place on the disk; any other as it is."""
    if location.site == ROOT_SITE and location.outer is None:
        return Location(LOCAL_SITE, Path(str(location.path)))
    return location


def readable_plainly(location: Location) -> bool:
    """Whether the user may list a ``root:`` directory without root, so a
    panel there goes back to the disk itself."""
    return (location.site == ROOT_SITE and location.outer is None
            and os.access(str(location.path), os.R_OK | os.X_OK))


class RootSiteDrive(Drive):
    """The disk at :data:`ROOT_SITE`: each step :data:`ROOT_DRIVE`'s, on the
    place the location names.  Mounted while a panel is there
    (:func:`hold`); programs are not run from it (no ``exec``), the panel
    is not watched for changes, and the free space is not asked."""

    site = ROOT_SITE
    capabilities = frozenset((WRITE, RENAME, SYMLINK, CHMOD, CHOWN))

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.drives.listing import DirEntry

        options = {key: value for key, value in options.items() if key != "job"}
        packed, error, space = ELEVATION.call("listing", path=str(location.path), show_hidden=show_hidden,
                                              sort=sort, free=free, options=options)
        entries = []
        for name, is_dir, size, mode, mtime, is_link, target, uid, gid, counted in packed:
            entry = DirEntry(name, is_dir, size, mode, mtime, is_link, target, uid, gid)
            entry.counted = counted
            entries.append(entry)
        return entries, error, tuple(space) if space else None

    def stat(self, location: Location) -> os.stat_result:
        return ROOT_DRIVE.stat(on_disk(location))

    def lstat(self, location: Location) -> os.stat_result:
        return ROOT_DRIVE.lstat(on_disk(location))

    def lexists(self, location: Location) -> bool:
        return ROOT_DRIVE.lexists(on_disk(location))

    def exists(self, location: Location) -> bool:
        return ROOT_DRIVE.exists(on_disk(location))

    def is_dir(self, location: Location) -> bool:
        return ROOT_DRIVE.is_dir(on_disk(location))

    def is_link(self, location: Location) -> bool:
        return ROOT_DRIVE.is_link(on_disk(location))

    def children(self, location: Location) -> list[Child]:
        return ROOT_DRIVE.children(on_disk(location))

    def names(self, location: Location) -> list[str]:
        return ROOT_DRIVE.names(on_disk(location))

    def readlink(self, location: Location) -> str:
        return ROOT_DRIVE.readlink(on_disk(location))

    def realpath(self, location: Location) -> Location:
        return root_location(ROOT_DRIVE.realpath(on_disk(location)))

    def same_file(self, a: Location, b: Location) -> bool:
        try:
            first, second = self.stat(a), self.stat(b)
        except OSError:
            return False
        return (first.st_dev, first.st_ino) == (second.st_dev, second.st_ino)

    def writable(self, location: Location, st: Any) -> bool:
        return True  # root's: what would refuse it is not a mode

    def open_read(self, location: Location) -> IO[bytes]:
        return ROOT_DRIVE.open_read(on_disk(location))

    def open_random(self, location: Location) -> Any:
        return ROOT_DRIVE.open_random(on_disk(location))

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        return ROOT_DRIVE.open_write(on_disk(location), append=append, mode=mode)

    def sync(self, handle: IO[bytes]) -> None:
        ROOT_DRIVE.sync(handle)

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        ROOT_DRIVE.mkdir(on_disk(location), mode)

    def makedirs(self, location: Location) -> None:
        ROOT_DRIVE.makedirs(on_disk(location))

    def rmdir(self, location: Location) -> None:
        ROOT_DRIVE.rmdir(on_disk(location))

    def unlink(self, location: Location) -> None:
        ROOT_DRIVE.unlink(on_disk(location))

    def rename(self, source: Location, dest: Location) -> None:
        ROOT_DRIVE.rename(on_disk(source), on_disk(dest))

    def replace(self, source: Location, dest: Location) -> None:
        ROOT_DRIVE.replace(on_disk(source), on_disk(dest))

    def symlink(self, target: str, location: Location) -> None:
        ROOT_DRIVE.symlink(target, on_disk(location))

    def chmod(self, location: Location, mode: int) -> None:
        ROOT_DRIVE.chmod(on_disk(location), mode)

    def chown(self, location: Location, uid: int, gid: int, *, follow: bool = True) -> None:
        ROOT_DRIVE.chown(on_disk(location), uid, gid, follow=follow)

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        ROOT_DRIVE.utime(on_disk(location), atime_ns, mtime_ns, follow=follow)

    def copy_attributes(self, source_drive: Drive, source: Location, dest: Location, st: Any, *,
                        follow: bool) -> None:
        if isinstance(source_drive, (LocalDrive, RootSiteDrive)):
            ELEVATION.call("copystat", source=str(source.path), dest=str(dest.path), follow=follow)
            return
        Drive.copy_attributes(self, source_drive, source, dest, st, follow=follow)

    def write_file(self, path: Path | Location, chunks: Iterable[bytes], job: Any = None,
                   backup: bool = False) -> None:
        """The editor's write as root: what a file fetched from here goes back by."""
        ROOT_DRIVE.write_file(Path(str(path.path if isinstance(path, Location) else path)), chunks, job, backup)

    def watch(self, location: Location, notify: Any) -> Any:
        """*Auto refresh*: the directory listed through the helper every
        :data:`POLL_INTERVAL` seconds (``PollWatch``), *notify* called on a change."""
        from navigator.lib.drives.base import PollWatch

        return PollWatch(self, location, notify, POLL_INTERVAL)

    def describe(self) -> list[tuple[str, str]]:
        return [("Kind", "root")]


ROOT_SITE_DRIVE = RootSiteDrive()

#: The panels at :data:`ROOT_SITE`, which hold the helper open between them.
_HOLDERS: set[int] = set()


def mount_drive() -> None:
    """The root drive mounted, holder or none yet: what a ``root:`` place
    reached from a history is read through before its panel holds it."""
    from navigator.lib.drives import mount, mounted

    if not any(drive is ROOT_SITE_DRIVE for drive in mounted()):
        mount(ROOT_SITE_DRIVE)


def hold(holder: object) -> None:
    """*holder* (a panel) is at :data:`ROOT_SITE`: the drive mounted, the
    helper held open until the last holder :func:`leave` s."""

    if id(holder) in _HOLDERS:
        return
    mount_drive()
    _HOLDERS.add(id(holder))
    ELEVATION.hold()


def leave(holder: object) -> bool:
    """*holder* gone from :data:`ROOT_SITE`; True when it was the last, and
    the caller lets the helper go (``ELEVATION.release``, on a thread)."""
    from navigator.lib.drives import unmount

    if id(holder) not in _HOLDERS:
        return False
    _HOLDERS.discard(id(holder))
    ELEVATION.unhold()
    if _HOLDERS:
        return False
    unmount(ROOT_SITE)
    return True


__all__ = ["ROOT_DRIVE", "ROOT_SITE", "ROOT_SITE_DRIVE", "RootDrive", "RootSiteDrive", "hold", "leave",
           "mount_drive", "on_disk", "readable_plainly", "root_location"]
