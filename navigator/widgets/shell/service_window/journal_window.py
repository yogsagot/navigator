"""Services' F3: a unit's journal in the viewer, following its end.

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


def _journal_lines() -> int:
    from navigator.settings import SETTINGS

    try:
        return max(0, int(SETTINGS.services.journal_lines))
    except (AttributeError, TypeError, ValueError):
        return 200


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


async def open_journal(window: Any, unit: services.Unit) -> JournalWindow | None:
    """F3 in Services: *unit*'s journal, followed, in a viewer on *window*'s
    desktop.  Said in a box when it cannot be; None then."""
    from navigator.lib.viewer import ViewSource

    app = window.application
    desktop = window.parent
    lines = _journal_lines()
    try:
        path = await asyncio.to_thread(_make_file, unit)
    except OSError as error:
        await _say(app, error)
        return None
    stop: Callable[[], None] | None = None
    try:
        root = False
        if not services.can_read_journal(unit) and await asyncio.to_thread(ELEVATION.available):
            from navigator.widgets.file_ops.as_root import ask_as_root

            message = tr("Only root and the systemd-journal group read all of {unit}'s journal: "
                         "as you, only your own lines show.").format(unit=unit.name)
            root = await ask_as_root(app, escape_caption(message), title=tr("Journal"))
        if root:
            pid = await asyncio.to_thread(ELEVATION.call, "journal_follow", unit=unit.name, path=str(path),
                                          lines=lines)
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
            follower = await asyncio.to_thread(services.Follower,
                                               services.journal_argv(unit.name, unit.user, lines), path)
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


__all__ = ["JournalWindow", "open_journal"]
