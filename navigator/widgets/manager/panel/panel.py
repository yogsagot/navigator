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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from navkit.commands import key_label
from navkit.events import Event, KeyEvent, MouseClickEvent, WakeEvent
from navkit import glyphs as glyphs_module
from navkit.glyphs import GLYPHS_NERD
from navkit.i18n import tr, tr_n
from navkit.reactive import bind, computed, effect, peek, reactive, untracked
from navkit.screen import Surface, char_width
from navkit.style import Style
from navkit.stylesheet import StyleProperty

from navml.quick_search import name_pattern
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.menu.context_menu import ContextMenu, ContextMenuHost

# Imported under another name because ``Panel`` declares an ``icons`` style
# property: inside a method the global still wins, but two ``icons`` a few
# lines apart meaning a module and a keyword is a trap rather than a saving.
from navigator.lib.appearance import filetypes
from navigator.lib.appearance import icons as icon_glyphs
from navigator.lib.config import country
from navigator.lib.config.bookmarks import bookmarked_paths
from navigator.lib.drives import Drive, DriveGone, Location, drive_of
from navigator.lib.file_ops.clip import CLIP
from navigator.lib.drives.listing import (  # noqa: F401 -- re-exported, see listing's docstring
    DirEntry, ScanJob, count_lengths, entry_at, free_space_of, make_entry, order_entries,
    read_listing, restat_found, scan_directory,
)
from navigator.lib.system import dirwatch, gitstatus
from navigator.settings import SETTINGS, PanelDefaultsData
from navigator.widgets.manager.panel.drag import Dropped
from navigator.widgets.manager.panel.option_items import PanelOptionStrip, panel_items


@dataclass(frozen=True, slots=True)
class ExecuteFile(Event):
    """Enter on an executable: run it.

    Raised by the panel, which knows the file and not the shell, and taken by
    whoever runs commands -- ``Shell``, in Navigator.  DOS Navigator ran an
    ``.EXE``, ``.COM`` or ``.BAT`` the same way, through ``cmExecString``;
    here "executable" is what the file system says.
    """

    path: Path | Location


@dataclass(frozen=True, slots=True)
class OpenFile(Event):
    """Enter on a file that is not itself a program: whatever its name says
    to run, which ``Shell`` reads from ``extensions.ini`` -- DOS Navigator's
    ``_GotoExt``, ``cmExecFile`` and ``DN.EXT``."""

    path: Path | Location


#: What ends a name cut short to fit its column, by default -- three dots, the
#: ASCII tier's; a panel passes its own (``Panel.ellipsis``), ``…`` above it.
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


def fit_text(text: str, room: int, marker: str = ELLIPSIS) -> str:
    """*text* in *room* cells, ending in *marker* if it had to be cut.

    With no room for the marker and a character beside it, just cut.
    """
    if text_width(text) <= room:
        return text
    size = text_width(marker)
    keep = room - size if room > size else room
    used = 0
    for index, char in enumerate(text):
        used += char_width(char)
        if used > keep:
            head = text[:index]
            break
    else:
        head = text
    return head + marker if room > size else head


def window_text(text: str, offset: int, room: int, marker: str = ELLIPSIS) -> str:
    """Cells *offset* to *offset* + *room* of *text*, marked where it is cut.

    Scrolled at all, the first cells of the window are *marker*
    rather than a marker pushed in front, so the window does not move -- a
    name shows its end exactly when it would have without the marker.  A
    name scrolled wholly out of the window leaves the marker alone, saying
    there is a name there.  With no room for the marker and a character
    beside it, the text is just cut.
    """
    size = text_width(marker)
    if offset <= 0 or room <= size:
        return fit_text(skip_cells(text, offset), room, marker)
    return marker + fit_text(skip_cells(text, offset + size), room - size, marker)


#: How long a rescan may hold the frame up before it is left to finish on
#: its own: long enough for any local directory, short enough not to be felt.
SCAN_GRACE = 0.05

#: The threads directories are read on.  More than one, so a read stuck on a
#: dead mount does not hold up the other panel's.
_SCANNER = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="nav-scan")

#: The threads other drives are read on: their own, so a server that stops
#: answering holds up none of the local panels' reads.
_REMOTE_SCANNER = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="nav-scan-remote")


def _scanner_for(location: Location) -> concurrent.futures.ThreadPoolExecutor:
    return _SCANNER if location.is_local else _REMOTE_SCANNER


def _read_location(location: Location, show_hidden: bool, sort: str, *, free: bool,
                   **options: Any) -> tuple[list[DirEntry], str | None, tuple[int, str] | None]:
    """A panel's read of *location*, on its thread: its drive's ``scan``,
    and a drive gone or failing as the panel's error line."""
    try:
        return drive_of(location).scan(location, show_hidden, sort, free=free, **options)
    except OSError as error:
        return [], error.strerror or str(error), None

#: How long a change on disk waits for the ones after it before the panel
#: re-reads (*Auto refresh panels*): a copy of a thousand files is a handful
#: of re-reads, not a thousand, and one file is still there at once.
REFRESH_DELAY = 0.3


@dataclass
class _ScanRequest:
    """One read of a directory, and where its cursor is to go once it lands."""

    path: Location
    return_to: str | None
    keep: tuple[Location, str, int, int] | None
    #: What is listed: the path, or the *Find:* listing shown at it -- so a
    #: listing's own re-reads keep tags and cursor, and entering one does not.
    where: Any = None


#: DN's sort modes (``psm*``, ``SortMode``), named as the *New Manager
#: defaults* name them; "type" is DN's *Group*.
SORT_MODES: tuple[str, ...] = PanelDefaultsData.SORT_BY

#: Which way each sort mode runs unreversed: ``True`` ascending.  Size and
#: time go largest and newest first (:func:`order_entries`); *Unsorted* has
#: no direction.
SORT_ASCENDS = {"name": True, "extension": True, "size": False, "time": False,
                "attributes": True, "owner": True, "type": True}


def _archive_file(entry: Any) -> bool:
    """A file Shift+F2 extracts -- the *archive* file type's -- as the
    right-click menu offers *Extract archive* on it (``Manager`` decides)."""
    return (entry is not None and not entry.is_dir and entry.name != ".."
            and filetypes.group_of(entry.name) == "archive")


def direction_arrow(mode: str, reverse: bool, glyphs: int) -> str:
    """``↑`` where *mode* (*reverse* or not) runs ascending, ``↓`` descending
    -- ``^``/``v`` at the ASCII *glyphs* tier -- and nothing for *Unsorted*."""
    if mode not in SORT_ASCENDS:
        return ""
    ascending = SORT_ASCENDS[mode] != reverse
    if glyphs <= glyphs_module.GLYPHS_ASCII:
        return "^" if ascending else "v"
    return "\u2191" if ascending else "\u2193"


def command_line_text(widget: Any) -> str:
    """What the command line of the screen *widget* is on holds; ``""`` with none."""
    while widget is not None:
        line = getattr(widget, "command_line", None)
        if line is not None:
            return line.value
        widget = widget.parent
    return ""


def human_size(size: int) -> str:
    """*size* bytes as ``df -h`` puts them: ``977K``, ``9.5G``, ``384G`` --
    one decimal below ten, the size column's K/M/G/T, powers of 1024.  Bytes
    under a kilobyte keep their digits."""
    value = float(size)
    for unit in ("", "K", "M", "G", "T"):
        if value < 1023.5 or unit == "T":
            break
        value /= 1024
    if not unit:
        return f"{size:,}"
    return f"{value:.1f}{unit}" if value < 9.95 else f"{value:.0f}{unit}"


class Panel(ContextMenuHost, ListViewer):
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
    emits = (ExecuteFile, OpenFile, Dropped)

    #: Whether a listing shows a Nerd Font glyph beside each name.  ``auto``
    #: means "whenever the terminal can draw one" and ``none`` refuses even
    #: then, which is what a sheet aiming at strict DOS fidelity sets.  The
    #: application's to declare rather than the kit's: navkit draws box frames
    #: and knows nothing about icons.
    icons = StyleProperty("auto", values=("auto", "none"))

    #: Where the panel is: a directory on a drive (DN's ``Drive`` and its
    #: ``CurDir``), what the panel navigates.  :attr:`path` is the same on
    #: the local disk, as the :class:`~pathlib.Path` the code before drives
    #: knew; it raises for a location elsewhere.
    location: Location = reactive(Location.of(Path(".")))
    #: Bumped to re-read a directory whose path has not changed.
    reload_token: int = reactive(0)
    #: Bumped when entries' sizes change where they stand (Alt+G's count):
    #: the list is the same list of the same entries, so nothing else moves.
    sizes_token: int = reactive(0)
    #: Set while a directory the panel has moved to is still being read on its
    #: thread, which takes a slow disk or a dead network mount longer than a
    #: frame: the rows say *Reading directory...* meanwhile.
    scanning: bool = reactive(False)
    #: *Free space*'s bytes and mount point for the directory read last;
    #: ``None`` without the box, or over a *Find:* listing.
    free_space: tuple[int, str] | None = reactive(None)
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
    #: Whether the footer -- the *Info divider* and the *Totals* and *Free
    #: space* lines under the listing -- is shown.  Alt+I flips it, per panel;
    #: a departure, DN had only the *Display* boxes for it.
    show_info: bool = reactive(True)
    #: How the listing is ordered, one of :data:`SORT_MODES`: DN's ``SortMode``,
    #: per panel, seeded from the *New Manager defaults* and changed by Alt+B.
    sort_mode: str = reactive("name")
    #: Whether :attr:`sort_mode`'s order is turned round (:func:`order_entries`'s
    #: *reverse*): a second click on the sorted column's title.  A departure.
    sort_reverse: bool = reactive(False)
    #: The *Display* boxes this panel has: ``PanelDefaultsData.DISPLAY``'s
    #: names that are on.  None while it follows the *New Manager defaults*,
    #: read live; Alt+S's *Panel Options* gives it its own (DN's per-panel
    #: ``PanelFlags``).  Ask :meth:`shows`.
    display: Any = reactive(None)
    #: Which files are listed (DN's ``FileMask``): ``;``-separated patterns,
    #: ``-`` to leave out (:func:`navigator.lib.appearance.filetypes.in_filter`).  Per panel,
    #: set by Alt+S; directories are always listed.
    file_mask: str = reactive(filetypes.ALL_FILES)
    #: A *Find:* listing shown in place of the directory (Alt+F7, DN's
    #: ``TFindDrive``, :class:`navigator.lib.file_ops.filefind.FindListing`), or None.  It
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
    #: The same in an archive (DN's ``TArcDrive``, whose ``ShowFlags`` were
    #: ``ColumnsDefaults.Arc``): seeded from *Archives* by each archive gone
    #: into, and the only one where ``packed`` and ``ratio`` count.
    archive_columns: frozenset[str] = reactive(
        frozenset(("size", "packed", "ratio", "attributes", "owner", "date")))
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
    #: What git says of the directory shown (:mod:`navigator.lib.system.gitstatus`):
    #: a letter per entry and the branch for the title, or None outside a
    #: work tree, off the local disk, over a *Find:* listing, or with File
    #: Manager Setup's *Git status* off.  A departure: DN knew no git.
    git: Any = reactive(None)

    #: ``simple``: name and size.  ``detailed``: name, size, permissions and
    #: date in columns.  ``list``: names alone, in as many columns as fit.
    VIEW_MODES = ("simple", "detailed", "list")

    #: ``heading`` is the column-titles row the detailed and list modes draw.
    parts = ListViewer.parts + (
        "heading", "current-file", "selected-files", "selected-files-numbers",
        "totals", "totals-numbers", "free-space", "free-space-numbers", "git",
    )

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
        self._keep: tuple[Location, str, int, int] | None = None
        #: The directory the last rescan read, which tells a re-read (keep
        #: the tags) from a move (drop them).
        self._listed: Any = None
        #: The archive the panel holds open (:meth:`_hold_archive`), by its
        #: location, or None.
        self._archive: Location | None = None
        #: Whether the panel is at ``root:`` and holds the root helper open
        #: (:meth:`_hold_root`), and the directory *As root* was last offered
        #: for, so a re-read of it does not ask again.
        self._at_root = False
        self._root_offered: Location | None = None
        #: The last directory on the local disk the panel showed: where it
        #: goes back to when the drive it is on closes (DN's ``cmCloseLinked``).
        self.local_anchor: Location = Location.of(Path("."))
        #: Counts the reads started, so one that lands after a later one was
        #: asked for is dropped; and the read still on its thread, if any.
        self._generation = 0
        self._pending: _ScanRequest | None = None
        #: A press that may become a drag, or one under way: its row, its
        #: label once the pointer has moved, and the entries it carries.
        self._drag: dict[str, Any] | None = None
        #: A right-button drag tagging rows, DN's way (*Right button* set to
        #: select): what every row it passes gets -- tagged or not -- and the
        #: row it last reached.
        self._right_mark: tuple[bool, int] | None = None
        #: What stops the read's directory counting (*Directory length*).
        self._scan_job: ScanJob | None = None
        #: The directory being watched (*Auto refresh panels*), and the
        #: re-read a change on it has asked for, waiting out REFRESH_DELAY.
        self._watch: dirwatch.Watch | None = None
        self._refresh: asyncio.TimerHandle | None = None
        #: Set on the watcher's thread by the first change after a re-read,
        #: cleared on the loop when the next re-read starts: what keeps a copy
        #: writing into this directory -- a change per block written -- from
        #: costing the loop a wake-up per block.
        self._heard = False
        #: Counts the git reads started, so one that lands after a later one
        #: was asked for is dropped.
        self._git_generation = 0
        #: The git directory being watched for the user's ``git add``,
        #: ``commit`` and ``checkout`` -- which change it and not the directory
        #: shown -- the read again a change asked for, and whether the
        #: watcher's thread has told the loop already, as for :attr:`_watch`.
        self._git_watch: dirwatch.Watch | None = None
        self._git_watched: Path | None = None
        self._git_refresh: asyncio.TimerHandle | None = None
        self._git_heard = False
        # Seeded, not bound: Ctrl+H toggles it per panel.
        self.show_hidden = SETTINGS.system.show_hidden
        self.sort_mode = SETTINGS.panel_defaults.sort_by
        self.sort_reverse = SETTINGS.panel_defaults.sort_reverse and self.sort_mode != "unsorted"
        self.view_mode = SETTINGS.panel_defaults.view_mode
        self.columns = SETTINGS.column_defaults.columns(False)
        self.archive_columns = SETTINGS.column_defaults.columns(False, archive=True)
        if path is not None:
            self.location = Location.of(path)
        #: A departure: the panel's options on its bottom frame, right-aligned
        #: before the corner as the editor's are, each lit while on and
        #: switched by a click (``option_items.panel_items``); File Manager
        #: Setup's *Option flags* shows them.  A quick search's label, centred
        #: on the same row, comes first: the strip drops items to keep clear.
        self.options = self.add(PanelOptionStrip(name="options"))
        self.options.target = self
        self.options.items = panel_items(self)
        self.options.room = bind(lambda s: s.parent._options_room())
        self.options.width = bind(lambda s: s.used_width)
        self.options.height = 1
        self.options.x = bind(lambda s: max(0, s.parent.width - 3 - s.width))
        self.options.y = bind(lambda s: max(0, s.parent.height - 1))
        self.options.visible = bind(lambda s: s.parent.framed and s.parent.error is None
                                    and SETTINGS.file_manager.show_options)

    def _options_room(self) -> int:
        """The columns the option strip may take: up to the quick search's
        label while one runs, else the bottom frame less its corners."""
        footer = self.footer_text()
        start = self.label_x(footer) + len(footer) + 1 if footer else 1
        return max(0, self.width - 3 - start)

    @property
    def path(self) -> Path:
        """The directory shown, on the local disk; :class:`RemoteLocation`
        (a ``TypeError``) when the panel is on another drive -- code that
        means to work anywhere reads :attr:`location`."""
        return self.location.local

    @path.setter
    def path(self, value: Path | str | Location) -> None:
        self.location = Location.of(value)

    @property
    def drive(self) -> Drive:
        """The drive the panel is on (:func:`navigator.lib.drives.drive_of`);
        :class:`~navigator.lib.drives.DriveGone` once it has closed."""
        return drive_of(self.location)

    def entry_location(self, entry: DirEntry) -> Location:
        """Where *entry* is: in the directory shown, or a *Find:* entry's own."""
        if entry.directory is not None:
            return Location.of(entry.directory) / entry.name
        return self.location / entry.name

    def mounted(self) -> None:
        # Before ListViewer's two, because a rescan replaces the very list
        # they are about to clamp a cursor onto.
        effect(self, Panel._rescan)
        super().mounted()
        effect(self, Panel._end_search_unfocused)
        effect(self, Panel._follow_column_titles)
        effect(self, Panel._watch_directory)
        effect(self, Panel._hold_archive)
        effect(self, Panel._hold_root)
        effect(self, Panel._follow_git)
        effect(self, Panel._watch_git)

    def unmounting(self) -> None:
        self._stop_watching()
        self._stop_watching_git()
        self._let_go_of_archive()
        self._let_go_of_root()
        super().unmounting()

    # -- the archive the panel is in -----------------------------------------

    def _hold_archive(self) -> None:
        """While the panel is in an archive it holds it open; the last panel
        out closes it (DN's ``TArcDrive.Done`` once ``ChangeUp`` left it)."""
        outer = self.location.outer
        with untracked():
            if outer == self._archive:
                return
            self._let_go_of_archive()
            if outer is not None:
                from navigator.lib.drives import archive

                archive.hold(outer, self)
                self._archive = outer
                # ``TArcDrive.Init``: a new drive, *Archives*' columns.
                self.archive_columns = SETTINGS.column_defaults.columns(False, archive=True)

    def _let_go_of_archive(self) -> None:
        outer, self._archive = self._archive, None
        if outer is None:
            return
        from navigator.lib.drives import archive

        drive = archive.leave(outer, self)
        if drive is not None:
            try:
                # A file fetched from a server goes with it: not on the loop.
                asyncio.get_running_loop().run_in_executor(None, drive.close)
            except RuntimeError:
                drive.close()

    # -- browsing as root (a departure; navigator.lib.system.elevate) ----------

    def _hold_root(self) -> None:
        """While the panel is at ``root:`` it holds the root helper open
        (``root.hold``); the last panel to leave lets it go."""
        from navigator.lib.drives import root

        location = self.location
        at_root = location.site == root.ROOT_SITE
        with untracked():
            if at_root and not self._at_root:
                root.hold(self)
                self._at_root = True
                app = self.application
                if app is not None:
                    # Come to by a way that asked nothing -- a saved desktop,
                    # the command line: the read before the hold found no
                    # drive, and root access may not be open at all.
                    app.spawn(self._arrived_at_root(location))
            elif not at_root and self._at_root:
                self._let_go_of_root()

    def _let_go_of_root(self) -> None:
        if not self._at_root:
            return
        from navigator.lib.drives import root
        from navigator.lib.system.elevate import ELEVATION

        self._at_root = False
        if root.leave(self):
            try:
                asyncio.get_running_loop().run_in_executor(None, ELEVATION.release)
            except RuntimeError:
                ELEVATION.release()

    async def _arrived_at_root(self, location: Location) -> None:
        """At ``root:`` with nothing asked: read again once root access is
        open -- *Open it as root?* if it is not -- or, declined, the disk's
        own place shown instead (not asked about again)."""
        from navigator.lib.drives import root
        from navigator.lib.system.elevate import ELEVATION

        if not ELEVATION.running:
            from navigator.widgets.file_ops.as_root import reach_root

            if not await reach_root(self.application, location):
                if self.location == location:
                    plain = root.on_disk(location)
                    self._root_offered = plain
                    self.location = plain
                return
        if self.location == location:
            self.reload()
            # Watched again: the watch set up as the panel came here found
            # no drive mounted yet, and nothing else moves it to look again.
            self._watch_directory()

    def _plain_where_readable(self, location: Location) -> Location:
        """A ``root:`` place the user may read is the disk's own again."""
        from navigator.lib.drives import root

        return root.on_disk(location) if root.readable_plainly(location) else location

    def _offer_root(self, path: Location) -> None:
        """A directory the panel came to and may not read: *As root* -- at
        once, unasked, while root access is open already; else asked, once
        for that directory.  Yes puts the panel at ``root:`` there."""
        if path == self._root_offered:
            return
        self._root_offered = path
        app = self.application
        if app is not None:
            app.spawn(self._go_root(path))

    async def _go_root(self, path: Location) -> None:
        from navigator.lib.drives import root
        from navigator.lib.system.elevate import ELEVATION
        from navigator.widgets.file_ops.as_root import ask_as_root

        if not await asyncio.to_thread(ELEVATION.available):
            return
        if not ELEVATION.running:
            message = tr("Cannot read {path}: {error}").format(path=str(path), error=self.error or "")
            if not await ask_as_root(self.application, message):
                return
        if self.location == path:  # not moved on meanwhile
            # Held -- and so mounted -- before the move: the read the move
            # starts must find the drive.
            if not self._at_root:
                root.hold(self)
                self._at_root = True
            self.location = root.root_location(path)

    # -- auto refresh --------------------------------------------------------

    def _watch_directory(self) -> None:
        """Watch the directory shown, while *Auto refresh panels* is on.

        Not a *Find:* listing, whose entries are from anywhere.  With no
        application there is no loop to hear a change on, and nothing is
        watched: a test driving the model reads only when it says so.
        """
        location = self.location
        wanted = SETTINGS.file_manager.auto_refresh and self.found is None
        with untracked():
            app = self.application
            self._stop_watching()
            if not wanted or app is None:
                return
            try:
                drive = drive_of(location)
            except DriveGone:
                return
            self._watch = drive.watch(location, lambda: self._heard_change(app))

    def _heard_change(self, app: Any) -> None:
        """On the watcher's thread: tell the loop, unless it has been told already."""
        if self._heard:
            return
        self._heard = True
        app.call_from_thread(self._changed_on_disk)

    def _stop_watching(self) -> None:
        if self._watch is not None:
            self._watch.cancel()
            self._watch = None
        if self._refresh is not None:
            self._refresh.cancel()
            self._refresh = None
        self._heard = False

    def _changed_on_disk(self) -> None:
        """The watched directory changed: re-read it once the burst is over."""
        if self._watch is None or self._refresh is not None:
            return
        self._refresh = asyncio.get_running_loop().call_later(REFRESH_DELAY, self._refresh_now)

    def _refresh_now(self) -> None:
        self._refresh = None
        if self._watch is None:
            return
        if self._pending is not None:
            # A slow directory is still being read: re-read after it, not over it.
            self._refresh = asyncio.get_running_loop().call_later(REFRESH_DELAY, self._refresh_now)
            return
        # Before the read, so a change made while it runs asks for another.
        self._heard = False
        self.reload()
        app = self.application
        if app is not None:
            app.post_event(WakeEvent())

    # -- git -----------------------------------------------------------------

    def _follow_git(self) -> None:
        """Read git again whenever a listing lands -- every re-read, Ctrl+R,
        an auto refresh -- or File Manager Setup's *Git status* changes.

        After the listing rather than in its read, so a slow ``git status``
        never holds the listing up.  Only the local disk outside an archive,
        never a *Find:* listing.  With no application it reads nothing, as
        :meth:`_watch_directory` watches nothing, so model tests stay
        deterministic; before the loop runs it waits for the read.
        """
        _ = self.items  # read for the dependency: replaced by every read landed
        _ = self.error, self.found, self.location, self.scanning
        _ = SETTINGS.file_manager.git_status
        with untracked():
            self._read_git()

    def _read_git(self) -> None:
        """Start a read of git for the directory shown, or say there is none."""
        self._git_generation += 1
        generation = self._git_generation
        location = self.location
        app = self.application
        if self.scanning:
            return  # the listing's landing reads again
        if (app is None or not SETTINGS.file_manager.git_status
                or not location.is_local or location.outer is not None
                or self.found is not None or self.error is not None):
            self.git = None
            return
        future = _SCANNER.submit(gitstatus.read, location.local)
        if not app.is_running:
            # Navigator's first listing, before the loop starts: waited for,
            # as the listing itself is (:meth:`_rescan`).
            self.git = future.result()
            return
        app.spawn(self._await_git(generation, location, future))

    async def _await_git(self, generation: int, location: Location,
                         future: concurrent.futures.Future[Any]) -> None:
        state = await asyncio.wrap_future(future)
        if generation != self._git_generation or self.location != location:
            return  # read again, or somewhere else, since
        self.git = state
        app = self.application
        if app is not None:
            app.post_event(WakeEvent())

    def _watch_git(self) -> None:
        """Watch the git directory while *Auto refresh panels* is on: the
        user's ``git add`` changes the index there, not the directory shown."""
        git = self.git
        wanted = git.git_dir if git is not None and SETTINGS.file_manager.auto_refresh else None
        with untracked():
            if wanted == self._git_watched:
                return
            self._stop_watching_git()
            app = self.application
            if wanted is None or app is None:
                return
            self._git_watched = wanted
            self._git_watch = dirwatch.watch(wanted, lambda: self._heard_git(app))

    def _heard_git(self, app: Any) -> None:
        """On the watcher's thread: tell the loop, unless it has been told already."""
        if self._git_heard:
            return
        self._git_heard = True
        app.call_from_thread(self._git_changed)

    def _git_changed(self) -> None:
        """The git directory changed: read git again once the burst is over."""
        if self._git_watch is None or self._git_refresh is not None:
            return
        self._git_refresh = asyncio.get_running_loop().call_later(REFRESH_DELAY, self._git_refresh_now)

    def _git_refresh_now(self) -> None:
        self._git_refresh = None
        if self._git_watch is None:
            return
        # Before the read, so a change made while it runs asks for another.
        self._git_heard = False
        self._read_git()

    def _stop_watching_git(self) -> None:
        if self._git_watch is not None:
            self._git_watch.cancel()
            self._git_watch = None
        if self._git_refresh is not None:
            self._git_refresh.cancel()
            self._git_refresh = None
        self._git_watched = None
        self._git_heard = False

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
        path = self.location
        show_hidden = self.show_hidden
        sort = self.sort_mode
        reverse = self.sort_reverse
        mask = self.file_mask
        found = self.found
        _ = self.display  # Alt+S re-reads, as DN's ``Setup`` did (``RereadDir``)
        if found is not None and Location.of(found.origin) != path:
            # The panel went somewhere: the *Find:* listing is left behind.
            with untracked():
                self.found = found = None
        with untracked():
            # The defaults are read at each read, not followed: changing them
            # re-sorts a panel following them at its next read.
            flags = {"executables_first": self.shows("executables_first"),
                     "archives_first": self.shows("archives_first"),
                     "reverse": reverse, "mask": mask}
            dir_length = self.shows("directory_length")
            free = self.shows("free_space")
        if self._scan_job is not None:
            self._scan_job.stop()  # the counting of a read this one supersedes
        self._scan_job = None
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
                                               archives_first=flags["archives_first"], reverse=reverse), None)
            return
        if found is not None:
            future = _SCANNER.submit(restat_found, list(found.entries), show_hidden, sort, **flags)
        else:
            job = self._scan_job = ScanJob() if dir_length else None
            future = _scanner_for(path).submit(_read_location, path, show_hidden, sort, free=free,
                                               dir_length=dir_length, job=job, **flags)
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

    def _apply(self, request: _ScanRequest, entries: list[DirEntry], error: str | None,
               free: tuple[int, str] | None = None) -> None:
        """Show what a read of ``request.path`` found."""
        path = request.path
        self._pending = None
        self._scan_job = None
        self.scanning = False
        self.free_space = free
        self.items = entries
        self.error = error
        # Peeked, not read: the rescan must not depend on the tags, or every
        # Insert would re-read the directory.
        marked = peek(self, Panel.marked)
        where = request.where if request.where is not None else path
        if path.is_local and error is None:
            self.local_anchor = path
        if (path.is_local and error is not None and where != self._listed
                and os.path.isdir(path.local) and not os.access(path.local, os.R_OK | os.X_OK)):
            # A directory come to and refused: *As root* (a departure).
            self._offer_root(path)
        if where != self._listed and where == path and error is None and path.outer is None:
            # ``AddToDirectoryHistory``: a directory the panel has come to --
            # not one inside an archive, which is no place to come back to.
            self._remember_directory(path)
        if where != self._listed:
            marked = frozenset()
            self.quick_search = None
            self.name_scroll = 0
            # The last directory's letters are not this one's names'.
            self.git = None
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
            self._keep = (self.location, key or entry.key, self.cursor, self.scroll)
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
        *Find:* listing, :attr:`archive_columns` in an archive, :attr:`columns`
        over a directory."""
        if self.found is not None:
            return self.find_columns
        return self.archive_columns if self.location.outer is not None else self.columns

    @shown_columns.setter
    def shown_columns(self, columns: frozenset[str]) -> None:
        if self.found is not None:
            self.find_columns = columns
        elif self.location.outer is not None:
            self.archive_columns = columns
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
        self.location = Location.of(entry.directory)

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
        self._return_to = self.location.name if entry.name == ".." else None
        if self.location.is_local:
            self.path = (self.path / entry.name).resolve()
        elif entry.name == ".." and self.location.is_root:
            self.go_up()
        else:
            # Another drive's links are its own to follow: the name is enough.
            self.location = self._plain_where_readable((self.location / entry.name).normalized())

    def go_up(self) -> None:
        """Go to the parent directory, the cursor on the one just left.

        DN's ``_CtrlPgUp``: what choosing ``..`` does, from anywhere in the
        listing.  At the root there is nowhere to go, so the cursor goes to
        the top as Home would -- a departure: DN did nothing there.
        """
        if self.found is not None:
            self.leave_found()
            return
        if not self.location.is_local:
            self._go_up_elsewhere()
            return
        parent = (self.path / "..").resolve()
        if parent == self.path:
            self.move_cursor(-len(self.items))
            return
        self._return_to = self.path.name
        self.path = parent

    def _go_up_elsewhere(self) -> None:
        """:meth:`go_up` on a drive other than the disk: the parent by name,
        and at the drive's root wherever its ``ChangeUp`` says -- an archive's
        is back on the drive it was opened from, the cursor on its file; the
        Trash's is back in the last local directory (``leaves_to_anchor``)."""
        location = self.location
        if not location.is_root:
            self._return_to = location.name
            self.location = self._plain_where_readable(location.parent)
            return
        try:
            drive = drive_of(location)
            up = drive.change_up(location)
            if up is None and drive.leaves_to_anchor:
                self._return_to = None
                self.location = self.local_anchor
                return
        except DriveGone:
            up = None
        if up is None:
            self.move_cursor(-len(self.items))
            return
        self.location, self._return_to = up

    # -- tagging -------------------------------------------------------------

    def is_marked(self, item: DirEntry) -> bool:
        return item.key in self.marked

    def untag_paths(self, paths: Iterable[Path]) -> None:
        """Take the tags off the entries at *paths*: what a copy, a move or an
        erase leaves of the ones it finished."""
        done = {Location.of(path) for path in paths}
        if done:
            self.untag(item for item in self.items if self.entry_location(item) in done)

    def tag_paths(self, locations: Iterable[Location]) -> None:
        """Tag the entries at *locations* this panel lists: what Verify
        checksums leaves on the files that did not match."""
        def key(location: Location) -> Location:
            location = location.normalized()
            return Location.of(Path(location.path).absolute()) if location.is_local else location

        wanted = {key(location) for location in locations}
        if not wanted:
            return
        keys = {item.key for item in self.items
                if item.name != ".." and key(self.entry_location(item)) in wanted}
        if keys - self.marked:
            self.marked = self.marked | keys

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
        if entry is not None and not entry.is_dir and self._may_enter_archive(entry):
            # Read on a thread: one that is no archive after all runs below.
            self.spawn(self._enter_or_run(entry))
            return True
        if entry is not None and not entry.is_dir:
            await self._run_file(entry)
            return True
        self.enter()
        return True

    def _may_enter_archive(self, entry: DirEntry) -> bool:
        """DN's ``fmoEnterArchives`` test: *Enter opens an archive* on, a file
        whose name the *archive* file type takes, and the panel not in an
        archive already -- DN opened none from inside another.  Whether it
        is one is the file's to say (:func:`navigator.lib.drives.archive.open_archive`),
        by what is in it, as ``ArcViewer`` read the signature."""
        return (SETTINGS.file_manager.enter_opens_archive and self.location.outer is None
                and stat.S_ISREG(entry.mode) and filetypes.group_of(entry.name) == "archive")

    async def _enter_or_run(self, entry: DirEntry) -> None:
        from navigator.widgets.drives.archives import enter_archive

        if not await enter_archive(self, self.entry_location(entry)):
            await self._run_file(entry)

    async def _run_file(self, entry: DirEntry) -> None:
        """Enter on a file: :class:`ExecuteFile` for one the user may run,
        :class:`OpenFile` for any other."""
        if not self.location.is_local:
            # Nothing on another drive can be run from here, so an executable
            # is opened as any file is: a departure DN never met, its link
            # drive having no programs of its own to run.
            if stat.S_ISREG(entry.mode):
                await self.emit(OpenFile(self.entry_location(entry)))
            return
        path = entry.path_in(self.path)
        if path.is_file() and os.access(path, os.X_OK):
            await self.emit(ExecuteFile(path))
        elif path.is_file():
            await self.emit(OpenFile(path))

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

    def set_options(self, sort: str, display: frozenset[str], mask: str, reverse: bool = False) -> None:
        """Alt+S's answer (DN's ``Setup``): this panel's order and its
        direction, *Display* boxes and file mask, and one re-read keeping the
        cursor on its entry."""
        if sort not in SORT_MODES:
            raise ValueError(f"unknown sort mode {sort!r}")
        entry = self.selected
        if entry is not None:
            self._keep = (self.location, entry.key, self.cursor, self.scroll)
        self.sort_reverse = reverse and sort != "unsorted"
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
            self._keep = (self.location, entry.key, self.cursor, self.scroll)
        self.file_mask = mask

    def sort_by(self, mode: str, reverse: bool = False) -> None:
        """Order the listing by *mode*: what Alt+B's choice does (``CM_SortBy``),
        *reverse* turning it round (a column title's second click).

        A re-read, as DN's ``RereadDir`` was, keeping the cursor on its entry;
        the order it already has changes nothing.
        """
        if mode not in SORT_MODES:
            raise ValueError(f"unknown sort mode {mode!r}")
        if mode == "unsorted":
            reverse = False
        if (mode, reverse) == (self.sort_mode, self.sort_reverse):
            return
        entry = self.selected
        if entry is not None:
            self._keep = (self.location, entry.key, self.cursor, self.scroll)
        self.sort_mode = mode
        self.sort_reverse = reverse

    #: The sort modes a click on a column's title steps through, each up and
    #: then reversed; the other columns sort nothing.  The name's title takes
    #: the extension too, there being no column of its own for it.
    COLUMN_SORTS = {"name": ("name", "extension"), "size": ("size",), "attributes": ("attributes",), "owner": ("owner",), "date": ("time",)}

    def heading_at(self, x: int, y: int) -> str | None:
        """The key of the column whose title is at *x*, *y*, or None."""
        if not self.header or self.view_mode == "simple" or self.error is not None or y != self.inset:
            return None
        if self.view_mode == "list":
            return "name" if self.inset <= x < self.inset + self.inner_width else None
        for key, left, width in self.detail_columns:
            if left <= x < left + width:
                return key
        return None

    def sort_by_column(self, key: str) -> bool:
        """A click on column *key*'s title: the next of its orders -- each of
        :data:`COLUMN_SORTS`' modes, then that reversed, wrapping -- or its
        first when sorted by another column.  False for a column that sorts
        nothing.  Name's: name, name reversed, extension, extension reversed."""
        modes = self.COLUMN_SORTS.get(key)
        if modes is None:
            return False
        steps = [(mode, reverse) for mode in modes for reverse in (False, True)]
        here = (self.sort_mode, self.sort_reverse)
        mode, reverse = steps[(steps.index(here) + 1) % len(steps)] if here in steps else steps[0]
        self.sort_by(mode, reverse=reverse)
        return True

    def sort_arrow(self, key: str) -> str:
        """What follows column *key*'s title: ``↑`` sorted by it ascending,
        ``↓`` descending (``^``/``v`` in ASCII), else nothing; ``.`` before
        the arrow on the name's when it is the extension that sorts."""
        mode = self.sort_mode
        if mode not in self.COLUMN_SORTS.get(key, ()):
            return ""
        return ("." if mode == "extension" else "") + self.direction_arrow(mode, self.sort_reverse)

    def direction_arrow(self, mode: str, reverse: bool) -> str:
        """:func:`direction_arrow` at this panel's glyph tier."""
        return direction_arrow(mode, reverse, self.glyphs)

    def toggle_hidden(self) -> None:
        """Ctrl+H: hide the dot-files, or show them again.

        A re-read like :meth:`reload`'s, so the cursor stays on its entry, or
        where it was if that entry is the one just hidden.  A tag on a name
        that goes is dropped with it, so nothing unseen stays selected.
        """
        entry = self.selected
        if entry is not None:
            self._keep = (self.location, entry.key, self.cursor, self.scroll)
        self.show_hidden = not self.show_hidden

    def toggle_info(self) -> None:
        """Alt+I: hide the footer under the listing, or show it again; the
        listing takes the rows it gives up."""
        self.show_info = not self.show_info

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

        Esc ends the search where it stands.  Any other key that is not the
        search's ends it too and is declined, so it goes on to do what it
        always does -- Enter descends into what was found, Down moves, F3
        views.
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
        return event.matches("escape")

    def _end_search_unfocused(self) -> None:
        """The search ends when the keyboard leaves the panel."""
        if not self.focus_within and peek(self, Panel.quick_search) is not None:
            self.quick_search = None

    @property
    def search_label(self) -> str:
        """What the footer says before the typed text while searching."""
        return f" {tr('Search:')} "

    def cursor_position(self) -> tuple[int, int] | None:
        """While searching, the caret after what has been typed, on the footer."""
        text = self.quick_search
        if text is None or not self.framed:
            return None
        footer = self.footer_text()
        x = self.label_x(footer) + len(self.search_label) + len(text)
        return min(x, self.width - 2), self.height - 1

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if self._drag is not None and event.action in ("move", "release"):
            return self._dragging(event)
        if event.button == "right" or self._right_mark is not None:
            if self._right_mark is not None or (
                event.action == "press" and self._right_selects()
            ):
                return self._right_marking(event)
        if event.action == "press" and not event.is_wheel:
            self.quick_search = None
        taken = await super().on_mouse_click(event)
        if (not taken and not self.inert and event.action == "press" and event.button == "left"
                and not event.is_wheel):
            key = self.heading_at(event.x, event.y)
            if key is not None and self.sort_by_column(key):
                return True
        if (taken and event.action == "press" and event.button == "left"
                and SETTINGS.file_manager.drag_drop_columns):
            # File Manager Setup's *Drag-and-drop*: the press may be a drag's
            # start, which the first move with the button held decides.
            index = self.index_at(event.x, event.y)
            app = self.application
            if index is not None and app is not None:
                self._drag = {"index": index, "label": None, "entries": None}
                app.capture_mouse(self)
        return taken

    # -- the right button -----------------------------------------------------
    #
    # File Manager Setup's *Right button*: the context menu (the default; see
    # ``ContextMenuHost``), or DOS Navigator's own use of it, which selected.

    @staticmethod
    def _right_selects() -> bool:
        return SETTINGS.file_manager.right_button == "select"

    def _right_marking(self, event: MouseClickEvent) -> bool:
        """DN's right button: a press toggles the row's tag, and a drag gives
        every row it passes the same one.

        ``FLPANELX.PAS``: ``MSelect`` when the right button is down,
        ``SelectFlag := not Selected`` from the row pressed, and the loop
        applying it to each row the pointer crosses; past the top or the
        bottom of the rows the list scrolls a row at a time, as it did.
        ``..`` is never tagged.
        """
        app = self.application
        if event.action == "press":
            if self.inert:
                return False
            self.quick_search = None
            index = self.index_at(event.x, event.y)
            if index is None:
                return True
            entry = self.items[index]
            self.cursor = index
            flag = not self.is_marked(entry)
            self._tag_rows(index, index, flag)
            self._right_mark = (flag, index)
            if app is not None:
                app.capture_mouse(self)
            return True
        if self._right_mark is None:
            return False
        flag, last = self._right_mark
        if event.action == "release":
            self._right_mark = None
            return True
        if event.action != "move":
            return True
        index = self.index_at(event.x, event.y)
        if index is None:
            row = event.y - self.inset - self.header
            if row < 0 and last > 0:
                index = last - 1
            elif row >= self.rows and last < len(self.items) - 1:
                index = last + 1
            else:
                return True
        if index != last:
            step = 1 if index > last else -1
            self._tag_rows(last + step, index, flag)
            self.cursor = index
            self._right_mark = (flag, index)
        return True

    def _tag_rows(self, first: int, last: int, flag: bool) -> None:
        """Tag (*flag*) or untag every row from *first* to *last*, either way round."""
        low, high = min(first, last), max(first, last)
        keys = {item.key for item in self.items[low:high + 1] if item.name != ".."}
        if keys:
            self.marked = (self.marked | keys) if flag else (self.marked - keys)

    # -- the context menu -------------------------------------------------------

    async def on_context_menu(self, event: Any) -> bool:
        """Declined while the right button selects, which the press did."""
        if self._right_selects():
            return False
        return await super().on_context_menu(event)

    def prepare_context(self, x: int, y: int) -> None:
        """The cursor to the row clicked, as a left click puts it; the tags
        stay, and the menu acts on them when there are any."""
        self.quick_search = None
        index = self.index_at(x, y)
        if index is not None:
            self.cursor = index

    def context_point(self) -> tuple[int, int]:
        """Under the cursor's row, a little way in from its name."""
        row = self.cursor - self.scroll + self.inset + self.header
        if self.view_mode == "list":
            for first, left, width in self.list_columns:
                if first <= self.cursor < first + self.rows:
                    return left + 2, self.cursor - first + self.inset + self.header + 1
        return 3, min(max(row + 1, 0), max(0, self.height - 1))

    def context_menu(self) -> ContextMenu:
        """The File menu's everyday operations, for what the click is on.

        What an operation acts on is DN's ``GetSelection``: the tagged
        entries when there are any, else the one at the cursor.  So *View*
        and *Edit* are offered for a file with nothing tagged, the copy, move,
        link, erase and attribute operations for any selection, *Count
        directory length* for a directory, and *Make directory* and the
        selection's three always.  Whoever runs the File menu -- ``Manager``
        -- runs these, from this panel, and greys what does not apply.
        Built each time, so its captions follow the language.
        """
        from navigator.widgets.manager.commands import (
            ArcTest,
            ChangeAttributes,
            ChangeInactive,
            Copy,
            CountLength,
            CutToClipboard,
            Delete,
            Edit,
            ExtractArchive,
            ExtractTo,
            GoToFile,
            InvertSelection,
            MakeDirectory,
            MakeLink,
            OpenWith,
            PasteFromClipboard,
            PutInClipboard,
            RenameMove,
            RestoreTrash,
            SelectGroup,
            UnselectGroup,
            View,
        )
        from navigator.widgets.shell.commands import InsertName, InsertPath

        menu = ContextMenu()
        entry = self.selected
        tagged = bool(self.marked)
        on_parent = entry is None or entry.name == ".."
        if self.found is not None and not on_parent:
            # A *Find:* listing's Enter and Shift+Enter -- a departure, asked
            # for: DN had them on no menu.
            menu.add_item(tr("Go to ~f~ile"), GoToFile, "Enter")
            menu.add_item(tr("Show in ~o~ther panel"), ChangeInactive)
            menu.add_line()
        if (tagged or not on_parent) and self.location.site.scheme == "trash" and self.location.is_root:
            # The Trash (not DN's): what it is there for.
            menu.add_item(tr("Restore from Tras~h~"), RestoreTrash)
            menu.add_line()
        if not tagged and not on_parent and not entry.is_dir:
            # ``w``, not the File menu's ``v``: *Invert selection* has that here.
            menu.add_item(tr("Vie~w~"), View)
            menu.add_item(tr("~E~dit"), Edit)
            # The desktop's applications (``gio``, KIO): not DN's, and only
            # where there are some to open it in.
            from navigator.lib.system import desktop

            if desktop.program() is not None and desktop.graphical():
                menu.add_item(tr("Ope~n~ with..."), OpenWith)
            menu.add_line()
        if tagged or not on_parent:
            menu.add_item(tr("~C~opy..."), Copy)
            menu.add_item(tr("~R~ename/Move..."), RenameMove)
            menu.add_item(tr("Create ~s~ymlink..."), MakeLink)
            menu.add_item(tr("~D~elete"), Delete)
            menu.add_item(tr("File ~A~ttributes..."), ChangeAttributes)
            menu.add_line()
        # The clipboard's three, a departure as the keys are; theirs are
        # ``by_key`` too, so named here.
        if tagged or not on_parent:
            menu.add_item(tr("Cop~y~ to clipboard"), PutInClipboard, key_label("ctrl+c"))
            menu.add_item(tr("Cut to c~l~ipboard"), CutToClipboard, key_label("ctrl+x"))
        menu.add_item(tr("Paste from clip~b~oard"), PasteFromClipboard, key_label("ctrl+v"))
        menu.add_line()
        # The archive's own two in one, and Shift+F2 on an archive outside one
        # -- a departure, asked for, as the menu is.  ``x`` for both: an
        # archive panel offers no *Extract archive*.
        if self.location.outer is not None:
            menu.add_item(tr("E~x~tract to..."), ExtractTo, "Shift-F2")
            menu.add_item(tr("Test arc~h~ive"), ArcTest)
            menu.add_line()
        elif any(_archive_file(item) for item in (self.marked_entries if tagged else [entry])):
            menu.add_item(tr("E~x~tract archive..."), ExtractArchive, "Shift-F2")
            menu.add_line()
        if entry is not None and entry.is_dir:
            menu.add_item(tr("Count directory len~g~th"), CountLength)
        menu.add_item(tr("~M~ake directory"), MakeDirectory)
        menu.add_line()
        # Their keys are bound as ``by_key`` commands, which these are not, so
        # no live key is found: the keypad's, as the Panel menu writes them.
        menu.add_item(tr("Select grou~p~..."), SelectGroup, key_label("kp_plus"))
        menu.add_item(tr("~U~nselect group..."), UnselectGroup, key_label("kp_minus"))
        menu.add_item(tr("In~v~ert selection"), InvertSelection, key_label("kp_multiply"))
        # Ctrl+Enter and Ctrl+Shift+Enter, which DN had on no menu -- a
        # departure, asked for; the shell answers them.
        menu.add_line()
        menu.add_item(tr("~I~nsert name"), InsertName)
        menu.add_item(tr("Insert pa~t~h"), InsertPath)
        return menu

    def _dragging(self, event: MouseClickEvent) -> bool:
        """``DragMover``: the label follows the pointer, and the release drops."""
        from navigator.widgets.manager.panel.drag import TRASH, DragLabel, Dropped, drop_target, label_for

        drag, app = self._drag, self.application
        assert drag is not None
        ox, oy = self.offset()
        x, y = event.x + ox + self.x, event.y + oy + self.y
        label = drag["label"]
        if event.action == "move":
            if app is None:
                return True
            if label is None:
                entries = self._drag_entries(drag["index"])
                if not entries:
                    self._drag = None
                    app.release_mouse()
                    return True
                drag["entries"] = entries
                label = drag["label"] = app.overlay(DragLabel(label_for(entries)))
            root = app.root
            label.place(x, y, root.width, root.height)
            return True
        # The release: the label goes, and the files go where it was dropped.
        self._drag = None
        if label is None or app is None:
            return True
        label.parent.remove(label)
        where = drop_target(app, x, y, self)
        if where == TRASH:
            self.spawn(self.emit(Dropped(self, tuple(drag["entries"]), None, False, trash=True)))
        elif where is not None:
            target, panel = where
            self.spawn(self.emit(Dropped(self, tuple(drag["entries"]), target, event.shift, panel,
                                           x=x, y=y)))
        return True

    def _drag_entries(self, index: int) -> list[DirEntry]:
        """``CM_DragDropper``'s files: the tagged ones when the row is tagged,
        else the row's own -- never ``..``."""
        if not 0 <= index < len(self.items):
            return []
        entry = self.items[index]
        if self.is_marked(entry):
            return self.marked_entries
        return [] if entry.name == ".." else [entry]

    async def on_key(self, event: KeyEvent) -> bool:
        """The quick search's keys while it is on, then the listing's.

        In the list mode Left and Right move a column, as DN's did.
        Otherwise they are declined, and reach the manager's key table, which
        scrolls the names with them (:meth:`scroll_names`).
        """
        if self.quick_search is not None and not self.inert and self._search_key(event):
            return True
        if event.key == "escape" and self._scan_job is not None and self.scanning:
            # DN's ``Abort`` while counting: the box goes off for this panel,
            # and the directory is read without it.
            self._scan_job.stop()
            self.display = frozenset(name for name in PanelDefaultsData.DISPLAY
                                     if name != "directory_length" and self.shows(name))
            return True
        if self.arrows_to_line(event):
            return False
        if self.view_mode == "list" and not self.inert and self.rows and not event.alt:
            if event.key == "left":
                self.move_cursor(-min(self.rows, self.cursor))
                return True
            if event.key == "right":
                self.move_cursor(min(self.rows, len(self.items) - 1 - self.cursor))
                return True
        return await super().on_key(event)

    #: The keys File Manager Setup's *Use arrows* gives the command line.
    LINE_KEYS = ("left", "right", "home", "end")

    def arrows_to_line(self, event: KeyEvent) -> bool:
        """Whether *event* is the command line's rather than this panel's.

        Left, Right, Home and End go to a command line holding text --
        unshifted with *Use arrows* on (DN's default), with Shift held with
        it off; the other way round they are the panel's (``fmoUseArrows``,
        ``(ShiftState and 3 <> 0) xor (Options and fmoUseArrows = 0)``).
        """
        if event.key not in self.LINE_KEYS or event.ctrl or event.alt:
            return False
        if SETTINGS.file_manager.use_arrows == event.shift:
            return False
        return bool(command_line_text(self))

    #: The detailed mode's columns after the name: heading, width, and the
    #: ``DirEntry`` property that fills it.  Dropped in :data:`DROP_ORDER`
    #: when the name would get too narrow.  A width of ``None`` is measured
    #: off the listing (:meth:`_owner_width`), or off *Country support*'s
    #: format for the date (``country.stamp_width``).
    DETAIL_COLUMNS = {
        "size": ("Size", 8, "display_size"),
        "packed": ("Packed", 8, "display_packed"),
        "ratio": ("%", 4, "display_ratio"),
        "attributes": ("Attr", 9, "display_attributes"),
        "owner": ("Owner", None, "display_owner"),
        "date": ("Date", None, "display_date"),
        "path": ("Path", None, "display_path"),
    }
    DETAIL_ORDER = ("size", "packed", "ratio", "attributes", "owner", "date", "path")
    DROP_ORDER = ("owner", "attributes", "ratio", "packed", "path", "date")
    #: The columns only an archive's entries fill.
    ARCHIVE_ONLY = frozenset(("packed", "ratio"))
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
        # *Columns Setup*'s choice, the path only where entries are from
        # elsewhere, the packed size and ratio only in an archive.
        wanted, listing = self.shown_columns, self.found is not None
        in_archive = self.location.outer is not None and not listing
        shown = [key for key in self.DETAIL_ORDER
                 if key in wanted and (key != "path" or listing)
                 and (key not in self.ARCHIVE_ONLY or in_archive)]
        widths = {key: width for key, (_, width, _) in self.DETAIL_COLUMNS.items()}
        widths["owner"] = self._owner_width()
        widths["date"] = country.stamp_width()
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
        return max(len(self.heading("path")), min(longest, self.MAX_PATH_WIDTH))

    def _owner_width(self) -> int:
        """The owner column's width: its longest ``user:group``, never
        narrower than its heading nor wider than :data:`MAX_OWNER_WIDTH`."""
        longest = max((text_width(item.display_owner) for item in self.items), default=0)
        return max(len(self.heading("owner")), min(longest, self.MAX_OWNER_WIDTH))

    @computed
    def list_columns(self) -> tuple[tuple[int, int, int], ...]:
        """``(first index, x, width)`` for every list-mode column on show.

        Columns hold ``rows`` items each, from ``scroll``; each is as wide as
        its longest name (and the icon gutter), capped at half the panel so
        that a long name cannot push the second column off it.  The last may
        run past the right edge and be clipped.
        """
        rows, inner, inset = self.rows, self.inner_width, self.inset
        items, gutter = self.items, self.gutter + self.git_cells
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
        return max(0, width - self.gutter - self.git_cells)

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

    #: The cells a git letter takes at the end of a name: a blank, it, and a
    #: blank keeping it off the column divider.
    GIT_CELLS = 3

    @property
    def git_cells(self) -> int:
        """:data:`GIT_CELLS` while the directory shown is in a work tree, else none."""
        return self.GIT_CELLS if self.git is not None else 0

    def git_mark(self, item: DirEntry) -> str:
        """*item*'s letter (:mod:`navigator.lib.system.gitstatus`), or a blank."""
        git = self.git
        if git is None or item.name == ".." or item.directory is not None:
            return " "
        return git.marks.get(item.name, " ")

    def git_text(self) -> str:
        """The branch for the title, with how far it is ahead of and behind
        its upstream (``master ↑2↓1``), or ``""`` outside a work tree."""
        git = self.git
        if git is None or not git.branch:
            return ""
        up, down = ("^", "v") if self.glyphs <= glyphs_module.GLYPHS_ASCII else ("\u2191", "\u2193")
        counts = (f"{up}{git.ahead}" if git.ahead else "") + (f"{down}{git.behind}" if git.behind else "")
        return f"{git.branch} {counts}" if counts else git.branch

    @property
    def title_location(self) -> str:
        """What the title names the directory by: its path on the disk, and
        elsewhere what the drive calls it (``GetDir``)."""
        location = self.location
        if location.is_local:
            return str(location.path)
        try:
            return drive_of(location).get_dir(location)
        except DriveGone:
            return str(location)

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

        **In a git work tree the branch follows** (:meth:`git_text`), also
        not DN's: it is dropped before the path would be cut under
        :data:`MIN_NAME_WIDTH` cells to keep it.
        """
        title = self.found.title if self.found is not None else self.title_location
        mask = self.file_mask.strip()
        suffix = f" [{mask}]" if mask not in ("", filetypes.ALL_FILES) else ""
        room = max(4, self.width - 4 - 2 * self.title_margin)
        if suffix and len(suffix) > room - 4:
            suffix = suffix[: max(0, room - 8)] + "...]" if room > 12 else ""
        # The branch goes before the mask does, once the path would be cut
        # under a dozen cells to keep it.
        branch = self.git_text()
        if branch:
            branch = f"  {branch}"
            if room - len(suffix) - len(branch) < min(len(title), self.MIN_NAME_WIDTH):
                branch = ""
        space = room - len(suffix) - len(branch)
        title = self._cut_start(title, space)
        return f" {title}{suffix}{branch} "

    def footer_text(self) -> str:
        """What a search has typed, while it is searching; else nothing --
        the current file and the selection are info lines, as DN's were."""
        if self.quick_search is not None:
            return f"{self.search_label}{self.quick_search} "
        return ""

    def key_hints(self) -> list[tuple[str, str]]:
        """While searching, Ctrl+S again finds the next -- for the key bar."""
        return [("Ctrl+S", tr("Next"))] if self.quick_search else []

    # -- the info lines: TInfoView ------------------------------------------------

    #: The parts drawn as they are, from the left: a name may hold a ``~``.
    PLAIN_INFO = frozenset({"current-file"})

    @property
    def info_lines(self) -> tuple[tuple[str, str], ...]:
        """The lines under the listing, ``(text, part)``, ``~`` around what is
        bright: :attr:`_info_lines` with *Current file* laid out as it is
        read, since the rows' gutter it follows is not reactive
        (:attr:`Widget.glyphs`)."""
        return tuple(
            (self._current_file_text(self.selected) if text is None else text, part)
            for text, part in self._info_lines
        )

    @computed
    def _info_lines(self) -> tuple[tuple[str | None, str], ...]:
        """``TInfoView``'s *Current file* (its text None here), *Selected
        files*, *Totals* and *Free space*, in its order, each behind its
        *Display* box.

        With files tagged and *Selected files* off, the selection takes the
        current file's line, as DN's did.  A *Find:* listing gives the
        current file's directory a line of its own under it, as DN's find
        drive did, and so does a symlink its target (Navigator's).  That line
        is kept while the listing could need it -- always on a *Find:*
        listing, while it holds a symlink otherwise -- so the listing does
        not change height as the cursor moves.

        Totals is ``CalcTotalInfo``: the files and their bytes, directories
        not counted.  Free space is not shown over a *Find:* listing, as it
        was not over DN's find drive.
        """
        if not self.framed or self.error is not None or not self.show_info:
            return ()
        lines = []
        _ = self.sizes_token  # read for the dependency: a counted directory's bytes
        marked = self.marked_entries
        selected_files = self.shows("selected_files")
        if self.shows("current_file"):
            if marked and not selected_files:
                lines.append((self._selection_text(marked), "selected-files"))
            else:
                lines.append((None, "current-file"))
            second = self._second_line(self.selected)
            if second is not None:
                lines.append((second, "current-file"))
        if selected_files:
            lines.append((self._selection_text(marked), "selected-files"))
        if CLIP:
            # Every panel says what Ctrl+V would paste, wherever it was clipped.
            count = len(CLIP.entries)
            if CLIP.move:
                text = tr_n("Clipboard: ~{n}~ file to move", "Clipboard: ~{n}~ files to move", count)
            else:
                text = tr_n("Clipboard: ~{n}~ file to copy", "Clipboard: ~{n}~ files to copy", count)
            lines.append((text, "selected-files"))
        if self.shows("totals"):
            items = self.items
            if not any(item.name != ".." for item in items):
                text = tr("No files in this directory")
            else:
                files = [item for item in items if not item.is_dir]
                size = sum(item.size for item in files)
                total = tr_n("~{n:,}~ byte", "~{n:,}~ bytes", size)
                text = tr_n("Total: ~{n:,}~ file with {total}", "Total: ~{n:,}~ files with {total}", len(files),
                            total=total)
            lines.append((text, "totals"))
        if self.shows("free_space") and self.found is None and self.free_space:
            free, mount = self.free_space
            # Shortened as ``df -h`` does (a departure: DN gave every digit),
            # which a panel's width has room for; a kilobyte and under keeps
            # its bytes.
            if free < 1024:
                text = tr_n("~{n:,}~ free byte on ~{mount}", "~{n:,}~ free bytes on ~{mount}", free, mount=mount)
            else:
                text = tr("~{size}~ free on ~{mount}").format(size=human_size(free), mount=mount)
            lines.append((text, "free-space"))
        return tuple(lines)

    def _selection_text(self, marked: list[DirEntry]) -> str:
        """*Selected files*: DN's ``dlBytesIn`` and ``dlSelectedFiles``, or
        its ``No files selected``."""
        if not marked:
            return tr("No files selected")
        size = sum(item.size for item in marked)
        total = tr_n("{n:,} byte", "{n:,} bytes", size)
        return tr_n("~{total} in {n}~ selected file", "~{total} in {n}~ selected files", len(marked), total=total)

    def _current_file_text(self, entry: DirEntry | None) -> str:
        """*Current file*: the entry laid out as a detailed row is, in every
        mode -- :attr:`detail_columns`' columns at their places, a blank
        where each divider stands.

        DN's ``GetDown`` was name, size, date and time whatever the columns;
        following *Columns Setup* is Navigator's.  The size has every digit,
        right-aligned on the column's edge, and where that is wider than the
        column it takes the cells before it from the name.  The name starts
        where the rows' names do, the gutter left blank.
        """
        if entry is None:
            return ""
        inset = self.inset
        pieces = []
        name_x = name_width = 0
        for key, x, width in self.detail_columns:
            x -= inset
            if key == "name":
                # Under the rows' names, past the gutter their marks take.
                gutter = min(self.gutter, max(0, width - 1))
                name_x, name_width = x + gutter, width - gutter
                continue
            if key == "size":
                text = entry.info_size
                if text_width(text) > width:
                    start = max(name_x + 2, x + width - text_width(text))
                    name_width = min(name_width, start - name_x - 1)
                    width = x + width - start
                    x = start
                text = fit_text(text, width, self.ellipsis)
                text = " " * (width - text_width(text)) + text
            elif key == "path":
                text = self._cut_start(entry.display_path, width)
            else:
                text = fit_text(getattr(entry, self.DETAIL_COLUMNS[key][2]), width, self.ellipsis)
            pieces.append((x, text))
        line = fit_text(entry.name, max(1, name_width), self.ellipsis)
        line = " " * name_x + line
        for x, text in pieces:
            line += " " * max(0, x - text_width(line)) + text
        return line

    def _second_line(self, entry: DirEntry | None) -> str | None:
        """The line under *Current file*, or None where the listing needs
        none: the directory of a *Find:* listing's file, unless the path
        column shows it, ``-> target`` for a symlink, blank for anything else
        while the line is kept."""
        if self.found is not None:
            if any(key == "path" for key, _, _ in self.detail_columns):
                return None  # the path column already says it
            if entry is None:
                return ""
            where = str(entry.directory) if entry.directory is not None else str(self.location)
            return self._cut_start(where, self.inner_width)
        if any(item.trashed is not None for item in self.items):
            # The Trash (not DN's): where the entry came from, and when.
            if entry is None or entry.trashed is None:
                return ""
            origin, deleted = entry.trashed
            if deleted is None:
                template = tr("From {path}")
            else:
                template = tr("From {path}, deleted {when}").replace("{when}", country.stamp(deleted))
            # The path gives up its start, as a *Find:* listing's does; the date stays.
            room = self.inner_width - text_width(template.replace("{path}", ""))
            text = template.replace("{path}", self._cut_start(origin or tr("an unknown place"), max(1, room)))
            return fit_text(text, self.inner_width, self.ellipsis)
        if not SETTINGS.file_manager.link_line or not any(item.is_link for item in self.items):
            return None
        if entry is None or entry.link_target is None:
            return ""
        return fit_text(f"-> {entry.link_target}", self.inner_width, self.ellipsis)

    @computed
    def info_height(self) -> int:
        """The rows the info lines take, with File Manager Setup's *Info
        divider* above them (``fmsDivider``) -- none without a line to divide."""
        lines = len(self._info_lines)
        return lines + (1 if lines and SETTINGS.file_manager.info_divider else 0)

    @computed
    def rows(self) -> int:
        """How many listing lines fit between the frames, the header and the info lines."""
        return max(0, self.height - 2 * self.inset - self.header - self.info_height)

    def render_info(self, surface: Surface) -> None:
        """The divider and the info lines, centred, between the listing and the frame."""
        height = self.info_height
        if not height:
            return
        left, width = self.inset, self.inner_width
        y = self.height - self.inset - height
        if SETTINGS.file_manager.info_divider:
            # DN's ``─``, ``┴`` where a column divider comes down onto it.
            single = glyphs_module.charset("single", self.glyphs)[4]
            tee = glyphs_module.joins("single", self.glyphs)[3]
            divider = self.part_style("divider")
            surface.draw_text(left, y, single * width, divider, width)
            if self.view_mode != "simple":
                spans = self._column_spans()
                for index, (_, x, span) in enumerate(spans[:-1]):
                    if x + span < left + width:
                        surface.draw_text(x + span, y, tee, divider, 1)
            if self.framed:
                # Joined to the frame at both ends, ``├``/``┤`` (``╟``/``╢``
                # on a double one), in the frame's colour.
                vertical = self.box_charset()[5]
                left_tee, right_tee = self.box_joins()[:2]
                for edge, tee in ((left - 1, left_tee), (left + width, right_tee)):
                    char, style = surface.get(edge, y)
                    if char == vertical:
                        surface.set_cell(edge, y, tee, style)
            y += 1
        for text, part in self.info_lines:
            surface.fill(left, y, width, 1, " ", self.part_style(part))
            if part in self.PLAIN_INFO:
                surface.draw_text(left, y, text, self.part_style(part), width)
                y += 1
                continue
            plain = text.replace("~", "")
            x = left + max(0, (width - text_width(plain)) // 2)
            bright = False
            for piece in text.split("~"):
                room = left + width - x
                if piece and room > 0:
                    style = self.part_style(f"{part}-numbers" if bright else part)
                    surface.draw_text(x, y, piece[:room], style, room)
                    x += len(piece[:room])
                bright = not bright
            y += 1

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
        if CLIP and CLIP.holds(self.entry_location(item)):
            # Waiting for Ctrl+V: ``Panel::row.clip-cut`` / ``.clip-copy``.
            classes += ("clip-cut" if CLIP.move else "clip-copy",)
        classes += self.row_classes(index, item)
        return self.part_style("row", classes=classes, selected=self.row_selected(index))

    def row_classes(self, index: int, item: DirEntry) -> tuple[str, ...]:
        """More classes for row *index*'s ``Panel::row``: none here; a Miller
        column marks the entry its next column shows (``.trail``)."""
        return ()

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

    #: What stands in the gutter of an entry Ctrl+C or Ctrl+X has clipped, a
    #: tag's sign winning over it: ``(copy, cut)`` per glyph tier.
    CLIP_MARKS = {
        glyphs_module.GLYPHS_ASCII: ("c", "x"),
        glyphs_module.GLYPHS_UNICODE: ("❐", "✂"),
        glyphs_module.GLYPHS_NERD: ("\U000f018f", "\U000f0190"),  # md-content_copy, md-content_cut
    }

    def clip_mark(self, move: bool) -> str:
        return self.CLIP_MARKS.get(self.glyphs, self.CLIP_MARKS[glyphs_module.GLYPHS_UNICODE])[move]

    def is_bookmarked(self, item: DirEntry) -> bool:
        """Whether *item* is a directory on the Alt+F1/Alt+F2 list."""
        if not item.is_dir or item.name == "..":
            return False
        return str(self.entry_location(item)) in bookmarked_paths()

    @property
    def ellipsis(self) -> str:
        """What marks a name or path cut short: ``…``, or ``...`` in ASCII."""
        return glyphs_module.ellipsis(self.glyphs)

    def _cut_start(self, text: str, room: int) -> str:
        """*text* in *room* characters, its start cut and marked if it must be."""
        if len(text) <= room:
            return text
        marker = self.ellipsis
        if room > len(marker):
            return marker + text[-(room - len(marker)):]
        return text[-room:] if room > 0 else ""

    def _draw_name(self, surface: Surface, x: int, y: int, width: int,
                   item: DirEntry, style: Style, offset: int = 0, selected: bool = False) -> None:
        """The tag, the icon or the type mark, the name, and in a work tree
        its git letter, in *width* cells.

        A tag takes the gutter over whichever of the other two it would hold:
        the colour says *tagged* too, but not on a monochrome terminal.  The
        letter stands a cell before the end, in its own colour (``Panel::git``) except
        under the cursor bar, whose colours keep it readable.
        """
        gutter = min(self.gutter, width)
        if gutter:
            if self.is_marked(item) and self.tag_char:
                mark = self.tag_char
            elif CLIP and CLIP.holds(self.entry_location(item)):
                mark = self.clip_mark(CLIP.move)
            elif self.show_icons:
                mark = icon_glyphs.icon_for(item.name, item.is_dir, item.type_mark,
                                            self.is_bookmarked(item))
            elif self.glyphs > glyphs_module.GLYPHS_ASCII and self.is_bookmarked(item):
                mark = self.BOOKMARK_MARK
            else:
                mark = item.type_mark
            surface.draw_text(x, y, mark, style, gutter)
        git = self.git_cells if width > gutter + self.git_cells else 0
        if git:
            mark = self.git_mark(item)
            letter = style if selected or mark == " " else self.part_style(
                "git", classes=(gitstatus.CLASSES.get(mark, "modified"),))
            surface.draw_text(x + width - 2, y, mark, letter, 1)
        if width > gutter + git:
            room = width - gutter - git
            name = window_text(item.name, offset, room, self.ellipsis)
            surface.draw_text(x + gutter, y, name, style, room)

    def render_row(self, surface: Surface, y: int, index: int, item: DirEntry) -> None:
        style = self.row_style(index, item)
        if self.view_mode == "detailed":
            selected = self.row_selected(index)
            for key, x, width in self.detail_columns:
                if key == "name":
                    self._draw_name(surface, x, y, width, item, style, self.name_offset, selected)
                    continue
                if selected:
                    # The cursor bar covers the dividers; draw them back in it.
                    surface.draw_text(x - 1, y, self.divider_glyph, style, 1)
                text = getattr(item, self.DETAIL_COLUMNS[key][2])
                if key == "path":
                    text = self._cut_start(text, width)
                surface.draw_text(x, y, fit_text(text, width, self.ellipsis), style, width)
            return
        # Still an explicit limit: the name stops where the size column
        # begins, which is nearer than the edge the surface would clip at.
        self._draw_name(surface, 1, y, max(1, self.name_width), item, style, self.name_offset,
                        self.row_selected(index))
        surface.draw_text(self.width - 9, y, item.display_size, style, 8)

    def render(self, surface: Surface) -> None:
        super().render(surface)
        self.render_info(surface)

    def render_items(self, surface: Surface) -> None:
        if self.scanning:
            surface.draw_text(self.inset + 1, self.inset + self.header, tr("Reading directory..."),
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
                selected = self.row_selected(index)
                if selected:
                    surface.fill(x, top + row, width, 1, " ", style)
                self._draw_name(surface, x, top + row, width, item, style, selected=selected)

    @staticmethod
    def heading(key: str) -> str:
        """The column *key*'s heading in the current language: ``name`` or
        one of :data:`DETAIL_COLUMNS`, whose headings are these in English."""
        return {
            "name": tr("Name"),
            "size": tr("Size"),
            "packed": tr("Packed"),
            "ratio": tr("%"),
            "attributes": tr("Attr"),
            "owner": tr("Owner"),
            "date": tr("Date"),
            "path": tr("Path"),
        }[key]

    def _column_spans(self) -> list[tuple[str, int, int]]:
        """``(heading, x, width)`` for the columns of the current mode."""
        if self.view_mode == "detailed":
            return [(self.heading(key) + self.sort_arrow(key), x, width) for key, x, width in self.detail_columns]
        if self.view_mode == "list":
            columns = self.list_columns
            name = self.heading("name") + self.sort_arrow("name")
            if not columns:
                return [(name, self.inset, self.inner_width)]
            return [(name, x, width) for _, x, width in columns]
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
                    # The info lines stand between the column and the bottom
                    # frame: the divider over them takes the tee, if any.
                    ends = ((0, top_tee),) if self.info_height else ((0, top_tee), (self.height - 1, bottom_tee))
                    for y, tee in ends:
                        char, style = surface.get(edge, y)
                        if char == horizontal:
                            surface.set_cell(edge, y, tee, style)
