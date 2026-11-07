"""fzf and zoxide, where the user has them: not DOS Navigator's (a departure, asked for).

fzf is never run from here: its interface is drawn on the console by the
command line's shell (:meth:`navigator.lib.system.subshell.Subshell.pick`),
which is where the user's own ``FZF_*`` variables are.  What this module does
is say which of the two are installed, and tell zoxide where the panels have
been -- Interface's *Feed zoxide* -- so its database knows the directories
reached in Navigator, not only those ``cd`` reached in a shell.
"""

from __future__ import annotations

import queue
import shutil
import subprocess
import threading
from navigator.lib.system.which import which as _which

#: Where each program was found, by name: looked up once, or reported by the
#: shell, whose rc may put on ``PATH`` what Navigator's environment lacks.
_found: dict[str, str | None] = {}


def program(name: str) -> str | None:
    """Where *name* (``"fzf"`` or ``"zoxide"``) is, or None: not installed."""
    if name not in _found:
        _found[name] = _which(name)
    return _found[name]


def found(name: str, path: str | None) -> None:
    """The shell found *name* at *path*: that one is used from now on."""
    if path:
        _found[name] = path


def forget() -> None:
    """Look every program up again at its next use (tests)."""
    _found.clear()


_adds: queue.Queue[str] = queue.Queue()
_worker: threading.Thread | None = None
_lock = threading.Lock()


def add(directory: str) -> None:
    """``zoxide add`` *directory*, on a thread of its own: zoxide writes its
    database, which may wait on a disk.  Nothing is done without zoxide."""
    global _worker
    if program("zoxide") is None:
        return
    _adds.put(directory)
    with _lock:
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(target=_add_all, name="zoxide add", daemon=True)
            _worker.start()


def _add_all() -> None:
    while True:
        directory = _adds.get()
        zoxide = program("zoxide")
        if zoxide is None:
            continue
        try:
            subprocess.run([zoxide, "add", "--", directory], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass
