"""The loop's side of ``UseFile`` (:mod:`navigator.lib.drives.usefile`):
fetching under *Reading file*, and offering back what a program changed.

Both are called from a task a handler spawned, never awaited in a handler.
"""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location, usefile
from navigator.widgets.editor.loading import read_in_background, write_in_background


def upload_policy() -> str:
    """``[remote] upload_changed``: ``ask``, ``always`` or ``never``."""
    from navigator.settings import SETTINGS

    remote = getattr(SETTINGS, "remote", None)
    return getattr(remote, "upload_changed", "ask") if remote is not None else "ask"


async def _say(app: Any, prompt: str) -> None:
    if app is not None:
        await Dialog(title=tr("Error"), prompt=prompt, buttons="ok").execute(app)


async def materialize(app: Any, origins: list[Location]) -> usefile.UseSet | None:
    """*origins* fetched to the disk; None if stopped or failed, which is said."""
    try:
        return await read_in_background(app, lambda job, budget: usefile.fetch(origins, job))
    except OSError as error:
        await _say(app, tr("Cannot read {path}: {error}").format(
            path=escape_caption(str(origins[0])), error=error.strerror or error))
        return None


async def put_back(app: Any, use: usefile.UseSet, *, ask: bool = True) -> bool:
    """What a program changed in *use*, put back where it came from -- asked
    first unless *Upload changed files* says otherwise, or the caller has
    asked already (*ask* off: the editor's F2).  True if anything went up."""
    import asyncio

    changed = await asyncio.to_thread(usefile.changed, use)
    policy = upload_policy()
    if not ask:
        policy = "always"
    if not changed or policy == "never" or app is None:
        return False
    if policy == "ask":
        if len(changed) == 1:
            prompt = tr("{name} was changed. Upload it back to {place}?").format(
                name=escape_caption(changed[0].origin.name),
                place=escape_caption(str(changed[0].origin.parent)))
        else:
            prompt = tr_n("{n} file was changed. Upload it back?", "{n} files were changed. Upload them back?",
                          len(changed))
        if await Dialog(title=tr("Upload"), prompt=prompt, buttons="yes-no").execute(app) is not True:
            return False
    try:
        clashes = await asyncio.to_thread(usefile.conflicts, changed)
    except OSError as error:
        await _say(app, tr("Cannot write {path}: {error}").format(
            path=escape_caption(str(changed[0].origin)), error=error.strerror or error))
        return False
    if clashes:
        names = ", ".join(copy.origin.name for copy in clashes)
        prompt = tr("{names} changed there since it was fetched. Overwrite it?").format(
            names=escape_caption(names))
        if await Dialog(title=tr("Upload"), prompt=prompt, buttons="yes-no").execute(app) is not True:
            return False
    try:
        return await write_in_background(app, lambda job: usefile.upload(changed, job))
    except OSError as error:
        await _say(app, tr("Cannot write {path}: {error}").format(
            path=escape_caption(str(changed[0].origin)), error=error.strerror or error))
        return False


async def view_elsewhere(desktop: Any, origin: Location, mode: str | None = None) -> Any:
    """F3 on a file on another drive: read a chunk at a time where the drive
    can read anywhere in it (``Drive.open_random``) -- the window up at once,
    whatever the file's size -- else fetched whole, and the viewer opened on
    the copy under the file's own name.  None if the fetch was stopped."""
    import asyncio
    import stat
    from pathlib import Path

    from navigator.lib.config.file_history import open_viewer
    from navigator.lib.drives import drive_of
    from navigator.lib.viewer import ChunkedSource

    def chunked() -> Any:
        drive = drive_of(origin)
        st = drive.stat(origin)
        if not stat.S_ISREG(st.st_mode):
            raise OSError(21 if stat.S_ISDIR(st.st_mode) else 22, "Not a regular file", str(origin))
        reader = drive.open_random(origin)
        return None if reader is None else ChunkedSource(origin, st.st_size, reader)

    source = await asyncio.to_thread(chunked)
    if source is not None:
        from navigator.widgets.viewer.file_window import FileWindow

        window = FileWindow(Path(origin.name), mode=mode, source=source)
        desktop.open(window)
        window.title = str(origin)
        return window
    use = await materialize(desktop.application, [origin])
    if use is None:
        return None
    try:
        window = await open_viewer(desktop, use.local_for(origin), mode)
    except BaseException:
        usefile.discard(use)
        raise
    if window is None:
        usefile.discard(use)
        return None
    window.use_set = use
    window.title = str(origin)
    return window


async def edit_elsewhere(desktop: Any, origin: Location, *, new: bool = False) -> Any:
    """F4 on a file on another drive: fetched, and the editor opened on the
    copy; F2 there puts it back (``EditWindow.save``).  *new*, for a name not
    there yet (Shift+F4): an empty copy, which F2 makes there."""
    import asyncio

    from navigator.lib.config.file_history import open_editor

    if new:
        use = await asyncio.to_thread(usefile.blank, origin)
    else:
        use = await materialize(desktop.application, [origin])
    if use is None:
        return None
    try:
        window = await open_editor(desktop, use.local_for(origin))
    except BaseException:
        usefile.discard(use)
        raise
    if window is None:
        usefile.discard(use)
        return None
    window.use_set = use
    return window


async def database_elsewhere(desktop: Any, origin: Location) -> Any:
    """*As DataBase* on a file on another drive: fetched, and the dBase
    window opened on the copy; a field edited goes back (``DBWindow``).
    ``OSError`` and ``dbf.DBFError`` are the caller's."""
    from navigator.widgets.viewer.db_window.db_window import open_database

    use = await materialize(desktop.application, [origin])
    if use is None:
        return None
    try:
        window = await open_database(desktop, use.local_for(origin))
    except BaseException:
        usefile.discard(use)
        raise
    if window is None:
        usefile.discard(use)
        return None
    window.use_set = use
    window.title = str(origin)
    return window
