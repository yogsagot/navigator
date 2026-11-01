"""What takes the room under a directory: the model behind Disk > Directory sizes.

**Not DOS Navigator's** -- a departure, asked for: ``ncdu``'s view, which DN
never had.  Its nearest were Alt+G (``cmCountLen``, :mod:`dirlength`), which
put a directory's bytes in its size column, *Directory length* in Panel
Options, which did that to every directory read, and the tree window's info
line (``TTreeInfoView``), which said the highlighted directory's total.  None
of them ranked what is in a directory by what it holds.

:func:`scan` walks the whole tree once, into memory, as ``ncdu`` does, so that
going down and up again costs nothing; :func:`remove` takes a node out after a
delete and its totals with it, so that neither needs a second walk.  It runs
on a thread: the walk touches nothing but the file system, and a *job*
stopped meanwhile ends it with None.

The rules :mod:`dirlength` gives, and three of its own:

- **Dot-files count**, and **a symbolic link counts as itself**, never as what
  it points at, as Alt+G counts them.  **A directory that cannot be read**
  counts as nothing and the rest goes on; it is flagged ``unreadable``.
- **A directory counts too**: its own size and blocks, as ``ncdu`` counts them
  -- the room its list of names takes, which Alt+G leaves out.
- **Another file system is not entered** while *one_filesystem* is on
  (``ncdu -x``): a directory whose ``st_dev`` is not the starting one's is
  listed, flagged ``other_fs``, and counts as itself alone.  Scanning ``/``
  then stays out of ``/proc`` and of the network's mounts.  A drive other
  than the disk says 0 for every ``st_dev``, so there it never applies.
- **A hard link counts once**: a file met again under another name -- the
  same ``st_dev`` and ``st_ino``, ``st_nlink`` above one -- is listed with its
  size but flagged ``hardlink`` and left out of every total, as ``ncdu`` does.

Two sizes are kept for everything: ``size``, the bytes it says it holds
(``st_size``, ``ncdu``'s *apparent size*), and ``usage``, the room it takes on
the disk (``st_blocks`` of 512 bytes).  A drive that has no blocks to tell
gives its size for both.
"""

from __future__ import annotations

import os
import stat
from typing import Any, Iterator

from navigator.lib.system.job import Job

#: How :func:`ordered` can sort.
SORTS = ("size", "name", "items")


class UsageNode:
    """One file or directory met by :func:`scan`.

    For a directory, ``size``, ``usage`` and ``items`` are totals: its own
    size and blocks and everything's beneath it, and how many entries are
    beneath it however deep.  For anything else they are its own, ``items``
    0.  ``children`` is None for anything that is not a directory.
    """

    __slots__ = ("name", "is_dir", "is_link", "size", "usage", "items", "children", "parent",
                 "unreadable", "other_fs", "hardlink")

    def __init__(self, name: str, is_dir: bool = False, is_link: bool = False, size: int = 0, usage: int = 0,
                 parent: UsageNode | None = None) -> None:
        self.name = name
        self.is_dir = is_dir
        self.is_link = is_link
        self.size = size
        self.usage = usage
        self.items = 0
        self.children: list[UsageNode] | None = [] if is_dir else None
        self.parent = parent
        self.unreadable = False
        self.other_fs = False
        self.hardlink = False

    def __repr__(self) -> str:
        return f"UsageNode({self.name!r}, size={self.size}, usage={self.usage}, items={self.items})"

    def amount(self, apparent: bool) -> int:
        """Its ``size`` if *apparent*, else its ``usage``."""
        return self.size if apparent else self.usage

    def counted(self) -> tuple[int, int, int]:
        """What it adds to its parent's totals: ``(size, usage, items)`` --
        nothing but the entry itself for a hard link met before."""
        if self.hardlink:
            return 0, 0, 1
        return self.size, self.usage, self.items + 1

    def names(self) -> list[str]:
        """The names from the scanned directory's child down to this one;
        empty for the scanned directory itself."""
        names: list[str] = []
        node: UsageNode | None = self
        while node is not None and node.parent is not None:
            names.append(node.name)
            node = node.parent
        return names[::-1]

    def find(self, names: list[str]) -> UsageNode | None:
        """The node *names* lead to from this one, as :meth:`names` gave them."""
        node: UsageNode | None = self
        for name in names:
            if node is None or node.children is None:
                return None
            node = next((child for child in node.children if child.name == name), None)
        return node


class UsageJob(Job):
    """A walk under way, as the window's status line shows it: the directory
    being read now, and what has been met so far."""

    def __init__(self) -> None:
        super().__init__()
        self.current = ""
        self.items = 0
        self.size = 0
        self.usage = 0
        self.errors = 0


def _usage_of(st: Any) -> int:
    blocks = getattr(st, "st_blocks", None)
    return blocks * 512 if blocks is not None else st.st_size


def _children(where: Any) -> list[tuple[str, Any]]:
    """*where*'s names, each with its ``lstat`` or the error that stopped it."""
    if isinstance(where, (str, os.PathLike)):
        found: list[tuple[str, Any]] = []
        with os.scandir(where) as entries:
            for entry in entries:
                try:
                    found.append((entry.name, entry.stat(follow_symlinks=False)))
                except OSError as error:
                    found.append((entry.name, error))
        return found
    from navigator.lib.drives import drive_of

    return drive_of(where).children(where)


def _lstat(where: Any) -> Any:
    if isinstance(where, (str, os.PathLike)):
        return os.lstat(where)
    from navigator.lib.drives import drive_of

    return drive_of(where).lstat(where)


def _join(where: Any, name: str) -> Any:
    return os.path.join(where, name) if isinstance(where, str) else where / name


def scan(location: Any, job: Any = None, *, one_filesystem: bool = True) -> UsageNode | None:
    """Everything under *location* -- a :class:`~pathlib.Path`, or a
    :class:`~navigator.lib.drives.Location` on any drive -- as a tree of
    :class:`UsageNode`, its totals added up; None if *job* was stopped.

    Raises the ``OSError`` that keeps *location* itself from being read.
    *job*, if given, is anything with ``stopped``; a :class:`UsageJob` has
    its counters kept up as the walk goes.
    """
    counter = job if isinstance(job, UsageJob) else None
    if isinstance(location, os.PathLike):
        location = os.fspath(location)
    if not isinstance(location, str) and getattr(location, "is_local", False):
        location = os.fspath(location.local)
    top = _lstat(location)
    root = UsageNode(os.path.basename(location) if isinstance(location, str) else location.name,
                     is_dir=True, size=top.st_size, usage=_usage_of(top))
    device = top.st_dev
    seen: set[tuple[int, int]] = set()
    directories: list[UsageNode] = []
    pending: list[tuple[UsageNode, Any]] = [(root, location)]
    # The first listing's failure is the caller's to hear about; any deeper one only flags its directory.
    first = True
    while pending:
        if job is not None and job.stopped:
            return None
        node, where = pending.pop()
        directories.append(node)
        if counter is not None:
            counter.current = str(where)
        try:
            children = _children(where)
        except OSError:
            if first:
                raise
            node.unreadable = True
            if counter is not None:
                counter.errors += 1
            continue
        first = False
        for name, st in children:
            if isinstance(st, OSError):
                if counter is not None:
                    counter.errors += 1
                continue
            mode = st.st_mode
            child = UsageNode(name, is_dir=stat.S_ISDIR(mode), is_link=stat.S_ISLNK(mode),
                              size=st.st_size, usage=_usage_of(st), parent=node)
            node.children.append(child)  # type: ignore[union-attr]
            if child.is_dir:
                if one_filesystem and st.st_dev != device:
                    child.other_fs = True
                else:
                    pending.append((child, _join(where, name)))
            elif getattr(st, "st_nlink", 1) > 1 and st.st_ino:
                key = (st.st_dev, st.st_ino)
                if key in seen:
                    child.hardlink = True
                else:
                    seen.add(key)
            if counter is not None:
                counter.items += 1
                if not child.hardlink:
                    counter.size += child.size
                    counter.usage += child.usage
    # Each directory came out of the stack after its parent, so backwards
    # every one is complete before what holds it is added up.
    for node in reversed(directories):
        for child in node.children or ():
            size, usage, items = child.counted()
            node.size += size
            node.usage += usage
            node.items += items
    return root


def remove(node: UsageNode) -> None:
    """*node* taken out of its parent, and what it counted for taken off
    every total above it."""
    parent = node.parent
    if parent is None or parent.children is None or node not in parent.children:
        return
    parent.children.remove(node)
    size, usage, items = node.counted()
    above: UsageNode | None = parent
    while above is not None:
        above.size -= size
        above.usage -= usage
        above.items -= items
        above = above.parent
    node.parent = None


def ordered(node: UsageNode, by: str = "size", descending: bool = True,
            apparent: bool = False) -> list[UsageNode]:
    """*node*'s children sorted *by* ``"size"`` (the size shown: apparent or
    on the disk), ``"name"`` or ``"items"``, largest -- or, by name, A --
    first unless not *descending*.  Directories are not put first: the point
    is what is biggest, whichever it is.  A tie goes by name."""
    children = list(node.children or ())
    children.sort(key=lambda child: child.name.casefold())
    if by == "name":
        children.sort(key=lambda child: child.name.casefold(), reverse=not descending)
    elif by == "items":
        children.sort(key=lambda child: child.items, reverse=descending)
    else:
        children.sort(key=lambda child: child.amount(apparent), reverse=descending)
    return children


def location_of(root: Any, node: UsageNode) -> Any:
    """Where *node* is, for a scan started at *root* (a ``Path`` or a ``Location``)."""
    where = root
    for name in node.names():
        where = where / name
    return where


def walk(node: UsageNode) -> Iterator[UsageNode]:
    """*node* and everything under it."""
    pending = [node]
    while pending:
        each = pending.pop()
        yield each
        pending.extend(each.children or ())


__all__ = ["SORTS", "UsageJob", "UsageNode", "location_of", "ordered", "remove", "scan", "walk"]
