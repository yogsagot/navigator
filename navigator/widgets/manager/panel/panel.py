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

The methods are split by feature into mixins (``navkit.widget.Mixin``), one
module each beside this one -- ``places``, ``tagging``, ``modes``,
``quick_search``, ``mouse``, ``info_lines``, ``painting`` -- with the
module-level helpers in ``helpers``, re-exported here.  What stays here is the
state, the listing (its scan, Enter, going up) and the computed columns;
``SCAN_GRACE`` and ``_read_location`` stay with the listing, which the tests
patch them for.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from navkit.application import REPEAT_EVERY
from navkit.bidi import display_width
from navkit.events import KeyEvent, WakeEvent
from navkit.i18n import tr, tr_n
from navkit.reactive import Binding, Reactive, bind, computed, effect, peek, reactive, unbind, untracked
from navkit.stylesheet import StyleProperty

from navml.widgets.dialog.list_viewer import ListViewer

from navigator.lib.appearance import filetypes
from navigator.lib.config import country
from navigator.lib.drives import Drive, DriveGone, Location, drive_of
from navigator.lib.file_ops.clip import CLIP
from navigator.lib.drives.listing import (
    DirEntry,
    ScanJob,
    entry_at,
    make_entry,
    order_entries,
    restat_found,
    scan_directory,
    shown_in_listing,
)
from navigator.lib.system import dirwatch
from navigator.settings import SETTINGS, PanelDefaultsData
from navigator.widgets.manager.panel.drag import Dropped
from navigator.widgets.manager.panel.helpers import ExecuteFile, ListingFacts, OpenFile, SORT_MODES, _SCANNER, _answers_here, _is_read_only, _scanner_for, command_line_text, direction_arrow, fit_text, human_size, skip_cells, text_width, window_text

from navigator.widgets.manager.panel.places import Places
from navigator.widgets.manager.panel.tagging import Tagging
from navigator.widgets.manager.panel.modes import Modes
from navigator.widgets.manager.panel.quick_search import QuickSearching
from navigator.widgets.manager.panel.mouse import Mouse
from navigator.widgets.manager.panel.info_lines import InfoLines
from navigator.widgets.manager.panel.painting import Painting


#: How long a rescan may hold the frame up before it is left to finish on
#: its own: long enough for any local directory, short enough not to be felt.
SCAN_GRACE = 0.05


def _read_location(location: Location, show_hidden: bool, sort: str, *, free: bool,
                   **options: Any) -> tuple[list[DirEntry], str | None, tuple[int, str] | None, bool]:
    """A panel's read of *location*, on its thread: its drive's ``scan``,
    and a drive gone or failing as the panel's error line -- and whether the
    directory is on a file system mounted read-only (:func:`_is_read_only`)."""
    try:
        entries, error, free_space = drive_of(location).scan(location, show_hidden, sort, free=free, **options)
    except OSError as error:
        return [], error.strerror or str(error), None, False
    return entries, error, free_space, error is None and _is_read_only(location)


@dataclass
class _ScanRequest:
    """One read of a directory, and where its cursor is to go once it lands."""

    path: Location
    return_to: str | None
    keep: tuple[Location, str, int, int] | None
    #: What is listed: the path, or the *Find:* listing shown at it -- so a
    #: listing's own re-reads keep tags and cursor, and entering one does not.
    where: Any = None


class _Arrival(Reactive):
    """:attr:`Panel.location`: a reactive whose every write is told to the
    panel first (``Panel._arriving``), wherever it is made -- Enter, ``..``,
    a bookmark, the tree, the command line's ``cd`` -- so a remembered
    directory's settings change in the same step as the place, and the one
    read that follows is in their order and with their mask."""

    def __set__(self, obj: Any, value: Any) -> None:
        if not isinstance(value, Binding):
            arriving = getattr(obj, "_arriving", None)
            if arriving is not None and "_kept_dir" in vars(obj):
                arriving(value)
        super().__set__(obj, value)


class Panel(Places, Tagging, Modes, QuickSearching, Mouse, InfoLines, Painting, ListViewer):
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

    #: A held left button past the top or the bottom scrolls a row on every
    #: tick from the start: FLPANELX.PAS's loop ran with ``RepeatDelay := 0``
    #: and no ``MouseAutosToSkip``.
    edge_ticks = 1
    edge_delay = REPEAT_EVERY

    @property
    def follows_drag(self) -> bool:
        """The left button follows the pointer unless File Manager Setup's
        *Drag-and-drop* is on, which makes the press a drag's start instead
        (DN's ``fmoDragAndDrop`` branch)."""
        return not SETTINGS.file_manager.drag_drop_columns

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
    location: Location = _Arrival(Location.of(Path(".")))
    #: The record of :mod:`navigator.lib.config.directory_settings` the
    #: panel shows its directory with, by its key -- the directory's own, or
    #: one above marked for those below -- or ``""`` for the panel's own
    #: settings.
    remembered: str = reactive("")
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
    #: Whether the directory read last is on a file system mounted read-only.
    read_only: bool = reactive(False)
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
    find_columns: frozenset[str] = reactive(frozenset(("size", "attributes", "owner", "date")))
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

    #: ``simple``: name and size.  ``detailed``: name and *Columns Setup*'s
    #: choice of size, permissions, links, owner and date -- and the packed
    #: size and ratio in an archive -- in columns.  ``list``: names alone, in
    #: as many columns as fit.
    VIEW_MODES = ("simple", "detailed", "list")

    #: ``heading`` is the column-titles row the detailed and list modes draw.
    parts = ListViewer.parts + (
        "heading", "current-file", "selected-files", "selected-files-numbers", "packed", "packed-numbers",
        "totals", "totals-numbers", "free-space", "free-space-numbers", "git",
    )

    def __init__(self, path: Path | None = None, **kwargs: Any):
        """*path* is optional because a widget markup constructs must be.

        It is also *seeded* rather than bound, which is the rule a panel is
        the reason for: ``enter()`` assigns ``path`` on every descent, and an
        attribute carrying a binding is read-only until something unbinds it.
        """
        super().__init__(**kwargs)
        # The scroll bar's page is the whole view, as PgUp/PgDn's (``page``):
        # DN's panel gave its bar ``Size.Y * columns``, navml's list a row less.
        unbind(self.bar, type(self.bar).page)
        self.bar.page = bind(lambda bar: max(1, bar.parent.capacity))
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
        # The row and the tags before a Ctrl+click's range (``_shift_select``).
        self._before_range: tuple[int, frozenset] | None = None
        #: What stops the read's directory counting (*Directory length*).
        self._scan_job: ScanJob | None = None
        #: The directory being watched (*Auto refresh panels*), and the
        #: re-read a change on it has asked for, waiting out REFRESH_DELAY.
        self._watch: dirwatch.Watch | None = None
        #: Bumped whenever the watch is dropped: one set up on a thread for
        #: an earlier place is cancelled as it lands (:meth:`_watch_directory`).
        self._watch_generation = 0
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
        #: The panel's own settings (``directory_settings.KEPT``), held aside
        #: while a remembered directory's are shown; None while its own are.
        self._base: dict[str, Any] | None = None
        #: The settings the panel came to its directory with, while that has
        #: no record: what it goes back to when the directory is marked after
        #: a sort or a mask changed in it -- those are the directory's then.
        self._arrival: dict[str, Any] | None = None
        #: What :meth:`_keep_directory_settings` saw last: the place, the
        #: record and the settings; None until its first look.  Its presence
        #: is also what tells :class:`_Arrival` the panel is ready.
        self._kept_dir: tuple[Location, str, dict[str, Any]] | None = None
        if path is not None:
            self.location = Location.of(path)

    def _options_room(self) -> int:
        """The columns the option strip may take: up to the quick search's
        label while one runs, else the bottom frame less its corners."""
        footer = self.footer_text()
        start = self.label_x(footer) + display_width(footer) + 1 if footer else 1
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
        effect(self, Panel._keep_directory_settings)

    def unmounting(self) -> None:
        self._stop_watching()
        self._stop_watching_git()
        self._let_go_of_archive()
        self._let_go_of_root()
        super().unmounting()

    # -- the listing ---------------------------------------------------------

    def _rescan(self) -> None:
        """Re-read the directory, whenever the path or the token changes.

        **Read on a thread** (:func:`scan_directory`), so a directory on a
        slow disk or a hung network mount does not stop the screen.  A read of
        somewhere new on a drive that answers here (``Drive.quick_listing``)
        is waited for up to :data:`SCAN_GRACE` -- nearly every one is in by
        then -- and shown in this same frame, sparing a flash of empty rows; a
        slower one, a re-read of the same place (whose rows stay up meanwhile)
        and any read from a drive a round trip away are shown when they are
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
        if found is not None and found.keep_order:
            sort = "unsorted"  # *Find duplicates*' groups stay together
        if found is not None and found.live:
            # Still being searched: the entries as found, only ordered, and
            # not counted -- redrawn at every batch found, it would walk the
            # same directories over and over; the settled read counts once
            # (DN's ``GetDirectory`` counted at each redraw) -- and masked as
            # the settled listing is (DN's ``GetDirectory``).
            entries = [DirEntry("..", True, 0)] + [e for e in found.entries
                                                   if shown_in_listing(e, show_hidden, mask)]
            self._apply(request, order_entries(entries, sort, executables_first=flags["executables_first"],
                                               archives_first=flags["archives_first"], reverse=reverse), None)
            return
        if found is not None:
            job = self._scan_job = ScanJob() if dir_length else None
            future = _SCANNER.submit(restat_found, list(found.entries), show_hidden, sort,
                                     dir_length=dir_length, job=job, **flags)
        else:
            job = self._scan_job = ScanJob() if dir_length else None
            future = _scanner_for(path).submit(_read_location, path, show_hidden, sort, free=free,
                                               dir_length=dir_length, job=job, **flags)
        with untracked():
            app = self.application
        if app is None or not app.is_running:
            self._apply(request, *future.result())
            return
        grace = SCAN_GRACE if request.where != self._listed and _answers_here(path) else 0
        try:
            if not grace and not future.done():
                raise concurrent.futures.TimeoutError
            result = future.result(timeout=grace)
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
               free: tuple[int, str] | None = None, read_only: bool = False) -> None:
        """Show what a read of ``request.path`` found."""
        path = request.path
        where = request.where if request.where is not None else path
        if where == self._listed and error is None:
            entries = self._keep_counts(entries)
        self._pending = None
        self._scan_job = None
        self.scanning = False
        self.free_space = free
        self.read_only = read_only
        self.items = entries
        self.error = error
        # Peeked, not read: the rescan must not depend on the tags, or every
        # Insert would re-read the directory.
        marked = peek(self, Panel.marked)
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
        # By key first: a listing's entries may share a name (``a/README``,
        # ``b/README``), never a key; a directory's key is its name.
        at = next((index for index, item in enumerate(entries) if item.key == target), None)
        if at is None:
            at = next((index for index, item in enumerate(entries) if item.name == target), 0)
        self.cursor = at
        self.scroll = 0

    def _keep_counts(self, entries: list[DirEntry]) -> list[DirEntry]:
        """*entries*, a re-read of the directory listed, with the bytes Alt+G
        counted for its directories carried over from the last listing, and in
        the panel's order again when that is by size.

        A departure: DN's re-read made new entries and the counts went with
        the old ones, so sorting by size (itself a re-read) lost them and
        could never order by them.  Only a change of directory forgets them.
        """
        counts = {entry.key: entry.size for entry in peek(self, Panel.items)
                  if entry.is_dir and entry.counted}
        carried = False
        for entry in entries:
            if entry.is_dir and not entry.counted and entry.key in counts:
                entry.size, entry.counted = counts[entry.key], True
                carried = True
        return self._ordered(entries) if carried and peek(self, Panel.sort_mode) == "size" else entries

    def _ordered(self, entries: list[DirEntry]) -> list[DirEntry]:
        """*entries* in the panel's order as it stands (:func:`order_entries`)."""
        with untracked():
            return order_entries(entries, self.sort_mode, reverse=self.sort_reverse,
                                 executables_first=self.shows("executables_first"),
                                 archives_first=self.shows("archives_first"))

    def set_lengths(self, entries: Iterable[tuple[DirEntry, int]]) -> None:
        """Alt+G's answer: each listed directory's bytes into its size, and,
        sorting by size, the listing ordered by them with the cursor kept on
        its entry."""
        changed = False
        for entry, size in entries:
            entry.size, entry.counted = size, True
            changed = changed or entry in self.items
        if not changed:
            return
        if self.sort_mode != "size":
            # The same entries, changed, while the panel still lists them:
            # an equal list would be no change, so the sizes say they moved.
            self.sizes_token += 1
            return
        current = self.selected
        items = self._ordered(list(self.items))
        self.items = items
        if current is not None:
            row = self.cursor - self.scroll
            self.cursor = items.index(current)
            self.scroll = max(0, min(self.cursor - row, max(0, len(items) - self.rows)))
        self.sizes_token += 1

    @staticmethod
    def _remember_directory(path: Path) -> None:
        """Interface's *Track directories*: *path* first in the ``directories``
        history (Alt+Backspace), as ``AddToDirectoryHistory`` put it.  And
        ``[interface] feed_zoxide``: a directory on the disk told to zoxide
        too (a departure), so its ``z`` knows where the panels have been."""
        if SETTINGS.interface.track_directories:
            from navml.history import HISTORY

            HISTORY.add("directories", str(path))
        if SETTINGS.interface.feed_zoxide and path.is_local:
            from navigator.lib.system import fuzzy

            fuzzy.add(str(path.local))

    def reload(self, key: str | None = None) -> None:
        """Re-read the directory this panel shows, keeping the cursor on its entry.

        DOS Navigator's re-read after a command left the cursor where it was;
        this one used to send it back to the top, so the file just run, or
        just renamed by a command, was lost.  *key* (:attr:`DirEntry.key`) is
        where the cursor goes instead, if it is there: the entry just renamed.
        """
        entry = self.selected
        if entry is not None or key:
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

    def show_found(self, listing: Any, at: str | None = None, *, stack: bool = True) -> None:
        """Show *listing* in place of the directory, the cursor at its top --
        or on the entry keyed or named *at*.

        Over a listing it is stacked (DN's ``InsertDrive``, ``Prev`` the
        drive it covered): ``..`` goes back to that one, the cursor where it
        was.  *stack* false replaces the listing shown instead, keeping what
        it covered -- Ctrl+R's panelized listing read anew."""
        shown = self.found
        if shown is not None and listing is not shown:
            if stack:
                selected = self.selected
                listing.previous, listing.previous_columns = shown, self.find_columns
                listing.previous_key = selected.key if selected is not None else None
            else:
                listing.previous, listing.previous_key = shown.previous, shown.previous_key
                listing.previous_columns = shown.previous_columns
        self._keep = None
        self._return_to = at
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
        """``..`` in a *Find:* listing: ``ChangeUp``, back to the listing it
        was made from (``TFindDrive``'s ``Prev``), or to the directory it was
        shown at -- the cursor where the panel had left it."""
        found = self.found
        if found is None:
            return
        if found.previous is not None:
            self._return_to = found.previous_key
            if found.previous_columns is not None:
                self.find_columns = found.previous_columns
            self.found = found.previous
            return
        self._return_to = found.return_to
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

    def go_to_file(self, path: Path) -> None:
        """The directory holding *path* on the disk, the cursor on it."""
        self.leave_found()
        self._return_to = path.name
        self.location = Location.of(path.parent)

    def image_file(self) -> Path | None:
        """The disk image at the cursor that *Mount image* mounts: an
        ``.iso``/``.img`` on the disk, outside an archive or a *Find:*
        listing; None for none."""
        from navigator.lib.system import udisks

        entry = self.selected
        if (entry is None or entry.is_dir or entry.name == ".." or self.found is not None
                or not self.location.is_local or self.location.outer is not None
                or not stat.S_ISREG(entry.mode) or not udisks.is_image_name(entry.name)):
            return None
        return entry.path_in(self.path)

    def image_here(self) -> list[Any]:
        """The mounts of the disk image this panel is in -- or, with nothing
        tagged, the mounted ``.iso``/``.img`` at its cursor -- for *Unmount
        image*; ``[]`` for none, off the disk, or without ``udisksctl``.
        ``/proc`` and ``/sys`` only (:func:`navigator.lib.system.udisks.image_at`),
        kept a moment -- a menu asks every frame -- and the cursor's file by
        the letters and the link the listing read, never ``realpath()`` on
        the loop (an image through a link to a link is found from inside its
        mount only)."""
        from navigator.lib.system import udisks

        if not self.location.is_local or self.found is not None or udisks.program() is None:
            return []
        entry = self.selected
        if (not self.marked and entry is not None and not entry.is_dir and entry.name != ".."
                and udisks.is_image_name(entry.name)):
            here = self.path
            if entry.is_link and entry.link_target:
                where = os.path.normpath(here / entry.link_target)
            else:
                where = str(here / entry.name)
            mounts = udisks.image_at(where)
            if mounts:
                return mounts
        return udisks.image_at(self.path)

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
            self.path = self._entered(entry)
        elif entry.name == ".." and self.location.is_root:
            self.go_up()
        else:
            # Another drive's links are its own to follow: the name is enough.
            self.location = self._plain_where_readable((self.location / entry.name).normalized())

    def _entered(self, entry: DirEntry) -> Path:
        """Where Enter on *entry* goes on the disk, by the letters and what the
        listing already read -- never ``resolve()``, which stats each step of
        the path on the loop and waits there on a hung mount.

        ``..`` is the parent of the path shown; a link to a directory goes
        where it points (its ``link_target``, read with the directory), as
        ``resolve()`` took it.  A departure only for a link to a link: the
        first is followed and the path reached is shown, as bash's ``cd``
        shows it -- the same directory, by another way.
        """
        here = self.path
        if entry.name == "..":
            return Path(os.path.normpath(here / ".."))
        if entry.is_link and entry.link_target:
            return Path(os.path.normpath(here / entry.link_target))
        return here / entry.name

    def go_into(self) -> None:
        """Ctrl+PgDn, DN's ``_CtrlPgDn``: what Enter does on a directory,
        ``..`` or a *Find:* listing's entry; on a file, which DN's left
        alone, the file opened as an archive whatever its name
        (:meth:`open_as_archive`, a departure)."""
        entry = self.selected
        if entry is None:
            return
        if self.found is not None or entry.is_dir:
            self.enter()
            return
        self.open_as_archive()

    def archive_candidate(self) -> DirEntry | None:
        """The file at the cursor that *Open archive* may open: a regular
        file, not in an archive already (DN opened none from inside
        another) nor in a *Find:* listing."""
        entry = self.selected
        if (entry is None or entry.is_dir or self.found is not None or self.location.outer is not None
                or not stat.S_ISREG(entry.mode)):
            return None
        return entry

    def open_as_archive(self) -> None:
        """The file at the cursor opened as an archive, by what is in it --
        never run, as Enter runs one that is not."""
        entry = self.archive_candidate()
        if entry is not None:
            self.spawn(self._open_as_archive(entry))

    async def _open_as_archive(self, entry: DirEntry) -> None:
        from navigator.widgets.drives.archives import enter_archive

        await enter_archive(self, self.entry_location(entry), forced=True)

    def go_up(self) -> None:
        """Go to the parent directory, the cursor on the one just left.

        DN's ``_CtrlPgUp``: what choosing ``..`` does, from anywhere in the
        listing.  At the disk's root there is nowhere to go, and it is read
        again with the cursor on top, as DN's ``GotoFile(DirectoryName)`` did.
        At another drive's root with nowhere to go the cursor goes to the top
        -- a departure there: DN did nothing.
        """
        if self.found is not None:
            self.leave_found()
            return
        if not self.location.is_local:
            self._go_up_elsewhere()
            return
        # By the letters: the place above the path shown (see :meth:`_entered`).
        parent = Path(os.path.normpath(self.path / ".."))
        if parent == self.path:
            self.move_cursor(-len(self.items))
            self._return_to = ""
            self.reload_token += 1
            return
        self._return_to = self.path.name
        self.path = parent

    def go_root(self) -> None:
        """Ctrl+\\: ``Drive^.ChangeRoot``, the cursor on the first entry
        whatever was remembered there (``ScrollBar^.SetValue(0)``).

        The root of the drive the panel is on: the disk's ``/``; an
        archive's own root, staying inside it (``TArcDrive.ChangeRoot``'s
        ``CurDir := ''``); another drive's ``/`` on the same site.  A *Find:*
        listing is left for the root of where it was found, as ``TFindDrive``
        had ``TDrive``'s.  At the root already, it is read again.
        """
        if self.found is not None:
            self.leave_found()
        location = self.location
        root = Location(location.site, type(location.path)("/"), location.outer)
        # A name no entry has: the first one, and no remembered cursor.
        self._return_to = ""
        if root == location:
            self.reload_token += 1
            return
        self.location = root

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

    @computed
    def _marked_tuple(self) -> tuple[DirEntry, ...]:
        """The tagged entries, walked out of the listing only when the listing
        or the tags change -- never on a cursor move."""
        marked = self.marked
        if not marked:
            return ()
        return tuple(item for item in self.items if item.key in marked)

    @computed
    def _listing_facts(self) -> ListingFacts:
        """What the footer says of the whole listing, in one walk per listing
        (not per cursor move): :class:`ListingFacts`."""
        return ListingFacts.of(self.items)

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
        if event.key == "home" and not (event.ctrl or event.alt or event.shift):
            # ``kbHome``: ``DeltaX := 0`` too -- the names scrolled back.
            self.name_scroll = 0
        if event.shift and not (event.ctrl or event.alt) and event.key in ("up", "down"):
            # DN's panel handed Shift+Up/Down to the command line, its history:
            # declined here for the manager's key table (``PreviousCommand``).
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
        ``(ShiftState and 3 <> 0) xor (Options and fmoUseArrows = 0)``) -- as
        DN meant it.  As compiled, Pascal's ``and`` binding tighter than
        ``xor`` made it ``Shift xor (off and arrow)``: with *Use arrows* on
        only Shift-held keys reached the line, the reverse of the option's
        name.  The intent is followed, a reading recorded (``FLPANEL.PAS:1149-1151``,
        and ``TSpecScroll``'s ``:176-179``).
        Ctrl+Home and Ctrl+End go to a line holding text whatever *Use arrows*
        says: DN's line took them as Home and End (``CMDLINE.PAS:391-392``).
        """
        if (event.key in ("home", "end") and event.ctrl and not (event.shift or event.alt)
                and command_line_text(self)):
            return True
        if event.key not in self.LINE_KEYS or event.ctrl or event.alt:
            return False
        if SETTINGS.file_manager.use_arrows == event.shift:
            return False
        return bool(command_line_text(self))

    @computed
    def detail_columns(self) -> tuple[tuple[str, int, int], ...]:
        """``(key, x, width)`` for every detailed-mode column, the name's first.

        Each column after the name has a divider in the cell before it.  The
        name takes whatever is left; when that is under
        :data:`MIN_NAME_WIDTH`, the link count goes, the owner, then the attributes, and then
        the date.  The owner column is as wide as the longest owner listed.

        Two departures: a wide panel widens the name, where DN repeated the
        whole line across it (``Size.X div LineLength``), and a narrow one
        drops columns, where DN scrolled the line sideways.
        """
        inset, inner = self.inset, self.inner_width
        # *Columns Setup*'s choice, the packed size and ratio only in an
        # archive.  A *Find:* listing's directories have a footer line of
        # their own (:meth:`_second_line`), not a column.
        wanted, listing = self.shown_columns, self.found is not None
        in_archive = self.location.outer is not None and not listing
        # No archive keeps a link count: *Links* is left out there.
        shown = [key for key in self.DETAIL_ORDER
                 if key in wanted and (key not in self.ARCHIVE_ONLY or in_archive)
                 and not (key == "links" and in_archive)]
        widths = {key: width for key, (_, width, _) in self.DETAIL_COLUMNS.items()}
        widths["owner"] = self._owner_width()
        widths["date"] = country.stamp_width()
        # As wide as its heading in the language, which may be wider than five.
        widths["links"] = max(widths["links"], display_width(self.heading("links")))

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
            longest = max(text_width(self.shown_name(item)) for item in items[first : first + rows])
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
        longest = max(text_width(self.shown_name(item)) for item in self.items)
        return max(0, longest - self.name_room)

    @computed
    def name_offset(self) -> int:
        """:attr:`name_scroll`, as far as there is anything to scroll."""
        return max(0, min(self.name_scroll, self.max_name_scroll))

    @computed
    def name_width(self) -> int:
        """How much of a listing line is left once the size column is taken."""
        return max(1, self.width - 12)

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
        marked = self._marked_tuple
        selected_files = self.shows("selected_files")
        if self.shows("current_file"):
            if marked and not selected_files:
                lines.append((self._selection_text(marked), "selected-files"))
            else:
                lines.append((None, "current-file"))
            if self.in_archive:
                lines.append((self._packed_line(self.selected), "packed"))
            else:
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
            facts = self._listing_facts
            if not facts.has_entries:
                text = tr("No files in this directory")
            else:
                total = tr_n("~{n:,}~ byte", "~{n:,}~ bytes", facts.file_bytes)
                text = tr_n("Total: ~{n:,}~ file with {total}", "Total: ~{n:,}~ files with {total}", facts.files,
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
