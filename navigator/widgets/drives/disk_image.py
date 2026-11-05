"""The loop's side of disk images (:func:`navigator.lib.system.udisks.attach_image`):
Enter on an ``.iso`` or ``.img`` attaches it read-only, mounts what is on it
and takes the panel there -- with several file systems, the one chosen from
a box.  Not DOS Navigator's, which had no loop devices; GNOME's Disk Image
Mounter does the same."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.system.job import Stopped
from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress


async def enter_image(panel: Any, path: Path) -> bool:
    """*panel* into the disk image at *path*, mounted.  False when there is
    no ``udisksctl`` to mount it with -- the caller opens it as any file;
    True otherwise, a failure said."""
    from navigator.lib.system import udisks
    from navigator.widgets.editor.loading import FileJob, progress_box, refresh_box

    if udisks.program() is None:
        return False
    app = panel.application
    job = FileJob()
    try:
        mounted = await run_with_progress(
            app, lambda: udisks.attach_image(path, stop=lambda: job.stopped), job,
            lambda: progress_box(job, tr("Mounting image")), refresh_box(job), delay=SLOW_PROGRESS_DELAY,
        )
    except Stopped:
        return True
    except OSError as error:
        if app is not None:
            await Dialog(title=tr("Error"), buttons="ok", prompt=tr("Cannot mount {path}: {error}").format(
                path=escape_caption(str(path)), error=escape_caption(error.strerror or str(error)),
            )).execute(app)
        return True
    if job.stopped or not mounted:
        return True
    _say_mounted(app, path, mounted)
    volume = mounted[0] if len(mounted) == 1 else await _choose(panel, path, mounted)
    if volume is None or panel.parent is None:
        return True
    panel.leave_found()
    panel.path = Path(volume.local)
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


__all__ = ["enter_image"]
