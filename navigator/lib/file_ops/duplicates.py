"""Panel > Find duplicates: files with the same contents, as a panel's listing.

DOS Navigator had no such command -- a departure, asked for.  The files
under the panel's directory that the box's mask and minimum size let in are
narrowed three times, each step reading only what the last left: by size,
then by a quick hash of each file's first and last :data:`CHUNK` bytes, then
by a hash of the whole file.  What is left is shown as a *Find:* listing
whose order is its own (``FindListing.keep_order``): the groups that waste
the most bytes first, each group's files by path, so a group stays together
whatever the panel sorts by.  Nothing is tagged; the panel's own keys tag
the copies and F8 erases them.

Symbolic links are passed over, and a file under two hard-linked names is
one file: erasing either name would free nothing.
"""

from __future__ import annotations

import os
import stat
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from navigator.lib.appearance import filetypes
from navigator.lib.file_ops.checksum import new_hash
from navigator.lib.file_ops.filefind import CHUNK, Advanced, FindJob, FindRequest, search
from navigator.lib.system.job import Stopped


@dataclass(frozen=True)
class DuplicatesRequest:
    """What the *Find duplicates* box asked for."""

    mask: str = filetypes.ALL_FILES
    #: The smallest file looked at, in bytes; the default 1 leaves empty files out.
    min_size: int = 1
    recursive: bool = True


class DuplicatesJob(FindJob):
    """A search under way: :class:`FindJob`'s directory and files found while
    walking, then the file being read and how many are still candidates."""

    def __init__(self) -> None:
        super().__init__()
        #: ``"scan"`` while walking, ``"compare"`` while hashing.
        self.phase = "scan"
        #: Files still possibly duplicates, once the walk is done.
        self.candidates = 0


def find_duplicates(request: DuplicatesRequest, start: Path, job: DuplicatesJob, *,
                    show_hidden: bool = True) -> list[list[Path]]:
    """The groups of identical files under *start*, the most bytes wasted
    first, each group's paths sorted.  Raises :class:`Stopped` if *job* is
    stopped.  Touches only the file system: a thread runs it."""
    find = FindRequest(mask=request.mask, recursive=request.recursive, scope="directory", directories=False,
                       advanced=True, limits=Advanced(greater=max(1, request.min_size)))

    def entry(directory: Path, item: os.DirEntry[str], info: os.stat_result) -> Any:
        return Path(item.path), item.is_symlink(), info

    search(find, Path(start), entry, job, show_hidden=show_hidden)
    if job.stopped:
        raise Stopped
    by_size: dict[int, list[Path]] = defaultdict(list)
    inodes: set[tuple[int, int]] = set()
    # Sorted, so of two hard-linked names the first by path is the one kept.
    for path, is_link, info in sorted(job.found, key=lambda found: found[0]):
        if is_link or not stat.S_ISREG(info.st_mode):
            continue
        inode = (info.st_dev, info.st_ino)
        if inode in inodes:
            continue  # a second name for a file already listed
        inodes.add(inode)
        by_size[info.st_size].append(path)
    job.phase = "compare"
    groups = [(size, paths) for size, paths in by_size.items() if len(paths) > 1]
    job.candidates = sum(len(paths) for _, paths in groups)
    found: list[tuple[int, list[Path]]] = []
    for size, paths in groups:
        for quick in _split(paths, lambda path: quick_hash(path, size, job), job):
            if size <= 2 * CHUNK:
                found.append((size, quick))  # the quick hash read it whole
                continue
            found.extend((size, same) for same in _split(quick, lambda path: full_hash(path, job), job))
    found.sort(key=lambda group: (-group[0] * (len(group[1]) - 1), sorted(group[1])[0]))
    return [sorted(paths) for _, paths in found]


def _split(paths: Iterable[Path], digest: Callable[[Path], bytes | None], job: DuplicatesJob) -> list[list[Path]]:
    """*paths* grouped by *digest*, the groups of one and the unreadable left out."""
    by_digest: dict[bytes, list[Path]] = defaultdict(list)
    for path in paths:
        if job.stopped:
            raise Stopped
        job.directory = str(path)
        value = digest(path)
        if value is None:
            job.candidates -= 1
        else:
            by_digest[value].append(path)
    groups = []
    for same in by_digest.values():
        if len(same) > 1:
            groups.append(same)
        else:
            job.candidates -= 1
    return groups


def quick_hash(path: Path, size: int, job: Any = None) -> bytes | None:
    """A hash of *path*'s first and last :data:`CHUNK` bytes -- all of it, for a
    file of at most twice that -- or None if it cannot be read."""
    digest = new_hash("blake2b")
    try:
        with open(path, "rb") as file:
            digest.update(file.read(CHUNK))
            if size > CHUNK:
                file.seek(max(CHUNK, size - CHUNK))
                digest.update(file.read(CHUNK))
    except OSError:
        return None
    return digest.digest()


def full_hash(path: Path, job: Any = None) -> bytes | None:
    """A hash of the whole of *path*, or None if it cannot be read.  Raises
    :class:`Stopped` between reads once *job* is stopped."""
    digest = new_hash("blake2b")
    try:
        with open(path, "rb") as file:
            while chunk := file.read(CHUNK):
                if job is not None and job.stopped:
                    raise Stopped
                digest.update(chunk)
    except OSError:
        return None
    return digest.digest()
