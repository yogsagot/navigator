"""Services' F3: a service's log in the viewer, following its end.

What is followed is the backend's to say (``services.log``): systemd's
journal through ``journalctl --follow`` (:func:`open_journal`, below), or a
log file -- an OpenRC service's own, or the system log with only the lines
holding the service's name shown, through the viewer's *Filter lines*
(:func:`open_log_file`).  A log file the user may not read is offered *As
root* and read through the root helper, as F3 reads any file.

**systemd's journal**:

``journalctl --follow`` writes into a private temporary file
(:func:`navigator.lib.system.tempdir.private_dir`), and the F3 viewer opens it
with *Follow end* (Ctrl+T) on, so the viewer's search, filters, hex and *Save
as* all work on the journal and each new line shows as it is written.  The
viewer's own tick looks at the file's size; nothing here reads the journal.

**Whose journal**: a user unit's, or anyone's for root or a member of
``systemd-journal``/``adm``/``wheel``, is followed as the user.  Anyone else
sees only their own lines in a system unit's, so they are offered *As root*,
and the root helper's ``journal_follow`` writes into the same file -- the
helper is then held open (``ELEVATION.hold``) while the window is, and stops
its ``journalctl`` when it closes, or when it ends itself.

**Closing the window** stops ``journalctl`` and deletes the file, on a thread;
a follower still running when Navigator quits is stopped at exit.  The
window keeps no File View History record: its file is gone once it closes.
"""

from __future__ import annotations

import asyncio
import atexit
import os
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable

from navkit.i18n import tr
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.system import services
from navigator.lib.system.elevate import ELEVATION
from navigator.widgets.viewer.commands import FollowEnd
from navigator.widgets.viewer.file_window import FileWindow

#: How long to wait for ``journalctl``'s first lines before the viewer opens,
#: so it does not open on an empty file and show nothing until the next tick.
FIRST_LINES = 1.5

#: What still runs, stopped at exit if its window never closed.
_LIVE: set[Callable[[], None]] = set()
_LIVE_LOCK = threading.Lock()


def _stop_all() -> None:
    with _LIVE_LOCK:
        stops = list(_LIVE)
        _LIVE.clear()
    for stop in stops:
        try:
            stop()
        except Exception:  # noqa: BLE001 - exiting: nothing to say it to
            pass


atexit.register(_stop_all)


def _make_file(unit: services.Unit) -> Path:
    """An empty file of the user's alone, named after *unit*, to follow."""
    from navigator.lib.system.tempdir import private_dir

    stem = re.sub(r"[^A-Za-z0-9_.@-]", "_", unit.name)[:80]
    fd, name = tempfile.mkstemp(prefix=f"journal-{stem}-", suffix=".log", dir=private_dir())
    os.close(fd)
    return Path(name)


def _first_lines(path: Path, ended: Callable[[], bool]) -> None:
    """Back once *path* holds something, its writer *ended*, or :data:`FIRST_LINES` passed."""
    until = time.monotonic() + FIRST_LINES
    while time.monotonic() < until and not ended():
        try:
            if path.stat().st_size:
                return
        except OSError:
            return
        time.sleep(0.05)


class JournalWindow(FileWindow):
    """The viewer on a unit's journal, following it; closing it stops the follower."""

    def __init__(self, path: Path, *, unit: services.Unit, stop: Callable[[], None], **kwargs: Any) -> None:
        super().__init__(path, **kwargs)
        self.unit = unit
        self._stop: Callable[[], None] | None = stop
        #: The thread stopping the follower once the window has gone (tests join it).
        self.stopping: threading.Thread | None = None
        self.title = tr("Journal: {unit}").format(unit=unit.name)

    def list_name(self) -> str:
        return self.title

    def short_name(self) -> str:
        return self.unit.name

    # A temporary file: nothing to come back to.

    def remember_history(self) -> None:
        return

    def recall_history(self, *, keep_mode: bool = False) -> None:
        return

    def unmounting(self) -> None:
        super().unmounting()
        stop, self._stop = self._stop, None
        if stop is not None:
            self.stopping = threading.Thread(target=stop, name="nav-journal-stop", daemon=True)
            self.stopping.start()


def _stopper(path: Path, end: Callable[[], None]) -> Callable[[], None]:
    """What ends a follower: *end*, then *path* deleted -- once, from the
    window's close or Navigator's exit, whichever is first."""
    done = threading.Event()

    def stop() -> None:
        if done.is_set():
            return
        done.set()
        with _LIVE_LOCK:
            _LIVE.discard(stop)
        try:
            end()
        finally:
            try:
                path.unlink()
            except OSError:
                pass

    with _LIVE_LOCK:
        _LIVE.add(stop)
    return stop


async def open_log(window: Any, unit: services.Unit) -> Any:
    """F3 in Services: what *unit*'s backend says its log is, followed in a
    viewer on *window*'s desktop.  Said in a box when there is none; None then."""
    try:
        target = await asyncio.to_thread(services.log, unit)
    except OSError as error:
        await _say(window.application, error)
        return None
    if isinstance(target, services.Journal):
        return await open_journal(window, unit, target)
    return await open_log_file(window, unit, target)


async def open_log_file(window: Any, unit: services.Unit, target: services.LogFile) -> Any:
    """*target*'s file in the viewer, following its end -- only the lines
    holding the service's name when it is a log every service writes to."""
    from navigator.lib.system.elevate import refused
    from navigator.lib.viewer import ViewSource
    from navigator.lib.viewer.lines import LinePattern

    app = window.application
    desktop = window.parent
    path = target.path
    try:
        try:
            source = await asyncio.to_thread(ViewSource, path)
            viewer = FileWindow(path, mode="text", source=source)
            desktop.open(viewer)
        except OSError as error:
            if not (refused(error) and await asyncio.to_thread(ELEVATION.available)):
                raise
            from navigator.widgets.file_ops.as_root import ask_as_root, view_as_root

            message = tr("Only root reads {path}, where {unit}'s log is.").format(path=path, unit=unit.name)
            if not await ask_as_root(app, escape_caption(message), title=tr("Journal")):
                return None
            viewer = await view_as_root(desktop, path, mode="text")
    except OSError as error:
        await _say(app, error)
        return None
    if target.pattern:
        viewer.title = tr("Log: {unit} (its lines in {path})").format(unit=unit.name, path=path)
        await viewer.show_lines(LinePattern(target.pattern))
    elif target.guessed:
        viewer.title = tr("Log: {unit} ({path}, found by its name)").format(unit=unit.name, path=path)
    else:
        viewer.title = tr("Log: {unit}").format(unit=unit.name)
    await viewer.on_follow_end(FollowEnd())
    return viewer


async def open_journal(window: Any, unit: services.Unit, target: services.Journal) -> JournalWindow | None:
    """*unit*'s journal (*target*'s ``journalctl``), followed, in a viewer on
    *window*'s desktop.  Said in a box when it cannot be; None then."""
    from navigator.lib.viewer import ViewSource

    app = window.application
    desktop = window.parent
    try:
        path = await asyncio.to_thread(_make_file, unit)
    except OSError as error:
        await _say(app, error)
        return None
    stop: Callable[[], None] | None = None
    try:
        root = False
        if not target.readable and await asyncio.to_thread(ELEVATION.available):
            from navigator.widgets.file_ops.as_root import ask_as_root

            message = tr("Only root and the systemd-journal group read all of {unit}'s journal: "
                         "as you, only your own lines show.").format(unit=unit.name)
            root = await ask_as_root(app, escape_caption(message), title=tr("Journal"))
        if root:
            pid = await asyncio.to_thread(ELEVATION.call, "journal_follow", unit=unit.name, path=str(path),
                                          lines=services.journal_lines())
            ELEVATION.hold()

            def end_as_root() -> None:
                try:
                    ELEVATION.call("journal_stop", pid=pid)
                except OSError:
                    pass  # the helper has gone, and its journals with it
                finally:
                    ELEVATION.unhold()
                    ELEVATION.release()

            stop = _stopper(path, end_as_root)
            await asyncio.to_thread(_first_lines, path, lambda: False)
        else:
            follower = await asyncio.to_thread(services.Follower, target.argv, path)
            stop = _stopper(path, follower.stop)
            await asyncio.to_thread(_first_lines, path, lambda: follower.process.poll() is not None)
        source = await asyncio.to_thread(ViewSource, path)
        journal = JournalWindow(path, unit=unit, stop=stop, mode="text", source=source)
    except OSError as error:
        if stop is not None:
            await asyncio.to_thread(stop)
        else:
            path.unlink(missing_ok=True)
        await _say(app, error)
        return None
    desktop.open(journal)
    await journal.on_follow_end(FollowEnd())
    return journal


async def _say(app: Any, error: OSError) -> None:
    await Dialog(title=tr("Journal"), buttons="ok",
                 prompt=escape_caption(error.strerror or str(error))).execute(app)


__all__ = ["JournalWindow", "open_journal", "open_log", "open_log_file"]
