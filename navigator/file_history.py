"""File View History and File Edit History: what a viewer or editor is left as.

DOS Navigator remembered, per file, the window a viewer or an editor was closed
in and how it was left -- the position, the mode, the switches -- and put it all
back the next time that file was opened, from F3/F4 or from the *File View
History* (Alt+PgDn) and *File Edit History* (Alt+PgUp) lists
(``HISTRIES.PAS``, ``TDNApplication.ViewFile``/``EditFile`` in
``DNUTIL.PAS``).  The records are the ``ViewRecord`` and ``EditRecord`` models;
the windows say what goes in one and what comes out (``remember_history``,
``recall_history``), and this module holds what the two have in common: the
window's rectangle, and opening one.

Both are gated, as they were, on Options > Configuration > Interface's
*Track viewing history* and *Track editing history* (``ouiTrackViewers``,
``ouiTrackEditors``): off, nothing is written, nothing is restored, and the
lists say to turn the option on.

A record is written when a window opens on a file that has none -- so the file
is listed straight away, as ``StoreViewInfo(W)`` did after ``Init`` -- and
again when it closes, by any route: Esc, the close icon, Close all, and Alt+X,
whose ``cmQuit`` went through every window's ``Valid`` the way ``cmClose`` did.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.i18n import tr

#: ``MinWinSize``: a rectangle smaller than this, once scaled, is not used.
MIN_WIDTH, MIN_HEIGHT = 16, 6


def window_values(window: Any) -> dict[str, Any]:
    """The record's window columns: ``fOrigin``, ``fSize`` and ``fDeskSize``.

    A zoomed window is recorded as zoomed with the rectangle a zoom set aside,
    so that coming back zoomed still has somewhere to unzoom to.
    """
    desktop = window.parent
    rectangle = (window.x, window.y, window.width, window.height)
    if window.zoomed:
        rectangle = window._restore or (0, 0, 0, 0)
    x, y, width, height = rectangle
    return {
        "zoomed": bool(window.zoomed),
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "desk_width": desktop.width if desktop is not None else 0,
        "desk_height": desktop.height if desktop is not None else 0,
    }


def scaled(record: Any, width: int, height: int) -> tuple[int, int, int, int] | None:
    """``AdjustToDesktopSize``: the recorded rectangle on a desktop *width* x *height*.

    Scaled by how the desktop has changed size since, or ``None`` where what
    is left would be off the desktop or smaller than a window may be -- for
    which DN took the whole desktop.
    """
    if record.width <= 0 or record.height <= 0:
        return None
    ax, ay = record.x, record.y
    bx, by = record.x + record.width, record.y + record.height
    old_w = record.desk_width or width
    old_h = record.desk_height or height
    if (old_w, old_h) != (width, height):
        kx, ky = width / old_w, height / old_h
        ax, bx = int(ax * kx), int(bx * kx)
        ay, by = int(ay * ky), int(by * ky)
    if (
        ax >= width or bx < 0 or ay >= height or by < 0
        or bx - ax < MIN_WIDTH or by - ay < MIN_HEIGHT
    ):
        return None
    return ax, ay, bx - ax, by - ay


def place_window(window: Any, record: Any) -> None:
    """Put *window*, already on its desktop, where *record* says it was."""
    desktop = window.parent
    if desktop is None:
        return
    rectangle = scaled(record, desktop.width, desktop.height)
    if record.zoomed:
        window._restore = rectangle
        if not window.zoomed:
            window.toggle_zoom()
        return
    if rectangle is None:
        if not window.zoomed:
            window.toggle_zoom()
        return
    window.locate(*rectangle)
    window.layout(desktop.width, desktop.height)


async def open_viewer(desktop: Any, path: Path | str, mode: str | None = None) -> Any:
    """A viewer on *path*, opened on *desktop* and put back as it was left.

    *mode* is File > View > As Text / As Hex's: asked for, it wins over the
    record's.  The file is opened on a thread -- a file on a dead mount, or
    one of ``/proc``'s read whole, does not stop the screen -- under *Reading
    file* if it takes a while.  None if that was cancelled.  Raises
    ``OSError`` before anything is opened.
    """
    from navigator.progress import SLOW_PROGRESS_DELAY, run_with_progress
    from navigator.viewer import ViewSource
    from navigator.widgets.editor.loading import FileJob, progress_box, refresh_box
    from navigator.widgets.viewer.file_window import FileWindow

    job = FileJob()
    source = await run_with_progress(
        desktop.application, lambda: ViewSource(path), job,
        lambda: progress_box(job, tr("Reading file")), refresh_box(job),
        delay=SLOW_PROGRESS_DELAY,
    )
    if job.stopped:
        source.close()
        return None
    window = FileWindow(path, mode=mode, source=source)
    desktop.open(window)
    window.recall_history(keep_mode=mode is not None)
    return window


#: The files an editor is being opened on, per desktop: pressed twice while a
#: large file is still being read, F4 opens it once.
_opening: set[tuple[int, str]] = set()


async def open_editor(desktop: Any, path: Path | str, *, new: bool = False) -> Any:
    """An editor on *path*, opened on *desktop* and put back as it was left.

    The file is read on a thread, under *Reading file* if it takes a while
    (``navigator.widgets.editor.loading``).  Returns the window, or None if
    the read was cancelled, the file would not fit in memory -- said already
    -- or the same file is already being opened.  Raises ``OSError`` before
    anything is opened.
    """
    from navigator.widgets.editor.edit_window import EditWindow
    from navigator.widgets.editor.loading import load_document

    key = (id(desktop), str(path))
    if key in _opening:
        return None
    _opening.add(key)
    try:
        document = await load_document(desktop.application, path, new=new)
    finally:
        _opening.discard(key)
    if document is None:
        return None
    # Opened and focused in the same step that follows the read: nothing the
    # user did meanwhile is undone by a window jumping up later.
    window = EditWindow(path, document=document, new=new)
    desktop.open(window)
    window.recall_history()
    return window


def remember_windows(desktop: Any) -> None:
    """Record every viewer and editor still open: Alt+X's ``Valid(cmQuit)``."""
    for window in desktop.windows():
        remember = getattr(window, "remember_history", None)
        if remember is not None:
            remember()
