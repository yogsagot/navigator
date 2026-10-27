"""GVfs places as a drive: ``mtp://``, ``dav://``, ``afp://``, ``google-drive://``...

Not DOS Navigator's.  Where the desktop's GVfs is installed it speaks a
dozen protocols Navigator does not (:data:`navigator.lib.system.gio.GVFS_SCHEMES`),
and its FUSE bridge shows each mount as a directory under
``/run/user/$UID/gvfs``.  This drive is that directory under the URI's own
name, so a panel's title, Disconnect (Alt+H) and the fall back to the disk
when it closes are a connection's, as SFTP's are -- not a local path that
happens to be a phone.

* **Connecting** is ``gio mount URI`` (:func:`connect`).  Its prompts --
  ``User``, ``Domain``, ``Password`` -- are answered from the site and the
  :class:`~navigator.lib.drives.sessions.Answers`; a password not given yet
  raises :class:`~navigator.lib.drives.sessions.NeedPassword`, and the
  shell's password box tries again, as for any server.  A place mounted
  already (by the desktop's file manager, say) is used as it is.
* **Where the mount starts** is found once: ``gio info`` gives the asked
  place's FUSE path, and the first name under the bridge is the mount's top.
  What it stands for on the server is the *prefix* (``/`` for a phone,
  ``/remote.php/webdav`` for a WebDAV share mounted there), the drive's
  :attr:`home`; a place above it is not on the mount.
* **Every step is the disk's** (:data:`~navigator.lib.drives.local.LOCAL`)
  on the FUSE path, as the Trash's are: copying in and out goes through the
  one copier, the drive not being local.
* **Closing** unmounts what this drive mounted (``gio mount -u``), and
  leaves a mount it found alone.
* **The host keeps its case** (:func:`navigator.lib.drives.location.Location.parse`):
  an MTP device's name is not a DNS name.
"""

from __future__ import annotations

import errno
import os
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import IO, Any

from navigator.lib.drives.base import CHMOD, FIND, FREE_SPACE, RENAME, SYMLINK, TREE, WRITE, Child, Drive
from navigator.lib.drives.local import LOCAL
from navigator.lib.drives.location import Location, Site
from navigator.lib.system import gio

#: Why a place above where the mount starts cannot be reached.
OUTSIDE = "Not on this GVfs mount"
#: Why a mounted place has no directory to read: the FUSE bridge is not running.
NO_FUSE = "GVfs's FUSE bridge (gvfsd-fuse) is not running"


def available() -> str | None:
    """Why GVfs cannot be reached here, or None if it can."""
    if gio.program() is None:
        return gio.NO_GIO
    return None


def uri_of(site: Site, path: PurePosixPath | str = "/") -> str:
    """The URI ``gio`` is given for *path* on *site*."""
    return str(Location(site, PurePosixPath(path or "/")))


def bridge_top(local: Path) -> Path:
    """The mount's own directory under the FUSE bridge that holds *local*:
    the first name below the directory called ``gvfs``."""
    parts = local.parts
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] == "gvfs" and index + 1 < len(parts):
            return Path(*parts[:index + 2])
    return local


class GvfsDrive(Drive):
    """A GVfs mount, read and written through its FUSE path."""

    capabilities = frozenset((WRITE, RENAME, SYMLINK, CHMOD, FREE_SPACE, TREE, FIND))
    seekable = True

    def __init__(self, site: Site, root: Path, prefix: PurePosixPath, *, ours: bool) -> None:
        self.site = site
        #: The mount's directory under the FUSE bridge.
        self.root = root
        #: What :attr:`root` is on the server.
        self.prefix = prefix
        self.home = prefix
        #: Whether this drive mounted it, and so unmounts it when closed.
        self.ours = ours
        self.on_lost: Any = None

    # -- names -------------------------------------------------------------------

    def get_dir(self, location: Location) -> str:
        from navigator.lib.drives.sessions import protocol_sign

        return f"{protocol_sign(self.site.scheme)}:{self.site.host}:{location.path}"

    def disk(self, location: Location) -> Location:
        """Where *location* is under the FUSE bridge; ``ENOENT`` above the mount."""
        path = PurePosixPath(os.path.normpath(str(location.path)))
        try:
            rest = path.relative_to(self.prefix)
        except ValueError:
            raise OSError(errno.ENOENT, OUTSIDE, str(location)) from None
        return Location.of(self.root / rest if rest.parts else self.root)

    def back(self, local: Path) -> Location:
        """The location on this drive of *local*, a path under :attr:`root`."""
        rest = Path(local).relative_to(self.root)
        return Location(self.site, self.prefix / PurePosixPath(*rest.parts) if rest.parts else self.prefix)

    # -- reading -----------------------------------------------------------------

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        try:
            disk = self.disk(location)
        except OSError as error:
            return [], error.strerror or str(error), None
        return LOCAL.scan(disk, show_hidden, sort, free=free, **options)

    def stat(self, location: Location) -> Any:
        return LOCAL.stat(self.disk(location))

    def lstat(self, location: Location) -> Any:
        return LOCAL.lstat(self.disk(location))

    def children(self, location: Location) -> list[Child]:
        return LOCAL.children(self.disk(location))

    def names(self, location: Location) -> list[str]:
        return LOCAL.names(self.disk(location))

    def readlink(self, location: Location) -> str:
        return LOCAL.readlink(self.disk(location))

    def realpath(self, location: Location) -> Location:
        real = LOCAL.realpath(self.disk(location)).local
        try:
            return self.back(real)
        except ValueError:
            return location

    def same_file(self, a: Location, b: Location) -> bool:
        if a.site != self.site or b.site != self.site:
            return False
        try:
            return LOCAL.same_file(self.disk(a), self.disk(b))
        except OSError:
            return False

    def writable(self, location: Location, st: Any) -> bool:
        try:
            return LOCAL.writable(self.disk(location), st)
        except OSError:
            return False

    def free_bytes(self, location: Location) -> int | None:
        try:
            return LOCAL.free_bytes(self.disk(location))
        except OSError:
            return None

    def open_read(self, location: Location) -> IO[bytes]:
        return LOCAL.open_read(self.disk(location))

    def open_random(self, location: Location) -> Any:
        return LOCAL.open_random(self.disk(location))

    # -- writing -----------------------------------------------------------------

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        return LOCAL.open_write(self.disk(location), append=append, mode=mode)

    def sync(self, handle: IO[bytes]) -> None:
        LOCAL.sync(handle)

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        LOCAL.mkdir(self.disk(location), mode)

    def makedirs(self, location: Location) -> None:
        LOCAL.makedirs(self.disk(location))

    def rmdir(self, location: Location) -> None:
        LOCAL.rmdir(self.disk(location))

    def unlink(self, location: Location) -> None:
        LOCAL.unlink(self.disk(location))

    def rename(self, source: Location, dest: Location) -> None:
        LOCAL.rename(self.disk(source), self.disk(dest))

    def replace(self, source: Location, dest: Location) -> None:
        LOCAL.replace(self.disk(source), self.disk(dest))

    def symlink(self, target: str, location: Location) -> None:
        LOCAL.symlink(target, self.disk(location))

    def chmod(self, location: Location, mode: int) -> None:
        LOCAL.chmod(self.disk(location), mode)

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        LOCAL.utime(self.disk(location), atime_ns, mtime_ns, follow=follow)

    # -- the rest ----------------------------------------------------------------

    def watch(self, location: Location, notify: Callable[[], None]) -> Any:
        """Nothing: a FUSE mount tells no one what changed on the server."""
        from navigator.lib.system.dirwatch import Watch

        return Watch()

    def describe(self) -> list[tuple[str, str]]:
        return [("Server", uri_of(self.site, self.prefix)), ("Kind", "GVfs")]

    def close(self) -> None:
        if self.ours:
            try:
                gio.unmount(uri_of(self.site, self.prefix))
            except OSError:
                pass


def connect(site: Site, answers: Any) -> GvfsDrive:
    """*site* mounted through GVfs, if it is not already: blocks, and raises
    :class:`~navigator.lib.drives.sessions.NeedPassword` for the user to answer."""
    from navigator.lib.drives.sessions import NeedPassword

    start = PurePosixPath(answers.start or "/")
    uri = uri_of(site, start)
    ours = False
    local = gio.local_path(uri)
    if local is None:
        given = {"User": site.user, "Domain": ""}
        if answers.password is not None:
            given["Password"] = answers.password
        try:
            gio.mount_uri(uri, given)
        except gio.Prompted as prompt:
            if prompt.what != "Password":
                raise OSError(errno.EACCES, f"{prompt.message or 'gio mount'}: {prompt.what}?") from None
            raise NeedPassword(site, site.user, site.host, wrong=prompt.again) from None
        ours = True
        local = gio.local_path(uri)
        if local is None:
            try:
                gio.unmount(uri)
            except OSError:
                pass
            raise OSError(errno.ENOENT, NO_FUSE)
    top = bridge_top(local)
    rest = local.relative_to(top).parts
    prefix = PurePosixPath(*start.parts[:len(start.parts) - len(rest)]) if rest else start
    return GvfsDrive(site, top, prefix if str(prefix) else PurePosixPath("/"), ours=ours)


__all__ = ["GvfsDrive", "NO_FUSE", "OUTSIDE", "available", "bridge_top", "connect", "uri_of"]
