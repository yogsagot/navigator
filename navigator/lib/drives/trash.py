"""The Trash as a drive: ``trash:///``, everything in every trash directory.

Not DOS Navigator's: its trash can erased (``cmEraseGroup``) and a double
click on it ran the *Reanimator*, an undelete.  The freedesktop Trash
(:mod:`navigator.lib.file_ops.trash`) is the undelete a POSIX system has, and
this is the panel onto it -- what the trash can's double click opens now.

* **The root lists every item** of the home trash and of each mount's, by
  its name in ``files/``.  A name another trash directory has shown already
  is given ``.2``, ``.3`` before its extension; which name is which item is
  worked out again on every listing of the root (:meth:`TrashDrive.item`).
* **Below the root is the disk**: ``trash:///docs/a.txt`` is
  ``files/docs/a.txt`` in that item's trash, and every read is
  :data:`~navigator.lib.drives.local.LOCAL`'s.
* **Only erasing writes.**  F8 here erases for good, and an item erased
  whole takes its info file with it; nothing is put into the Trash but by
  F8 elsewhere -- making, writing or renaming here is ``EROFS``.  Restore
  (:func:`navigator.lib.file_ops.trash.restore`) puts an item back.
* **``..`` at the root leaves it**, as Backspace does, for the last local
  directory the panel read (``Drive.leaves_to_anchor``).
* It is no connection: :func:`navigator.lib.drives.drive_of` answers
  :data:`TRASH` for its site without mounting, and nothing reaps it.
"""

from __future__ import annotations

import errno
import os
import stat
import threading
from collections.abc import Callable
from pathlib import PurePosixPath
from typing import IO, Any

from navigator.lib.drives.base import FIND, TREE, WATCH, WRITE, Child, Drive, FileStat
from navigator.lib.drives.local import LOCAL
from navigator.lib.drives.location import Location, Site
from navigator.lib.file_ops import trash as model

#: The Trash's site: ``trash:///``.
TRASH_SITE = Site("trash")

#: Why anything but erasing is refused here.
READ_ONLY = "Files go to the Trash only through F8"


def _read_only(location: Location) -> OSError:
    return OSError(errno.EROFS, READ_ONLY, str(location))


def _unique(name: str, taken: set[str]) -> str:
    """*name*, or ``stem.N.ext`` with the first *N* not in *taken*."""
    if name not in taken:
        return name
    stem, extension = os.path.splitext(name)
    number = 2
    while f"{stem}.{number}{extension}" in taken:
        number += 1
    return f"{stem}.{number}{extension}"


class TrashDrive(Drive):
    """Every trash directory as one drive."""

    site = TRASH_SITE
    capabilities = frozenset((WRITE, TREE, FIND, WATCH))
    seekable = True
    #: ``..`` and Backspace at the root go back where the panel was.
    leaves_to_anchor = True

    def __init__(self) -> None:
        self._lock = threading.Lock()
        #: The root's names, to their items, as the last listing found them.
        self._index: dict[str, model.Item] = {}

    # -- names -------------------------------------------------------------------

    def get_dir(self, location: Location) -> str:
        return f"TRASH:{location.path}"

    def items(self) -> dict[str, model.Item]:
        """The root's names, to their items: read again now."""
        found: dict[str, model.Item] = {}
        for item in model.items():
            found[_unique(item.name, set(found))] = item
        with self._lock:
            self._index = found
        return dict(found)

    def item(self, name: str) -> model.Item | None:
        """The item the root lists as *name*, looking again if it is not known."""
        with self._lock:
            found = self._index.get(name)
        if found is None or not os.path.lexists(found.path):
            found = self.items().get(name)
        return found

    def _split(self, location: Location) -> tuple[model.Item | None, PurePosixPath]:
        parts = location.normalized().path.parts[1:]
        if not parts:
            return None, PurePosixPath()
        item = self.item(parts[0])
        if item is None:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(location))
        return item, PurePosixPath(*parts[1:])

    def real(self, location: Location) -> Location | None:
        """Where *location* is on the disk; None for the root, which is nowhere."""
        item, rest = self._split(location)
        if item is None:
            return None
        return Location.of(item.path / rest if rest.parts else item.path)

    def _on_disk(self, location: Location) -> Location:
        real = self.real(location)
        if real is None:
            raise _read_only(location)
        return real

    # -- reading -----------------------------------------------------------------

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.appearance import filetypes
        from navigator.lib.drives.listing import DirEntry, entry_at, order_entries, read_listing

        try:
            real = self.real(location)
        except OSError as error:
            return [], error.strerror or str(error), None
        if real is not None:
            entries, error, _ = read_listing(real.local, show_hidden, sort, free=False, **options)
            return entries, error, None
        mask = options.get("mask", filetypes.ALL_FILES)
        filtered = mask.strip() not in ("", filetypes.ALL_FILES)
        # ``..`` out of the Trash, back where the panel was (``leaves_to_anchor``).
        entries: list[DirEntry] = [DirEntry("..", True, 0, stat.S_IFDIR | 0o755)]
        for name, item in self.items().items():
            if not show_hidden and name.startswith("."):
                continue
            entry = entry_at(item.path)
            if entry is None:
                continue
            if filtered and not entry.is_dir and not filetypes.in_filter(name, mask):
                continue
            entry.name = name
            entry.trashed = (str(item.original) if item.original is not None else "", item.deleted)
            entries.append(entry)
        order = {key: options[key] for key in ("executables_first", "archives_first", "reverse")
                 if key in options}
        return order_entries(entries, sort, **order), None, None

    def stat(self, location: Location) -> Any:
        real = self.real(location)
        if real is None:
            return FileStat(stat.S_IFDIR | 0o700, 0, 0.0, 0.0)
        return LOCAL.stat(real)

    def lstat(self, location: Location) -> Any:
        real = self.real(location)
        if real is None:
            return FileStat(stat.S_IFDIR | 0o700, 0, 0.0, 0.0)
        return LOCAL.lstat(real)

    def children(self, location: Location) -> list[Child]:
        real = self.real(location)
        if real is not None:
            return LOCAL.children(real)
        found: list[Child] = []
        for name, item in self.items().items():
            try:
                found.append((name, os.lstat(item.path)))
            except OSError as error:
                found.append((name, error))
        return found

    def names(self, location: Location) -> list[str]:
        real = self.real(location)
        return LOCAL.names(real) if real is not None else list(self.items())

    def readlink(self, location: Location) -> str:
        return LOCAL.readlink(self._on_disk(location))

    def writable(self, location: Location, st: Any) -> bool:
        return True

    def open_read(self, location: Location) -> IO[bytes]:
        return LOCAL.open_read(self._on_disk(location))

    def open_random(self, location: Location) -> Any:
        return LOCAL.open_random(self._on_disk(location))

    # -- erasing, and nothing else -----------------------------------------------

    def unlink(self, location: Location) -> None:
        item, rest = self._split(location)
        LOCAL.unlink(self._on_disk(location))
        if item is not None and not rest.parts:
            model.forget(item)

    def rmdir(self, location: Location) -> None:
        item, rest = self._split(location)
        LOCAL.rmdir(self._on_disk(location))
        if item is not None and not rest.parts:
            model.forget(item)

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        raise _read_only(location)

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        raise _read_only(location)

    def makedirs(self, location: Location) -> None:
        raise _read_only(location)

    def rename(self, source: Location, dest: Location) -> None:
        raise _read_only(source)

    def replace(self, source: Location, dest: Location) -> None:
        raise _read_only(source)

    def symlink(self, target: str, location: Location) -> None:
        raise _read_only(location)

    def chmod(self, location: Location, mode: int) -> None:
        raise _read_only(location)

    # -- the rest ----------------------------------------------------------------

    def watch(self, location: Location, notify: Callable[[], None]) -> Any:
        """The root: the home trash's ``files/``, where F8 puts things; below it, the disk's."""
        from navigator.lib.system.dirwatch import Watch

        try:
            real = self.real(location)
        except OSError:
            return Watch()
        where = real if real is not None else Location.of(model.home_trash() / "files")
        if not os.path.isdir(where.local):
            return Watch()
        return LOCAL.watch(where, notify)

    def describe(self) -> list[tuple[str, str]]:
        return [("Kind", "Trash"), ("Files", str(len(self.items())))]


#: The one Trash drive.
TRASH = TrashDrive()


def location(name: str = "") -> Location:
    """``trash:///`` or the item the root lists as *name*."""
    return Location(TRASH_SITE, PurePosixPath("/") / name if name else PurePosixPath("/"))


def is_trash(where: Any) -> bool:
    """Whether *where* (a location, or anything else) is on the Trash."""
    return isinstance(where, Location) and where.site == TRASH_SITE and where.outer is None


__all__ = ["READ_ONLY", "TRASH", "TRASH_SITE", "TrashDrive", "is_trash", "location"]
