"""Printing: the system's spooler, where DOS Navigator had its own.

DN's ``Print`` (``EDITOR.PAS``) wrote what was to be printed to a ``.PRN``
file and posted ``cmFilePrint``, and ``PRINTMAN.PAS``'s print manager fed the
file to the printer port set up under Options.  A POSIX system has that
manager already -- CUPS, or the BSD spooler -- so the text is handed to
``lp``, or ``lpr`` where there is no ``lp``, which print on ``$PRINTER`` or
the default destination.  No temporary file, no queue window, and no form
feed at the end: the spooler ejects the page itself.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable

#: How long the spooler may take to accept a job.
TIMEOUT = 10.0

#: What says there is nothing to print with.
NO_SPOOLER = "No print command: neither lp nor lpr is installed"


def print_command(which: Callable[[str], str | None] | None = None) -> list[str] | None:
    """The command that prints its standard input, if there is one.

    ``shutil.which`` is looked up at the call, not bound as the default, so
    that replacing it -- as the tests do -- reaches this function too.
    """
    if which is None:
        which = shutil.which
    for argv in (["lp"], ["lpr"]):
        if which(argv[0]):
            return argv
    return None


def _run(argv: list[str], data: bytes | None) -> str | None:
    try:
        result = subprocess.run(argv, input=data, capture_output=True, timeout=TIMEOUT)
    except (OSError, subprocess.SubprocessError) as error:
        return f"{argv[0]}: {error}"
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        return message or f"{argv[0]} failed ({result.returncode})"
    return None


def spool_file(path: Path) -> str | None:
    """Print the file at *path* as it is on disk; None once queued, else why not.

    The file manager's Ctrl+F9: the spooler is given the name, as DN's print
    manager was given ``cmFilePrint``'s, and reads the file itself.
    """
    argv = print_command()
    if argv is None:
        return NO_SPOOLER
    # Absolute, so the name can never be read as an option, with or without ``--``.
    return _run([*argv, str(path.absolute())], None)


def spool(text: str) -> str | None:
    """Print *text*; None once the spooler has the job, else why not.

    Blocks for as long as the spooler takes to answer, so it is run in an
    executor.  A byte that was not UTF-8 in the file goes out as it was.
    """
    argv = print_command()
    if argv is None:
        return NO_SPOOLER
    return _run(argv, text.encode("utf-8", "surrogateescape"))
