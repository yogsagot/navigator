"""Keeping other programs off a file being edited: ``TFileEditor.LockFile``.

With *Lock edited files* (``ebfLck``) DN kept the edited file open, read-only
in DOS's compatibility mode (``Locker``, opened with ``$3D00``), from the
moment it was read until the editor let it go, and under ``SHARE`` no other
program could then open it to write.  A program of its own could: sharing
modes were between programs, so two of DN's editors on one file both saved.

POSIX has no locks a writer is held to, so this is the advisory one,
``flock``: an exclusive lock held on an open descriptor.  It keeps off what
asks for a lock -- another Navigator, ``flock(1)``, a program that checks --
and nothing else; ``vi`` writes regardless.  What it is in this program is
shared: one descriptor per file, counted (``_held``), so a second window on a
file this Navigator holds shares the lock rather than being refused it, as
DN's own editors were not refused.

:func:`refuse_if_locked` is the other half, ``CantWrite`` on a file another
program holds: every write the editor makes asks it first, whatever this
editor's own *Lock edited files* says, as ``SHARE`` refused DN's write to a
file another program had open whether DN locked its own files or not.
"""

from __future__ import annotations

import errno
import fcntl
import os
from pathlib import Path

#: The locks this program holds: (device, inode) -> [descriptor, holders].
_held: dict[tuple[int, int], list[int]] = {}

#: Non-blocking, so a FIFO is not waited on; a symbolic link is followed,
#: so what is locked is the file it names, as a save writes that.
_FLAGS = os.O_RDONLY | os.O_NONBLOCK


def take(path: Path) -> tuple[int, int] | None:
    """Lock *path*'s file; the key :func:`release` is given, or None.

    None when the file cannot be opened (not there yet, not readable) or
    another program holds it, which DN's ``Locker`` failing to open let pass
    in silence too.
    """
    try:
        descriptor = os.open(path, _FLAGS)
    except OSError:
        return None
    try:
        info = os.fstat(descriptor)
        key = (info.st_dev, info.st_ino)
        if key in _held:
            _held[key][1] += 1
            os.close(descriptor)
            return key
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(descriptor)
        return None
    _held[key] = [descriptor, 1]
    return key


def release(key: tuple[int, int] | None) -> None:
    """Let go of what :func:`take` gave *key* for; the last holder unlocks."""
    entry = _held.get(key) if key is not None else None
    if entry is None:
        return
    entry[1] -= 1
    if entry[1] == 0:
        del _held[key]
        os.close(entry[0])  # closing the descriptor drops its lock


def locked_elsewhere(path: Path) -> bool:
    """Whether another program holds *path*'s file locked."""
    try:
        descriptor = os.open(path, _FLAGS)
    except OSError:
        return False
    try:
        info = os.fstat(descriptor)
        if (info.st_dev, info.st_ino) in _held:
            return False
        try:
            # Shared: refused only while somebody holds it exclusively.
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        except OSError:
            return False
        return False
    finally:
        os.close(descriptor)


def refuse_if_locked(path: Path) -> None:
    """Raise ``OSError`` if another program holds *path* locked: ``CantWrite``."""
    if locked_elsewhere(path):
        raise OSError(errno.EAGAIN, "locked by another program", str(path))
