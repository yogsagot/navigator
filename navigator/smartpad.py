"""SmartPad: DOS Navigator's notepad (``OpenSmartpad`` in ``MICROED.PAS``).

One editor window on one file, :func:`navigator.settings.smartpad_path`,
opened by Alt+Q from anywhere and never more than once: a second Alt+Q
brings the one open to the front.  Every opening stamps the text's end with
the date and time (``InsertInfo``) and leaves the cursor on a fresh line
under it, so the pad reads as a log of what was noted when.  The window
fills the desktop less two cells all round, is titled *SmartPad(TM) - *
and the file, keeps no edit history, and saves itself on closing without a
question -- the window, :class:`EditWindow`, knows itself by ``smartpad``.
"""

from __future__ import annotations

import time
from typing import Any

from navigator.fileattr import DATE_FORMAT, TIME_FORMAT
from navigator.settings import smartpad_path


def stamp_text(when: time.struct_time | None = None) -> str:
    """``InsertInfo``'s line: ``──────< date time >`` and a run of rule after it."""
    when = when or time.localtime()
    date, clock = time.strftime(DATE_FORMAT, when), time.strftime(TIME_FORMAT, when)
    return f"──────< {date} {clock} >" + "─" * 36


def open_smartpad(desktop: Any) -> Any:
    """SmartPad on *desktop*: the one open brought up, or a new one; stamped either way."""
    from navigator.widgets.editor.edit_window import EditWindow

    for window in desktop.windows():
        if isinstance(window, EditWindow) and window.smartpad:
            desktop.activate(window)
            window.editor.stamp(stamp_text())
            return window
    path = smartpad_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    window = EditWindow(path, new=True, smartpad=True)
    desktop.open(window)
    # ``Desktop^.GetExtent(R); R.Grow(-2, -2)``.
    window.locate(2, 2, max(1, desktop.width - 4), max(1, desktop.height - 4))
    window.layout(desktop.width, desktop.height)
    window.editor.stamp(stamp_text())
    return window
