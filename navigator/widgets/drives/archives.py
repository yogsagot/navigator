"""The loop's side of archives as drives (:mod:`navigator.lib.drives.archive`):
Enter on one opens it, on a thread, under *Reading archive* if it takes a
while -- a compressed tar is read whole to learn what is in it."""

from __future__ import annotations

import asyncio
from typing import Any

from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location
from navigator.lib.system.job import Stopped
from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress


async def open_archive_or_root(app: Any, origin: Location, job: Any) -> Any:
    """``archive.open_archive`` on a thread under *Reading archive* -- and,
    for one on the disk the user may not read, *As root* offered and the
    archive opened through the root helper (a departure;
    :mod:`navigator.lib.system.elevate`).  ``PermissionError`` still if that
    was declined; whatever else ``open_archive`` raises."""
    from navigator.lib.drives import archive
    from navigator.lib.system.elevate import ELEVATION, refused
    from navigator.widgets.editor.loading import progress_box, refresh_box

    def opening(as_root: bool) -> Any:
        return run_with_progress(
            app, lambda: archive.open_archive(origin, job, as_root=as_root), job,
            lambda: progress_box(job, tr("Reading archive")), refresh_box(job), delay=SLOW_PROGRESS_DELAY,
        )

    try:
        return await opening(False)
    except OSError as error:
        if not (origin.is_local and refused(error) and app is not None
                and await asyncio.to_thread(ELEVATION.available)):
            raise
        from navigator.widgets.file_ops.as_root import ask_as_root

        message = tr("Cannot read {path}: {error}").format(path=str(origin), error=error.strerror or error)
        if not await ask_as_root(app, message):
            raise Stopped from None
        return await opening(True)


async def enter_archive(panel: Any, origin: Location) -> bool:
    """*panel* into the archive at *origin*: DN's ``ArcViewer`` and
    ``InsertDrive``.  False if it is no archive this can read -- the caller
    runs it as a file instead, as DN did; True otherwise, a failure said."""
    from navigator.lib.drives import archive
    from navigator.widgets.editor.loading import FileJob

    app = panel.application
    job = FileJob()
    try:
        drive = await open_archive_or_root(app, origin, job)
    except archive.NeedsTool as error:
        if app is not None:
            await Dialog(title=tr("Error"), prompt=tr("Cannot read {path}: {error}").format(
                path=escape_caption(str(origin)), error=escape_caption(str(error))), buttons="ok").execute(app)
        return True
    except archive.NotAnArchive:
        return False
    except Stopped:
        return True
    except OSError as error:
        if app is not None:
            await Dialog(title=tr("Error"), prompt=tr("Cannot read {path}: {error}").format(
                path=escape_caption(str(origin)), error=error.strerror or error), buttons="ok").execute(app)
        return True
    if job.stopped:
        return True
    if panel.parent is None:
        return True
    panel.leave_found()
    panel.location = drive.at("/")
    return True
