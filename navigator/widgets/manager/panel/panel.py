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
from typing import Any

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


class DirEntry:
    """One line in a panel: a name, whether it is a directory, its size, its
    permission bits, when it was last modified, who owns it and whether it
    is a symlink.

    ``mode`` is the link's *target*'s, except for a link pointing nowhere,
    where there is no target to describe and it is the link's own.
    ``link_target`` is what a link says it points at, as ``readlink`` gives
    it, read with the directory so that painting it costs no system call.
    """

    __slots__ = ("name", "is_dir", "size", "mode", "mtime", "is_link", "link_target", "uid", "gid")

    def __init__(self, name: str, is_dir: bool, size: int, mode: int = 0, mtime: float = 0.0,
                 is_link: bool = False, link_target: str | None = None,
                 uid: int | None = None, gid: int | None = None):
        self.name = name
        self.is_dir = is_dir
        self.size = size
        self.mode = mode
        self.mtime = mtime
        self.is_link = is_link
        self.link_target = link_target
        self.uid = uid
        self.gid = gid

    @property
    def is_executable(self) -> bool:
        """A regular file someone may run: DN's ``ttExec``, read off the mode."""
        return not self.is_dir and stat.S_ISREG(self.mode) and bool(self.mode & 0o111)

    @property
    def display_size(self) -> str:
        if self.name == "..":
            return " UP--DIR"
        if self.is_dir:
            return "     DIR"
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


def scan_directory(
    path: Path, show_hidden: bool, sort: str = "name", *,
    executables_first: bool = False, archives_first: bool = False,
) -> tuple[list[DirEntry], str | None]:
    """*path*'s entries, ``..`` first and in *sort*'s order
    (:func:`order_entries`), and why not if it cannot be read.

    Touches nothing but the file system, so a thread may run it.
    """
    entries: list[DirEntry] = []
    error: str | None = None
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
                    entries.append(DirEntry(item.name, False, 0, is_link=is_link, link_target=target))
                    continue
                is_dir = stat.S_ISDIR(info.st_mode)
                size = 0 if is_dir else info.st_size
                entries.append(DirEntry(item.name, is_dir, size, info.st_mode, info.st_mtime, is_link,
                                        target, info.st_uid, info.st_gid))
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
    emits = (ExecuteFile,)

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
        with untracked():
            # Read at each read, not followed: changing them re-sorts a panel
            # at its next read, where DN's applied to the next manager made.
            defaults = SETTINGS.panel_defaults
            flags = {"executables_first": defaults.executables_first,
                     "archives_first": defaults.archives_first}
        # Taken now, for this read: a later move or reload sets its own.
        request = _ScanRequest(path, self._return_to, self._keep)
        self._return_to = self._keep = None
        pending = self._pending
        if pending is not None and pending.path == path:
            # A read superseded before it landed hands on where the cursor
            # was to go, unless the new one says otherwise.
            if request.return_to is None and request.keep is None:
                request.return_to, request.keep = pending.return_to, pending.keep
        self._generation += 1
        generation = self._generation
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
            if path != self._listed:
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
        if path != self._listed:
            marked = frozenset()
            self.quick_search = None
            self.name_scroll = 0
        elif marked:
            marked &= {entry.name for entry in entries}
        self.marked = marked
        self._listed = path
        target, keep = request.return_to, request.keep
        if keep is not None and keep[0] == path and target is None:
            # A re-read of the same directory: the cursor stays on its entry,
            # or where the entry was if it went, and the view does not jump.
            _, name, cursor, scroll = keep
            found = next((i for i, item in enumerate(entries) if item.name == name), None)
            self.cursor = found if found is not None else min(cursor, max(0, len(entries) - 1))
            self.scroll = scroll
            return
        self.cursor = next(
            (index for index, item in enumerate(entries) if item.name == target), 0
        )
        self.scroll = 0

    def reload(self) -> None:
        """Re-read the directory this panel shows, keeping the cursor on its entry.

        DOS Navigator's re-read after a command left the cursor where it was;
        this one used to send it back to the top, so the file just run, or
        just renamed by a command, was lost.
        """
        entry = self.selected
        if entry is not None:
            self._keep = (self.path, entry.name, self.cursor, self.scroll)
        self.reload_token += 1

    def enter(self) -> None:
        """Descend into the selected directory."""
        entry = self.selected
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
        parent = (self.path / "..").resolve()
        if parent == self.path:
            return
        self._return_to = self.path.name
        self.path = parent

    # -- tagging -------------------------------------------------------------

    def is_marked(self, item: DirEntry) -> bool:
        return item.name in self.marked

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
            self.marked = self.marked ^ {entry.name}
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
            item.name
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
            item.name
            for item in self.items
            if item.name != ".." and (directories or not item.is_dir)
        }
        self.marked = self.marked ^ flipped

    @property
    def marked_entries(self) -> list[DirEntry]:
        """The tagged entries, in listing order."""
        marked = self.marked
        return [item for item in self.items if item.name in marked]

    async def choose(self) -> bool:
        """What Enter and a double click mean here: descend, or run.

        A directory is descended into.  A file the user may execute is run --
        :class:`ExecuteFile`, emitted up to whoever runs commands.  Anything
        else is left alone.
        """
        entry = self.selected
        if entry is not None and not entry.is_dir:
            path = self.path / entry.name
            if path.is_file() and os.access(path, os.X_OK):
                await self.emit(ExecuteFile(path))
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
            self._keep = (self.path, entry.name, self.cursor, self.scroll)
        self.sort_mode = mode

    def toggle_hidden(self) -> None:
        """Ctrl+H: hide the dot-files, or show them again.

        A re-read like :meth:`reload`'s, so the cursor stays on its entry, or
        where it was if that entry is the one just hidden.  A tag on a name
        that goes is dropped with it, so nothing unseen stays selected.
        """
        entry = self.selected
        if entry is not None:
            self._keep = (self.path, entry.name, self.cursor, self.scroll)
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
    }
    DETAIL_ORDER = ("size", "attributes", "owner", "date")
    DROP_ORDER = ("owner", "attributes", "date")
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
        shown = list(self.DETAIL_ORDER)
        widths = {key: width for key, (_, width, _) in self.DETAIL_COLUMNS.items()}
        widths["owner"] = self._owner_width()

        def rest() -> int:
            return inner - sum(widths[key] + 1 for key in shown)

        for key in self.DROP_ORDER:
            if rest() >= self.MIN_NAME_WIDTH:
                break
            shown.remove(key)
        name_width = max(1, rest())
        columns = [("name", inset, name_width)]
        x = inset + name_width + 1
        for key in shown:
            width = widths[key]
            columns.append((key, x, width))
            x += width + 1
        return tuple(columns)

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
        """The path across the top frame, clipped to fit."""
        title = str(self.path)
        room = max(4, self.width - 4 - 2 * self.title_margin)
        if len(title) > room:
            title = "..." + title[-(room - 3) :]
        return f" {title} "

    def footer_text(self) -> str:
        """The selected name, or an item count when there is nothing to name.

        A symlink is named ``name -> target``, as ``ls -l`` shows it. While
        searching, what the search has typed instead.
        """
        if self.quick_search is not None:
            return f"{self.SEARCH_LABEL}{self.quick_search} "
        # New Manager defaults' *Selected files* and *Current file* say which
        # of the two the line may show; with neither it is empty.  Read live
        # rather than copied into each new manager as DN's were, so the boxes
        # apply to the panels already open.
        shown = SETTINGS.panel_defaults
        marked = self.marked_entries if shown.selected_files else []
        if marked:
            # DN's info line: ``dlBytesIn`` and ``dlSelectedFiles``.
            size = sum(item.size for item in marked)
            summary = f" {size:,} bytes in {len(marked)} selected files "
        elif not shown.current_file:
            return ""
        else:
            entry = self.selected
            if entry is None:
                summary = f" {len(self.items)} items "
            elif entry.link_target is not None:
                summary = f" {entry.name} -> {entry.link_target} "
            else:
                summary = f" {entry.name} "
        room = max(1, self.width - 4)
        return summary[: room - 1] + " " if len(summary) > room else summary

    def row_style(self, index: int, item: DirEntry) -> Style:
        classes = ("directory",) if item.is_dir else ()
        # New Manager defaults' *Files highlight*: off, every file is coloured
        # alike (read live, as the info line's boxes are).
        category = (
            filetypes.category_of(item.name, item.is_dir, item.type_mark)
            if SETTINGS.panel_defaults.files_highlight else None
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
        return os.path.join(str(self.path), item.name) in bookmarked_paths()

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
