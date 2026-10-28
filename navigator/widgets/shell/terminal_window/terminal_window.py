"""The handlers behind ``terminal_window.nml``, and :func:`open_terminal`, which opens one."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from navkit.i18n import tr
from navkit.reactive import bind
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.window import Window

from navigator.settings import SETTINGS

#: The screen a window not zoomed gives its command: a terminal's classic size.
COLUMNS, LINES = 80, 24

#: How far each window not zoomed is set from the last, so they do not hide
#: one another exactly; it comes round again after this many.
_STAGGER, _STAGGERS = 2, 5


def describe(status: int | None) -> str:
    """How a command ended, for the title: None while it runs."""
    if status is None:
        return ""
    if os.WIFSIGNALED(status):
        return tr("killed by signal {number}").format(number=os.WTERMSIG(status))
    return tr("exit status {status}").format(status=os.waitstatus_to_exitcode(status))


class TerminalWindow(Window):
    """A command in a window of its own."""

    def __init__(self, command: str = "", cwd: Path | None = None, *, shell: str | None = None,
                 title: str | None = None, on_close: Callable[[], Any] | None = None,
                 closes: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: What the title calls the command: *command* itself unless given.
        self.command = title or command
        self.view.command = command
        self.view.cwd = cwd
        self.view.shell = shell
        #: Called once the window has gone -- the command line puts back the
        #: files it fetched from another drive for the command (``UseFile``).
        self.on_close = on_close
        #: Gone as soon as the command ends with status 0, rather than kept
        #: with its output: Alt+F4's console editors, whose screen is done with.
        self.closes = closes
        self.title = bind(lambda w: w.caption())

    def caption(self) -> str:
        """The command, and once it has ended, how."""
        ended = describe(self.view.status)
        if not ended:
            return self.command
        return tr("{command} - {ended}").format(command=self.command, ended=ended)

    def command_ended(self, status: int) -> None:
        """The command has ended (``TerminalView``): the window closed if it
        :attr:`closes` and the command ended well; one that failed stays, to
        say how."""
        if self.closes and status == 0:
            self.close()

    def take_keyboard(self) -> None:
        self.view.focus()

    def list_name(self) -> str:
        return self.caption()

    def short_name(self) -> str:
        return self.command.split(None, 1)[0] if self.command.strip() else self.command

    def key_hints(self) -> list[tuple[str, str]]:
        if not self.view.busy and not self.moving:
            return [("Esc", tr("Close"))]
        return super().key_hints()

    def must_ask(self) -> bool:
        """The command is still running, and Confirmations' *Close command
        window* is ticked -- so the close icon, Ctrl+F4, Close all and Alt+X
        all ask before hanging it up."""
        return self.view.busy and SETTINGS.confirmations.close_command_window

    async def ask_to_close(self) -> bool:
        """Yes closes the window and stops the command; No leaves both running."""
        answer = await Dialog(
            title=tr("Close command window"),
            prompt=tr("{command} is still running. Stop it and close the window?").format(command=self.command),
            buttons="yes-no",
        ).execute(self.application)
        return answer is True

    def close(self) -> None:
        """Take the window off, which hangs the command up (``TerminalView.unmounting``)."""
        super().close()
        on_close, self.on_close = self.on_close, None
        if on_close is not None:
            on_close()


def open_terminal(desktop: Any, command: str, cwd: Path | None = None, *, zoomed: bool = True,
                  modal: bool = False, shell: str | None = None, title: str | None = None,
                  closes: bool = False, on_close: Callable[[], Any] | None = None) -> TerminalWindow:
    """Run *command* in a new window on *desktop*: zoomed or :data:`COLUMNS` x
    :data:`LINES` (cut to the desktop) in the middle, one among the windows or
    *modal*, holding every key until it is closed.  *closes* takes it off as
    soon as the command ends with status 0.

    A window opened zoomed still has that rectangle to go back to.
    """
    window = TerminalWindow(command, cwd, shell=shell, title=title, on_close=on_close, closes=closes)
    width, height = min(COLUMNS + 2, desktop.width), min(LINES + 2, desktop.height)
    others = sum(1 for other in desktop.windows() if isinstance(other, TerminalWindow))
    shift = _STAGGER * (others % _STAGGERS)
    x = min(max(0, (desktop.width - width) // 2 + shift), max(0, desktop.width - width))
    y = min(max(0, (desktop.height - height) // 2 + shift // 2), max(0, desktop.height - height))
    window.x, window.y, window.width, window.height = x, y, width, height
    if zoomed:
        window._restore = (x, y, width, height)
        window.zoomed = True
    if modal:
        window.modal = True
        window.view.holds_all_keys = True
    desktop.open(window)
    window.take_keyboard()
    return window
