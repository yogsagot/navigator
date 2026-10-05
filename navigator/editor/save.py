"""Writing a text back: ``TFileEditor.SaveFile`` and ``WriteBlock``.

**A new file replaces the old one in a single rename**, so a crash or a full
disk half way through leaves the old text rather than half of the new one --
DN wrote in place, which cost nothing on a floppy and costs a file here.  The
new file is made beside the old one, given its mode, flushed and renamed over
it.

Two cases cannot be renamed over, and are written in place as DN wrote every
file: **a file with other hard links**, which a rename would split from its
siblings, and **a directory Navigator may not create in**, where there is
nowhere to make the new file.  A symbolic link is followed, so the file it
points at is what changes and the link stays a link.

**Written on a thread, and stoppable** (``EditWindow._write``): the text comes
as chunks, a *job* sees each one go and may stop the write between two -- the
new file is then removed and the old one was never touched.  A write in place
cannot be stopped half way without leaving half a file, so it says so
(``job.cancellable``) and runs to its end.
"""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Iterable

from navigator.job import Stopped


def resolve(path: Path) -> Path:
    """The file a write to *path* changes: a symlink's target, however deep."""
    try:
        return path.resolve(strict=True)
    except (FileNotFoundError, RuntimeError):
        return path


def write_file(path: Path, data: bytes | Iterable[bytes], job: Any = None) -> None:
    """Put *data* in *path*, as safely as the file allows.  Raises ``OSError``.

    *data* is the bytes, or an iterable of chunks of them.  A *job* that is
    stopped between chunks raises :class:`~navigator.job.Stopped`, with the
    old file as it was -- unless the write is in place, which finishes.
    """
    chunks = [data] if isinstance(data, (bytes, bytearray)) else data
    target = resolve(path)
    try:
        info = os.stat(target)
    except FileNotFoundError:
        info = None
    if info is not None and (info.st_nlink > 1 or not os.access(target.parent, os.W_OK)):
        if job is not None:
            job.cancellable = False
        _write_in_place(target, chunks)
        return
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as file:
            for chunk in chunks:
                if job is not None and job.stopped:
                    raise Stopped
                file.write(chunk)
            file.flush()
            os.fsync(file.fileno())
        if info is not None:
            os.chmod(temporary, stat.S_IMODE(info.st_mode))
            try:
                os.chown(temporary, info.st_uid, info.st_gid)
            except PermissionError:
                pass  # somebody else's file in a directory of ours: ours now
        else:
            umask = os.umask(0)
            os.umask(umask)
            os.chmod(temporary, 0o666 & ~umask)
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _write_in_place(path: Path, chunks: Iterable[bytes]) -> None:
    with open(path, "r+b") as file:
        for chunk in chunks:
            file.write(chunk)
        file.truncate()
        file.flush()
        os.fsync(file.fileno())
