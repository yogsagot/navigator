"""The loop's side of *As root* (:mod:`navigator.lib.system.elevate`): the
question that offers it, and opening the root helper -- sudo's password asked
in Navigator's own box, polkit's agent left to ask for itself.

A departure: DOS refused no one.  Called from a task a handler spawned, or
from a worker's question being answered, never awaited in a handler.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.system.elevate import ELEVATION, Asked, Refused, untrusted_code


async def open_root(app: Any) -> bool:
    """Start the root helper, asking for what it needs; True once it runs.

    A refusal is said in an *Error* box; Cancel in the password box says
    nothing.
    """
    from navigator.widgets.drives.password_dialog import PasswordDialog

    state = await asyncio.to_thread(ELEVATION.begin)
    while isinstance(state, Asked):
        prompt = tr("Wrong password. Try again:") if state.wrong else escape_caption(state.prompt)
        box = PasswordDialog(prompt)
        box.title = tr("Root access")
        answer = await box.execute(app)
        state = await asyncio.to_thread(ELEVATION.answer, None if answer is None else answer[0])
    if isinstance(state, Refused):
        if state.reason:
            await Dialog(
                title=tr("Error"),
                prompt=tr("Root access was refused: {reason}").format(reason=escape_caption(state.reason)),
                buttons="ok",
            ).execute(app)
        return False
    return True


def root_source(path: Path) -> Any:
    """*path* as a viewer source read through the root helper, a chunk at a
    time on a thread (:class:`~navigator.lib.viewer.ChunkedSource`), never
    copied to the disk.  Blocking: on a thread.  Raises ``OSError``."""
    import stat

    from navigator.lib.drives.location import Location
    from navigator.lib.drives.root import ROOT_DRIVE
    from navigator.lib.viewer import ChunkedSource

    origin = Location.of(Path(path))
    st = ROOT_DRIVE.stat(origin)
    if not stat.S_ISREG(st.st_mode):
        raise OSError(21 if stat.S_ISDIR(st.st_mode) else 22, "Not a regular file", str(path))
    source = ChunkedSource(origin, st.st_size, ROOT_DRIVE.open_random(origin))
    source.path = Path(path)  # its whole name: the quick view compares it
    source.drive = ROOT_DRIVE
    return source


async def database_as_root(desktop: Any, path: Path) -> Any:
    """*As DataBase* on a file the user may not read: it and its memo file
    fetched through the root helper into the private directory (owner only),
    the dBase window opened on the copy, and a field edited put back through
    the helper, owner and mode kept -- as a file on a server is
    (``usefile``).  ``OSError`` and ``dbf.DBFError`` are the caller's."""
    from navigator.lib.drives import usefile
    from navigator.lib.drives.location import Location
    from navigator.widgets.viewer.db_window.db_window import open_database

    origin = Location.of(Path(path))

    use = await fetch_database(desktop.application, path)
    if use is None:
        return None
    try:
        window = await open_database(desktop, use.local_for(origin))
    except BaseException:
        usefile.discard(use)
        ELEVATION.unhold()
        await asyncio.to_thread(ELEVATION.release)
        raise
    if window is None:
        usefile.discard(use)
        ELEVATION.unhold()
        await asyncio.to_thread(ELEVATION.release)
        return None
    window.use_set = use
    window.root_held = True
    window.title = str(path)
    return window


async def fetch_database(app: Any, path: Path) -> Any:
    """*path* and its memo file fetched through the root helper into the
    private directory (owner only), the helper **held** for the window that
    will put fields back -- its ``close()`` lets go.  None if stopped."""
    from navigator.lib.drives import usefile
    from navigator.lib.drives.location import Location
    from navigator.lib.drives.root import ROOT_DRIVE
    from navigator.widgets.editor.loading import read_in_background

    origin = Location.of(Path(path))

    def fetch(job: Any, budget: Any) -> Any:
        origins = [origin]
        for suffix in (".fpt", ".FPT", ".dbt", ".DBT"):
            memo = Location.of(Path(path).with_suffix(suffix))
            if memo != origin and ROOT_DRIVE.exists(memo):
                origins.append(memo)
        try:
            use = usefile.fetch(origins, job, drive=ROOT_DRIVE)
        except BaseException:
            ELEVATION.release()  # stopped or failed: nothing will put back
            raise
        ELEVATION.hold()
        return use

    return await read_in_background(app, fetch)


async def view_as_root(desktop: Any, path: Path, mode: str | None = None) -> Any:
    """F3 on a file the user may not read: its chunks fetched through the
    root helper on a thread, as a file on a server's are
    (:class:`~navigator.lib.viewer.ChunkedSource`).  The window holds the
    helper open until it closes.  Raises ``OSError``."""
    from navigator.lib.viewer import ChunkedSource
    from navigator.widgets.viewer.file_window import FileWindow

    def opened() -> ChunkedSource:
        try:
            return root_source(path)
        except BaseException:
            ELEVATION.release()
            raise

    source = await asyncio.to_thread(opened)
    window = FileWindow(Path(path), mode=mode, source=source)
    desktop.open(window)
    window.title = str(path)
    return window


def _question(title: str, message: str, buttons: str) -> Dialog:
    """The box that offers *As root*, saying so when root would run code the
    user could change (a checkout, a virtualenv): their own consent to that,
    not a refusal (``elevate.untrusted_code``)."""
    prompt = escape_caption(message)
    path = None if ELEVATION.running else untrusted_code()
    if path is None:
        return Dialog(title=title, prompt=prompt, buttons=buttons)
    warning = tr("Root will run code from {path}, which your user can change.").format(path=str(path))
    box = Dialog(title=title, prompt=f"{prompt}\n\n{escape_caption(warning)}", buttons=buttons)
    box.modal_width = 64
    box.modal_height = 14
    return box


async def ask_as_root(app: Any, message: str, *, title: str | None = None) -> bool:
    """*message*, with *As root* and *Cancel*: True once the helper runs.
    *title* is the box's, an *Error* unless given."""
    while True:
        box = _question(title or tr("Error"), message, "ok-cancel")
        box.ok.text = tr("As ~r~oot")
        if await box.execute(app) is not True:
            return False
        if await open_root(app):
            return True


async def reach_root(app: Any, place: Any) -> bool:
    """A ``root:`` place come back to -- from a history, a bookmark, a
    saved desktop -- with root access not open: *Open it as root?* asked,
    the helper started, and the root drive mounted.  True once it is; False
    if there is no way to root, which is said, or it was not wanted."""
    from navigator.lib.drives import root

    if not ELEVATION.running:
        if not await asyncio.to_thread(ELEVATION.available):
            await Dialog(title=tr("Root access"), prompt=tr("{path}: root access is not available").format(
                path=escape_caption(str(root.on_disk(place)))), buttons="ok").execute(app)
            return False
        if not await ask_as_root(app, tr("Open {path} as root?").format(path=str(root.on_disk(place))),
                                 title=tr("Root access")):
            return False
    root.mount_drive()
    return True


async def ask_skip(app: Any, message: str, *, elevate: bool = False) -> Any:
    """An error with *Skip* and *Cancel* -- and *As root* when *elevate* and
    there is a way to ask for root.  True skips, None cancels, and
    :data:`~navigator.lib.file_ops.filecopy.AS_ROOT` once the helper runs."""
    from navigator.lib.file_ops.filecopy import AS_ROOT

    offer = elevate and ELEVATION.available()
    while True:
        box = (_question(tr("Error"), message, "yes-no-cancel") if offer
               else Dialog(title=tr("Error"), prompt=escape_caption(message), buttons="ok-cancel"))
        box.ok.text = tr("~S~kip")
        if offer:
            box.no.text = tr("As ~r~oot")
        answer = await box.execute(app)
        if answer is not False:
            return answer is True or None
        if await open_root(app):
            return AS_ROOT


__all__ = ["ask_as_root", "ask_skip", "database_as_root", "fetch_database", "open_root", "reach_root",
           "root_source", "view_as_root"]
