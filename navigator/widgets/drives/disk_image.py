"""The loop's side of disk images (:func:`navigator.lib.system.udisks.attach_image`):
Enter on an ``.iso`` or ``.img`` attaches it read-only, mounts what is on it
and takes the panel there -- with several file systems, the one chosen from
a box -- and *Unmount image* undoes it (:func:`unmount_image`).  The panel's
commands, the Disk menu's and Disk > Volumes' all come here.  Not DOS
Navigator's, which had no loop devices; GNOME's Disk Image Mounter does the
same."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.system.job import Stopped
from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress


#: How many times :func:`unmount_image` asks, while the mount is still
#: busy, and how long it waits between: a shell following a panel out takes
#: a moment.
UNMOUNT_TRIES = 4
UNMOUNT_WAIT = 0.3


async def mount_image(app: Any, path: Path) -> list[Any] | None:
    """The disk image at *path* mounted on a thread under *Mounting image*,
    a toast saying so: its file systems, mounted -- or None, Stop pressed or
    a failure said in a box."""
    from navigator.lib.system import udisks
    from navigator.widgets.editor.loading import FileJob, progress_box, refresh_box

    job = FileJob()
    try:
        mounted = await run_with_progress(
            app, lambda: udisks.attach_image(path, stop=lambda: job.stopped), job,
            lambda: progress_box(job, tr("Mounting image")), refresh_box(job), delay=SLOW_PROGRESS_DELAY,
        )
    except Stopped:
        return None
    except OSError as error:
        if app is not None:
            await Dialog(title=tr("Error"), buttons="ok", prompt=tr("Cannot mount {path}: {error}").format(
                path=escape_caption(str(path)), error=escape_caption(error.strerror or str(error)),
            )).execute(app)
        return None
    if job.stopped or not mounted:
        return None
    _say_mounted(app, path, mounted)
    return mounted


async def enter_image(panel: Any, path: Path) -> bool:
    """*panel* into the disk image at *path*, mounted.  False when there is
    no ``udisksctl`` to mount it with -- the caller opens it as any file;
    True otherwise, a failure said."""
    from navigator.lib.system import udisks

    if udisks.program() is None:
        return False
    mounted = await mount_image(panel.application, path)
    if not mounted:
        return True
    volume = mounted[0] if len(mounted) == 1 else await _choose(panel, path, mounted)
    if volume is None or panel.parent is None:
        return True
    panel.leave_found()
    panel.path = Path(volume.local)
    return True


async def unmount_image(app: Any, mounts: list[Any]) -> bool:
    """The disk image *mounts* are of (``udisks.image_at``'s) unmounted,
    every file system of it, and its loop device detached
    (:func:`navigator.lib.system.udisks.eject`).  Each panel inside it, in
    every file manager, is first taken back to the image file, so that
    neither it nor the shell that follows it keeps the mount busy; a mount
    still busy a moment later (the shell's ``cd`` not yet done) is tried
    again, up to :data:`UNMOUNT_TRIES` times.  A toast says it is done, a box
    why not; True when it was."""
    from navigator.lib.system import udisks
    from navigator.widgets.manager.manager.manager import Manager

    if not mounts:
        return False
    image = Path(mounts[0].backing)
    points = [mount.point.rstrip("/") for mount in mounts]
    shell = getattr(app, "root", None)
    desktop = getattr(shell, "desktop", None)
    for window in desktop.windows() if desktop is not None else ():
        if not isinstance(window, Manager):
            continue
        for side in window.all_panels:
            where = side.location
            if where.is_local and any(str(where.local) == point or str(where.local).startswith(point + "/")
                                      for point in points):
                side.go_to_file(image)
    failure: OSError | None = None
    for attempt in range(UNMOUNT_TRIES):
        # Let the panels' reads and the shell's ``cd`` land first.
        await asyncio.sleep(UNMOUNT_WAIT if attempt else 0)
        try:
            await asyncio.to_thread(udisks.eject, mounts[0].device)
        except OSError as error:
            failure = error
            if "busy" not in str(error).lower():
                break
        else:
            failure = None
            break
    if app is None:
        return failure is None
    if failure is not None:
        await Dialog(title=tr("Error"), buttons="ok", prompt=tr("Cannot unmount {name}: {error}").format(
            name=escape_caption(image.name), error=escape_caption(failure.strerror or str(failure)),
        )).execute(app)
        return False
    toast = getattr(shell, "toast", None)
    if toast is not None and app.is_running:
        toast(tr("Unmounted"), title=image.name)
    return True


def _say_mounted(app: Any, path: Path, mounted: list[Any]) -> None:
    """A toast that *path* is mounted, and where -- said before any box asks
    which file system to open, since Cancel there leaves them mounted."""
    toast = getattr(getattr(app, "root", None), "toast", None)
    if toast is None or not app.is_running:
        return
    if len(mounted) == 1:
        text = tr("Mounted at {where}").format(where=mounted[0].local)
    else:
        text = tr_n("{n} file system mounted", "{n} file systems mounted", len(mounted))
    toast(text, title=path.name)


async def _choose(panel: Any, path: Path, mounted: list[Any]) -> Any:
    """The file system of *mounted* the panel goes to, chosen from a box --
    each by its name, size and mount point -- or None for Cancel."""
    from navigator.lib.system.sysinfo import size_text
    from navml.widgets.menu.popup_menu import PopupMenu
    from navml.widgets.menu.sub_menu import SubMenu

    app = panel.application
    menu = SubMenu()
    chosen_of: dict[int, Any] = {}
    for volume in mounted:
        size = f"  {size_text(volume.size)}" if volume.size else ""
        item = menu.add_item(escape_caption(f"{volume.name}{size}  {volume.local}"))
        chosen_of[id(item)] = volume
    title = tr("Mount {name}").format(name=path.name)
    box = PopupMenu(menu, behind=panel, title=title)
    width, height = PopupMenu.measure(menu, app, panel, title)
    box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
    chosen = await box.execute(app)
    return None if chosen is None else chosen_of.get(id(chosen))


__all__ = ["UNMOUNT_TRIES", "UNMOUNT_WAIT", "enter_image", "mount_image", "unmount_image"]
