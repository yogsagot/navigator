"""The loop's side of archives as drives (:mod:`navigator.lib.drives.archive`):
Enter on one opens it, on a thread, under *Reading archive* if it takes a
while -- a compressed tar is read whole to learn what is in it."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location
from navigator.lib.system.job import Stopped
from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress


async def enter_archive(panel: Any, origin: Location) -> bool:
    """*panel* into the archive at *origin*: DN's ``ArcViewer`` and
    ``InsertDrive``.  False if it is no archive this can read -- the caller
    runs it as a file instead, as DN did; True otherwise, a failure said."""
    from navigator.lib.drives import archive
    from navigator.widgets.editor.loading import FileJob, progress_box, refresh_box

    app = panel.application
    job = FileJob()
    try:
        drive = await run_with_progress(
            app, lambda: archive.open_archive(origin, job), job,
            lambda: progress_box(job, tr("Reading archive")), refresh_box(job), delay=SLOW_PROGRESS_DELAY,
        )
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
