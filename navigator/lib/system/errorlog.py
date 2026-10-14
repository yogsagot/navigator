"""``errors.log`` beside the database: every failure, kept past the screen.

Navigator draws on the alternate screen, which the terminal wipes on the way
out, and over ssh the window that showed a failure is often gone before
anyone reads it.  So every exception that escapes Navigator's code is
appended here as well as shown or printed (``Navigator.log_error``), and
:mod:`faulthandler` writes here when the interpreter itself dies -- a
segfault in an extension, an abort -- which leaves no Python traceback
anywhere else.

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
import os
import sys
import traceback
from pathlib import Path
from typing import IO

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
