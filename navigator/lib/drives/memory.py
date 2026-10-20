"""A drive held in memory: files that are nowhere but this process.

What the tests put a panel on to see it work away from the disk -- every
call is a dictionary lookup, so nothing is slow and nothing is left behind
-- and the ground DN's ``TTempDrive`` (``TEMP:``, a panel of files gathered
from anywhere) can stand on later.  It behaves as a POSIX file system does
where that is cheap (``ENOENT``, ``ENOTDIR``, ``EEXIST``, ``ENOTEMPTY``) and
does not pretend to the rest: there are no owners, no devices, no hard links.
"""

from __future__ import annotations

import errno
import io
import os
import stat
import threading
import time
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import IO, Any

from navigator.lib.drives.base import CHMOD, RENAME, SYMLINK, WRITE, Child, Drive, FileStat
from navigator.lib.drives.location import Location, Site


@dataclass
class _Node:
    mode: int
    data: bytearray = field(default_factory=bytearray)
    target: str = ""
    mtime: float = field(default_factory=time.time)
    atime: float = field(default_factory=time.time)
    children: dict[str, _Node] | None = None

    @property
    def is_dir(self) -> bool:
        return stat.S_ISDIR(self.mode)

    @property
    def is_link(self) -> bool:
        return stat.S_ISLNK(self.mode)

    def stat(self) -> FileStat:
        size = len(self.data) if stat.S_ISREG(self.mode) else len(self.target)
        return FileStat(self.mode, size, self.mtime, self.atime)


def _error(code: int, location: Location | PurePosixPath | str) -> OSError:
    error_type = {errno.ENOENT: FileNotFoundError, errno.EEXIST: FileExistsError,
                  errno.ENOTDIR: NotADirectoryError, errno.EISDIR: IsADirectoryError}.get(code, OSError)
    return error_type(code, os.strerror(code), str(location))


class _Writer(io.BytesIO):
    """A file opened to write: its bytes land on the node when it closes."""

    def __init__(self, drive: MemoryDrive, node: _Node, start: bytes) -> None:
        super().__init__()
        self.write(start)
        self._drive, self._node = drive, node

    def flush(self) -> None:
        super().flush()
        if not self.closed:
            with self._drive.lock:
                self._node.data = bytearray(self.getvalue())
                self._node.mtime = time.time()

    def close(self) -> None:
        if not self.closed:
            self.flush()
        super().close()


class MemoryDrive(Drive):
    """Files in memory, on the site ``mem://<name>``."""

    capabilities = frozenset((WRITE, RENAME, SYMLINK, CHMOD))
    seekable = True

    def __init__(self, name: str = "memory") -> None:
        self.site = Site("mem", host=name)
        self.lock = threading.RLock()
        self._root = _Node(stat.S_IFDIR | 0o755, children={})

    def location(self, path: str = "/") -> Location:
        """*path* on this drive."""
        return Location(self.site, PurePosixPath(path))

    # -- the tree ----------------------------------------------------------------

    def _walk(self, path: PurePosixPath, *, follow: bool = True, depth: int = 0) -> _Node:
        if depth > 40:
            raise _error(errno.ELOOP, path)
        node = self._root
        parts = [part for part in path.parts if part != "/"]
        for index, part in enumerate(parts):
            if node.children is None:
                raise _error(errno.ENOTDIR, path)
            child = node.children.get(part)
            if child is None:
                raise _error(errno.ENOENT, path)
            last = index == len(parts) - 1
            if child.is_link and (follow or not last):
                here = PurePosixPath("/", *parts[:index])
                target = here / child.target
                child = self._walk(PurePosixPath(os.path.normpath(target)), depth=depth + 1)
            node = child
        return node

    def _parent(self, location: Location) -> tuple[_Node, str]:
        path = location.path
        parent = self._walk(path.parent)
        if parent.children is None:
            raise _error(errno.ENOTDIR, location)
        return parent, path.name

    def _node(self, location: Location, *, follow: bool = True) -> _Node:
        return self._walk(location.path, follow=follow)

    # -- writing helpers for tests -------------------------------------------------

    def make(self, path: str, data: bytes | str | None = None, *, mode: int | None = None) -> Location:
        """A file holding *data*, or a directory when *data* is None, with
        every directory above it made too."""
        location = self.location(path)
        with self.lock:
            self.makedirs(location.parent)
            if data is None:
                if not self.is_dir(location):
                    self.mkdir(location, 0o755 if mode is None else mode)
            else:
                raw = data.encode() if isinstance(data, str) else data
                parent, name = self._parent(location)
                parent.children[name] = _Node(stat.S_IFREG | (0o644 if mode is None else mode), bytearray(raw))
        return location

    def read(self, path: str) -> bytes:
        with self.lock:
            return bytes(self._node(self.location(path)).data)

    # -- reading -----------------------------------------------------------------

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.appearance import filetypes
        from navigator.lib.drives.listing import DirEntry, order_entries

        mask = options.get("mask", filetypes.ALL_FILES)
        filtered = mask.strip() not in ("", filetypes.ALL_FILES)
        entries: list[DirEntry] = []
        if not location.is_root:
            entries.append(DirEntry("..", True, 0, stat.S_IFDIR | 0o755))
        try:
            children = self.children(location)
        except OSError as error:
            return entries, error.strerror or str(error), None
        for name, st in children:
            if not show_hidden and name.startswith("."):
                continue
            if isinstance(st, OSError):
                entries.append(DirEntry(name, False, 0))
                continue
            link_target = None
            is_link = stat.S_ISLNK(st.st_mode)
            if is_link:
                link_target = self.readlink(location / name)
                try:
                    st = self.stat(location / name)
                except OSError:
                    pass
            is_dir = stat.S_ISDIR(st.st_mode)
            if filtered and not is_dir and not filetypes.in_filter(name, mask):
                continue
            entries.append(DirEntry(name, is_dir, 0 if is_dir else st.st_size, st.st_mode, st.st_mtime,
                                    is_link, link_target))
        order = {key: options[key] for key in ("executables_first", "archives_first", "reverse")
                 if key in options}
        return order_entries(entries, sort, **order), None, None

    def stat(self, location: Location) -> FileStat:
        with self.lock:
            return self._node(location).stat()

    def lstat(self, location: Location) -> FileStat:
        with self.lock:
            return self._node(location, follow=False).stat()

    def children(self, location: Location) -> list[Child]:
        with self.lock:
            node = self._node(location)
            if node.children is None:
                raise _error(errno.ENOTDIR, location)
            return [(name, child.stat()) for name, child in sorted(node.children.items())]

    def readlink(self, location: Location) -> str:
        with self.lock:
            node = self._node(location, follow=False)
            if not node.is_link:
                raise _error(errno.EINVAL, location)
            return node.target

    def realpath(self, location: Location) -> Location:
        path = location.normalized().path
        with self.lock:
            resolved = PurePosixPath("/")
            for part in path.parts[1:]:
                candidate = resolved / part
                try:
                    node = self._walk(candidate, follow=False)
                except OSError:
                    resolved = candidate
                    continue
                if node.is_link:
                    resolved = PurePosixPath(os.path.normpath(resolved / node.target))
                else:
                    resolved = candidate
        return Location(self.site, resolved, location.outer)

    def open_read(self, location: Location) -> IO[bytes]:
        with self.lock:
            node = self._node(location)
            if node.is_dir:
                raise _error(errno.EISDIR, location)
            node.atime = time.time()
            return io.BytesIO(bytes(node.data))

    # -- writing -----------------------------------------------------------------

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        with self.lock:
            parent, name = self._parent(location)
            node = parent.children.get(name)
            if node is not None and node.is_link:
                node = self._node(location)
            if node is None:
                node = parent.children[name] = _Node(stat.S_IFREG | (mode & 0o7777))
            elif node.is_dir:
                raise _error(errno.EISDIR, location)
            start = bytes(node.data) if append else b""
            node.data = bytearray(start)
            return _Writer(self, node, start)

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        with self.lock:
            parent, name = self._parent(location)
            if name in parent.children:
                raise _error(errno.EEXIST, location)
            parent.children[name] = _Node(stat.S_IFDIR | (mode & 0o7777), children={})

    def rmdir(self, location: Location) -> None:
        with self.lock:
            parent, name = self._parent(location)
            node = parent.children.get(name)
            if node is None:
                raise _error(errno.ENOENT, location)
            if not node.is_dir:
                raise _error(errno.ENOTDIR, location)
            if node.children:
                raise _error(errno.ENOTEMPTY, location)
            del parent.children[name]

    def unlink(self, location: Location) -> None:
        with self.lock:
            parent, name = self._parent(location)
            node = parent.children.get(name)
            if node is None:
                raise _error(errno.ENOENT, location)
            if node.is_dir:
                raise _error(errno.EISDIR, location)
            del parent.children[name]

    def _move(self, source: Location, dest: Location, *, replace: bool) -> None:
        with self.lock:
            source_parent, source_name = self._parent(source)
            node = source_parent.children.get(source_name)
            if node is None:
                raise _error(errno.ENOENT, source)
            dest_parent, dest_name = self._parent(dest)
            there = dest_parent.children.get(dest_name)
            if there is not None:
                if there.is_dir and (not node.is_dir or there.children):
                    raise _error(errno.EISDIR if not node.is_dir else errno.ENOTEMPTY, dest)
                if not replace and node.is_dir and not there.is_dir:
                    raise _error(errno.ENOTDIR, dest)
            del source_parent.children[source_name]
            dest_parent.children[dest_name] = node

    def rename(self, source: Location, dest: Location) -> None:
        self._move(source, dest, replace=False)

    def replace(self, source: Location, dest: Location) -> None:
        self._move(source, dest, replace=True)

    def symlink(self, target: str, location: Location) -> None:
        with self.lock:
            parent, name = self._parent(location)
            if name in parent.children:
                raise _error(errno.EEXIST, location)
            parent.children[name] = _Node(stat.S_IFLNK | 0o777, target=target)

    def chmod(self, location: Location, mode: int) -> None:
        with self.lock:
            node = self._node(location)
            node.mode = stat.S_IFMT(node.mode) | (mode & 0o7777)

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        with self.lock:
            node = self._node(location, follow=follow)
            node.atime, node.mtime = atime_ns / 1e9, mtime_ns / 1e9


__all__ = ["MemoryDrive"]
