"""Two directory trees compared, and brought level: *Compare directories*'
*Window, recursive*.

**A departure**: DOS Navigator compared the two panels one level deep and
answered by tagging (``CM_CompareDirs``, :mod:`dircompare`); it had nothing
that walked down both trees, nor anything to act on what differed but the
tags.  This is Total Commander's *Synchronize directories*: every file that
is on one side alone, or differs from its namesake, listed by its path below
the two panels' directories, each with what is to be done with it -- copied
across, one way or the other, deleted, or left -- and the whole done by one
:class:`~navigator.lib.file_ops.filecopy.CopyRequest` and one erase.

The model half, run on a thread (:func:`walk`):

- **Files are compared by the dialog's own checks**, made symmetric
  (:func:`~navigator.lib.file_ops.dircompare.same_file`): a different time is
  a difference whichever side is newer, and the newer side is the one copied
  from by default.
- **A directory on one side alone is one row**, not walked into: copying it
  across copies all of it.
- **Links are not followed**; two are the same when they point at the same
  name.  A file facing a directory, or anything that is neither, is a
  conflict, left alone.
- **Every drive**: each directory is listed by its drive
  (``Drive.children``), as a *Find* on a server is.
"""

from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from navigator.lib.file_ops.dircompare import CompareRequest, same_file
from navigator.lib.system.job import Job, Stopped

#: What a row is: on the left alone, on the right alone, on both and
#: different, on both and the same, or two things that cannot be compared.
LEFT_ONLY, RIGHT_ONLY, DIFFERS, SAME, CONFLICT = "left-only", "right-only", "differs", "same", "conflict"

#: What is to be done with a row: copied to the right, copied to the left,
#: left alone, or deleted from the one side it is on.
COPY_RIGHT, COPY_LEFT, SKIP, DELETE = "right", "left", "skip", "delete"

#: Which actions each status allows, the first of them its default (but for
#: :data:`DIFFERS`, whose default is the newer side's: :attr:`SyncRow.default_action`).
ALLOWED = {
    LEFT_ONLY: (COPY_RIGHT, SKIP, DELETE),
    RIGHT_ONLY: (COPY_LEFT, SKIP, DELETE),
    DIFFERS: (COPY_RIGHT, COPY_LEFT, SKIP),
    SAME: (SKIP,),
    CONFLICT: (SKIP,),
}


class SyncJob(Job):
    """A walk running: the directory in hand, and how many differences so far."""

    def __init__(self) -> None:
        super().__init__()
        self.directory = ""
        self.found = 0


@dataclass(frozen=True)
class Side:
    """One side of a row: what is there, as its ``lstat`` says."""

    kind: str  # "file", "dir", "link" or "other"
    size: int
    mtime: float
    mode: int

    @classmethod
    def of(cls, info: Any) -> Side:
        mode = info.st_mode
        if stat.S_ISDIR(mode):
            kind = "dir"
        elif stat.S_ISLNK(mode):
            kind = "link"
        elif stat.S_ISREG(mode):
            kind = "file"
        else:
            kind = "other"
        return cls(kind, 0 if kind == "dir" else info.st_size, info.st_mtime, mode)


@dataclass(frozen=True)
class SyncRow:
    """One path below the two directories, and what is to be done with it."""

    path: PurePosixPath
    left: Side | None
    right: Side | None
    status: str
    #: ``"left"`` or ``"right"`` for a pair whose times differ, else None.
    newer: str | None = None
    action: str = SKIP
    #: Why a conflict is one, for a directory that could not be listed.
    error: str = ""

    @property
    def allowed(self) -> tuple[str, ...]:
        return ALLOWED[self.status]

    @property
    def default_action(self) -> str:
        if self.status == DIFFERS:
            return {"left": COPY_RIGHT, "right": COPY_LEFT}.get(self.newer or "", SKIP)
        return self.allowed[0]

    @property
    def is_dir(self) -> bool:
        side = self.left or self.right
        return side is not None and side.kind == "dir"


def make_row(path: PurePosixPath, left: Side | None, right: Side | None, status: str,
             error: str = "") -> SyncRow:
    """A row with its default action."""
    newer = None
    if left is not None and right is not None and int(left.mtime) != int(right.mtime):
        newer = "left" if left.mtime > right.mtime else "right"
    row = SyncRow(path, left, right, status, newer, SKIP, error)
    return with_action(row, "default")


@dataclass(frozen=True)
class SyncPlan:
    """What :func:`plan` makes of the rows: the copies, each ``(source,
    target)``, and the deletes."""

    pairs: list[tuple[Any, Any]]
    deletes: list[Any]


@dataclass(frozen=True)
class Summary:
    """What the rows' actions come to, for the window's summary line."""

    right: int = 0
    right_bytes: int = 0
    left: int = 0
    left_bytes: int = 0
    delete: int = 0
    skip: int = 0


def walk(left: Any, right: Any, request: CompareRequest, job: Any = None,
         show_hidden: bool = True) -> list[SyncRow]:
    """Every path below *left* and *right* (two directories, on any drives),
    each a :class:`SyncRow` -- the ones the same included, which the window
    hides until asked.  Raises ``OSError`` when either directory itself
    cannot be listed, :class:`Stopped` when *job* is stopped."""
    from navigator.lib.drives import Location, drive_of

    left, right = Location.of(left), Location.of(right)
    left_drive, right_drive = drive_of(left), drive_of(right)
    rows: list[SyncRow] = []
    pending = [PurePosixPath()]
    while pending:
        relative = pending.pop()
        here, there = below(left, relative), below(right, relative)
        if job is not None:
            if job.stopped:
                raise Stopped
            job.directory = str(relative) if relative.parts else ""
        try:
            mine = _listing(left_drive, here, show_hidden)
            theirs = _listing(right_drive, there, show_hidden)
        except OSError as error:
            if not relative.parts:
                raise
            from navigator.lib.file_ops.filecopy import error_message

            rows.append(make_row(relative, Side("dir", 0, 0, stat.S_IFDIR), Side("dir", 0, 0, stat.S_IFDIR),
                                 CONFLICT, error_message(error)))
            continue
        subdirectories = []
        for name in sorted(mine.keys() | theirs.keys()):
            if job is not None and job.stopped:
                raise Stopped
            path = relative / name
            one, two = mine.get(name), theirs.get(name)
            if isinstance(one, OSError) or isinstance(two, OSError):
                from navigator.lib.file_ops.filecopy import error_message

                failed = one if isinstance(one, OSError) else two
                rows.append(make_row(path, None if isinstance(one, OSError) else _side(one),
                                     None if isinstance(two, OSError) else _side(two),
                                     CONFLICT, error_message(failed)))  # type: ignore[arg-type]
                continue
            a = None if one is None else Side.of(one)
            b = None if two is None else Side.of(two)
            if b is None:
                status = LEFT_ONLY
            elif a is None:
                status = RIGHT_ONLY
            elif a.kind != b.kind or a.kind == "other":
                status = CONFLICT
            elif a.kind == "dir":
                subdirectories.append(path)
                continue
            elif a.kind == "link":
                status = SAME if _same_link(left_drive, here / name, right_drive, there / name) else DIFFERS
            else:
                status = SAME if same_file(a, b, request, *_contents(here / name, there / name, request)) \
                    else DIFFERS
            rows.append(make_row(path, a, b, status))
            if job is not None and status != SAME:
                job.found += 1
        pending.extend(reversed(subdirectories))
    rows.sort(key=lambda row: row.path.parts)
    return rows


def below(root: Any, relative: PurePosixPath) -> Any:
    """*relative*'s place under *root*, a location or a path: joined whole,
    as both take a name with slashes in it."""
    return root / str(relative) if relative.parts else root


def _listing(drive: Any, place: Any, show_hidden: bool) -> dict[str, Any]:
    return {name: info for name, info in drive.children(place) if show_hidden or not name.startswith(".")}


def _side(info: Any) -> Side | None:
    return None if info is None else Side.of(info)


def _same_link(left_drive: Any, a: Any, right_drive: Any, b: Any) -> bool:
    try:
        return left_drive.readlink(a) == right_drive.readlink(b)
    except OSError:
        return False


def _contents(a: Any, b: Any, request: CompareRequest) -> tuple[Any, Any]:
    """The two files as the contents check reads them -- paths on the disk,
    so ``filecmp`` does it there -- or nothing when it is not asked for."""
    if not request.contents:
        return None, None
    from navigator.lib.file_ops.filecopy import shown

    return shown(a), shown(b)


def plan(rows: list[SyncRow], left: Any, right: Any) -> SyncPlan:
    """The copies and deletes the rows' actions ask for, below the
    directories *left* and *right*.  Each copy's target is the very path it
    replaces or makes: its directory is there, as a row in a directory on
    one side alone is never listed apart from it."""
    from navigator.lib.file_ops.filecopy import shown

    # Below the shown places, not their locations: a local path joined as a
    # path is what the copier is handed anyway, and a row a time is many.
    left, right = shown(left), shown(right)
    pairs: list[tuple[Any, Any]] = []
    deletes: list[Any] = []
    for row in rows:
        here, there = below(left, row.path), below(right, row.path)
        if row.action == COPY_RIGHT:
            pairs.append((here, there))
        elif row.action == COPY_LEFT:
            pairs.append((there, here))
        elif row.action == DELETE:
            deletes.append(here if row.left is not None else there)
    return SyncPlan(pairs, deletes)


def summary(rows: list[SyncRow]) -> Summary:
    """How many rows go each way, and how many bytes; how many are deleted
    or left (the rows the same not counted)."""
    counts = {COPY_RIGHT: 0, COPY_LEFT: 0, DELETE: 0, SKIP: 0}
    right_bytes = left_bytes = 0
    for row in rows:
        if row.status == SAME:
            continue
        counts[row.action] += 1
        if row.action == COPY_RIGHT and row.left is not None:
            right_bytes += row.left.size
        elif row.action == COPY_LEFT and row.right is not None:
            left_bytes += row.right.size
    return Summary(counts[COPY_RIGHT], right_bytes, counts[COPY_LEFT], left_bytes, counts[DELETE], counts[SKIP])


def with_action(row: SyncRow, action: str) -> SyncRow:
    """*row* with *action*, or as it is when its status does not allow it;
    ``"default"`` is the status's own."""
    if action == "default":
        action = row.default_action
    if action not in row.allowed or action == row.action:
        return row
    return SyncRow(row.path, row.left, row.right, row.status, row.newer, action, row.error)


__all__ = [
    "ALLOWED", "CONFLICT", "COPY_LEFT", "COPY_RIGHT", "DELETE", "DIFFERS", "LEFT_ONLY", "RIGHT_ONLY", "SAME",
    "SKIP", "Side", "Summary", "below", "SyncJob", "SyncPlan", "SyncRow", "make_row", "plan", "summary",
    "walk", "with_action",
]
