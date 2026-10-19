"""``errors.log`` beside the database: every failure, kept past the screen.

Navigator draws on the alternate screen, which the terminal wipes on the way
out, and over ssh the window that showed a failure is often gone before
anyone reads it.  So every exception that escapes Navigator's code is
appended here as well as shown or printed (``Navigator.log_error``), and
:mod:`faulthandler` writes here when the interpreter itself dies -- a
segfault in an extension, an abort -- which leaves no Python traceback
anywhere else.

A **stall** is logged too, though nothing failed: the frame loop busy with
one batch for longer than ``[system] stall_report`` seconds
(:func:`start_watchdog`) leaves a ``STALL`` entry with the input that led up
to it, every thread's stack, and every task's -- the first shows a loop
thread stuck in a system call, the second a handler awaiting something slow.
``kill -USR1`` writes every thread's stack here at any moment.

Opened only by ``main()`` (:func:`open_log`), for :func:`open_database`'s
reason: an application a test builds never writes to the user's state
directory, and until then :func:`append` does nothing.

**Written on the loop, synchronously** -- an exception to *nothing that can
wait on a disk runs on the loop*, and a deliberate one: a failure is rare, the
file is local state beside the database, and the path that writes it may be
the application going down, with no loop left to hand a thread's answer to.
"""

from __future__ import annotations

import contextlib
import datetime
import faulthandler
import asyncio
import os
import signal
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import IO, Any

from navigator import __version__
from navigator.settings import state_dir

#: The file's name, in :func:`navigator.settings.state_dir`.
FILE_NAME = "errors.log"

#: Where failures go, or None before :func:`open_log` (and in tests).
PATH: Path | None = None

#: Held open for :mod:`faulthandler`, which writes to a file descriptor at
#: the moment the process is dying and cannot open one then.
_fault_file: IO[str] | None = None


def default_path() -> Path:
    return state_dir() / FILE_NAME


def open_log(path: Path | None = None) -> Path | None:
    """Start logging to *path* (default :func:`default_path`), and arm
    :mod:`faulthandler` there.  Returns the path, or None if it cannot be
    written -- said on stderr, before the screen is taken, and not fatal."""
    global PATH, _fault_file
    path = path if path is not None else default_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _fault_file = open(path, "a", encoding="utf-8")  # noqa: SIM115 - held for faulthandler
    except OSError as error:
        print(f"nav: {path}: {error.strerror or error}; errors are not logged", file=sys.stderr)
        return None
    PATH = path
    faulthandler.enable(_fault_file, all_threads=True)
    # ``kill -USR1``: every thread's stack, now, without stopping.
    faulthandler.register(signal.SIGUSR1, _fault_file, all_threads=True)
    return path


def format_error(error: BaseException) -> str:
    """*error*'s full traceback, chained causes and all, as Python prints it."""
    return "".join(traceback.format_exception(error))


def append(error: BaseException) -> None:
    """Add *error* to the log, stamped.  Never raises: it runs on the way
    down, and a log that cannot be written must not hide the failure."""
    if PATH is None:
        return
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    entry = (
        f"=== {stamp} nav {__version__} pid {os.getpid()} "
        f"python {sys.version.split()[0]}\n"
        f"argv: {' '.join(sys.argv)}\n"
        f"{format_error(error)}\n"
    )
    with contextlib.suppress(OSError):
        with open(PATH, "a", encoding="utf-8") as log:
            log.write(entry)


def _stamp() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _write(text: str) -> None:
    """Append *text* through the file :mod:`faulthandler` holds, flushed, so
    what it writes by descriptor lands in order with it."""
    if _fault_file is None:
        return
    with contextlib.suppress(OSError, ValueError):
        _fault_file.write(text)
        _fault_file.flush()


#: How long the loop thread is given to answer for its tasks before a stall
#: report says it is blocked.
TASKS_TIMEOUT = 1.0


class Watchdog:
    """A daemon thread that writes a ``STALL`` entry when *app*'s frame loop
    has been on one batch for *threshold* seconds, and another when it is
    over.  Reads only *app*'s plain ``handling_since``/``handling``/
    ``recent_events``; writes nothing back.  One report per stall.
    *threshold* is a plain field, set from the loop; 0 reports nothing."""

    def __init__(self, app: Any, loop: asyncio.AbstractEventLoop, threshold: float,
                 poll: float = 0.5) -> None:
        self.app, self.loop, self.threshold, self.poll = app, loop, threshold, poll
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="nav-watchdog", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        reported: float | None = None  # the ``handling_since`` reported on
        while not self._stop.wait(self.poll):
            since = self.app.handling_since
            if reported is not None and since != reported:
                _write(f"=== {_stamp()} STALL ENDED after {time.monotonic() - reported:.1f} s\n\n")
                reported = None
            if since is None or reported is not None or self.threshold <= 0:
                continue
            busy = time.monotonic() - since
            if busy >= self.threshold:
                reported = since
                self.report(busy)

    def report(self, busy: float) -> None:
        try:
            recent = list(self.app.recent_events)
        except RuntimeError:  # appended to mid-copy: the loop is not stalled after all
            recent = []
        events = "".join(
            f"  {datetime.datetime.fromtimestamp(when).strftime('%H:%M:%S.%f')[:-3]}  {what}\n"
            for when, what in recent
        ) or "  (none)\n"
        _write(
            f"=== {_stamp()} STALL nav {__version__} pid {os.getpid()}: "
            f"busy for {busy:.1f} s with {self.app.handling}\n"
            f"recent input, oldest first:\n{events}"
            "threads:\n"
        )
        if _fault_file is not None:
            with contextlib.suppress(OSError, ValueError):
                faulthandler.dump_traceback(_fault_file, all_threads=True)
        answered = threading.Event()
        lines: list[str] = []

        def tasks() -> None:
            # On the loop thread, where the tasks may be looked at.
            import io
            for task in asyncio.all_tasks(self.loop):
                out = io.StringIO()
                task.print_stack(file=out)
                lines.append(out.getvalue())
            answered.set()

        try:
            self.loop.call_soon_threadsafe(tasks)
        except RuntimeError:  # the loop is closed
            return
        if answered.wait(TASKS_TIMEOUT):
            _write("tasks (the loop thread is free; a handler is waiting):\n" + "".join(lines) + "\n")
        else:
            _write(f"tasks: the loop thread did not answer in {TASKS_TIMEOUT:.0f} s -- "
                   "it is blocked; see the threads above\n\n")


def start_watchdog(app: Any, threshold: float) -> Watchdog | None:
    """A :class:`Watchdog` over *app*, started from its running loop; None
    before :func:`open_log` has found somewhere to write.  Its *threshold*
    may be changed while it runs; 0 reports nothing."""
    if _fault_file is None:
        return None
    watchdog = Watchdog(app, asyncio.get_running_loop(), threshold)
    watchdog.start()
    return watchdog
