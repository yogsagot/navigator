"""Alt+F7: finding files -- DOS Navigator's ``FindFile`` and ``FindFiles`` (FILEFIND.PAS).

What is found goes into the active panel as a *Find:* listing
(``TFindDrive``, :class:`FindListing`): the panel shows the entries found
anywhere, each knowing its own directory, sorted and masked as the panel
sorts and masks, under ``..`` that goes back to where the panel was.

**What matches** (``SearchData``): a name the *file mask* lets through
(:func:`navigator.lib.appearance.filetypes.in_filter`, so ``*.c;*.h`` and ``-`` work as in a
panel), passing *Advanced search*'s dates, sizes and kinds if it is ticked,
and holding the *text to find* if there is one -- a directory then never
matches.  With *Regular expression* ticked (not DN's: a departure, asked
for) the text is Python's ``re`` pattern, matched against the file's bytes
whole -- up to :data:`WHOLE_LARGEST`, a larger file passed over, as
*Replace in files* does -- so it may span lines; without, it is the text itself, looked for a
chunk at a time as the viewer's search looks (DN's Find called
``SearchFileStr``): each letter in either case, whatever its alphabet, and
*Whole words* breaking at blanks and punctuation, never inside a letter.  *Replace in files* (:mod:`navigator.lib.file_ops.filereplace`)
walks the same way, through :func:`search`'s *match*.  A directory is walked into with *Recursive search*, whatever its
name; never through a symbolic link, and never onto another file system
when the scope is a disk.  *Current directory* crosses into what is mounted
below it, as ``find`` does, but never into a kernel file system
(:data:`VIRTUAL_KINDS`: ``/proc``, ``/sys``, ``/dev`` ...), whose files are
not the user's and may block when read -- a departure, as DN's drives had
none; a search started inside one walks it, as asked.

**The scope**, read for POSIX: *Current directory* is the active panel's;
*Entire disk* is the file system it is on, from where that is mounted -- as
DN's was the current drive's root -- not crossing into what is mounted
inside it; *All drives* is the panel's own file system, then ``/``, then
every disk file system mounted (:func:`searchable_mounts`, by kind from
``/proc/self/mounts``), each one alone.  Kernel and memory file systems,
images (``squashfs``, CDs) and network mounts are left out unless the panel
is on one: DN skipped its slow drives (floppies and CDs) but never the
current one.  On a server, container or device the two are its ``/``,
less its ``/proc``, ``/sys``, ``/dev`` and ``/run`` (:data:`SYSTEM_PLACES`).  Leaving network mounts out is a departure -- DN searched a
LAN's drives, where here a mount may be a server or a bucket across the
internet, read whole by a text search.

Departures: the dialog opens on *Recursive search* and *Current directory*,
where DN's record started all zeros -- a one-level look at the root;
*Regular expression* with *Case sensitive* off folds ASCII letters only,
as Python's ``re`` does on bytes (plain text folds any alphabet's, through
the viewer's pattern: a user's pattern cannot be rewritten letter by
letter, and decoding would cost Replace in files its byte-exact rewrite);
*Advanced search*'s dates are ``YYYY-MM-DD [HH:MM]`` rather than the
country's format, and its kinds are POSIX's -- executable, symbolic
link, hidden (a dot-file), read-only, and a link pointing nowhere -- where
DN's were the DOS attributes; names are matched case and all, as everywhere in a panel.
"""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from navigator.lib.appearance import filetypes
from navigator.lib.system.job import Job

#: *Scope*'s three, in the dialog's order.
SCOPES = ("disk", "directory", "drives")

#: *Advanced search*'s kinds, in the dialog's order.
KINDS = ("executable", "symlink", "hidden", "read_only", "broken_link")

#: How much of a file is read at a time looking for the text.
CHUNK = 1 << 16

#: The largest file a *Regular expression* looks through: it is held whole,
#: as nothing bounds how far a match may span.  A larger one is passed over,
#: as *Replace in files* passes it (``filereplace.LARGEST`` is this).
WHOLE_LARGEST = 64 << 20


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
    #: *Regular expression*: *text* is a pattern, not the text itself.
    regex: bool = False


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


def text_pattern(text: str, *, case: bool, words: bool, regex: bool = False) -> re.Pattern[bytes] | None:
    """What a file has to hold, as ``SearchFileStr`` looked for it; None for no text.

    Plain text is the viewer's own pattern
    (:func:`navigator.lib.viewer.compile_search`), as DN's Find called the
    viewer's search: each letter in either case, whatever its alphabet.
    With *regex*, *text* is a pattern (``^`` and ``$`` at each line), and
    an invalid one raises ``re.error``; *Case sensitive* off folds its ASCII
    letters only, as ``re`` does on bytes.  *Whole words* breaks where the
    viewer's does (``WORD_BYTES``) either way."""
    from navigator.lib.viewer import WORD_BYTES, compile_search

    if not text:
        return None
    if not regex:
        return compile_search(text, case=case, words=words, encoding="utf-8")[0]
    body = b"(?:" + text.encode("utf-8", "surrogateescape") + b")"
    if words:
        body = rb"(?<![" + WORD_BYTES + rb"])" + body + rb"(?![" + WORD_BYTES + rb"])"
    return re.compile(body, (0 if case else re.IGNORECASE) | re.MULTILINE)


def request_pattern(request: FindRequest) -> re.Pattern[bytes] | None:
    """:func:`text_pattern` for what *request* asks."""
    return text_pattern(request.text, case=request.case, words=request.words, regex=request.regex)


def holds(path: str, pattern: re.Pattern[bytes], job: Any = None, *, whole: bool = False) -> bool:
    """Whether the file at *path* holds *pattern*: read a chunk at a time,
    each overlapping the last by as much as a match could span -- or, for a
    regular expression (*whole*), whose span nothing bounds, gathered whole
    (:func:`_holds`), a file larger than :data:`WHOLE_LARGEST` passed over
    unread.

    Only a regular file is read: opened without blocking (a FIFO with no
    writer would wait for one for good) and checked by what was opened, so
    one swapped for a FIFO or a device since the walk saw it is passed over.
    DN's search never met anything but files."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except OSError:
        return False
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or (whole and info.st_size > WHOLE_LARGEST):
            os.close(descriptor)
            return False
        with os.fdopen(descriptor, "rb") as file:
            return _holds(file, pattern, job, whole)
    except OSError:
        return False


def _holds(file: Any, pattern: re.Pattern[bytes], job: Any, whole: bool) -> bool:
    """:func:`holds` on an open *file*.

    *whole* gathers the file a chunk at a time, looking at *job* between
    them, and gives up past :data:`WHOLE_LARGEST` however large the file
    said it was (``/proc``'s say 0); then one search.  That search itself
    cannot be stopped -- Python's ``re`` takes no interruption -- so a
    pattern that backtracks badly runs until it ends, over at most that."""
    if whole:
        data = bytearray()
        while True:
            if job is not None and job.stopped:
                return False
            chunk = file.read(CHUNK)
            if not chunk:
                break
            data += chunk
            if len(data) > WHOLE_LARGEST:
                return False
        return pattern.search(data) is not None
    # The overlap has to hold the longest match and the byte before it, for
    # a whole word's look-behind: the pattern's source holds every byte of a
    # match, escaped, and the look-arounds besides.
    overlap = max(0, len(pattern.pattern) * 4)
    tail = b""
    deferred = False
    while True:
        if job is not None and job.stopped:
            return False
        chunk = file.read(CHUNK)
        if not chunk:
            # Nothing follows a match that ended the last buffer: it stands.
            return deferred
        buffer = tail + chunk
        found = pattern.search(buffer)
        # A match ending the buffer is not trusted yet: a whole word's
        # look-ahead passes there for want of the next byte, which the next
        # round (the overlap holding the match) has in view.
        if found is not None and found.end() < len(buffer):
            return True
        deferred = found is not None
        tail = buffer[-overlap:] if overlap else b""


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
    #: The shell command whose output this is, for a panelized one: Ctrl+R
    #: runs it again rather than asking about each entry.
    command: str | None = None
    #: The listing's own order is kept whatever the panel sorts by: *Find
    #: duplicates*' groups (:mod:`navigator.lib.file_ops.duplicates`).
    keep_order: bool = False


#: The file systems *All drives* walks: those on a disk.  An unknown kind is
#: left out rather than walked, so ``proc``, ``sysfs``, ``tmpfs``, ``overlay``
#: and the like need no list; ``squashfs``, ``iso9660`` and ``udf`` are DN's
#: ``SlowDrive`` CD, and network kinds the departure the docstring records.
DISK_KINDS = frozenset({
    "ext2", "ext3", "ext4", "xfs", "btrfs", "zfs", "f2fs", "jfs", "reiserfs", "bcachefs", "nilfs2",
    "vfat", "exfat", "ntfs", "ntfs3", "fuseblk", "hfsplus", "apfs",
})


#: The kernel's file systems: a walk never crosses into one (it may start
#: in one).  ``autofs`` is here because entering one mounts it, perhaps over
#: a network; ``tmpfs`` is not, as ``/tmp`` and ``/dev/shm`` hold real files.
VIRTUAL_KINDS = frozenset({
    "proc", "sysfs", "devtmpfs", "devpts", "cgroup", "cgroup2", "securityfs", "debugfs", "tracefs", "pstore",
    "bpf", "mqueue", "hugetlbfs", "configfs", "fusectl", "binfmt_misc", "efivarfs", "nsfs", "rpc_pipefs",
    "selinuxfs", "autofs",
})

#: A running system's kernel places, by name: what a search keeps out of on a
#: drive whose ``/`` is a server's, container's or device's
#: (``Drive.system_root``) -- :data:`VIRTUAL_KINDS`' rule where the mounts
#: cannot be asked.  ``/run`` is memory full of sockets, which a remote
#: drive cannot tell from a disk; ``/acct`` and ``/config`` are Android's.
SYSTEM_PLACES = frozenset({"/proc", "/sys", "/dev", "/run", "/acct", "/config"})

#: Where the mounts are read from (a test points it elsewhere).
MOUNTS_TABLE = Path("/proc/self/mounts")


def _read_mounts() -> str:
    """:data:`MOUNTS_TABLE`'s text, empty without one."""
    try:
        return MOUNTS_TABLE.read_text(encoding="utf-8", errors="surrogateescape")
    except OSError:
        return ""


def virtual_points(text: str) -> set[Path]:
    """The mount points in ``/proc/self/mounts`` *text* of a kernel file
    system (:data:`VIRTUAL_KINDS`)."""
    from navigator.lib.config.bookmarks import unescape_mount

    found: set[Path] = set()
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[2] in VIRTUAL_KINDS:
            found.add(Path(unescape_mount(fields[1])))
    return found


def disk_mounts(text: str) -> list[Path]:
    """The mount points in ``/proc/self/mounts`` *text* that are on a disk
    (:data:`DISK_KINDS`), in mounting order, each once."""
    from navigator.lib.config.bookmarks import unescape_mount

    found: list[Path] = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 3 or fields[2] not in DISK_KINDS:
            continue
        point = Path(unescape_mount(fields[1]))
        if point not in found:
            found.append(point)
    return found


def searchable_mounts(table: Path = Path("/proc/self/mounts")) -> list[Path]:
    """*All drives*' mounts now: :func:`disk_mounts` of *table*, less what
    the user cannot enter and a second mount of one file system (a bind
    mount).  Reads the disk, so it runs on the search's thread."""
    try:
        text = table.read_text(encoding="utf-8", errors="surrogateescape")
    except OSError:
        return []
    found: list[Path] = []
    devices: set[int] = set()
    for point in disk_mounts(text):
        try:
            device = point.stat().st_dev
        except OSError:
            continue
        if device in devices or not os.access(point, os.R_OK | os.X_OK):
            continue
        devices.add(device)
        found.append(point)
    return found


def roots(start: Path, scope: str, mounts: Iterable[Path] = ()) -> list[Path]:
    """Where a search of *scope* begins, from *start*.

    *All drives* begins on *start*'s own file system, as DN's always
    searched the current drive (``C = FN[1]``) however slow, then ``/`` and
    *mounts*."""
    if scope == "directory":
        return [start]
    if scope == "disk":
        return [mount_point(start)]
    found = [mount_point(start)]
    if Path("/") not in found:
        found.append(Path("/"))
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


def _passes(name: str, info: os.stat_result, is_link: bool, limits: Advanced,
            broken: Callable[[], bool] = lambda: False) -> bool:
    """Whether the file is within *limits*; *broken* answers whether a link
    points nowhere, asked only when that kind is wanted."""
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
            if "broken_link" in limits.kinds and broken():
                kinds.add("broken_link")
        if name.startswith("."):
            kinds.add("hidden")
        if not info.st_mode & stat.S_IWUSR:
            kinds.add("read_only")
        if not kinds & limits.kinds:
            return False
    return True


#: What decides whether a file passing the mask and the limits holds the
#: text: given the file (a path's text on the disk, a ``Location`` on
#: another drive) and the pattern.  *Replace in files* passes one that
#: replaces, and answers whether it did.
Match = Callable[[Any, "re.Pattern[bytes]"], bool]


def search(request: FindRequest, start: Path, make_entry: Any, job: FindJob,
           *, show_hidden: bool = True, mounts: Iterable[Path] = (), match: Match | None = None) -> list[Any]:
    """Walk the scope, appending to ``job.found`` every match, as *make_entry*
    makes it from ``(directory, os.DirEntry, stat)``.  Ends early when *job*
    is stopped.  Touches only the file system: a thread runs it.  *match*,
    if given, decides for a file whether it holds the text, in place of
    :func:`holds`.
    """
    pattern = request_pattern(request)
    limits = request.limits if request.advanced else Advanced()
    if match is None:
        def match(place: Any, wanted: re.Pattern[bytes]) -> bool:
            if isinstance(place, str):
                return holds(place, wanted, job, whole=request.regex)
            return holds_on_drive(place, wanted, job, whole=request.regex)
    if not isinstance(start, (str, os.PathLike)) and not start.is_local:
        return _search_drive(request, start, job, pattern, limits, show_hidden, match)
    if not isinstance(start, (str, os.PathLike)):
        start = start.local
    one_device = request.scope != "directory"
    seen: set[tuple[int, int]] = set()
    virtual: set[Path] | None = None  # read at the first crossing, if any

    def may_cross(path: str) -> bool:
        nonlocal virtual
        if virtual is None:
            virtual = virtual_points(_read_mounts())
        return Path(os.path.realpath(path)) not in virtual

    for root in roots(start, request.scope, mounts):
        try:
            device = root.stat().st_dev
        except OSError:
            continue
        pending = [(root, device)]
        while pending:
            if job.stopped:
                return job.found
            directory, here = pending.pop()
            job.directory = str(directory)
            try:
                scan = os.scandir(directory)
            except OSError:
                continue
            subdirectories = []
            with scan:
                for item in _listed(scan):
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
                        # Not a link (``is_dir`` did not follow), so ``info`` is its own stat.
                        own = info
                        key = (own.st_dev, own.st_ino)
                        if key not in seen and (
                                own.st_dev == here
                                or (not one_device and may_cross(item.path))):
                            seen.add(key)
                            subdirectories.append((Path(item.path), own.st_dev))
                    if is_dir and not request.directories:
                        continue
                    if not filetypes.in_filter(item.name, request.mask):
                        continue
                    # A link's ``info`` is its own only when it points nowhere.
                    if not _passes(item.name, info, is_link, limits, lambda: stat.S_ISLNK(info.st_mode)):
                        continue
                    if pattern is not None:
                        # Only a regular file (directly or through a link) is read
                        # for text: a FIFO, socket or device would block it.
                        if not stat.S_ISREG(info.st_mode) or not match(item.path, pattern):
                            continue
                    job.found.append(make_entry(directory, item, info))
            pending.extend(reversed(sorted(subdirectories)))
    return job.found


def _listed(scan: Iterable[os.DirEntry[str]]) -> Iterable[os.DirEntry[str]]:
    """*scan*'s entries, ending quietly when reading the directory fails
    halfway (``EIO``, a stale NFS handle, a FUSE daemon gone): DN's
    ``while DosError = 0`` ended that directory's ``FindNext`` loop, and the
    search went on with the next directory."""
    entries = iter(scan)
    while True:
        try:
            item = next(entries)
        except StopIteration:
            return
        except OSError:
            return
        yield item


def _search_drive(request: FindRequest, start: Any, job: FindJob, pattern: Any, limits: Advanced,
                  show_hidden: bool, match: Match) -> list[Any]:
    """:func:`search` on a drive other than the disk: the same walk, each
    directory listed by its drive (``Drive.children``), a file's text read
    through it.  Only *start* and below -- or the drive's top, for *disk*
    and *all drives*: it has no mounts of its own.  Links are not followed.
    On a server, container or device (``Drive.system_root``) the walk never
    goes into its kernel's places (:data:`SYSTEM_PLACES`, by name), though
    a search started inside one walks it -- a departure, as DN had no such
    drives."""
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
            if is_dir and request.recursive and not (
                    drive.system_root and str((directory / name).path) in SYSTEM_PLACES):
                subdirectories.append(directory / name)
            if is_dir and not request.directories:
                continue
            if not filetypes.in_filter(name, request.mask):
                continue
            # ``children`` answers ``lstat``: whether a link leads anywhere is one more question.
            if not _passes(name, info, is_link, limits, lambda: not drive.exists(directory / name)):
                continue
            if pattern is not None:
                if not _regular_on_drive(drive, directory / name, info) or not match(directory / name, pattern):
                    continue
            job.found.append(DirEntry(name, is_dir, 0 if is_dir else info.st_size, info.st_mode, info.st_mtime,
                                      is_link, directory=directory))
        pending.extend(reversed(sorted(subdirectories, key=lambda place: place.name)))
    return job.found


def holds_on_drive(location: Any, pattern: re.Pattern[bytes], job: Any = None, *, whole: bool = False) -> bool:
    """:func:`holds` for a file on another drive, read through it."""
    from navigator.lib.drives import drive_of

    try:
        with drive_of(location).open_read(location) as file:
            return _holds(file, pattern, job, whole)
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


def _regular_on_drive(drive: Any, place: Any, info: Any) -> bool:
    """Whether *place*, which *drive*'s ``children`` answered with *info* (an
    ``lstat``), is a regular file to read for text -- a link one more
    question, its target's.  Anything else could block a read."""
    if stat.S_ISREG(info.st_mode):
        return True
    if not stat.S_ISLNK(info.st_mode):
        return False
    try:
        return stat.S_ISREG(drive.stat(place).st_mode)
    except (OSError, NotImplementedError):
        return False


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
    text = Path(list_file).read_text(encoding="utf-8", errors="surrogateescape")
    return list_from_lines(text.splitlines(), here, make_entry)


def list_from_lines(lines: Iterable[str], here: Path, make_entry: Any) -> list[Any]:
    """:func:`read_list`'s reading of *lines*, wherever they came from -- a
    list file, or what a panelized command printed
    (:mod:`navigator.lib.file_ops.panelize`)."""
    import glob

    found: list[Any] = []
    seen: set[str] = set()
    for line in lines:
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
