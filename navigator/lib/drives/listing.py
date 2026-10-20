"""A directory's listing: the entries a panel shows, and how the local disk
reads them.

Moved out of the panel widget so that a drive (:mod:`navigator.lib.drives`)
can build the same entries without importing a widget: a model may not
depend on the screen that shows it.  ``navigator.widgets.manager.panel``
re-exports every name here, so what imported them from there still does.

Everything below the entry touches nothing but the file system, so a thread
may run it -- and only a thread does.
"""

from __future__ import annotations

import os
import stat
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from navkit.i18n import tr

from navigator.lib.appearance import filetypes
from navigator.lib.file_ops.fileattr import group_name, user_name

# Asked once per id rather than once per row painted: the password and group
# databases do not change under a running listing often enough to matter.
_user_name = lru_cache(maxsize=None)(user_name)
_group_name = lru_cache(maxsize=None)(group_name)


class DirEntry:
    """One line in a panel: a name, whether it is a directory, its size, its
    permission bits, when it was last modified, who owns it and whether it
    is a symlink.

    A directory's ``size`` is 0 until Alt+G counts it (``counted``, DN's
    ``Attr or $80``): the bytes beneath it, shown in the size column in
    place of ``DIR``.  A re-read makes new entries, and the count goes with
    the old ones, as it did in DN.

    ``mode`` is the link's *target*'s, except for a link pointing nowhere,
    where there is no target to describe and it is the link's own.
    ``link_target`` is what a link says it points at, as ``readlink`` gives
    it, read with the directory so that painting it costs no system call.
    """

    __slots__ = ("name", "is_dir", "size", "mode", "mtime", "is_link", "link_target", "uid", "gid",
                 "counted", "directory", "owner", "packed")

    def __init__(self, name: str, is_dir: bool, size: int, mode: int = 0, mtime: float = 0.0,
                 is_link: bool = False, link_target: str | None = None,
                 uid: int | None = None, gid: int | None = None,
                 directory: Path | None = None):
        self.name = name
        self.is_dir = is_dir
        self.size = size
        self.mode = mode
        self.mtime = mtime
        self.is_link = is_link
        self.link_target = link_target
        self.uid = uid
        self.gid = gid
        self.counted = False
        #: Where the entry is, for one listed away from the panel's own
        #: directory -- a *Find:* listing's (DN's per-file ``Owner``); None
        #: for one in the directory the panel shows.
        self.directory = directory
        #: ``user:group`` as the drive named them, for an entry on a drive
        #: whose ids mean nothing here (a server's); None to look the ids up.
        self.owner: str | None = None
        #: What it takes in the archive it is in (DN's ``PSize``): the
        #: *Packed* and *%* columns'; None off an archive, or not known.
        self.packed: int | None = None

    @property
    def key(self) -> str:
        """What tags and the cursor know the entry by: its name, or, for one
        from elsewhere, its whole path -- a *Find:* listing may hold two
        ``README``s."""
        return self.name if self.directory is None else os.path.join(str(self.directory), self.name)

    def path_in(self, here: Any) -> Any:
        """The entry's path, in the panel showing *here*: a
        :class:`~pathlib.Path`, or for a *here* that is a
        :class:`~navigator.lib.drives.Location` the entry's location."""
        if self.directory is None and not isinstance(here, (str, os.PathLike)):
            return here / self.name
        if self.directory is not None and not isinstance(self.directory, (str, os.PathLike)):
            return self.directory / self.name  # a *Find:* entry on another drive
        return Path(self.directory if self.directory is not None else here) / self.name

    @property
    def is_executable(self) -> bool:
        """A regular file someone may run: DN's ``ttExec``, read off the mode."""
        return not self.is_dir and stat.S_ISREG(self.mode) and bool(self.mode & 0o111)

    @property
    def display_size(self) -> str:
        if self.is_dir and not self.counted:
            mark = tr("UP--DIR") if self.name == ".." else tr("DIR")
            return f"{mark:>8.8}"
        size = float(self.size)
        for unit in ("", "K", "M", "G", "T"):
            if size < 1024 or unit == "T":
                return f"{self.size:>8}" if not unit else f"{size:>7.0f}{unit}"
            size /= 1024
        return f"{self.size:>8}"

    @property
    def display_packed(self) -> str:
        """The *Packed* column (DN's ``PSize``): blank where it is not known."""
        if self.is_dir or self.packed is None:
            return ""
        size = float(self.packed)
        for unit in ("", "K", "M", "G", "T"):
            if size < 1024 or unit == "T":
                return f"{self.packed:>8}" if not unit else f"{size:>7.0f}{unit}"
            size /= 1024
        return f"{self.packed:>8}"

    @property
    def display_ratio(self) -> str:
        """The *%* column: the packed size as a percentage of the original,
        DN's ``Percent(Size, PSize)`` -- 100 for an empty file."""
        if self.is_dir or self.packed is None:
            return ""
        ratio = 100 if self.size == 0 else round(self.packed * 100 / self.size)
        return f"{min(ratio, 999):>3}%"

    @property
    def display_attributes(self) -> str:
        """``rwxr-xr-x``: ``ls -l``'s permission string, less the type letter.

        DOS Navigator showed the four DOS attributes here; a POSIX file has
        permissions instead, and the type is already the size column's.
        """
        return stat.filemode(self.mode)[1:]

    @property
    def display_path(self) -> str:
        """Where an entry from elsewhere is: a *Find:* listing's path column."""
        return str(self.directory) if self.directory is not None else ""

    @property
    def display_owner(self) -> str:
        """``user:group``, as ``ls -l`` names them, a number where no name is
        known, and blank for an entry that could not be read.

        DOS had no owners, so DN had no such column; this is the detailed
        mode's one addition beyond reading DN's columns for POSIX.
        """
        if self.owner is not None:
            return self.owner
        if self.uid is None or self.gid is None:
            return ""
        return f"{_user_name(self.uid)}:{_group_name(self.gid)}"

    @property
    def type_mark(self) -> str:
        """Midnight Commander's one-character file type, for the gutter
        without an icon: ``/`` directory, ``*`` executable, ``@`` symlink,
        ``~`` symlink to a directory, ``!`` stale symlink, ``=`` socket, ``-``
        character device, ``+`` block device, ``|`` FIFO, and a blank for a
        plain file.

        Read off the mode bits rather than ``os.access``, so painting a row
        costs no system call.
        """
        mode = self.mode
        if self.is_link:
            if stat.S_ISLNK(mode):
                return "!"
            return "~" if self.is_dir else "@"
        if self.is_dir:
            return "/"
        if stat.S_ISSOCK(mode):
            return "="
        if stat.S_ISCHR(mode):
            return "-"
        if stat.S_ISBLK(mode):
            return "+"
        if stat.S_ISFIFO(mode):
            return "|"
        if stat.S_ISREG(mode) and mode & 0o111:
            return "*"
        return " "

    @property
    def display_date(self) -> str:
        """The modification time, ``DD-MM-YYYY hh:mm``.

        DN's default country order, with a four-digit year -- a departure from
        its ``YY``, which on DOS could not reach past 2107 anyway and here
        would make 1999 and 2099 one.  Modification, not creation: a DOS
        directory entry held one date, and Linux cannot report a creation time
        portably.
        """
        return time.strftime("%d-%m-%Y %H:%M", time.localtime(self.mtime))

    @property
    def info_size(self) -> str:
        """The size as the *Current file* info line gives it (DN's
        ``GetDown``): every digit -- a departure, where the column shortens
        it -- or ``UP--DIR``/``SUB-DIR`` for a directory not counted."""
        if self.is_dir and not self.counted:
            return tr("UP--DIR") if self.name == ".." else tr("SUB-DIR")
        return f"{self.size:,}"



def _extension(name: str) -> str:
    """What *Extension* sorts by: after the last dot, and none for a dot-file."""
    stem, dot, extension = name.rpartition(".")
    return extension.lower() if dot and stem else ""


def _group_rank(entry: DirEntry) -> int:
    """``GetFileType``'s number for *entry*, with no type (0) taken as 100."""
    if entry.is_dir:
        return 0
    if entry.is_executable:
        return 1
    group = filetypes.group_of(entry.name)
    return filetypes.GROUPS.index(group) if group is not None else 100


def order_entries(
    entries: list[DirEntry], sort: str = "name", *,
    executables_first: bool = False, archives_first: bool = False, reverse: bool = False,
) -> list[DirEntry]:
    """*entries* in a panel's order: ``TFilesCollection.Compare``.

    ``..`` comes first whatever the mode.  *Name*, *Extension*, *Size* and
    *Time* put the directories before the files; size and time go largest
    and newest first.  *Owner* (Navigator's: DOS had no owners) does too,
    by ``user:group`` as the column shows it, then by name; so does
    *Attributes* (Navigator's too), by the permission bits, fewest first.  *Type* is DN's *Group*: directories, executables,
    archives, the custom groups, then the rest, each by name.  Names compare
    without regard to case, as DOS's upper-cased ones did, the exact name
    breaking a tie.

    *executables_first* and *archives_first* are the panel flags
    (``fmiExeFirst``, ``fmiArchivesFirst``): among the files, those kinds
    first, except when sorting by size or time, as DN skipped them there.
    *Unsorted* is the directory's own order, and a departure in leaving the
    two flags out: DN's compare applied them to some pairs and not to
    others, which is no order at all.

    *reverse* turns each mode's own order round -- a departure, DN had no
    descending sort; it came with clicking a column title.  ``..``, the
    directories before the files and the two flags stay where they were:
    only the order within each of those groups turns.  *Unsorted* ignores it.
    """
    up = [entry for entry in entries if entry.name == ".."]
    rest = [entry for entry in entries if entry.name != ".."]
    if sort == "unsorted":
        return up + rest
    kinds = sort not in ("size", "time", "attributes", "owner")

    def first(entry: DirEntry) -> tuple[bool, bool]:
        if not kinds or entry.is_dir:
            return (False, False)
        return (
            executables_first and not entry.is_executable,
            archives_first and filetypes.group_of(entry.name) != "archive",
        )

    def by_name(entry: DirEntry) -> tuple[str, str]:
        return (entry.name.lower(), entry.name)

    # Each mode is a group (what stays put) and a value (what *reverse*
    # turns): two stable sorts, the value's first.
    group = lambda entry: (not entry.is_dir, *first(entry))
    if sort == "extension":
        value = lambda entry: (_extension(entry.name), *by_name(entry))
    elif sort == "size":
        value = lambda entry: (-entry.size, *by_name(entry))
    elif sort == "time":
        value = lambda entry: (-entry.mtime, *by_name(entry))
    elif sort == "attributes":
        value = lambda entry: (stat.S_IMODE(entry.mode), *by_name(entry))
    elif sort == "owner":
        value = lambda entry: (entry.display_owner.lower(), *by_name(entry))
    elif sort == "type":
        # The directories are *Group*'s first rank, so they lead as before.
        group = lambda entry: (not entry.is_dir,)
        value = lambda entry: (_group_rank(entry), *first(entry), *by_name(entry))
    else:
        value = by_name
    rest.sort(key=value, reverse=reverse)
    rest.sort(key=group)
    return up + rest



def make_entry(item: os.DirEntry[str], directory: Path | None = None) -> DirEntry:
    """*item* as a :class:`DirEntry`: its target's facts, or a dangling
    link's own, and what a link says it points at."""
    try:
        info = item.stat()
    except OSError:
        # A dangling link: describe the link itself.
        try:
            info = item.stat(follow_symlinks=False)
        except OSError:
            info = None
    try:
        is_link = item.is_symlink()
    except OSError:
        is_link = False
    target = None
    if is_link:
        try:
            target = os.readlink(item.path)
        except OSError:
            pass
    if info is None:
        return DirEntry(item.name, False, 0, is_link=is_link, link_target=target, directory=directory)
    is_dir = stat.S_ISDIR(info.st_mode)
    size = 0 if is_dir else info.st_size
    return DirEntry(item.name, is_dir, size, info.st_mode, info.st_mtime, is_link,
                    target, info.st_uid, info.st_gid, directory)


def entry_at(path: Path, directory: Path | None = None) -> DirEntry | None:
    """The entry for *path* as it is now, or None if it is gone."""
    try:
        info = path.lstat()
    except OSError:
        return None
    is_link = stat.S_ISLNK(info.st_mode)
    target = None
    if is_link:
        try:
            target = os.readlink(path)
        except OSError:
            pass
        try:
            info = path.stat()
        except OSError:
            pass
    is_dir = stat.S_ISDIR(info.st_mode)
    return DirEntry(path.name, is_dir, 0 if is_dir else info.st_size, info.st_mode, info.st_mtime,
                    is_link, target, info.st_uid, info.st_gid, directory)


def restat_found(entries: list[DirEntry], show_hidden: bool, sort: str = "name", *,
                 executables_first: bool = False, archives_first: bool = False, reverse: bool = False,
                 mask: str = filetypes.ALL_FILES) -> tuple[list[DirEntry], str | None]:
    """A *Find:* listing re-read (``DosReread``): each entry as it is now, the
    gone ones dropped, under a ``..`` that leads back.  A thread runs it."""
    filtered = mask.strip() not in ("", filetypes.ALL_FILES)
    found: list[DirEntry] = [DirEntry("..", True, 0)]
    for entry in entries:
        if entry.name == "..":
            continue
        if not show_hidden and entry.name.startswith("."):
            continue
        if entry.directory is not None and not isinstance(entry.directory, (str, os.PathLike)):
            fresh = _entry_elsewhere(entry)
        else:
            fresh = entry_at(entry.path_in(Path("/")), entry.directory)
        if fresh is None:
            continue
        if filtered and not fresh.is_dir and not filetypes.in_filter(fresh.name, mask):
            continue
        found.append(fresh)
    return order_entries(found, sort, executables_first=executables_first,
                         archives_first=archives_first, reverse=reverse), None


def _entry_elsewhere(entry: DirEntry) -> DirEntry | None:
    """A *Find:* entry on another drive as it is now, or None if it is gone."""
    from navigator.lib.drives import drive_of

    location = entry.directory / entry.name
    try:
        drive = drive_of(location)
        own = drive.lstat(location)
        info = drive.stat(location) if stat.S_ISLNK(own.st_mode) else own
    except OSError:
        return None
    is_dir = stat.S_ISDIR(info.st_mode)
    return DirEntry(entry.name, is_dir, 0 if is_dir else info.st_size, info.st_mode, info.st_mtime,
                    stat.S_ISLNK(own.st_mode), None, directory=entry.directory)


def scan_directory(
    path: Path, show_hidden: bool, sort: str = "name", *,
    executables_first: bool = False, archives_first: bool = False, reverse: bool = False,
    mask: str = filetypes.ALL_FILES, dir_length: bool = False, job: Any = None,
) -> tuple[list[DirEntry], str | None]:
    """*path*'s entries, ``..`` first and in *sort*'s order
    (:func:`order_entries`), and why not if it cannot be read.

    A file *mask* (:func:`navigator.lib.appearance.filetypes.in_filter`) leaves out the files
    it does not let through; every directory is listed whatever it says, as
    DN's ``GetDirectory`` listed them.

    *dir_length* is the *Display* box *Directory length* (``fmiDirLen``):
    every directory's bytes counted into its size, ``..`` standing for the
    one listed, as ``GetFilesColl`` called ``GetDirLen`` for each.  *job*'s
    ``stopped`` ends the counting -- what is not counted yet stays ``DIR``.

    Touches nothing but the file system, so a thread may run it.
    """
    entries: list[DirEntry] = []
    error: str | None = None
    filtered = mask.strip() not in ("", filetypes.ALL_FILES)
    if path != path.parent:
        try:
            info = path.parent.stat()
            entries.append(DirEntry("..", True, 0, info.st_mode, info.st_mtime,
                                   uid=info.st_uid, gid=info.st_gid))
        except OSError:
            entries.append(DirEntry("..", True, 0))
    try:
        with os.scandir(path) as scan:
            for item in scan:
                if not show_hidden and item.name.startswith("."):
                    continue
                if filtered and not filetypes.in_filter(item.name, mask):
                    try:
                        if not item.is_dir():
                            continue
                    except OSError:
                        continue
                entries.append(make_entry(item))
    except OSError as exc:
        error = exc.strerror or str(exc)
    if dir_length and error is None:
        count_lengths(path, entries, job)
    entries = order_entries(entries, sort, executables_first=executables_first,
                            archives_first=archives_first, reverse=reverse)
    return entries, error


def count_lengths(path: Path, entries: list[DirEntry], job: Any = None) -> None:
    """Each directory among *entries* given its bytes (:mod:`navigator.lib.file_ops.dirlength`),
    ``..`` the bytes of *path* itself; nothing more once *job* is stopped."""
    from navigator.lib.file_ops.dirlength import count_dir_length

    for entry in entries:
        if not entry.is_dir:
            continue
        size = count_dir_length(path if entry.name == ".." else entry.path_in(path), job)
        if size is None:
            return
        entry.size, entry.counted = size, True


def free_space_of(path: Path) -> tuple[int, str] | None:
    """*Free space*'s figures, ``TDrive.GetFreeSpace``: the bytes free on the
    file system holding *path*, and where it is mounted, as DN named the
    drive.  ``None`` when it cannot be told.  A thread runs it."""
    import shutil

    from navigator.lib.system import diskinfo
    try:
        free = shutil.disk_usage(path).free
    except OSError:
        return None
    try:
        mounts = Path("/proc/self/mounts").read_text(encoding="utf-8", errors="replace")
    except OSError:
        mounts = ""
    return free, diskinfo.mount_of(path.resolve(), mounts)[0]



class ScanJob:
    """What stops a read's counting: Esc while it shows *Reading directory...*,
    or the panel moving on (DN's ``Abort``)."""

    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def read_listing(path: Path, show_hidden: bool, sort: str, *, free: bool,
                 **options: Any) -> tuple[list[DirEntry], str | None, tuple[int, str] | None]:
    """:func:`scan_directory` and, with *free*, :func:`free_space_of`: one
    read on the panel's thread."""
    entries, error = scan_directory(path, show_hidden, sort, **options)
    return entries, error, free_space_of(path) if free and error is None else None



__all__ = [
    "DirEntry", "ScanJob", "count_lengths", "entry_at", "free_space_of", "make_entry",
    "order_entries", "read_listing", "restat_found", "scan_directory",
]
