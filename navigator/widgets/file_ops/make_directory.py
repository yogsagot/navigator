"""Making a directory: what F7 (``Manager.make_directory``) and Alt+T's
*Make directory* (``ChangeDirDialog``) both do, so they do it alike.

DN's ``MakeDirectory`` and ``CreateDirInheritance``: a ``;`` list, each
part made with every directory on its way that is missing, one there
already accepted.  On the disk at once (a ``mkdir`` per directory on a path
just named, which the rules allow on the loop); on another drive on a
thread, its archive rewritten.  A refusal on the disk -- or an archive on the disk whose
rewrite is refused -- offers *As root* (a departure;
:mod:`navigator.lib.system.elevate`) and is done again through the root
helper.  What is made goes on File > Undo's history.

Called from a task a handler spawned, never awaited in a handler.
"""

from __future__ import annotations

import asyncio
import errno
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from navkit.i18n import tr

from navigator.lib.drives import Location, drive_of
from navigator.lib.file_ops import undo as undo_history
from navigator.lib.file_ops.undo import UNDO


def failure_text(path: Any, error: OSError) -> str:
    """DN's ``dlFCNoCreateDir``: *Could not create the directory PATH* and
    why -- F7's words, Alt+T's and the *As root* question's."""
    return tr("Could not create the directory {path}\n{reason}").format(
        path=str(path), reason=error.strerror or str(error))


def parts_of(text: str) -> list[str]:
    """DN's ``MakeDirectory`` list: *text* split on ``;``, each part's
    blanks trimmed, the empty ones left out (``TREE.PAS:752-758``)."""
    return [part.strip() for part in text.split(";") if part.strip()]


@dataclass
class Made:
    """What :func:`make_directory_in` did."""

    #: The directory asked for, whole.
    place: Location
    #: Every directory made on the way, outermost first: empty when *place*
    #: was there already (DN's ``FindFirst`` found it, and that was all).
    made: list[Location] = field(default_factory=list)

    @property
    def top(self) -> Location | None:
        """The first directory made -- whose parent's listing changed."""
        return self.made[0] if self.made else None


async def _as_root(app: Any, error: OSError, path: Any) -> bool | None:
    """*As root* for *error*: True once the helper runs, False declined, None
    when it may not be offered (not a refusal, or no way to root)."""
    from navigator.lib.system.elevate import ELEVATION, refused
    from navigator.widgets.file_ops.as_root import ask_as_root

    if not refused(error) or not await asyncio.to_thread(ELEVATION.available):
        return None
    return await ask_as_root(app, failure_text(path, error))


def _missing(place: Location, drive: Any) -> list[Location]:
    """*place* and every directory above it not there yet, outermost first;
    ``EEXIST`` when *place* is there and not a directory."""
    chain: list[Location] = []
    here = place
    while not drive.lexists(here):
        chain.append(here)
        if here.is_root:
            break
        here = here.parent
    if not chain and not drive.is_dir(place):
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(place))
    chain.reverse()
    return chain


def _recorded(made: Made) -> Made:
    """*made* on File > Undo's history: the new directory and the new ones
    above it, taken back deepest first.  Nothing made, nothing pushed."""
    if made.made:
        UNDO.push(undo_history.MadeDirectory(made.made[-1], tuple(reversed(made.made[:-1]))))
    return made


async def make_directory_in(app: Any, base: Path | Location, name: str) -> Made | None:
    """*name* made in *base*, as DN's ``CreateDirInheritance``: each
    directory on the way that is not there made in turn, one there already
    accepted without a word.  What was done (:class:`Made`), or None when
    *As root* was declined.  Any other failure is raised (``OSError``) --
    what was made before it stays, as DN's did -- for the caller to say
    with :func:`failure_text`."""
    from navigator.lib.drives.root import ROOT_DRIVE
    from navigator.lib.system.elevate import ELEVATION

    base = Location.of(base)
    place = (base / name).normalized()
    if place.is_local:
        drive = drive_of(place)
        chain = _missing(place, drive)
        made: list[Location] = []
        for index, step in enumerate(chain):
            try:
                os.mkdir(step.local)
                made.append(step)
            except OSError as error:
                answer = await _as_root(app, error, step)
                if answer is None:
                    raise
                if not answer:
                    _recorded(Made(place, made))
                    return None
                rest = chain[index:]

                def make_as_root() -> None:
                    try:
                        for each in rest:
                            ROOT_DRIVE.mkdir(each)
                    finally:
                        ELEVATION.release()

                await asyncio.to_thread(make_as_root)
                made.extend(rest)
                break
        return _recorded(Made(place, made))

    # Another drive is a round trip away: a thread makes it.
    done: list[Location] = []

    def make() -> None:
        drive = drive_of(place)
        for step in _missing(place, drive):
            drive.mkdir(step)
            done.append(step)
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
        answer = await _as_root(app, error, place)
        if answer is None:
            raise
        if not answer:
            return None

        def finish_as_root() -> None:
            drive.go_root()
            drive.finish()

        await asyncio.to_thread(finish_as_root)
    return _recorded(Made(place, done))


async def make_directories(app: Any, base: Path | Location, text: str) -> tuple[list[Made], tuple[Any, OSError] | None]:
    """DN's ``MakeDirectory``: each part of *text*'s ``;`` list made in *base*
    in turn (:func:`make_directory_in`), stopping at the first failure or a
    declined *As root*.  What was made, and the failure -- ``(path, error)``
    -- for the caller to say, or None."""
    results: list[Made] = []
    base = Location.of(base)
    for part in parts_of(text):
        try:
            made = await make_directory_in(app, base, part)
        except OSError as error:
            return results, ((base / part).normalized(), error)
        if made is None:
            break
        results.append(made)
    return results, None


__all__ = ["Made", "failure_text", "make_directories", "make_directory_in", "parts_of"]
