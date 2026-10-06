"""Which files one panel has that the other lacks: DN's ``CM_CompareDirs``.

A file *matches* when the other panel lists a file of the same name that
passes every check asked for -- the size the same, this one no newer, the
same permissions, the same bytes.  So *Select* tags, on each side, what is
missing from the other or newer than its copy there: what a copy across
would bring up to date.  Directories are never compared, and never tagged.

``TFilesCollection.Compare`` with ``SortMode`` 5 and up, read for POSIX:

- **Names match exactly**, case and all, as two files differing in case are
  two files here.
- **Time is to the second**: DOS kept two, and a file copied without its
  time kept, or across file systems, is not newer for a fraction.
- **Attributes are the permission bits**, what the panel's attribute column
  shows where DN's showed the four DOS ones.
"""

from __future__ import annotations

import filecmp
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class CompareRequest:
    """What *Compare directories* asked: ``dlgCompareDirs``' boxes."""

    size: bool = True
    time: bool = True
    attributes: bool = False
    contents: bool = False
    #: *Select* (True) tags what differs, after untagging everything; *Unselect*
    #: (False) only untags what differs.
    select: bool = True


def differing(mine: Iterable[Any], theirs: Iterable[Any], request: CompareRequest,
              here: Path | None = None, there: Path | None = None, job: Any = None) -> set[str] | None:
    """The names of the files in *mine* with no match in *theirs*.

    *here* and *there* are the two directories, needed only to compare
    contents, which reads both files (``CompareFiles``); a *job* stopped
    meanwhile ends it with None.
    """
    others = {entry.name: entry for entry in theirs if not entry.is_dir}
    found: set[str] = set()
    for entry in mine:
        if entry.is_dir:
            continue
        if job is not None and job.stopped:
            return None
        other = others.get(entry.name)
        if other is None or not _matches(entry, other, request, here, there):
            found.add(entry.name)
    return found


def _matches(entry: Any, other: Any, request: CompareRequest,
             here: Path | None, there: Path | None) -> bool:
    if request.size and entry.size != other.size:
        return False
    if request.time and int(entry.mtime) > int(other.mtime):
        return False
    if request.attributes and stat.S_IMODE(entry.mode) != stat.S_IMODE(other.mode):
        return False
    if request.contents:
        if here is None or there is None:
            raise ValueError("comparing contents needs both directories")
        try:
            return filecmp.cmp(here / entry.name, there / other.name, shallow=False)
        except OSError:
            return False  # one that cannot be read is not shown to be the same
    return True


def tagged(marked: frozenset[str], found: set[str], request: CompareRequest) -> frozenset[str]:
    """A panel's tags once compared: *Select* tags exactly what was *found*,
    *Unselect* takes it out of what was tagged."""
    if request.select:
        return frozenset(found)
    return marked - found
