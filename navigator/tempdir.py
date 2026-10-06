"""Where Navigator puts its own temporary files: DN's ``SwpDir``.

The System setup's *Temporary directory* (``system.temp_dir``), or
``$TMPDIR`` -- ``tempfile.gettempdir()`` -- when it is empty, read each time
it is asked, so a change applies to the next file made.
"""

from __future__ import annotations

import errno
import os
import stat
import tempfile
from pathlib import Path

from navigator.settings import SETTINGS


def temp_root() -> Path:
    """The directory temporary files go in: the setting's, else the system's."""
    chosen = SETTINGS.system.temp_dir.strip()
    return Path(chosen).expanduser() if chosen else Path(tempfile.gettempdir())


def private_dir() -> Path:
    """``navigator-<uid>`` in :func:`temp_root`, made if need be, readable by
    this user alone.

    For files kept under fixed names -- the user menu's script and lists --
    which the shell then runs: one in a directory somebody else made, or
    could write to, is refused rather than run.  Raises ``OSError``.
    """
    directory = temp_root() / f"navigator-{os.getuid()}"
    os.makedirs(directory, mode=0o700, exist_ok=True)
    info = os.lstat(directory)
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise OSError(errno.EPERM, "not a directory of this user's alone", str(directory))
    return directory
