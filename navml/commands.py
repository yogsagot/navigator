"""The commands the widget library runs: Turbo Vision's window and dialog set.

Named after ``cmClose``, ``cmZoom``, ``cmResize``, ``cmNext``, ``cmPrev``,
``cmCancel`` and ``cmDefault``, with ``Window`` spelled out where the bare
word would be a handler name somebody else already means -- ``Resize`` would
be delivered to ``on_resize``, which is :class:`~navkit.events.ResizeEvent`'s.
Tab and Shift+Tab are commands here too, where Turbo Vision had ``TGroup``
select the next view directly: as commands they are rebindable, and a dialog
that wants Tab for itself can take the key without overriding a method.

A module rather than a component directory, because a command paints nothing
and is no component; it sits beside :mod:`navml.component` as the library's
other piece of support.  The application's own commands -- Copy, Mkdir, Quit
-- are the application's, and live with it.
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
    """Move and size the active window from the keyboard."""

    title = "Size/Move"


class NextWindow(Command):
    """Bring the next window forward."""

    title = "Next"


class PreviousWindow(Command):
    """Bring the previous window forward."""

    title = "Previous"


class Cancel(Command):
    """Dismiss a dialog without an answer."""

    title = "Cancel"


class Default(Command):
    """Press a dialog's default button, wherever the focus is."""

    title = "OK"


class SelectNext(Command):
    """Move the keyboard to the next control."""


class SelectPrevious(Command):
    """Move the keyboard to the previous control."""


__all__ = [
    "Cancel",
    "CloseWindow",
    "Default",
    "NextWindow",
    "PreviousWindow",
    "SelectNext",
    "SelectPrevious",
    "SizeMoveWindow",
    "ZoomWindow",
]
