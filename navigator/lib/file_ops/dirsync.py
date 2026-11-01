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

What Total Commander's window has besides, kept in ``navigator.ini``'s
``[synchronize]`` and handed to :func:`walk` as :class:`SyncOptions`:

- **Times within a tolerance are the same** (``same_time``): two seconds by
  default, as FAT keeps them, a minute for an FTP listing, and optionally an
  exact hour apart, as a daylight-saving change leaves them.
- **A file mask** (:class:`Mask`): a panel filter's patterns, a ``/`` ending
  one that names directories, which are then neither listed nor walked.
  While it holds back any file, a directory on one side alone is walked
  into, its files rows, so that copying it does not bring what it holds back.
- **Asymmetric**: the right side is to become a copy of the left -- what is
  on the right alone is deleted, and a pair that differs copied right,
  whichever side is newer (:attr:`SyncRow.mirror`).
"""

from __future__ import annotations

import stat
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any

from navigator.lib.appearance.filetypes import in_filter, patterns
from navigator.lib.file_ops.dircompare import CompareRequest, same_file, same_time
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


#: The *Show* boxes' statuses, a bit each: on the left alone, on the right
#: alone, different (conflicts with them), the same.
SHOW_GROUPS: tuple[tuple[str, ...], ...] = ((LEFT_ONLY,), (RIGHT_ONLY,), (DIFFERS, CONFLICT), (SAME,))
#: What the window shows at first: everything but the same.
SHOW_DEFAULT = 0b0111

#: ``[synchronize] times``' choices, as seconds of tolerance.
TOLERANCES = {"exact": 0, "fat": 2, "minute": 60}


def shown(rows: list[SyncRow], show: int) -> list[SyncRow]:
    """The rows whose status a bit of *show* (:data:`SHOW_GROUPS`) lets through."""
    statuses = {status for bit, group in enumerate(SHOW_GROUPS) if show & (1 << bit) for status in group}
    return [row for row in rows if row.status in statuses]


class Mask:
    """The *File mask*: a panel filter's patterns (``in_filter``), ``;``
    between them, ``-`` before one that excludes.  One ending in ``/`` is a
    directory's, the rest are files' (and links'); a side with only
    exclusions starts from everything, so ``-*.bak;-.git/`` is all but
    backups and ``.git``.  Names are matched, not paths."""

    def __init__(self, text: str = "") -> None:
        self.text = text
        files: list[str] = []
        dirs: list[str] = []
        for pattern in patterns(text.replace(" ", "")):
            if pattern.endswith("/"):
                dirs.append(pattern.rstrip("/"))
            else:
                files.append(pattern)
        self._files, self._dirs = self._from_all(files), self._from_all(dirs)
        #: Whether some file is held back: a directory on one side alone is
        #: then walked into, not copied or deleted whole.
        self.restricts_files = self._files not in ("", "*")

    @staticmethod
    def _from_all(found: list[str]) -> str:
        if found and all(pattern.startswith("-") for pattern in found):
            found = ["*", *found]
        return ";".join(found)

    def files(self, name: str) -> bool:
        return in_filter(name, self._files)

    def dirs(self, name: str) -> bool:
        return in_filter(name, self._dirs)


@dataclass(frozen=True)
class SyncOptions:
    """What *Synchronize options* answered (``[synchronize]``)."""

    #: The *File mask* (:class:`Mask`); empty takes everything.
    mask: str = ""
    #: Seconds two times may be apart and still be the same.
    tolerance: int = TOLERANCES["fat"]
    #: Times exactly an hour apart (within *tolerance*) are the same too.
    hour_shift: bool = False
    #: The right side is to become a copy of the left.
    asymmetric: bool = False


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
    #: Compared *Asymmetric*: the right side is to become a copy of the left.
    mirror: bool = False
    #: In a directory on one side alone, walked into under a file mask: a
    #: copy across makes the directory first (:attr:`SyncPlan.directories`).
    lonely_parent: bool = False

    @property
    def allowed(self) -> tuple[str, ...]:
        return ALLOWED[self.status]

    @property
    def default_action(self) -> str:
        if self.mirror and self.status == RIGHT_ONLY:
            return DELETE
        if self.status == DIFFERS:
            if self.mirror:
                return COPY_RIGHT
            return {"left": COPY_RIGHT, "right": COPY_LEFT}.get(self.newer or "", SKIP)
        return self.allowed[0]

    @property
    def is_dir(self) -> bool:
        side = self.left or self.right
        return side is not None and side.kind == "dir"


def make_row(path: PurePosixPath, left: Side | None, right: Side | None, status: str,
             error: str = "", options: SyncOptions | None = None, lonely_parent: bool = False) -> SyncRow:
    """A row with its default action; *options* say how near two times are
    the same, and whether the right is a mirror."""
    options = options or SyncOptions()
    newer = None
    if left is not None and right is not None and not same_time(left.mtime, right.mtime, options.tolerance,
                                                                 options.hour_shift):
        newer = "left" if left.mtime > right.mtime else "right"
    row = SyncRow(path, left, right, status, newer, SKIP, error, options.asymmetric, lonely_parent)
    return with_action(row, "default")


@dataclass(frozen=True)
class SyncPlan:
    """What :func:`plan` makes of the rows: the copies, each ``(source,
    target)``, and the deletes; and the directories the copies' targets
    need made first, which only a file mask leaves missing."""

    pairs: list[tuple[Any, Any]]
    deletes: list[Any]
    directories: list[Any] = field(default_factory=list)


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
         show_hidden: bool = True, options: SyncOptions | None = None) -> list[SyncRow]:
    """Every path below *left* and *right* (two directories, on any drives),
    each a :class:`SyncRow` -- the ones the same included, which the window
    hides until asked -- but what *options*' mask holds back.  Raises
    ``OSError`` when either directory itself cannot be listed,
    :class:`Stopped` when *job* is stopped."""
    from navigator.lib.drives import Location, drive_of

    options = options or SyncOptions()
    mask = Mask(options.mask)
    left, right = Location.of(left), Location.of(right)
    left_drive, right_drive = drive_of(left), drive_of(right)
    rows: list[SyncRow] = []
    # Each directory to list, and which sides have it: a directory on one
    # side alone is walked only while the mask holds back some file.
    pending: list[tuple[PurePosixPath, bool, bool]] = [(PurePosixPath(), True, True)]
    while pending:
        relative, on_left, on_right = pending.pop()
        here, there = below(left, relative), below(right, relative)
        if job is not None:
            if job.stopped:
                raise Stopped
            job.directory = str(relative) if relative.parts else ""
        try:
            mine = _listing(left_drive, here, show_hidden, mask) if on_left else {}
            theirs = _listing(right_drive, there, show_hidden, mask) if on_right else {}
        except OSError as error:
            if not relative.parts:
                raise
            from navigator.lib.file_ops.filecopy import error_message

            directory = Side("dir", 0, 0, stat.S_IFDIR)
            rows.append(make_row(relative, directory if on_left else None, directory if on_right else None,
                                 CONFLICT, error_message(error), options))
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
                                     CONFLICT, error_message(failed), options))  # type: ignore[arg-type]
                continue
            a = None if one is None else Side.of(one)
            b = None if two is None else Side.of(two)
            lonely = a if b is None else b if a is None else None
            if lonely is not None and lonely.kind == "dir" and mask.restricts_files:
                subdirectories.append((path, b is None, a is None))
                continue
            if b is None:
                status = LEFT_ONLY
            elif a is None:
                status = RIGHT_ONLY
            elif a.kind != b.kind or a.kind == "other":
                status = CONFLICT
            elif a.kind == "dir":
                subdirectories.append((path, True, True))
                continue
            elif a.kind == "link":
                status = SAME if _same_link(left_drive, here / name, right_drive, there / name) else DIFFERS
            else:
                status = SAME if same_file(a, b, request, *_contents(here / name, there / name, request),
                                           tolerance=options.tolerance, hour_shift=options.hour_shift) \
                    else DIFFERS
            rows.append(make_row(path, a, b, status, options=options, lonely_parent=not (on_left and on_right)))
            if job is not None and status != SAME:
                job.found += 1
        pending.extend(reversed(subdirectories))
    rows.sort(key=lambda row: row.path.parts)
    return rows


def below(root: Any, relative: PurePosixPath) -> Any:
    """*relative*'s place under *root*, a location or a path: joined whole,
    as both take a name with slashes in it."""
    return root / str(relative) if relative.parts else root


def _listing(drive: Any, place: Any, show_hidden: bool, mask: Mask) -> dict[str, Any]:
    return {name: info for name, info in drive.children(place)
            if (show_hidden or not name.startswith(".")) and _passes(mask, name, info)}


def _passes(mask: Mask, name: str, info: Any) -> bool:
    """Whether *mask* lets *name* through: a directory by its directory
    patterns, anything else by its files'; one that could not be read is
    kept, to be said."""
    if isinstance(info, OSError):
        return True
    return mask.dirs(name) if stat.S_ISDIR(info.st_mode) else mask.files(name)


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
    replaces or makes.  Its directory is there -- a row in a directory on one
    side alone is never listed apart from it -- but under a file mask, which
    walks into one: then the directory is in the plan's *directories*."""
    from navigator.lib.file_ops.filecopy import shown

    # Below the shown places, not their locations: a local path joined as a
    # path is what the copier is handed anyway, and a row a time is many.
    left, right = shown(left), shown(right)
    pairs: list[tuple[Any, Any]] = []
    deletes: list[Any] = []
    directories: dict[Any, None] = {}
    for row in rows:
        here, there = below(left, row.path), below(right, row.path)
        if row.action == COPY_RIGHT:
            pairs.append((here, there))
        elif row.action == COPY_LEFT:
            pairs.append((there, here))
        elif row.action == DELETE:
            deletes.append(here if row.left is not None else there)
        if row.lonely_parent and row.action in (COPY_RIGHT, COPY_LEFT):
            directories[below(right if row.action == COPY_RIGHT else left, row.path.parent)] = None
    return SyncPlan(pairs, deletes, list(directories))


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
    return SyncRow(row.path, row.left, row.right, row.status, row.newer, action, row.error, row.mirror,
                   row.lonely_parent)


# -- the tree view ------------------------------------------------------------------

#: A directory's action when the rows beneath it disagree.
MIXED = "mixed"


class DirNode:
    """A directory both sides have, as the window's tree view shows it: its
    subdirectories, its own rows, and what they all come to (:func:`annotate`).

    A directory on one side alone is not one: it is a row, a leaf, as
    :func:`walk` never goes into it -- unless a file mask holds back some
    file, when its files are the rows and it is a directory here too.
    """

    __slots__ = ("path", "parent", "depth", "dirs", "rows", "status", "action", "count", "allowed",
                 "statuses", "actions", "owners")

    def __init__(self, path: PurePosixPath, parent: DirNode | None = None) -> None:
        self.path = path
        self.parent = parent
        self.depth = 0 if parent is None else parent.depth + 1
        self.dirs: dict[str, DirNode] = {}
        self.rows: list[SyncRow] = []
        #: The statuses and actions beneath that are not the same ones', kept
        #: so a parent's roll-up is its children's, not a walk down again.
        self.statuses: frozenset[str] = frozenset()
        self.actions: frozenset[str] = frozenset()
        #: On the root: which directory holds each row, by ``id`` -- what
        #: :func:`replace_rows` finds a changed row's place by.
        self.owners: dict[int, DirNode] = {}
        #: The status the rows beneath share (the same ones aside), or
        #: :data:`DIFFERS` when they do not; :data:`SAME` when all are.
        self.status = SAME
        #: The action they share, or :data:`MIXED`.
        self.action = SKIP
        #: How many rows beneath are not the same.
        self.count = 0
        #: Every action some row beneath allows.
        self.allowed: frozenset[str] = frozenset()

    @property
    def name(self) -> str:
        return self.path.name


def build_tree(rows: list[SyncRow]) -> DirNode:
    """The rows as a tree of the directories both sides have, annotated."""
    root = DirNode(PurePosixPath())
    nodes = {root.path: root}

    def node_for(path: PurePosixPath) -> DirNode:
        node = nodes.get(path)
        if node is None:
            parent = node_for(path.parent)
            node = nodes[path] = DirNode(path, parent)
            parent.dirs[path.name] = node
        return node

    for row in rows:
        node = node_for(row.path.parent)
        node.rows.append(row)
        root.owners[id(row)] = node
    annotate(root)
    return root


def annotate(node: DirNode) -> None:
    """Give *node* and every directory beneath it its roll-up, bottom up."""
    for child in node.dirs.values():
        annotate(child)
    _annotate_one(node)


def replace_rows(root: DirNode, changed: dict[int, SyncRow]) -> None:
    """Put each new row in place of the old one (*changed* maps the old one's
    ``id`` to it) in the tree from :func:`build_tree`, and count again only
    the directories they are in and those above them -- not the whole tree,
    which an action on one row would otherwise rebuild."""
    holding: set[DirNode] = set()
    for old, new in changed.items():
        node = root.owners.pop(old, None)
        if node is not None:
            root.owners[id(new)] = node
            holding.add(node)
    touched: set[DirNode] = set()
    for node in holding:
        node.rows = [changed.get(id(row), row) for row in node.rows]
        while node is not None and node not in touched:
            touched.add(node)
            node = node.parent
    for node in sorted(touched, key=lambda node: -node.depth):
        _annotate_one(node)


def _annotate_one(node: DirNode) -> None:
    """*node*'s roll-up, from its own rows and its children's roll-ups."""
    statuses: set[str] = set()
    actions: set[str] = set()
    allowed: set[str] = set()
    count = 0
    for child in node.dirs.values():
        statuses |= child.statuses
        actions |= child.actions
        allowed |= child.allowed
        count += child.count
    for row in node.rows:
        if row.status == SAME:
            continue
        statuses.add(row.status)
        actions.add(row.action)
        allowed.update(row.allowed)
        count += 1
    node.count = count
    node.allowed = frozenset(allowed)
    node.statuses, node.actions = frozenset(statuses), frozenset(actions)
    node.status = _shared(statuses, SAME, DIFFERS)
    node.action = _shared(actions, SKIP, MIXED)


def _shared(values: set[str], none: str, several: str) -> str:
    """The one value in *values*; *none* when empty, *several* when not one."""
    if not values:
        return none
    return next(iter(values)) if len(values) == 1 else several


def rows_beneath(node: DirNode) -> list[SyncRow]:
    """Every row in *node* and the directories beneath it."""
    found: list[SyncRow] = []
    pending = [node]
    while pending:
        current = pending.pop()
        found.extend(current.rows)
        pending.extend(current.dirs.values())
    return found


__all__ = [
    "MIXED", "DirNode", "annotate", "build_tree", "replace_rows", "rows_beneath",
    "ALLOWED", "CONFLICT", "COPY_LEFT", "COPY_RIGHT", "DELETE", "DIFFERS", "LEFT_ONLY", "RIGHT_ONLY", "SAME",
    "SKIP", "Side", "Summary", "below", "SyncJob", "SyncPlan", "SyncRow", "make_row", "plan", "summary",
    "walk", "with_action", "Mask", "SHOW_DEFAULT", "SHOW_GROUPS", "SyncOptions", "TOLERANCES", "shown",
]
