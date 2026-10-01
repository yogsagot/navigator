"""The library's top-level commands: Turbo Vision's window set, which ``Desktop`` runs.

Named after ``cmClose``, ``cmZoom``, ``cmResize``, ``cmNext`` and ``cmPrev``,
with ``Window`` spelled out where the bare word would be a handler name
somebody else already means -- ``Resize`` would be delivered to ``on_resize``,
which is :class:`~navkit.events.ResizeEvent`'s.

A module rather than a component directory, because a command paints nothing
and is no component; it sits beside :mod:`navml.component` as the library's
other piece of support.  It holds the commands of the components that sit at
the top of ``navml/widgets/`` -- ``Window`` and ``Desktop`` -- and every other
command lives with the group whose widget handles it, in that group's
``commands.py``: ``navml.widgets.dialog.commands``,
``navml.widgets.menu.commands``.  Per group rather than per component,
because a component's ``__init__`` imports its widget and a group's imports
nothing.  The application's own commands -- Copy, Mkdir, Quit -- are the
application's, and live with it.
"""

from __future__ import annotations

from navkit.commands import Command


class CloseWindow(Command):
    """Close the active window.  Vetoed by a window that is not closable."""

    title = "Close"


class ZoomWindow(Command):
    """Zoom the active window, or restore it."""

    title = "Zoom"


class SizeMoveWindow(Command):
    """Move and size the active window from the keyboard.

    Untitled, like the two below: Turbo Vision's status lines bind
    ``kbCtrlF5``, ``kbF6`` and ``kbShiftF6`` with an empty caption, and DOS
    Navigator's ``kbCtrlF5``, ``kbF9`` and ``kbShiftF9`` likewise, so a key
    bar never shows them.
    """


class NextWindow(Command):
    """Bring the next window forward."""


class PreviousWindow(Command):
    """Bring the previous window forward."""


class WindowManager(Command):
    """List the windows on the desktop, to switch to one or close one.

    DOS Navigator's ``cmWindowManager``, Window > List (Alt-0).
    """

    title = "List"


class TileWindows(Command):
    """Lay the tileable windows side by side over the whole desktop.

    DOS Navigator's ``cmTile``, Window > Tile.  Like the two below it has no
    key, because the original bound none.
    """

    title = "Tile"


class CascadeWindows(Command):
    """Stack the tileable windows, each one cell down and right of the one under it.

    DOS Navigator's ``cmCascade``, Window > Cascade.
    """

    title = "Cascade"


class CloseAllWindows(Command):
    """Close every window that can be closed.

    DOS Navigator's ``cmClearDesktop``, Window > Close all: a ``cmClose``
    broadcast, so a window without a close icon stays.
    """

    title = "Close all"


__all__ = [
    "CascadeWindows",
    "CloseAllWindows",
    "CloseWindow",
    "NextWindow",
    "PreviousWindow",
    "SizeMoveWindow",
    "TileWindows",
    "WindowManager",
    "ZoomWindow",
]
