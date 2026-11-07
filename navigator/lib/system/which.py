"""``shutil.which``, remembered for a few seconds.

What a menu, the key bar or a command's ``refusal`` asks -- *is udisksctl
there, is gpg, is docker* -- is asked again on every frame they are painted,
and each ``shutil.which`` walks ``$PATH`` with a ``stat`` per directory.  So
the answer is kept for :data:`TTL` seconds: short enough that a tool
installed while Navigator runs turns its greyed entry on in a moment, long
enough that a menu held open costs nothing.

Keyed on the name, the search path, ``$PATH`` itself (a changed one is
looked through at once) and ``shutil.which``'s identity -- a test that puts
its own in place is asked at once, never answered from before it.
"""

from __future__ import annotations

import os
import shutil
import threading
import time

#: How long an answer is kept, in seconds.
TTL = 5.0

_lock = threading.Lock()
_answers: dict[tuple[str, str | None, str | None, int], tuple[float, str | None]] = {}


def which(name: str, path: str | None = None) -> str | None:
    """Where *name* is (on *path*, else ``$PATH``), or None: as
    ``shutil.which`` answers, from the last :data:`TTL` seconds' answer."""
    finder = shutil.which
    key = (name, path, os.environ.get("PATH"), id(finder))
    now = time.monotonic()
    with _lock:
        kept = _answers.get(key)
    if kept is not None and now - kept[0] < TTL:
        return kept[1]
    found = finder(name, path=path) if path is not None else finder(name)
    with _lock:
        _answers[key] = (now, found)
    return found


def forget() -> None:
    """Every program looked up again at its next use (tests; a changed setup)."""
    with _lock:
        _answers.clear()


__all__ = ["TTL", "forget", "which"]
