"""Making a directory: what F7 (``Manager.make_directory``) and Alt+T's
*Make directory* (``ChangeDirDialog``) both do, so they do it alike.

On the disk at once (a single ``mkdir`` on a path just named, which the
rules allow on the loop); on another drive on a thread, its archive
rewritten.  A refusal on the disk -- or an archive on the disk whose
rewrite is refused -- offers *As root* (a departure;
:mod:`navigator.lib.system.elevate`) and is done again through the root
helper.  What is made goes on File > Undo's history.

Called from a task a handler spawned, never awaited in a handler.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from navkit.i18n import tr

from navigator.lib.drives import Location, drive_of
from navigator.lib.file_ops import undo as undo_history
from navigator.lib.file_ops.undo import UNDO


def failure_text(name: str, error: OSError) -> str:
    """*Cannot make directory NAME: why* -- F7's words, now Alt+T's too."""
    return tr("Cannot make directory {name}: {error}").format(name=name, error=error.strerror or error)


async def _as_root(app: Any, error: OSError, name: str) -> bool | None:
    """*As root* for *error*: True once the helper runs, False declined, None
    when it may not be offered (not a refusal, or no way to root)."""
    from navigator.lib.system.elevate import ELEVATION, refused
    from navigator.widgets.file_ops.as_root import ask_as_root

    if not refused(error) or not await asyncio.to_thread(ELEVATION.available):
        return None
    return await ask_as_root(app, failure_text(name, error))


async def make_directory_in(app: Any, base: Path | Location, name: str) -> Location | None:
    """*name* made in *base*: where it was made, or None when *As root* was
    declined.  Any other failure is raised (``OSError``), for the caller to
    say with :func:`failure_text`."""
    from navigator.lib.drives.root import ROOT_DRIVE
    from navigator.lib.system.elevate import ELEVATION

    base = Location.of(base)
    place = base / name
    if base.is_local:
        try:
            (base.local / name).mkdir()
        except OSError as error:
            answer = await _as_root(app, error, name)
            if answer is None:
                raise
            if not answer:
                return None

            def make_as_root() -> None:
                try:
                    ROOT_DRIVE.mkdir(place)
                finally:
                    ELEVATION.release()

            await asyncio.to_thread(make_as_root)
        UNDO.push(undo_history.MadeDirectory(place))
        return place

    # Another drive is a round trip away: a thread makes it.
    def make() -> None:
        drive = drive_of(place)
        drive.mkdir(place)
        drive.finish()

    try:
        await asyncio.to_thread(make)
    except OSError as error:
        # An archive on the disk whose rewrite was refused: *As root*, its
        # rewrite put back through the helper.
        drive = drive_of(place)
        outer = getattr(drive, "outer", None)
        if (getattr(drive, "go_root", None) is None or outer is None or not outer.is_local
                or getattr(drive, "as_root", False)):
            raise
        answer = await _as_root(app, error, name)
        if answer is None:
            raise
        if not answer:
            return None

        def finish_as_root() -> None:
            drive.go_root()
            drive.finish()

        await asyncio.to_thread(finish_as_root)
    UNDO.push(undo_history.MadeDirectory(place))
    return place


__all__ = ["failure_text", "make_directory_in"]
