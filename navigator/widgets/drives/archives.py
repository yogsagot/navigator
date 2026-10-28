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
    :mod:`navigator.lib.system.elevate`).  An encrypted archive asks for its
    password, again after a wrong one, as DN's ``dlgSetPassword`` asked for
    an archiver's; Cancel is ``Stopped``.  ``PermissionError`` still if *As
    root* was declined; whatever else ``open_archive`` raises."""
    from navigator.lib.drives import archive
    from navigator.lib.system.elevate import ELEVATION, refused
    from navigator.widgets.editor.loading import progress_box, refresh_box

    as_root, password = False, ""

    def opening() -> Any:
        return run_with_progress(
            app, lambda: archive.open_archive(origin, job, as_root=as_root, password=password), job,
            lambda: progress_box(job, tr("Reading archive")), refresh_box(job), delay=SLOW_PROGRESS_DELAY,
        )

    while True:
        try:
            return await opening()
        except archive.NeedPassword:
            if app is None:
                raise
            answer = await ask_archive_password(app, origin, wrong=bool(password))
            if answer is None:
                raise Stopped from None
            password = answer
        except OSError as error:
            if as_root or not (origin.is_local and refused(error) and app is not None
                               and await asyncio.to_thread(ELEVATION.available)):
                raise
            from navigator.widgets.file_ops.as_root import ask_as_root

            message = tr("Cannot read {path}: {error}").format(path=str(origin), error=error.strerror or error)
            if not await ask_as_root(app, message):
                raise Stopped from None
            as_root = True


async def ask_archive_password(app: Any, origin: Location, *, wrong: bool = False) -> str | None:
    """The password of the encrypted archive at *origin*, or None for Cancel."""
    from navigator.widgets.drives.password_dialog import PasswordDialog

    if wrong:
        prompt = tr("Wrong password for {name}. Try again:").format(name=escape_caption(origin.name))
    else:
        prompt = tr("{name} is encrypted. Its password:").format(name=escape_caption(origin.name))
    answer = await PasswordDialog(title=tr("Archive password"), prompt=prompt).execute(app)
    return None if answer is None else answer[0]


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
