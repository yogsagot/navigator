"""File > Links > Show hard links: every name a file has, found by walking its file system.

A departure -- DOS had no hard links, so DOS Navigator never had to ask --
and one with no cheap answer: the kernel keeps how many names a file has
(``st_nlink``), not where they are.  So the file system the file lives on is
walked from its mount point (:func:`navigator.lib.file_ops.filefind.mount_point`)
for directory entries with the same inode:

- **one file system only**: a hard link cannot leave it, so a directory on
  another device is not entered (nor is a link to a directory followed);
- **hidden names too**, whatever the panel hides: they are names all the same;
- **cheap**: ``os.DirEntry.inode()`` comes with the directory read, so only
  an entry with the right number is ``lstat``-ed to check its device;
- **stopping early**, once ``st_nlink`` names are found -- often long before
  the walk would end.

An unreadable directory is passed over, so fewer names than ``st_nlink`` may
come back; so may a name only reachable under another mount of the same file
system (a bind mount).  The caller says so.  Touches only the file system:
a thread runs it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from navigator.lib.file_ops.filefind import FindJob, mount_point


class HardLinksJob(FindJob):
    """A search for a file's names: ``found`` the paths so far, ``directory``
    where it is looking, ``wanted`` how many there are to find."""

    def __init__(self) -> None:
        super().__init__()
        self.wanted = 0


@dataclass
class Names:
    """What :func:`find_names` found: every name, the file's own first, and
    how many the file has (``st_nlink`` when the walk began)."""

    paths: list[Path]
    count: int

    @property
    def complete(self) -> bool:
        return len(self.paths) >= self.count


def find_names(path: Path, job: HardLinksJob, *, follow: bool = True, root: Path | None = None) -> Names:
    """Every name of the file at *path* on its file system, *path* first.

    *follow* reads a symbolic link at *path* as its target's names (as the
    panel's *Links* column counts them); otherwise the link's own.  *root*
    is where the walk begins, the file system's mount point by default.  Raises
    the ``OSError`` of a *path* that cannot be read.  Ends early when *job*
    is stopped."""
    path = Path(os.path.abspath(path))
    info = path.stat() if follow else path.lstat()
    if follow and path.is_symlink():
        path = Path(os.path.realpath(path))
    wanted = (info.st_dev, info.st_ino)
    job.wanted = info.st_nlink
    found: list[Path] = [path]
    job.found = found
    if info.st_nlink <= 1:
        return Names(found, info.st_nlink)
    pending = [root if root is not None else mount_point(path.parent)]
    while pending and len(found) < info.st_nlink:
        if job.stopped:
            break
        directory = pending.pop()
        job.directory = str(directory)
        try:
            scan = os.scandir(directory)
        except OSError:
            continue
        subdirectories = []
        with scan:
            for item in scan:
                if job.stopped:
                    break
                try:
                    if item.inode() == info.st_ino:
                        own = item.stat(follow_symlinks=False)
                        if (own.st_dev, own.st_ino) == wanted:
                            name = Path(item.path)
                            if name != path:
                                found.append(name)
                                if len(found) >= info.st_nlink:
                                    break
                            continue
                    if item.is_dir(follow_symlinks=False):
                        subdirectories.append(Path(item.path))
                except OSError:
                    continue
        # A directory on another device is a mount point: not entered.
        for place in reversed(sorted(subdirectories)):
            try:
                if place.lstat().st_dev == info.st_dev:
                    pending.append(place)
            except OSError:
                continue
    return Names(found, info.st_nlink)


__all__ = ["HardLinksJob", "Names", "find_names"]
