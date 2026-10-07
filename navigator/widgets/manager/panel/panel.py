"""The file listing panel, and the entries it lists.

Everything here is about *files*.  Everything about *a list* -- the cursor,
the scroll, the two invariants that keep them honest, the framed container,
the row painting and the keys that move through it -- is
:class:`~navml.widgets.dialog.list_viewer.ListViewer`'s, which was extracted from
this file because this file was the only place in the repository that had it.

What is left is the four things a file manager adds to a list: where it is
(``path``), how it reads a directory (``_rescan``), what it does when you
press Enter on one (``enter``), and how a row of it looks -- the gutter (an
icon, or Midnight Commander's type mark), the name, and the size column the
original draws on the right.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
import stat
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from navkit.events import Event, KeyEvent, MouseClickEvent, WakeEvent
from navkit import glyphs as glyphs_module
from navkit.glyphs import GLYPHS_NERD
from navkit.reactive import computed, effect, peek, reactive, untracked
from navkit.screen import Surface, char_width
from navkit.style import Style
from navkit.stylesheet import StyleProperty

from navml.quick_search import name_pattern
from navml.widgets.dialog.list_viewer import ListViewer

# Imported under another name because ``Panel`` declares an ``icons`` style
# property: inside a method the global still wins, but two ``icons`` a few
# lines apart meaning a module and a keyword is a trap rather than a saving.
from navigator import filetypes
from navigator import icons as icon_glyphs
from navigator.bookmarks import bookmarked_paths
from navigator.fileattr import group_name, user_name
from navigator.settings import SETTINGS, PanelDefaultsData

# Asked once per id rather than once per row painted: the password and group
# databases do not change under a running listing often enough to matter.
_user_name = lru_cache(maxsize=None)(user_name)
_group_name = lru_cache(maxsize=None)(group_name)


@dataclass(frozen=True, slots=True)
class ExecuteFile(Event):
    """Enter on an executable: run it.

    Raised by the panel, which knows the file and not the shell, and taken by
    whoever runs commands -- ``Shell``, in Navigator.  DOS Navigator ran an
    ``.EXE``, ``.COM`` or ``.BAT`` the same way, through ``cmExecString``;
    here "executable" is what the file system says.
    """

    path: Path


@dataclass(frozen=True, slots=True)
class OpenFile(Event):
    """Enter on a file that is not itself a program: whatever its name says
    to run, which ``Shell`` reads from ``extensions.ini`` -- DOS Navigator's
    ``_GotoExt``, ``cmExecFile`` and ``DN.EXT``."""

    path: Path


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
                 "counted", "directory")

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

    @property
    def key(self) -> str:
        """What tags and the cursor know the entry by: its name, or, for one
        from elsewhere, its whole path -- a *Find:* listing may hold two
        ``README``s."""
        return self.name if self.directory is None else os.path.join(str(self.directory), self.name)

    def path_in(self, here: Path) -> Path:
        """The entry's path, in the panel showing *here*."""
        return Path(self.directory if self.directory is not None else here) / self.name

    @property
    def is_executable(self) -> bool:
        """A regular file someone may run: DN's ``ttExec``, read off the mode."""
        return not self.is_dir and stat.S_ISREG(self.mode) and bool(self.mode & 0o111)

    @property
    def display_size(self) -> str:
        if self.is_dir and not self.counted:
            return " UP--DIR" if self.name == ".." else "     DIR"
        size = float(self.size)
        for unit in ("", "K", "M", "G", "T"):
            if size < 1024 or unit == "T":
                return f"{self.size:>8}" if not unit else f"{size:>7.0f}{unit}"
            size /= 1024
        return f"{self.size:>8}"

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


#: What ends a name cut short to fit its column.
ELLIPSIS = "..."


def text_width(text: str) -> int:
    """The cells *text* takes on the terminal."""
    return sum(char_width(char) for char in text)


def skip_cells(text: str, cells: int) -> str:
    """*text* less its first *cells* cells; half a wide character is a blank."""
    if cells <= 0:
        return text
    skipped = 0
    for index, char in enumerate(text):
        if skipped >= cells:
            return text[index:]
        skipped += char_width(char)
        if skipped > cells:
            return " " + text[index + 1 :]
    return ""


def fit_text(text: str, room: int) -> str:
    """*text* in *room* cells, ending in :data:`ELLIPSIS` if it had to be cut.

    With no room for the marker and a character beside it, just cut.
    """
    if text_width(text) <= room:
        return text
    keep = room - len(ELLIPSIS) if room > len(ELLIPSIS) else room
    used = 0
    for index, char in enumerate(text):
        used += char_width(char)
        if used > keep:
            head = text[:index]
            break
    else:
        head = text
    return head + ELLIPSIS if room > len(ELLIPSIS) else head


def window_text(text: str, offset: int, room: int) -> str:
    """Cells *offset* to *offset* + *room* of *text*, marked where it is cut.

    Scrolled at all, the first cells of the window are :data:`ELLIPSIS`
    rather than a marker pushed in front, so the window does not move -- a
    name shows its end exactly when it would have without the marker.  A
    name scrolled wholly out of the window leaves the marker alone, saying
    there is a name there.  With no room for the marker and a character
    beside it, the text is just cut.
    """
    marker = len(ELLIPSIS)
    if offset <= 0 or room <= marker:
        return fit_text(skip_cells(text, offset), room)
    return ELLIPSIS + fit_text(skip_cells(text, offset + marker), room - marker)


#: How long a rescan may hold the frame up before it is left to finish on
#: its own: long enough for any local directory, short enough not to be felt.
SCAN_GRACE = 0.05

#: The threads directories are read on.  More than one, so a read stuck on a
#: dead mount does not hold up the other panel's.
_SCANNER = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="nav-scan")


@dataclass
class _ScanRequest:
    """One read of a directory, and where its cursor is to go once it lands."""

    path: Path
    return_to: str | None
    keep: tuple[Path, str, int, int] | None
    #: What is listed: the path, or the *Find:* listing shown at it -- so a
    #: listing's own re-reads keep tags and cursor, and entering one does not.
    where: Any = None


#: DN's sort modes (``psm*``, ``SortMode``), named as the *New Manager
#: defaults* name them; "type" is DN's *Group*.
SORT_MODES: tuple[str, ...] = PanelDefaultsData.SORT_BY


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
    executables_first: bool = False, archives_first: bool = False,
) -> list[DirEntry]:
    """*entries* in a panel's order: ``TFilesCollection.Compare``.

    ``..`` comes first whatever the mode.  *Name*, *Extension*, *Size* and
    *Time* put the directories before the files; size and time go largest
    and newest first.  *Type* is DN's *Group*: directories, executables,
    archives, the custom groups, then the rest, each by name.  Names compare
    without regard to case, as DOS's upper-cased ones did, the exact name
    breaking a tie.

    *executables_first* and *archives_first* are the panel flags
    (``fmiExeFirst``, ``fmiArchivesFirst``): among the files, those kinds
    first, except when sorting by size or time, as DN skipped them there.
    *Unsorted* is the directory's own order, and a departure in leaving the
    two flags out: DN's compare applied them to some pairs and not to
    others, which is no order at all.
    """
    up = [entry for entry in entries if entry.name == ".."]
    rest = [entry for entry in entries if entry.name != ".."]
    if sort == "unsorted":
        return up + rest
    kinds = sort not in ("size", "time")

    def first(entry: DirEntry) -> tuple[bool, bool]:
        if not kinds or entry.is_dir:
            return (False, False)
        return (
            executables_first and not entry.is_executable,
            archives_first and filetypes.group_of(entry.name) != "archive",
        )

    def by_name(entry: DirEntry) -> tuple[str, str]:
        return (entry.name.lower(), entry.name)

    if sort == "extension":
        key = lambda entry: (not entry.is_dir, *first(entry), _extension(entry.name), *by_name(entry))
    elif sort == "size":
        key = lambda entry: (not entry.is_dir, -entry.size, *by_name(entry))
    elif sort == "time":
        key = lambda entry: (not entry.is_dir, -entry.mtime, *by_name(entry))
    elif sort == "type":
        key = lambda entry: (_group_rank(entry), *first(entry), *by_name(entry))
    else:
        key = lambda entry: (not entry.is_dir, *first(entry), *by_name(entry))
    return up + sorted(rest, key=key)


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
                 executables_first: bool = False, archives_first: bool = False,
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
        fresh = entry_at(entry.path_in(Path("/")), entry.directory)
        if fresh is None:
            continue
        if filtered and not fresh.is_dir and not filetypes.in_filter(fresh.name, mask):
            continue
        found.append(fresh)
    return order_entries(found, sort, executables_first=executables_first,
                         archives_first=archives_first), None


def scan_directory(
    path: Path, show_hidden: bool, sort: str = "name", *,
    executables_first: bool = False, archives_first: bool = False,
    mask: str = filetypes.ALL_FILES,
) -> tuple[list[DirEntry], str | None]:
    """*path*'s entries, ``..`` first and in *sort*'s order
    (:func:`order_entries`), and why not if it cannot be read.

    A file *mask* (:func:`navigator.filetypes.in_filter`) leaves out the files
    it does not let through; every directory is listed whatever it says, as
    DN's ``GetDirectory`` listed them.

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
    entries = order_entries(entries, sort, executables_first=executables_first,
                            archives_first=archives_first)
    return entries, error


class Panel(ListViewer):
    """One side of the desktop: a directory, listed.

    The model is the one :class:`ListViewer` defines -- assign ``path`` and
    the listing, the cursor and the scroll all follow -- with one effect of
    its own in front of the two it inherits: re-read the directory.  The
    ordering matters and is guaranteed: ``Effect.order`` is stamped when
    ``effect()`` is called and the scheduler sorts on it, so a rescan runs,
    then the cursor is clamped onto the new listing, then the scroll follows
    it.
    """

    #: Enter on an executable, going up to whoever runs commands.
    emits = (ExecuteFile, OpenFile)

    #: Whether a listing shows a Nerd Font glyph beside each name.  ``auto``
    #: means "whenever the terminal can draw one" and ``none`` refuses even
    #: then, which is what a sheet aiming at strict DOS fidelity sets.  The
    #: application's to declare rather than the kit's: navkit draws box frames
    #: and knows nothing about icons.
    icons = StyleProperty("auto", values=("auto", "none"))

    path: Path = reactive(Path("."))
    #: Bumped to re-read a directory whose path has not changed.
    reload_token: int = reactive(0)
    #: Set while a directory the panel has moved to is still being read on its
    #: thread, which takes a slow disk or a dead network mount longer than a
    #: frame: the rows say *Reading directory...* meanwhile.
    scanning: bool = reactive(False)
    #: Columns kept clear at each end of the top edge, so the path never runs
    #: under a window icon painted there -- the file manager's close and zoom
    #: icons sit on its panels' frames.  Kept at both ends because the title
    #: is centred.
    title_margin: int = reactive(0)
    #: How the listing is laid out -- one of :data:`VIEW_MODES`, and Ctrl+Y
    #: (``cmToggleShowMode``) steps through them.  Per panel, as DN's
    #: ``ShowFlags`` were.
    view_mode: str = reactive("simple")
    #: Whether names starting with ``.`` are listed.  Ctrl+H flips it, per
    #: panel like ``view_mode``; ``..`` is always listed.
    show_hidden: bool = reactive(True)
    #: How the listing is ordered, one of :data:`SORT_MODES`: DN's ``SortMode``,
    #: per panel, seeded from the *New Manager defaults* and changed by Alt+B.
    sort_mode: str = reactive("name")
    #: The *Display* boxes this panel has: ``PanelDefaultsData.DISPLAY``'s
    #: names that are on.  None while it follows the *New Manager defaults*,
    #: read live; Alt+S's *Panel Options* gives it its own (DN's per-panel
    #: ``PanelFlags``).  Ask :meth:`shows`.
    display: Any = reactive(None)
    #: Which files are listed (DN's ``FileMask``): ``;``-separated patterns,
    #: ``-`` to leave out (:func:`navigator.filetypes.in_filter`).  Per panel,
    #: set by Alt+S; directories are always listed.
    file_mask: str = reactive(filetypes.ALL_FILES)
    #: A *Find:* listing shown in place of the directory (Alt+F7, DN's
    #: ``TFindDrive``, :class:`navigator.filefind.FindListing`), or None.  It
    #: belongs to the directory it was shown at: going anywhere else drops it.
    found: Any = reactive(None)
    #: The detailed mode's columns this panel shows over a directory
    #: (*Columns Setup*, Alt+K, DN's ``ShowFlags`` of its disk drive), seeded
    #: from *Column defaults*' *Disk Drive*.
    columns: frozenset[str] = reactive(frozenset(("size", "attributes", "owner", "date")))
    #: The same over a *Find:* listing, which was a drive of its own in DN
    #: with its own ``ShowFlags``: seeded from *File find* by each listing
    #: shown, and the only one of the two where ``path`` counts.
    find_columns: frozenset[str] = reactive(frozenset(("size", "attributes", "owner", "date", "path")))
    #: The names tagged with Insert -- DN's ``TFileRec.Selected``, held here
    #: rather than on the entry because a rescan builds new entries.  Kept
    #: across a re-read of the same directory, less the names that went, and
    #: cleared by a change of directory.
    marked: frozenset[str] = reactive(frozenset())
    #: What Ctrl+S's quick search has typed so far, or None when the panel is
    #: not searching -- ``""`` is searching with nothing typed yet.  Every
    #: character kept names at least one entry: one that would name none is
    #: refused, as Midnight Commander refuses it.
    quick_search: str | None = reactive(None)
    #: How many cells every name is scrolled left by, in the simple and the
    #: detailed modes: Left and Right move it, so the end of a name too long
    #: for its column can be read.  What is shown is :attr:`name_offset`,
    #: this clamped to what the longest name needs.  Back to 0 on a change of
    #: directory or of mode.
    name_scroll: int = reactive(0)

    #: ``simple``: name and size.  ``detailed``: name, size, permissions and
    #: date in columns.  ``list``: names alone, in as many columns as fit.
    VIEW_MODES = ("simple", "detailed", "list")

    #: ``heading`` is the column-titles row the detailed and list modes draw.
    parts = ListViewer.parts + ("heading",)

    def __init__(self, path: Path | None = None, **kwargs: Any):
        """*path* is optional because a widget markup constructs must be.

        It is also *seeded* rather than bound, which is the rule a panel is
        the reason for: ``enter()`` assigns ``path`` on every descent, and an
        attribute carrying a binding is read-only until something unbinds it.
        """
        super().__init__(**kwargs)
        #: Set by :meth:`enter` for the rescan that is about to happen, so the
        #: cursor can land on the directory we just climbed out of.
        self._return_to: str | None = None
        #: Set by :meth:`reload`: the directory, the entry under the cursor,
        #: the cursor and the scroll, for a re-read of *that* directory to put
        #: back.  Ignored if the panel has gone somewhere else meanwhile.
        self._keep: tuple[Path, str, int, int] | None = None
        #: The directory the last rescan read, which tells a re-read (keep
        #: the tags) from a move (drop them).
        self._listed: Path | None = None
        #: Counts the reads started, so one that lands after a later one was
        #: asked for is dropped; and the read still on its thread, if any.
        self._generation = 0
        self._pending: _ScanRequest | None = None
        # Seeded, not bound: Ctrl+H toggles it per panel.
        self.show_hidden = SETTINGS.system.show_hidden
        self.sort_mode = SETTINGS.panel_defaults.sort_by
        self.columns = SETTINGS.column_defaults.columns(False)
        if path is not None:
            self.path = path

    def mounted(self) -> None:
        # Before ListViewer's two, because a rescan replaces the very list
        # they are about to clamp a cursor onto.
        effect(self, Panel._rescan)
        super().mounted()
        effect(self, Panel._end_search_unfocused)
        effect(self, Panel._follow_column_titles)

    # -- the listing ---------------------------------------------------------

    def _rescan(self) -> None:
        """Re-read the directory, whenever the path or the token changes.

        **Read on a thread** (:func:`scan_directory`), so a directory on a
        slow disk or a hung network mount does not stop the screen.  One read
        within :data:`SCAN_GRACE` -- which is nearly every one -- is shown in
        this same frame, as it always was; a slower one is shown when it is
        done, unless the panel has moved on by then.  With no application
        running (a test driving the model), the read is waited for.
        """
        _ = self.reload_token  # read for the dependency; this is what Ctrl+R moves
        path = self.path
        show_hidden = self.show_hidden
        sort = self.sort_mode
        mask = self.file_mask
        found = self.found
        _ = self.display  # Alt+S re-reads, as DN's ``Setup`` did (``RereadDir``)
        if found is not None and found.origin != path:
            # The panel went somewhere: the *Find:* listing is left behind.
            with untracked():
                self.found = found = None
        with untracked():
            # The defaults are read at each read, not followed: changing them
            # re-sorts a panel following them at its next read.
            flags = {"executables_first": self.shows("executables_first"),
                     "archives_first": self.shows("archives_first"),
                     "mask": mask}
        # Taken now, for this read: a later move or reload sets its own.
        request = _ScanRequest(path, self._return_to, self._keep,
                               path if found is None else (path, id(found)))
        self._return_to = self._keep = None
        pending = self._pending
        if pending is not None and pending.path == path:
            # A read superseded before it landed hands on where the cursor
            # was to go, unless the new one says otherwise.
            if request.return_to is None and request.keep is None:
                request.return_to, request.keep = pending.return_to, pending.keep
        self._generation += 1
        generation = self._generation
        if found is not None and found.live:
            # Still being searched: the entries as found, only ordered.
            entries = [DirEntry("..", True, 0)] + [e for e in found.entries
                                                   if show_hidden or not e.name.startswith(".")]
            self._apply(request, order_entries(entries, sort, executables_first=flags["executables_first"],
                                               archives_first=flags["archives_first"]), None)
            return
        if found is not None:
            future = _SCANNER.submit(restat_found, list(found.entries), show_hidden, sort, **flags)
        else:
            future = _SCANNER.submit(scan_directory, path, show_hidden, sort, **flags)
        with untracked():
            app = self.application
        if app is None or not app.is_running:
            self._apply(request, *future.result())
            return
        try:
            result = future.result(timeout=SCAN_GRACE)
        except concurrent.futures.TimeoutError:
            self._pending = request
            if request.where != self._listed:
                # Somewhere new: its rows are not the last directory's.
                self.items = []
                self.error = None
                self.scanning = True
            app.spawn(self._await_scan(generation, request, future))
            return
        self._apply(request, *result)

    async def _await_scan(self, generation: int, request: _ScanRequest,
                          future: concurrent.futures.Future[Any]) -> None:
        result = await asyncio.wrap_future(future)
        if generation != self._generation:
            return  # the panel has been somewhere else, or re-read, since
        self._apply(request, *result)
        app = self.application
        if app is not None:
            app.post_event(WakeEvent())

    def _apply(self, request: _ScanRequest, entries: list[DirEntry], error: str | None) -> None:
        """Show what a read of ``request.path`` found."""
        path = request.path
        self._pending = None
        self.scanning = False
        self.items = entries
        self.error = error
        # Peeked, not read: the rescan must not depend on the tags, or every
        # Insert would re-read the directory.
        marked = peek(self, Panel.marked)
        where = request.where if request.where is not None else path
        if where != self._listed and where == path and error is None:
            # ``AddToDirectoryHistory``: a directory the panel has come to.
            self._remember_directory(path)
        if where != self._listed:
            marked = frozenset()
            self.quick_search = None
            self.name_scroll = 0
        elif marked:
            marked &= {entry.key for entry in entries}
        self.marked = marked
        self._listed = where
        target, keep = request.return_to, request.keep
        if keep is not None and keep[0] == path and target is None:
            # A re-read of the same directory: the cursor stays on its entry,
            # or where the entry was if it went, and the view does not jump.
            _, key, cursor, scroll = keep
            found = next((i for i, item in enumerate(entries) if item.key == key), None)
            self.cursor = found if found is not None else min(cursor, max(0, len(entries) - 1))
            self.scroll = scroll
            return
        self.cursor = next(
            (index for index, item in enumerate(entries) if item.name == target), 0
        )
        self.scroll = 0

    @staticmethod
    def _remember_directory(path: Path) -> None:
        """Interface's *Track directories*: *path* first in the ``directories``
        history (Alt+Backspace), as ``AddToDirectoryHistory`` put it."""
        if SETTINGS.interface.track_directories:
            from navml.history import HISTORY

            HISTORY.add("directories", str(path))

    def reload(self, key: str | None = None) -> None:
        """Re-read the directory this panel shows, keeping the cursor on its entry.

        DOS Navigator's re-read after a command left the cursor where it was;
        this one used to send it back to the top, so the file just run, or
        just renamed by a command, was lost.  *key* (:attr:`DirEntry.key`) is
        where the cursor goes instead, if it is there: the entry just renamed.
        """
        entry = self.selected
        if entry is not None:
            self._keep = (self.path, key or entry.key, self.cursor, self.scroll)
        self.reload_token += 1

    def name_cell(self) -> tuple[int, int, int] | None:
        """``(x, y, width)`` of the name at the cursor, past its gutter, in this
        panel's own cells; None when it is not on show.  Where Alt+F6's line
        goes, as DN put ``TInputFName`` over ``LastCurPos``."""
        index = self.cursor
        if not 0 <= index < len(self.items):
            return None
        gutter, top = self.gutter, self.inset + self.header
        if self.view_mode == "list":
            right = self.inset + self.inner_width
            for first, x, width in self.list_columns:
                if first <= index < first + self.rows:
                    return x + gutter, top + index - first, max(1, min(width, right - x) - gutter)
            return None
        row = index - self.scroll
        if not 0 <= row < self.rows:
            return None
        if self.view_mode == "detailed":
            columns = self.detail_columns
            if not columns:
                return None
            _, x, width = columns[0]
        else:
            x, width = 1, max(1, self.name_width)
        return x + gutter, top + row, max(1, width - gutter)

    def show_found(self, listing: Any) -> None:
        """Show *listing* in place of the directory, the cursor at its top."""
        self._keep = None
        # DN's ``TFindDrive.Init``: a new drive, *File find*'s defaults.
        self.find_columns = SETTINGS.column_defaults.columns(True)
        self.found = listing

    @property
    def shown_columns(self) -> frozenset[str]:
        """The columns of what the panel lists now: :attr:`find_columns` over a
        *Find:* listing, :attr:`columns` over a directory."""
        return self.find_columns if self.found is not None else self.columns

    @shown_columns.setter
    def shown_columns(self, columns: frozenset[str]) -> None:
        if self.found is not None:
            self.find_columns = columns
        else:
            self.columns = columns

    def leave_found(self) -> None:
        """``..`` in a *Find:* listing: ``ChangeUp``, back to the directory it
        was shown at, the cursor where the panel had left it."""
        if self.found is not None:
            self._return_to = self.found.return_to
            self.found = None

    def go_to_entry(self, entry: DirEntry | None = None) -> None:
        """A found entry's own directory, the cursor on it: DN's ``_CtrlPgDn``
        on a *Find:* listing (``GotoFile``)."""
        entry = entry if entry is not None else self.selected
        if entry is None or entry.directory is None:
            return
        self._return_to = entry.name
        self.found = None
        self.path = Path(entry.directory)

    def enter(self) -> None:
        """Descend into the selected directory -- or, in a *Find:* listing,
        go back (``..``) or go to the entry, as DN's Enter did there."""
        entry = self.selected
        if self.found is not None and entry is not None:
            if entry.name == "..":
                self.leave_found()
            else:
                self.go_to_entry(entry)
            return
        if entry is None or not entry.is_dir:
            return
        # The rescan is deferred, so the cursor we want afterwards has to be
        # left behind as a note rather than applied on the next line.
        self._return_to = self.path.name if entry.name == ".." else None
        self.path = (self.path / entry.name).resolve()

    def go_up(self) -> None:
        """Go to the parent directory, the cursor on the one just left.

        DN's ``_CtrlPgUp``: what choosing ``..`` does, from anywhere in the
        listing.  At the root there is nowhere to go and nothing happens.
        """
        if self.found is not None:
            self.leave_found()
            return
        parent = (self.path / "..").resolve()
        if parent == self.path:
            return
        self._return_to = self.path.name
        self.path = parent

    # -- tagging -------------------------------------------------------------

    def is_marked(self, item: DirEntry) -> bool:
        return item.key in self.marked

    def untag_paths(self, paths: Iterable[Path]) -> None:
        """Take the tags off the entries at *paths*: what a copy, a move or an
        erase leaves of the ones it finished."""
        done = {Path(path) for path in paths}
        if done:
            self.untag(item for item in self.items if item.path_in(self.path) in done)

    def untag(self, entries: Iterable[DirEntry]) -> None:
        """Take *entries*' tags off: what an operation done on them leaves."""
        keys = {entry.key for entry in entries}
        if keys & self.marked:
            self.marked = self.marked - keys

    def toggle_mark(self) -> None:
        """Insert: tag or untag the entry under the cursor, and step down.

        DN's ``kbIns`` in ``TFilePanel.HandleEvent``: ``..`` is never tagged
        -- DN refused any name starting with a dot, which in DOS meant only
        ``.`` and ``..`` -- and the cursor moves down one either way, so
        holding Insert tags a run.
        """
        entry = self.selected
        if entry is None:
            return
        if entry.name != "..":
            self.marked = self.marked ^ {entry.key}
        self.move_cursor(1)

    def select_group(self, mask: str, *, select: bool = True, invert: bool = False) -> None:
        """Gray ``+`` and ``-``: tag, or untag, every entry *mask* matches.

        DN's ``SelectFiles``: selecting passes directories over and
        unselecting does not, *invert* is *Except mask* (the entries the mask
        does **not** match), and ``..`` is never tagged.  *mask* is one or
        more shell patterns joined by ``;``, matched as a POSIX glob -- case
        counting, and ``*.*`` needing a dot (:func:`filetypes.matches`).
        """
        patterns = filetypes.patterns(mask)
        if not patterns:
            return
        matched = {
            item.key
            for item in self.items
            if item.name != ".."
            and (select is False or not item.is_dir)
            and filetypes.matches(item.name, patterns) != invert
        }
        self.marked = (self.marked | matched) if select else (self.marked - matched)

    def invert_marks(self, *, directories: bool = False) -> None:
        """Gray ``*``: DN's ``InvertSelection``.

        Every file's tag flips; a directory's flips only with *directories*
        (Ctrl+Gray ``*``) and otherwise keeps whatever it had.  ``..`` is
        never tagged.
        """
        flipped = {
            item.key
            for item in self.items
            if item.name != ".." and (directories or not item.is_dir)
        }
        self.marked = self.marked ^ flipped

    @property
    def marked_entries(self) -> list[DirEntry]:
        """The tagged entries, in listing order."""
        marked = self.marked
        return [item for item in self.items if item.key in marked]

    async def choose(self) -> bool:
        """What Enter and a double click mean here: descend, or run.

        A directory is descended into.  A file the user may execute is run --
        :class:`ExecuteFile`, emitted up to whoever runs commands -- and any
        other file is :class:`OpenFile`, for whoever knows what its name runs.
        """
        entry = self.selected
        if self.found is not None:
            self.enter()
            return True
        if entry is not None and not entry.is_dir:
            path = entry.path_in(self.path)
            if path.is_file() and os.access(path, os.X_OK):
                await self.emit(ExecuteFile(path))
            elif path.is_file():
                await self.emit(OpenFile(path))
            return True
        self.enter()
        return True

    async def on_double_click(self, event: MouseClickEvent) -> bool:
        """Ctrl+double click is Ctrl+Enter, as in DOS Navigator; a plain one opens."""
        if event.ctrl and event.button == "left" and self.index_at(event.x, event.y) is not None:
            from navigator.widgets.shell.commands import InsertName, InsertPath

            await self.emit(InsertPath() if event.shift else InsertName())
            return True
        return await super().on_double_click(event)

    # -- show modes ----------------------------------------------------------

    def cycle_view_mode(self) -> None:
        """Ctrl+Y: the next of :data:`VIEW_MODES`, the last wrapping to the first.

        The heading row comes and goes with it: the simple mode is the panel
        as it always was, and the other two title their columns.
        """
        modes = self.VIEW_MODES
        mode = modes[(modes.index(self.view_mode) + 1) % len(modes)]
        self.view_mode = mode
        self._follow_column_titles()
        self.name_scroll = 0

    def _follow_column_titles(self) -> None:
        """The heading row: the detailed and list modes', under File Manager
        Setup's *Column titles*; also an effect, so unticking it takes the
        row away at once.  The dividers stay either way."""
        titled = self.view_mode != "simple" and SETTINGS.file_manager.column_titles
        self.header = 1 if titled else 0

    def shows(self, option: str) -> bool:
        """Whether *Display* box *option* is on for this panel: its own, once
        Alt+S has set them, else the *New Manager defaults*' -- read live, a
        departure: DN copied the defaults into each manager it made, and only
        *Panel Options* changed one."""
        display = self.display
        if display is None:
            return bool(getattr(SETTINGS.panel_defaults, option))
        return option in display

    def set_options(self, sort: str, display: frozenset[str], mask: str) -> None:
        """Alt+S's answer (DN's ``Setup``): this panel's order, *Display*
        boxes and file mask, and one re-read keeping the cursor on its entry."""
        if sort not in SORT_MODES:
            raise ValueError(f"unknown sort mode {sort!r}")
        entry = self.selected
        if entry is not None:
            self._keep = (self.path, entry.key, self.cursor, self.scroll)
        self.sort_mode = sort
        self.display = frozenset(display)
        self.file_mask = mask.strip() or filetypes.ALL_FILES

    def set_file_mask(self, mask: str) -> None:
        """A new file mask, and one re-read keeping the cursor on its entry."""
        mask = mask.strip() or filetypes.ALL_FILES
        if mask == self.file_mask:
            return
        entry = self.selected
        if entry is not None:
            self._keep = (self.path, entry.key, self.cursor, self.scroll)
        self.file_mask = mask

    def sort_by(self, mode: str) -> None:
        """Order the listing by *mode*: what Alt+B's choice does (``CM_SortBy``).

        A re-read, as DN's ``RereadDir`` was, keeping the cursor on its entry;
        the mode it already has changes nothing.
        """
        if mode not in SORT_MODES:
            raise ValueError(f"unknown sort mode {mode!r}")
        if mode == self.sort_mode:
            return
        entry = self.selected
        if entry is not None:
            self._keep = (self.path, entry.key, self.cursor, self.scroll)
        self.sort_mode = mode

    def toggle_hidden(self) -> None:
        """Ctrl+H: hide the dot-files, or show them again.

        A re-read like :meth:`reload`'s, so the cursor stays on its entry, or
        where it was if that entry is the one just hidden.  A tag on a name
        that goes is dropped with it, so nothing unseen stays selected.
        """
        entry = self.selected
        if entry is not None:
            self._keep = (self.path, entry.key, self.cursor, self.scroll)
        self.show_hidden = not self.show_hidden

    # -- quick search --------------------------------------------------------

    @property
    def edits_text(self) -> bool:
        """True while searching, so the command line's Enter, Home, End and
        Tab step aside -- Enter ends the search rather than running the line."""
        return self.quick_search is not None

    def start_quick_search(self) -> None:
        """Ctrl+S: start searching, with nothing typed yet."""
        if self.quick_search is None:
            self.quick_search = ""

    def _find(self, text: str, start: int) -> int | None:
        """The first entry from *start* on, wrapping, whose name *text* begins.

        Case folded, and ``*`` and ``?`` are wildcards, as they are in
        Midnight Commander's; everything else is literal.  ``..`` is never
        found: it is not a name anybody searches for.
        """
        pattern = name_pattern(text)
        items = self.items
        for step in range(len(items)):
            index = (start + step) % len(items)
            name = items[index].name
            if name != ".." and pattern.match(name):
                return index
        return None

    def _search_key(self, event: KeyEvent) -> bool:
        """A key while searching: True if the search took it.

        Enter and Esc end the search where it stands.  Any other key that is
        not the search's ends it too and is declined, so it goes on to do
        what it always does -- Down moves, F3 views.
        """
        text = self.quick_search or ""
        if event.is_printable:
            found = self._find(text + event.char, self.cursor)
            if found is not None:
                self.cursor = found
                self.quick_search = text + event.char
            return True
        if event.matches("backspace"):
            self.quick_search = text[:-1]
            return True
        if event.matches("ctrl+s"):
            if text:
                found = self._find(text, self.cursor + 1)
                if found is not None:
                    self.cursor = found
            return True
        self.quick_search = None
        return event.matches("enter", "escape")

    def _end_search_unfocused(self) -> None:
        """The search ends when the keyboard leaves the panel."""
        if not self.focus_within and peek(self, Panel.quick_search) is not None:
            self.quick_search = None

    SEARCH_LABEL = " Search: "

    def cursor_position(self) -> tuple[int, int] | None:
        """While searching, the caret after what has been typed, on the footer."""
        text = self.quick_search
        if text is None or not self.framed:
            return None
        footer = self.footer_text()
        x = self.label_x(footer) + len(self.SEARCH_LABEL) + len(text)
        return min(x, self.width - 2), self.height - 1

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.action == "press" and not event.is_wheel:
            self.quick_search = None
        return await super().on_mouse_click(event)

    async def on_key(self, event: KeyEvent) -> bool:
        """The quick search's keys while it is on, then the listing's.

        In the list mode Left and Right move a column, as DN's did.
        Otherwise they are declined, and reach the manager's key table, which
        scrolls the names with them (:meth:`scroll_names`).
        """
        if self.quick_search is not None and not self.inert and self._search_key(event):
            return True
        if self.view_mode == "list" and not self.inert and self.rows:
            if event.key == "left":
                self.move_cursor(-min(self.rows, self.cursor))
                return True
            if event.key == "right":
                self.move_cursor(min(self.rows, len(self.items) - 1 - self.cursor))
                return True
        return await super().on_key(event)

    #: The detailed mode's columns after the name: heading, width, and the
    #: ``DirEntry`` property that fills it.  Dropped in :data:`DROP_ORDER`
    #: when the name would get too narrow.  A width of ``None`` is measured
    #: off the listing (:meth:`_owner_width`).
    DETAIL_COLUMNS = {
        "size": ("Size", 8, "display_size"),
        "attributes": ("Attr", 9, "display_attributes"),
        "owner": ("Owner", None, "display_owner"),
        "date": ("Date", 16, "display_date"),
        "path": ("Path", None, "display_path"),
    }
    DETAIL_ORDER = ("size", "attributes", "owner", "date", "path")
    DROP_ORDER = ("owner", "attributes", "path", "date")
    #: The widest the path column grows; a longer one starts with ``...``.
    MAX_PATH_WIDTH = 30
    #: The widest the owner column grows; a longer ``user:group`` ends in
    #: ``...``.
    MAX_OWNER_WIDTH = 17
    #: The narrowest the detailed mode lets the name column get before it
    #: gives up a column to widen it.
    MIN_NAME_WIDTH = 12

    @computed
    def detail_columns(self) -> tuple[tuple[str, int, int], ...]:
        """``(key, x, width)`` for every detailed-mode column, the name's first.

        Each column after the name has a divider in the cell before it.  The
        name takes whatever is left; when that is under
        :data:`MIN_NAME_WIDTH`, the owner goes, then the attributes, and then
        the date.  The owner column is as wide as the longest owner listed.
        """
        inset, inner = self.inset, self.inner_width
        # *Columns Setup*'s choice, the path only where entries are from elsewhere.
        wanted, listing = self.shown_columns, self.found is not None
        shown = [key for key in self.DETAIL_ORDER
                 if key in wanted and (key != "path" or listing)]
        widths = {key: width for key, (_, width, _) in self.DETAIL_COLUMNS.items()}
        widths["owner"] = self._owner_width()
        widths["path"] = self._path_width() if "path" in shown else 0

        def rest() -> int:
            return inner - sum(widths[key] + 1 for key in shown)

        for key in self.DROP_ORDER:
            if rest() >= self.MIN_NAME_WIDTH:
                break
            if key in shown:
                shown.remove(key)
        name_width = max(1, rest())
        columns = [("name", inset, name_width)]
        x = inset + name_width + 1
        for key in shown:
            width = widths[key]
            columns.append((key, x, width))
            x += width + 1
        return tuple(columns)

    def _path_width(self) -> int:
        """The path column's width: its longest directory, between its
        heading and :data:`MAX_PATH_WIDTH`."""
        longest = max((text_width(item.display_path) for item in self.items), default=0)
        return max(len(self.DETAIL_COLUMNS["path"][0]), min(longest, self.MAX_PATH_WIDTH))

    def _owner_width(self) -> int:
        """The owner column's width: its longest ``user:group``, never
        narrower than its heading nor wider than :data:`MAX_OWNER_WIDTH`."""
        longest = max((text_width(item.display_owner) for item in self.items), default=0)
        return max(len(self.DETAIL_COLUMNS["owner"][0]), min(longest, self.MAX_OWNER_WIDTH))

    @computed
    def list_columns(self) -> tuple[tuple[int, int, int], ...]:
        """``(first index, x, width)`` for every list-mode column on show.

        Columns hold ``rows`` items each, from ``scroll``; each is as wide as
        its longest name (and the icon gutter), capped at half the panel so
        that a long name cannot push the second column off it.  The last may
        run past the right edge and be clipped.
        """
        rows, inner, inset = self.rows, self.inner_width, self.inset
        items, gutter = self.items, self.gutter
        if not rows or inner <= 0:
            return ()
        cap = inner if len(items) - self.scroll <= rows else max(1, (inner - 1) // 2)
        columns = []
        first, x = self.scroll, inset
        while first < len(items) and x < inset + inner:
            longest = max(len(item.name) for item in items[first : first + rows])
            width = min(cap, gutter + max(1, longest))
            columns.append((first, x, width))
            first += rows
            x += width + 1
        return tuple(columns)

    @computed
    def capacity(self) -> int:
        """In the list mode, the items in every column shown whole."""
        if self.view_mode != "list":
            return self.rows
        right = self.inset + self.inner_width
        whole = [c for c in self.list_columns if c[1] + c[2] <= right]
        return self.rows * max(1, len(whole))

    def _follow_cursor(self) -> None:
        """In the list mode, scroll a whole column at a time.

        ``scroll`` stays a multiple of ``rows``, so a column's contents -- and
        so its width -- do not change as the cursor moves through it.
        """
        if self.view_mode != "list":
            super()._follow_cursor()
            return
        rows = self.rows
        if not rows:
            return
        cursor = self.cursor
        scroll = peek(self, ListViewer.scroll)
        scroll -= scroll % rows
        if cursor < scroll:
            scroll = cursor - cursor % rows
        # Advance a column at a time until the cursor's is shown whole.  The
        # columns depend on the scroll, so each step lays them out again.
        while True:
            self.scroll = scroll
            columns = self.list_columns
            right = self.inset + self.inner_width
            if not columns or any(
                first <= cursor < first + rows and x + width <= right
                for first, x, width in columns
            ) or (columns and columns[0][0] <= cursor < columns[0][0] + rows):
                break
            scroll += rows

    def page(self) -> int:
        if self.view_mode == "list":
            return max(1, self.capacity)
        return super().page()

    def index_at(self, x: int, y: int) -> int | None:
        if self.view_mode != "list":
            return super().index_at(x, y)
        row = y - self.inset - self.header
        if not 0 <= row < self.rows:
            return None
        for first, left, width in self.list_columns:
            if left <= x < left + width:
                index = first + row
                return index if index < len(self.items) else None
        return None

    # -- scrolling the names ---------------------------------------------------

    @computed
    def name_room(self) -> int:
        """The cells a name has in the simple and the detailed modes, less the gutter."""
        if self.view_mode == "detailed":
            columns = self.detail_columns
            width = columns[0][2] if columns else 0
        else:
            width = max(1, self.name_width)
        return max(0, width - self.gutter)

    @computed
    def max_name_scroll(self) -> int:
        """How far the names can scroll: until the longest one ends in view.

        None at all in the list mode, whose columns are laid out to the names.
        """
        if self.view_mode == "list" or not self.items:
            return 0
        longest = max(text_width(item.name) for item in self.items)
        return max(0, longest - self.name_room)

    @computed
    def name_offset(self) -> int:
        """:attr:`name_scroll`, as far as there is anything to scroll."""
        return max(0, min(self.name_scroll, self.max_name_scroll))

    def can_scroll_names(self, step: int) -> bool:
        offset = self.name_offset
        return offset > 0 if step < 0 else offset < self.max_name_scroll

    def scroll_names(self, step: int) -> None:
        """Left and Right in the simple and detailed modes: every name a cell along."""
        self.name_scroll = max(0, min(self.name_offset + step, self.max_name_scroll))

    # -- painting ------------------------------------------------------------

    @property
    def show_icons(self) -> bool:
        """Whether to reserve the icon gutter.

        Both halves have to agree, the way a terminal's mouse support and the
        caller's wish for it do: the sheet says whether icons are wanted and
        the terminal says whether its font could draw one.
        """
        return self.icons != "none" and self.glyphs >= GLYPHS_NERD

    @property
    def gutter(self) -> int:
        """Columns held back at the left of a row, for the icon or the type mark.

        Two with an icon, not one.  A Nerd Font *Mono* build patches its icons
        to a single cell but the plain build does not, and the difference is
        invisible until a name starts one column late on somebody else's
        terminal.  Without one it is a single cell holding
        :attr:`DirEntry.type_mark` -- and always kept, because a tagged
        entry's :attr:`tag_char` is drawn there too.
        """
        return 2 if self.show_icons else 1

    @computed
    def name_width(self) -> int:
        """How much of a listing line is left once the size column is taken."""
        return max(1, self.width - 12)

    def title_text(self) -> str:
        """The path across the top frame, clipped to fit -- or, for a *Find:*
        listing, what it was found by (DN's drive name, ``Find: *.c``).

        **A file mask other than ``*`` follows in brackets**, ``/src [*.c;*.h]``
        -- Alt+Del's *Filter* or Alt+S's *File mask*.  Not DN's: its panel said
        nothing of a mask, and a panel that hides files without saying so
        reads as a directory that lacks them.  The path gives way first; the
        mask is cut only when the bracket alone would not fit.
        """
        title = self.found.title if self.found is not None else str(self.path)
        mask = self.file_mask.strip()
        suffix = f" [{mask}]" if mask not in ("", filetypes.ALL_FILES) else ""
        room = max(4, self.width - 4 - 2 * self.title_margin)
        if suffix and len(suffix) > room - 4:
            suffix = suffix[: max(0, room - 8)] + "...]" if room > 12 else ""
        space = room - len(suffix)
        if len(title) > space:
            title = "..." + title[-(space - 3):] if space > 3 else title[-max(space, 0):]
        return f" {title}{suffix} "

    def footer_text(self) -> str:
        """The selected name, or an item count when there is nothing to name.

        A symlink is named ``name -> target``, as ``ls -l`` shows it. While
        searching, what the search has typed instead.
        """
        if self.quick_search is not None:
            return f"{self.SEARCH_LABEL}{self.quick_search} "
        # *Selected files* and *Current file* say which of the two the line
        # may show; with neither it is empty (:meth:`shows`).
        marked = self.marked_entries if self.shows("selected_files") else []
        if marked:
            # DN's info line: ``dlBytesIn`` and ``dlSelectedFiles``.
            size = sum(item.size for item in marked)
            summary = f" {size:,} bytes in {len(marked)} selected files "
        elif not self.shows("current_file"):
            return ""
        else:
            entry = self.selected
            if entry is None:
                summary = f" {len(self.items)} items "
            elif entry.directory is not None:
                # DN's find panel gave the file's directory a row of its own;
                # here it is the whole path, its start cut as the title's is.
                text, room = str(entry.path_in(self.path)), max(4, self.width - 6)
                if len(text) > room:
                    text = "..." + text[-(room - 3):]
                summary = f" {text} "
            elif entry.link_target is not None:
                summary = f" {entry.name} -> {entry.link_target} "
            else:
                summary = f" {entry.name} "
        room = max(1, self.width - 4)
        return summary[: room - 1] + " " if len(summary) > room else summary

    def row_style(self, index: int, item: DirEntry) -> Style:
        classes = ("directory",) if item.is_dir else ()
        # *Files highlight*: off, every file is coloured alike.
        category = (
            filetypes.category_of(item.name, item.is_dir, item.type_mark)
            if self.shows("files_highlight") else None
        )
        if category:
            classes += (category,)
        if self.is_marked(item):
            classes += ("marked",)
        return self.part_style("row", classes=classes, selected=self.row_selected(index))

    @property
    def divider_glyph(self) -> str:
        """``│`` between columns -- always single, whatever the frame, as DN's were."""
        return glyphs_module.charset("single", self.glyphs)[5]

    #: What stands in the gutter of a tagged entry where File Manager Setup's
    #: *Tag sign* is empty: DN's default ``FMSetup.TagChar``, CP437's
    #: ``$FB``.  A plain ``+`` where the terminal draws ASCII only and the
    #: sign is not ASCII.
    TAG_CHAR = "√"
    TAG_CHAR_ASCII = "+"

    @property
    def tag_char(self) -> str:
        """The tag sign, or ``""`` with *Tag character* off: the colour alone."""
        setup = SETTINGS.file_manager
        if not setup.tag_character:
            return ""
        sign = setup.tag_sign[:1] or self.TAG_CHAR
        if self.glyphs <= glyphs_module.GLYPHS_ASCII and not sign.isascii():
            return self.TAG_CHAR_ASCII
        return sign

    #: The type mark of a bookmarked directory, in place of ``/``: CP437's
    #: ``$04``, a character DN could have drawn.  The ASCII tier keeps ``/``.
    BOOKMARK_MARK = "♦"

    def is_bookmarked(self, item: DirEntry) -> bool:
        """Whether *item* is a directory on the Alt+F1/Alt+F2 list."""
        if not item.is_dir or item.name == "..":
            return False
        return str(item.path_in(self.path)) in bookmarked_paths()

    def _draw_name(self, surface: Surface, x: int, y: int, width: int,
                   item: DirEntry, style: Style, offset: int = 0) -> None:
        """The tag, the icon or the type mark, and the name, in *width* cells.

        A tag takes the gutter over whichever of the other two it would hold:
        the colour says *tagged* too, but not on a monochrome terminal.
        """
        gutter = min(self.gutter, width)
        if gutter:
            if self.is_marked(item) and self.tag_char:
                mark = self.tag_char
            elif self.show_icons:
                mark = icon_glyphs.icon_for(item.name, item.is_dir, item.type_mark,
                                            self.is_bookmarked(item))
            elif self.glyphs > glyphs_module.GLYPHS_ASCII and self.is_bookmarked(item):
                mark = self.BOOKMARK_MARK
            else:
                mark = item.type_mark
            surface.draw_text(x, y, mark, style, gutter)
        if width > gutter:
            room = width - gutter
            name = window_text(item.name, offset, room)
            surface.draw_text(x + gutter, y, name, style, room)

    def render_row(self, surface: Surface, y: int, index: int, item: DirEntry) -> None:
        style = self.row_style(index, item)
        if self.view_mode == "detailed":
            selected = self.row_selected(index)
            for key, x, width in self.detail_columns:
                if key == "name":
                    self._draw_name(surface, x, y, width, item, style, self.name_offset)
                    continue
                if selected:
                    # The cursor bar covers the dividers; draw them back in it.
                    surface.draw_text(x - 1, y, self.divider_glyph, style, 1)
                text = getattr(item, self.DETAIL_COLUMNS[key][2])
                if key == "path" and len(text) > width:
                    text = "..." + text[-(width - 3):] if width > 3 else text[-width:]
                surface.draw_text(x, y, fit_text(text, width), style, width)
            return
        # Still an explicit limit: the name stops where the size column
        # begins, which is nearer than the edge the surface would clip at.
        self._draw_name(surface, 1, y, max(1, self.name_width), item, style, self.name_offset)
        surface.draw_text(self.width - 9, y, item.display_size, style, 8)

    def render_items(self, surface: Surface) -> None:
        if self.scanning:
            surface.draw_text(self.inset + 1, self.inset + self.header, "Reading directory...",
                              self.style, max(0, self.width - 4))
            return
        if self.view_mode != "list":
            super().render_items(surface)
            return
        top = self.inset + self.header
        right = self.inset + self.inner_width
        items = self.items
        for first, x, width in self.list_columns:
            # The last column may run past the edge: end its names at the edge,
            # so the marker is shown rather than clipped.
            width = min(width, right - x)
            for row in range(self.rows):
                index = first + row
                if index >= len(items):
                    break
                item = items[index]
                style = self.row_style(index, item)
                if self.row_selected(index):
                    surface.fill(x, top + row, width, 1, " ", style)
                self._draw_name(surface, x, top + row, width, item, style)

    def _column_spans(self) -> list[tuple[str, int, int]]:
        """``(heading, x, width)`` for the columns of the current mode."""
        if self.view_mode == "detailed":
            return [
                ("Name" if key == "name" else self.DETAIL_COLUMNS[key][0], x, width)
                for key, x, width in self.detail_columns
            ]
        if self.view_mode == "list":
            columns = self.list_columns
            if not columns:
                return [("Name", self.inset, self.inner_width)]
            return [("Name", x, width) for _, x, width in columns]
        return []

    def render_header(self, surface: Surface) -> None:
        """The column titles, and the dividers from them down to the last row.

        Drawn before the rows, so the cursor bar covers a divider it crosses
        -- DN's did.  Nothing in the simple mode, and nothing over an error;
        the dividers alone with *Column titles* off.
        A divider meets the frame in a tee at each end, ``┬``/``┴`` or
        ``╤``/``╧`` as the frame is single or double, except where the title
        or the footer already stands on that cell.
        """
        if self.view_mode == "simple" or self.error is not None:
            return
        top = self.inset
        bottom = top + self.header + self.rows
        right = self.inset + self.inner_width
        glyph = self.divider_glyph
        heading = self.part_style("heading")
        divider = self.part_style("divider")
        horizontal = self.box_charset()[4]
        top_tee, bottom_tee = self.box_joins()[2:4]
        spans = self._column_spans()
        for index, (text, x, width) in enumerate(spans):
            shown = min(width, right - x)
            if shown <= 0:
                break
            if self.header:
                text = text[:shown]
                surface.draw_text(x + (shown - len(text)) // 2, top, text, heading, shown)
            # Dividers go between columns: none after the last one.
            edge = x + width
            if index < len(spans) - 1 and edge < right:
                for y in range(top, bottom):
                    surface.draw_text(edge, y, glyph, divider, 1)
                if self.framed:
                    for y, tee in ((0, top_tee), (self.height - 1, bottom_tee)):
                        char, style = surface.get(edge, y)
                        if char == horizontal:
                            surface.set_cell(edge, y, tee, style)
