"""Panel > Panelize command (Alt+O): what a shell command prints, as a panel's listing.

Midnight Commander's *External panelize*, which DOS Navigator never had --
a departure, for a system whose answers to "which files?" (``find``,
``git ls-files``, ``grep -l``) are commands.  The command runs in the
panel's directory under ``$SHELL -c``, off the console and its pty, with
nothing on its standard input; each line it prints names a file as a line
of an Alt+V list file does (:func:`navigator.lib.file_ops.filefind.list_from_lines`),
and output holding a NUL (``find -print0``) is split on NULs instead.

Three ways in: the Panel menu's box, a command line starting with ``|``,
and a user-menu item holding a ``<|`` line.
"""

from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path

from navigator.lib.system.job import Job, Stopped

#: How often the worker looks at *Stop* while the command runs.
POLL = 0.1


class PanelizeJob(Job):
    """A command under way: what it printed, and how it ended."""

    def __init__(self) -> None:
        super().__init__()
        self.output = ""
        self.errors = ""
        self.status: int | None = None


def capture(command: str, cwd: Path, job: PanelizeJob) -> None:
    """Run *command* in *cwd* to its end, its output into *job* (a thread runs
    it).  *Stop* ends the command's whole process group and raises
    :class:`Stopped`; a shell that cannot start raises ``OSError``."""
    shell = os.environ.get("SHELL") or "/bin/sh"
    process = subprocess.Popen([shell, "-c", command], cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    while True:
        try:
            out, err = process.communicate(timeout=POLL)
            break
        except subprocess.TimeoutExpired:
            if job.stopped:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except OSError:
                    pass
                process.communicate()
                raise Stopped from None
    job.output = out.decode("utf-8", "surrogateescape")
    job.errors = err.decode("utf-8", "surrogateescape")
    job.status = process.returncode


def lines_of(output: str) -> list[str]:
    """*output* as the names it holds: split on NULs if it has any, else on lines."""
    if "\0" in output:
        return output.split("\0")
    return output.splitlines()
