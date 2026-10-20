"""Alt+F7: finding files -- DOS Navigator's ``FindFile`` and ``FindFiles`` (FILEFIND.PAS).

What is found goes into the active panel as a *Find:* listing
(``TFindDrive``, :class:`FindListing`): the panel shows the entries found
anywhere, each knowing its own directory, sorted and masked as the panel
sorts and masks, under ``..`` that goes back to where the panel was.

**What matches** (``SearchData``): a name the *file mask* lets through
(:func:`navigator.lib.appearance.filetypes.in_filter`, so ``*.c;*.h`` and ``-`` work as in a
panel), passing *Advanced search*'s dates, sizes and kinds if it is ticked,
and holding the *text to find* if there is one -- a directory then never
matches.  A directory is walked into with *Recursive search*, whatever its
name; never through a symbolic link, and never onto another file system
when the scope is a disk.

**The scope**, read for POSIX: *Current directory* is the active panel's;
*Entire disk* is the file system it is on, from where that is mounted -- as
DN's was the current drive's root -- not crossing into what is mounted
inside it; *All drives* is every file system ``/`` and the drives under
``/mnt``, ``/media`` and ``/run/media`` hold, each one alone, so ``/proc``
and ``/sys`` are never walked.

Departures: the dialog opens on *Recursive search* and *Current directory*,
where DN's record started all zeros -- a one-level look at the root;
*Advanced search*'s dates are ``YYYY-MM-DD [HH:MM]`` rather than the
country's format, and its four kinds are POSIX's -- executable, symbolic
link, hidden (a dot-file) and read-only -- where DN's were the DOS
attributes; names are matched case and all, as everywhere in a panel.
"""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from navigator.lib.appearance import filetypes
from navigator.lib.system.job import Job

#: *Scope*'s three, in the dialog's order.
SCOPES = ("disk", "directory", "drives")

#: *Advanced search*'s kinds, in the dialog's order.
KINDS = ("executable", "symlink", "hidden", "read_only")

#: How much of a file is read at a time looking for the text.
CHUNK = 1 << 16


@dataclass(frozen=True)
class Advanced:
    """``AdvanceSearchData``: limits a match has to be within."""

    after: float | None = None
    before: float | None = None
    greater: int | None = None
    less: int | None = None
    kinds: frozenset[str] = frozenset()


@dataclass(frozen=True)
class FindRequest:
    """``TFindRec``: what *Find File* asked for."""

    mask: str = filetypes.ALL_FILES
    text: str = ""
    advanced: bool = False
    case: bool = False
    recursive: bool = True
    words: bool = False
    scope: str = "directory"
    limits: Advanced = Advanced()
    #: Whether a directory may be a match; *Directory Branch* lists files alone.
    directories: bool = True


def parse_time(text: str) -> float | None:
    """``ParseTime``: ``YYYY-MM-DD`` or ``YYYY-MM-DD HH:MM`` as a timestamp, or None."""
    text = " ".join(text.split())
    for shape in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, shape).timestamp()
        except ValueError:
            continue
    return None


def parse_size(text: str) -> int | None:
    """A size in bytes, or None for an empty or unreadable one (DN's ``StoI`` 0)."""
    text = text.strip()
    if not text.isdigit():
        return None
    return int(text) or None


def text_pattern(text: str, *, case: bool, words: bool) -> re.Pattern[bytes] | None:
    """What a file has to hold, as ``SearchFileStr`` looked for it; None for no text."""
    if not text:
        return None
    body = re.escape(text.encode("utf-8", "surrogateescape"))
    if words:
        body = rb"(?<![\w])" + body + rb"(?![\w])"
    return re.compile(body, 0 if case else re.IGNORECASE)


def holds(path: str, pattern: re.Pattern[bytes], job: Any = None) -> bool:
    """Whether the file at *path* holds *pattern*: read a chunk at a time,
    each overlapping the last by as much as a match could span."""
    overlap = max(0, len(pattern.pattern) * 4)
    tail = b""
    try:
        with open(path, "rb") as file:
            while True:
                if job is not None and job.stopped:
                    return False
                chunk = file.read(CHUNK)
                if not chunk:
                    return False
                if pattern.search(tail + chunk):
                    return True
                tail = (tail + chunk)[-overlap:] if overlap else b""
    except OSError:
        return False


class FindJob(Job):
    """A search under way: what it has found, and where it is looking."""

    def __init__(self) -> None:
        super().__init__()
        self.found: list[Any] = []
        self.directory = ""


@dataclass
class FindListing:
    """A panel's *Find:* listing (``TFindDrive``): the entries, and what to go back to."""

    title: str
    origin: Path
    entries: list[Any] = field(default_factory=list)
    #: While the search is still adding to *entries*: the panel shows them as
    #: they are, rather than asking the file system about each again.
    live: bool = False
    #: The entry the cursor was on when the search began, to go back to.
    return_to: str | None = None


def roots(start: Path, scope: str, mounts: Iterable[Path] = ()) -> list[Path]:
    """Where a search of *scope* begins, from *start*."""
    if scope == "directory":
        return [start]
    if scope == "disk":
        return [mount_point(start)]
    found = [Path("/")]
    for place in mounts:
        if place not in found:
            found.append(place)
    return found


def mount_point(path: Path) -> Path:
    """The directory *path*'s file system is mounted on."""
    path = path.resolve()
    try:
        device = path.stat().st_dev
    except OSError:
        return path
    while path != path.parent:
        try:
            if path.parent.stat().st_dev != device:
                break
        except OSError:
            break
        path = path.parent
    return path


def _passes(name: str, info: os.stat_result, is_link: bool, limits: Advanced) -> bool:
    if limits.after is not None and info.st_mtime < limits.after:
        return False
    if limits.before is not None and info.st_mtime > limits.before:
        return False
    is_dir = stat.S_ISDIR(info.st_mode)
    size = 0 if is_dir else info.st_size
    if limits.greater is not None and size < limits.greater:
        return False
    if limits.less is not None and size > limits.less:
        return False
    if limits.kinds:
        kinds = set()
        if not is_dir and stat.S_ISREG(info.st_mode) and info.st_mode & 0o111:
            kinds.add("executable")
        if is_link:
            kinds.add("symlink")
        if name.startswith("."):
            kinds.add("hidden")
        if not info.st_mode & stat.S_IWUSR:
            kinds.add("read_only")
        if not kinds & limits.kinds:
            return False
    return True


def search(request: FindRequest, start: Path, make_entry: Any, job: FindJob,
           *, show_hidden: bool = True, mounts: Iterable[Path] = ()) -> list[Any]:
    """Walk the scope, appending to ``job.found`` every match, as *make_entry*
    makes it from ``(directory, os.DirEntry, stat)``.  Ends early when *job*
    is stopped.  Touches only the file system: a thread runs it.
    """
    pattern = text_pattern(request.text, case=request.case, words=request.words)
    limits = request.limits if request.advanced else Advanced()
    if not isinstance(start, (str, os.PathLike)) and not start.is_local:
        return _search_drive(request, start, job, pattern, limits, show_hidden)
    if not isinstance(start, (str, os.PathLike)):
        start = start.local
    one_device = request.scope != "directory"
    seen: set[tuple[int, int]] = set()
    for root in roots(start, request.scope, mounts):
        try:
            device = root.stat().st_dev
        except OSError:
            continue
        pending = [root]
        while pending:
            if job.stopped:
                return job.found
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
                        return job.found
                    if not show_hidden and item.name.startswith("."):
                        continue
                    try:
                        is_link = item.is_symlink()
                        info = item.stat() if not is_link else _stat_or_lstat(item)
                        is_dir = item.is_dir(follow_symlinks=False)
                    except OSError:
                        continue
                    if is_dir and request.recursive:
                        own = item.stat(follow_symlinks=False)
                        key = (own.st_dev, own.st_ino)
                        if key not in seen and (not one_device or own.st_dev == device):
                            seen.add(key)
                            subdirectories.append(Path(item.path))
                    if is_dir and not request.directories:
                        continue
                    if not filetypes.in_filter(item.name, request.mask):
                        continue
                    if not _passes(item.name, info, is_link, limits):
                        continue
                    if pattern is not None:
                        if stat.S_ISDIR(info.st_mode) or not holds(item.path, pattern, job):
                            continue
                    job.found.append(make_entry(directory, item, info))
            pending.extend(reversed(sorted(subdirectories)))
    return job.found


def _search_drive(request: FindRequest, start: Any, job: FindJob, pattern: Any, limits: Advanced,
                  show_hidden: bool) -> list[Any]:
    """:func:`search` on a drive other than the disk: the same walk, each
    directory listed by its drive (``Drive.children``), a file's text read
    through it.  Only *start* and below -- or the drive's top, for *disk*
    and *all drives*: it has no mounts of its own.  Links are not followed."""
    from pathlib import PurePosixPath

    from navigator.lib.drives import Location, drive_of
    from navigator.lib.drives.listing import DirEntry

    if request.scope != "directory":
        start = Location(start.site, PurePosixPath("/"), start.outer)
    pending = [start]
    while pending:
        if job.stopped:
            return job.found
        directory = pending.pop()
        job.directory = str(directory)
        try:
            drive = drive_of(directory)
            children = drive.children(directory)
        except OSError:
            continue
        subdirectories = []
        for name, info in children:
            if job.stopped:
                return job.found
            if isinstance(info, OSError) or (not show_hidden and name.startswith(".")):
                continue
            is_link = stat.S_ISLNK(info.st_mode)
            is_dir = stat.S_ISDIR(info.st_mode)
            if is_dir and request.recursive:
                subdirectories.append(directory / name)
            if is_dir and not request.directories:
                continue
            if not filetypes.in_filter(name, request.mask):
                continue
            if not _passes(name, info, is_link, limits):
                continue
            if pattern is not None:
                if is_dir or not holds_on_drive(directory / name, pattern, job):
                    continue
            job.found.append(DirEntry(name, is_dir, 0 if is_dir else info.st_size, info.st_mode, info.st_mtime,
                                      is_link, directory=directory))
        pending.extend(reversed(sorted(subdirectories, key=lambda place: place.name)))
    return job.found


def holds_on_drive(location: Any, pattern: re.Pattern[bytes], job: Any = None) -> bool:
    """:func:`holds` for a file on another drive, read through it."""
    from navigator.lib.drives import drive_of

    overlap = max(0, len(pattern.pattern) * 4)
    tail = b""
    try:
        with drive_of(location).open_read(location) as file:
            while True:
                if job is not None and job.stopped:
                    return False
                chunk = file.read(CHUNK)
                if not chunk:
                    return False
                if pattern.search(tail + chunk):
                    return True
                tail = (tail + chunk)[-overlap:] if overlap else b""
    except OSError:
        return False


def read_list_on_drive(list_file: Any, here: Any) -> list[Any]:
    """:func:`read_list` for a list file on another drive, naming that drive's
    files: relative to *here* there, ``/`` its top, a mask matched against a
    directory's listing.  ``~`` means nothing there, and is a name.  A thread
    runs it; raises ``OSError`` if the list cannot be read."""
    import fnmatch
    import posixpath
    from pathlib import PurePosixPath

    from navigator.lib.drives import drive_of
    from navigator.lib.drives.listing import DirEntry

    drive = drive_of(list_file)
    with drive.open_read(list_file) as stream:
        text = stream.read().decode("utf-8", "surrogateescape")
    found: list[Any] = []
    seen: set[str] = set()
    for line in text.splitlines():
        name = line.strip()
        if not name:
            continue
        path = name if name.startswith("/") else posixpath.join(str(here.path), name)
        path = posixpath.normpath(path)
        place = here.__class__(here.site, PurePosixPath(path), here.outer)
        if any(char in place.name for char in "*?["):
            try:
                names = [child for child, _ in drive.children(place.parent)]
            except OSError:
                continue
            places = [place.parent / child for child in sorted(names) if fnmatch.fnmatchcase(child, place.name)]
        else:
            places = [place]
        for each in places:
            key = str(each.path)
            if each.name in (".", "..", "") or key in seen:
                continue
            try:
                own = drive.lstat(each)
                info = drive.stat(each) if stat.S_ISLNK(own.st_mode) else own
            except OSError:
                continue
            seen.add(key)
            is_dir = stat.S_ISDIR(info.st_mode)
            found.append(DirEntry(each.name, is_dir, 0 if is_dir else info.st_size, info.st_mode, info.st_mtime,
                                  stat.S_ISLNK(own.st_mode), directory=each.parent))
    return found


def _stat_or_lstat(item: os.DirEntry[str]) -> os.stat_result:
    try:
        return item.stat()
    except OSError:
        return item.stat(follow_symlinks=False)


def read_list(list_file: Path, here: Path, make_entry: Any) -> list[Any]:
    """Alt+V: the files a list file names, as DN's ``ReadList`` read them.

    A line each, blanks round it dropped; relative to *here*, the panel's
    directory, as ``FExpand`` read it, ``~`` a home; a line with ``*``, ``?``
    or ``[`` a mask, every file it matches.  A name not there is passed
    over, ``.`` and ``..`` too, and a file named twice is listed once.
    *make_entry* makes the entry for a path that is there, or None.  A
    departure: DN cut a line at its first blank, which no 8.3 name had; a
    POSIX name may, so the whole line is the name.  Raises ``OSError`` if
    the list cannot be read.  A thread runs it.
    """
    import glob

    text = Path(list_file).read_text(encoding="utf-8", errors="surrogateescape")
    found: list[Any] = []
    seen: set[str] = set()
    for line in text.splitlines():
        name = line.strip()
        if not name:
            continue
        path = Path(name).expanduser()
        if not path.is_absolute():
            path = Path(here) / path
        if glob.has_magic(str(path)):
            paths = [Path(match) for match in sorted(glob.glob(str(path)))]
        else:
            paths = [path]
        for each in paths:
            if each.name in (".", ".."):
                continue
            key = os.path.normpath(str(each))
            if key in seen:
                continue
            entry = make_entry(Path(key))
            if entry is not None:
                seen.add(key)
                found.append(entry)
    return found
