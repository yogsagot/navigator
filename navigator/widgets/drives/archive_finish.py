"""Archives with changes not yet written, finished on the way out -- asking
when they cannot be.

An archive written into (copy, erase, mkdir, ...) is rewritten by
``ArchiveDrive.finish``; when that fails the operation says so and the
changes stay staged (``ArchiveDrive.dirty``).  Before Navigator quits, and
before a panel lets go of such an archive, they are written here, under a
progress box; one that still cannot be is asked about: try again, drop the
changes, or stop there.  DOS Navigator's ``TArcDrive`` rewrote at once and
had no changes left to lose; this is a departure with the staging itself.

Called from a task a handler spawned, never awaited in a handler.
"""

from __future__ import annotations

import asyncio
from typing import Any

from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog


async def _write(app: Any, drive: Any) -> OSError | None:
    """*drive*'s changes written on a thread; the failure, or None."""
    from navigator.widgets.editor.loading import write_in_background

    try:
        await write_in_background(app, lambda job: drive.finish())
    except OSError as error:
        return error
    return None


async def _as_root(app: Any, drive: Any, message: str) -> bool:
    """A refused rewrite of an archive on the disk, offered *As root*
    (``ArchiveDrive.go_root``, as a copy's packing offers it): True once the
    next try will be root's."""
    from navigator.lib.system.elevate import ELEVATION
    from navigator.widgets.file_ops.as_root import ask_as_root

    if drive.as_root or not drive.outer.is_local or not await asyncio.to_thread(ELEVATION.available):
        return False
    if not await ask_as_root(app, message):
        return False
    try:
        await asyncio.to_thread(drive.go_root)
    except OSError:
        return False
    return True


async def finish_pending(app: Any, drives: list[Any]) -> bool:
    """Each of *drives* written, or its changes dropped as the user chose:
    True once none is left pending; False on *Cancel*, which leaves that one
    (and those after it) with their changes still staged."""
    from navigator.lib.system.elevate import refused

    for drive in drives:
        while drive.dirty:
            error = await _write(app, drive)
            if error is None:
                break
            message = tr("The changes to {name} could not be written: {error}").format(
                name=escape_caption(drive.outer.name), error=escape_caption(error.strerror or str(error)))
            if refused(error) and await _as_root(app, drive, message):
                continue
            answer = await Dialog(
                title=tr("Error"), prompt=message + "\n" + tr("Try again? No drops the changes."),
                buttons="yes-no-cancel",
            ).execute(app)
            if answer is None:
                return False
            if answer is False:
                await asyncio.to_thread(drive.discard)
    return True


async def let_go(app: Any, drive: Any) -> None:
    """A panel's last hold on *drive* gone: its changes finished first, then
    it closes, on a thread.  *Cancel* keeps it open, held by no one, its
    changes still staged -- the next visit or quitting asks again
    (``archive.keep_open``)."""
    from navigator.lib.drives import archive

    if drive.dirty and app is not None and not await finish_pending(app, [drive]):
        archive.keep_open(drive)
        return
    await asyncio.to_thread(drive.close)


__all__ = ["finish_pending", "let_go"]
