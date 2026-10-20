"""The drive: what a panel, a copy or an erase asks of wherever files are.

DOS Navigator's ``TDrive`` (``DRIVES.PAS``) and its descendants -- the disk,
an archive (``TArcDrive``), a *Find:* listing (``TFindDrive``), the other
PC over a cable (``TLinkDrive``) -- were one object a panel held, whose
virtual methods read the directory, copied, erased and made directories.
:class:`Drive` is that object, with the names kept where they still fit:
:meth:`get_dir` is ``GetDir``, the panel's title; :meth:`real_name` is
``GetRealName``, what the other panel offers as a copy's target;
:meth:`use_file` is ``UseFile``, a file made local for a program to open.

DN's drive did whole operations (``CopyFiles``, ``EraseFiles``).  This one
does the steps of them -- stat, list, open, rename, unlink -- and the
operations (:mod:`navigator.lib.file_ops.filecopy`, ``fileerase``) are
written once over those, so a copy from a remote drive to the disk is the
same code, asking the same questions, as one between two local directories.

**Every method blocks, and runs on a thread** -- a remote one is a round
trip, and a local one may be a dead network mount.  A failure is an
:class:`OSError`, with ``errno`` and ``filename`` where they are known, so
what shows it (:func:`navigator.lib.file_ops.filecopy.error_message`) need
not care which drive it came from.
"""

from __future__ import annotations

import errno
import os
import stat
from collections.abc import Callable
from typing import IO, Any, NamedTuple

from navigator.lib.drives.location import Location, Site

#: What a drive may be able to do, beyond being read: the commands needing one
#: are greyed out on a drive that cannot.
WRITE = "write"
RENAME = "rename"
SYMLINK = "symlink"
CHMOD = "chmod"
CHOWN = "chown"
WATCH = "watch"
FREE_SPACE = "free_space"
EXEC = "exec"
TREE = "tree"
FIND = "find"
UUCODE = "uucode"
PRINT = "print"

#: Everything: the local disk's.
EVERYTHING = frozenset((WRITE, RENAME, SYMLINK, CHMOD, CHOWN, WATCH, FREE_SPACE, EXEC, TREE, FIND,
                        UUCODE, PRINT))


class DriveGone(OSError):
    """The drive cannot be reached: the connection is closed, or was lost.

    DN's ``TLinkDrive.GetDirectory`` put *Remote drive X is not accessible*
    where the free space went; this is that, as an error.
    """

    def __init__(self, name: str, reason: str = "") -> None:
        super().__init__(errno.ENOTCONN, reason or f"Remote drive {name} is not accessible")
        self.name = name


class FileStat(NamedTuple):
    """What a drive that is not the disk says of a file: ``os.stat_result``'s
    fields, so code reading one reads the other.  ``st_dev`` and ``st_ino``
    are 0 where the drive has no such thing."""

    st_mode: int
    st_size: int = 0
    st_mtime: float = 0.0
    st_atime: float = 0.0
    st_uid: int = 0
    st_gid: int = 0
    st_nlink: int = 1
    st_dev: int = 0
    st_ino: int = 0

    @property
    def st_mtime_ns(self) -> int:
        return int(self.st_mtime * 1_000_000_000)

    @property
    def st_atime_ns(self) -> int:
        return int(self.st_atime * 1_000_000_000)


#: A child of a directory: its name, and its own (``lstat``) facts or why not.
Child = tuple[str, Any]


def unsupported(location: Location | None = None, what: str = "") -> OSError:
    """The error for something *location*'s drive cannot do."""
    return OSError(errno.ENOTSUP, what or os.strerror(errno.ENOTSUP),
                   None if location is None else str(location))


class Drive:
    """Files somewhere: the disk, a server, an archive.

    A subclass answers what it can and leaves the rest raising
    :func:`unsupported`; :attr:`capabilities` says which is which, so the
    commands that would fail are greyed out before they are tried.
    """

    #: The site this drive serves.
    site: Site = Site()
    #: What it can do beyond reading (the constants above).
    capabilities: frozenset[str] = frozenset()

    def can(self, capability: str) -> bool:
        return capability in self.capabilities

    # -- names -------------------------------------------------------------------

    def get_dir(self, location: Location) -> str:
        """``GetDir``: what the panel's title says *location* is."""
        return str(location)

    def real_name(self, location: Location) -> str:
        """``GetRealName``: *location* as a copy's target line names it."""
        return str(location)

    # -- reading -----------------------------------------------------------------

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        """A panel's read: the entries, why not, and the free space (or None)."""
        raise unsupported(location)

    def stat(self, location: Location) -> Any:
        raise unsupported(location)

    def lstat(self, location: Location) -> Any:
        return self.stat(location)

    def lexists(self, location: Location) -> bool:
        try:
            self.lstat(location)
        except FileNotFoundError:
            return False
        except OSError:
            return True
        return True

    def exists(self, location: Location) -> bool:
        try:
            self.stat(location)
        except OSError:
            return False
        return True

    def is_dir(self, location: Location) -> bool:
        try:
            return stat.S_ISDIR(self.stat(location).st_mode)
        except OSError:
            return False

    def is_link(self, location: Location) -> bool:
        try:
            return stat.S_ISLNK(self.lstat(location).st_mode)
        except OSError:
            return False

    def children(self, location: Location) -> list[Child]:
        """*location*'s entries, each with its ``lstat`` or the error that
        stopped it; raises if the directory cannot be listed at all."""
        raise unsupported(location)

    def names(self, location: Location) -> list[str]:
        return [name for name, _ in self.children(location)]

    def readlink(self, location: Location) -> str:
        raise unsupported(location)

    def realpath(self, location: Location) -> Location:
        """*location* with its links followed, as far as the drive can tell."""
        return location.normalized()

    def same_file(self, a: Location, b: Location) -> bool:
        """Whether *a* and *b* are one file."""
        if a.site != b.site:
            return False
        try:
            return self.realpath(a) == self.realpath(b)
        except OSError:
            return False

    def writable(self, location: Location, st: Any) -> bool:
        """Whether the user may write *location* (*st* its ``lstat``), as
        far as the drive can tell -- what makes an erase ask first."""
        return True

    def free_bytes(self, location: Location) -> int | None:
        """Bytes free where *location* is, or None when it cannot be told."""
        return None

    def open_read(self, location: Location) -> IO[bytes]:
        raise unsupported(location)

    def open_random(self, location: Location) -> Any:
        """A handle that reads anywhere in *location* -- ``read_at(offset,
        count)`` and ``close()``, one read at a time -- or None where the drive
        can only stream a file from its start: what the viewer reads a file on
        another drive through, a chunk at a time (``viewer.ChunkedSource``)."""
        return SeekingReader(self.open_read(location)) if self.seekable else None

    #: Whether :meth:`open_read`'s files can ``seek``: what the default
    #: :meth:`open_random` stands on.
    seekable = False

    # -- writing -----------------------------------------------------------------

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        """*location* opened to write, created with *mode* if it is not there."""
        raise unsupported(location)

    def sync(self, handle: IO[bytes]) -> None:
        """What *Flush buffers* asks: *handle*'s bytes on the medium."""
        handle.flush()

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        raise unsupported(location)

    def makedirs(self, location: Location) -> None:
        """*location* and every directory above it that is missing."""
        missing: list[Location] = []
        here = location
        while not here.is_root and not self.is_dir(here):
            missing.append(here)
            here = here.parent
        for each in reversed(missing):
            try:
                self.mkdir(each)
            except FileExistsError:
                pass

    def rmdir(self, location: Location) -> None:
        raise unsupported(location)

    def unlink(self, location: Location) -> None:
        raise unsupported(location)

    def rename(self, source: Location, dest: Location) -> None:
        """``os.rename``: *dest* must not be a directory that is there."""
        raise unsupported(source)

    def replace(self, source: Location, dest: Location) -> None:
        """``os.replace``: a file at *dest* goes."""
        raise unsupported(source)

    def symlink(self, target: str, location: Location) -> None:
        raise unsupported(location)

    def chmod(self, location: Location, mode: int) -> None:
        raise unsupported(location)

    def chown(self, location: Location, uid: int, gid: int, *, follow: bool = True) -> None:
        raise unsupported(location)

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        raise unsupported(location)

    def copy_attributes(self, source_drive: Drive, source: Location, dest: Location, st: Any, *,
                        follow: bool) -> None:
        """*Preserve attributes*: *source*'s mode and times (its ``stat`` *st*)
        given to *dest* on this drive.  What cannot be set is passed over."""
        try:
            self.chmod(dest, stat.S_IMODE(st.st_mode))
        except OSError:
            pass
        try:
            self.utime(dest, st.st_atime_ns, st.st_mtime_ns, follow=follow)
        except OSError:
            pass

    # -- the rest ----------------------------------------------------------------

    #: Whether :meth:`watch` looks again every *Communications* ``refresh``
    #: seconds, for a drive that cannot say when something changed: a server's.
    polled = False

    def watch(self, location: Location, notify: Callable[[], None]) -> Any:
        """Call *notify* when *location*'s listing changes: a ``dirwatch.Watch``.

        A drive that cannot tell answers one that never calls -- or, being
        :attr:`polled`, one that lists *location* again on a thread of its own
        every ``[remote] refresh`` seconds and calls when the names, sizes or
        times differ."""
        from navigator.lib.system.dirwatch import Watch
        from navigator.settings import SETTINGS

        interval = SETTINGS.remote.refresh
        if not self.polled or interval <= 0:
            return Watch()
        return PollWatch(self, location, notify, interval)

    def describe(self) -> list[tuple[str, str]]:
        """What the information panel (Ctrl+L) says of the drive, as
        ``(what, value)`` pairs -- DN's ``GetDirInfo``: a link drive's remote
        volume, an archive's packed and unpacked sizes."""
        return []

    def change_up(self, location: Location) -> tuple[Location, str] | None:
        """``ChangeUp`` at the top of the drive: where ``..`` goes from its root,
        and the name for the cursor there -- an archive's, back on the drive it
        was opened from.  None where the root is the end."""
        return None

    def finish(self) -> None:
        """The steps since the last, made final: called once by whoever made
        them -- a copy, an erase, a rename -- when it is done.  Nothing on a
        drive whose every step is final already; an archive is written anew
        (:meth:`navigator.lib.drives.archive.ArchiveDrive.finish`)."""

    def close(self) -> None:
        """Let go of whatever the drive holds open."""


#: Every name ``Drive.describe`` gives a fact, in English: what the
#: information panel translates, listed for the catalogues
#: (``navigator/locales/__init__.py``).
DESCRIBED = ("Server", "Host key", "Software", "Cipher", "Security", "Shares", "Archive", "Kind", "Files",
             "Packed", "Unpacked", "Region")


class SeekingReader:
    """``read_at`` over a file object that can seek."""

    def __init__(self, handle: Any) -> None:
        self._handle = handle

    def read_at(self, offset: int, count: int) -> bytes:
        self._handle.seek(offset)
        parts, left = [], count
        while left > 0:
            data = self._handle.read(left)
            if not data:
                break
            parts.append(data)
            left -= len(data)
        return b"".join(parts)

    def close(self) -> None:
        self._handle.close()


class PollWatch:
    """A ``dirwatch.Watch`` by looking: *location* listed every *interval*
    seconds on a thread, *notify* called when what is there changed."""

    def __init__(self, drive: Drive, location: Location, notify: Callable[[], None], interval: float) -> None:
        import threading

        self.path = location
        self._notify: Callable[[], None] | None = notify
        self._drive, self._interval = drive, interval
        self._stop = threading.Event()
        # Made on the loop: the first look, a round trip, is the thread's.
        threading.Thread(target=self._run, daemon=True, name="nav-poll").start()

    @property
    def active(self) -> bool:
        return self._notify is not None

    def _look(self) -> Any:
        try:
            return sorted((name, getattr(st, "st_size", None), getattr(st, "st_mtime", None))
                          for name, st in self._drive.children(self.path))
        except OSError:
            return None

    def _run(self) -> None:
        self._last = self._look()
        while not self._stop.wait(self._interval):
            now = self._look()
            if now is not None and now != self._last:
                self._last = now
                notify = self._notify
                if notify is not None:
                    notify()

    def cancel(self) -> None:
        self._notify = None
        self._stop.set()


__all__ = [
    "CHMOD", "CHOWN", "Child", "Drive", "DriveGone", "EVERYTHING", "EXEC", "FIND", "FREE_SPACE",
    "FileStat", "PRINT", "PollWatch", "RENAME", "SYMLINK", "TREE", "UUCODE", "WATCH", "WRITE", "unsupported",
]
