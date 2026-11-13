"""Where the panel is besides a directory: the archive it holds open, browsing as root, the
watch that refreshes it, and git.

A mixin of :class:`Panel` (``navkit.widget.Mixin``): methods only; its state,
keys and the listing are in ``panel.py``.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import TYPE_CHECKING, Any

from navkit.events import WakeEvent
from navkit.i18n import tr
from navkit.reactive import untracked

from navigator.lib.drives import DriveGone, Location, drive_of
from navigator.lib.system import dirwatch, gitstatus
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel.helpers import REFRESH_DELAY, _SCANNER, _scanner_for

if TYPE_CHECKING:
    from navigator.widgets.manager.panel.panel import Panel as _Base
else:
    from navkit.widget import Mixin as _Base


class Places(_Base):
    """Where the panel is besides a directory: the archive it holds open, browsing as root, the"""

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
        if drive is not None and drive.dirty:
            # Changes a rewrite could not make: written now, or asked about,
            # before the archive goes (``archive_finish.let_go``) -- with no
            # loop left to ask on, kept open for quitting's ``close_all``.
            app = self.application
            if app is None or not app.is_running:
                archive.keep_open(drive)
                return
            from navigator.widgets.drives.archive_finish import let_go

            app.spawn(let_go(app, drive))
            return
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
        for that directory.  Yes puts the panel at ``root:`` there.

        Once only while asking is what it would take: with root access open
        there is no question to repeat, so a directory come to that way --
        the root console's ``cd`` -- and then left is ``root:`` again when
        the panel enters it (asked for), not *Permission denied*."""
        from navigator.lib.system.elevate import ELEVATION

        if path == self._root_offered and not ELEVATION.running:
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

        **Set up on the scan's pool**, not here on the loop: a drive's watch
        may look at the place first -- the Trash's reads every ``.trashinfo``,
        an inotify watch on a dead mount waits -- and the panel has to come
        up regardless.  A watch that lands after the panel has moved on (or
        stopped watching) is cancelled at once (``_watch_generation``).
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
            generation = self._watch_generation
            notify = lambda: self._heard_change(app)  # noqa: E731 - handed to the thread
            if not app.is_running:
                self._watch = drive.watch(location, notify)
                return
            future = _scanner_for(location).submit(drive.watch, location, notify)

            def landed(done: concurrent.futures.Future[Any]) -> None:
                try:
                    watch = done.result()
                except Exception:  # noqa: BLE001 - no watch, as a drive without one
                    return
                if generation != self._watch_generation or not app.is_running:
                    watch.cancel()
                    return
                self._watch = watch

            future.add_done_callback(lambda done: app.call_from_thread(lambda: landed(done)))

    def _heard_change(self, app: Any) -> None:
        """On the watcher's thread: tell the loop, unless it has been told already."""
        if self._heard:
            return
        self._heard = True
        app.call_from_thread(self._changed_on_disk)

    def _stop_watching(self) -> None:
        self._watch_generation += 1  # a watch still being set up is not wanted
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
