"""One command on a pty of its own: what a terminal window shows.

The console's screen is the command line's shell's, and one command at a time
runs there.  This view is the same screen (:class:`~navigator.widgets.shell.console.screen_view.ScreenView`)
over a child of its own -- ``sh -c command`` -- so a command can run in a
window beside the panels, as many at once as there are windows.  A departure:
DOS Navigator ran one program and was not running itself while it did.
"""

from __future__ import annotations

import os
from pathlib import Path

from navkit.events import KeyEvent
from navkit.process import PtyProcess
from navkit.reactive import effect, reactive
from navml.commands import SelectWindow, WindowManager
from navml.widgets.desktop import Desktop

from navigator.lib.system.subshell import command_shell
from navigator.widgets.shell.console.screen_view import ScreenView

#: The desktop's keys a running program does not get: the ones that go to
#: another window.  Read from ``Desktop.keys`` rather than copied, so a
#: rebinding is followed.
_WINDOW_COMMANDS = (SelectWindow, WindowManager)


def window_keys() -> tuple[str, ...]:
    """The keys that bring another window forward, as ``Desktop.keys`` binds them."""
    return tuple(
        key for key, command in Desktop.keys.items()
        if isinstance(command, _WINDOW_COMMANDS)
        or (isinstance(command, type) and issubclass(command, _WINDOW_COMMANDS))
    )


class TerminalView(ScreenView):
    """A command's own screen, its child started on :meth:`mounted`.

    :attr:`command`, :attr:`cwd` and :attr:`shell` are set before it is
    mounted -- markup constructs a view with no arguments.
    """

    #: The child's exit status, as ``waitpid`` reports it, once it has ended;
    #: None while it runs and before it starts.
    status: int | None = reactive(None)

    #: Holding all input (a modal window): the window keys have nowhere to
    #: go, so the program gets them too.
    holds_all_keys: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.command = ""
        self.cwd: Path | None = None
        #: The shell the command is run by; the command line's own when None.
        self.shell: str | None = None
        self.process: PtyProcess | None = None

    # -- the child -----------------------------------------------------------

    @property
    def busy(self) -> bool:
        return self.process is not None and self.process.is_running

    @property
    def alive(self) -> bool:
        return self.busy

    def write_child(self, data: bytes) -> None:
        if self.process is not None:
            self.process.write(data)

    def mounted(self) -> None:
        super().mounted()
        effect(self, TerminalView._follow_size)
        if self.process is None and self.command:
            self.start()

    def unmounting(self) -> None:
        """Taken off the screen -- its window closed -- the command goes with it."""
        self.stop()
        super().unmounting()

    def start(self) -> None:
        """Start the command, the size the view is now."""
        columns, lines = max(1, self.width), max(1, self.height)
        self.screen.resize(columns, lines)
        self.process = PtyProcess(
            [command_shell(self.shell), "-c", self.command],
            cwd=self.cwd, env=os.environ, columns=columns, lines=lines,
            on_output=self._on_output, on_exit=self._on_exit,
        )
        self.screen.respond = self.process.write
        try:
            self.process.start()
        except OSError:
            self.process = None
            self.status = 127 << 8
            return
        self._changed()

    def stop(self) -> None:
        """Hang the command up, as closing a terminal does -- never waiting on it."""
        process = self.process
        if process is not None and process.is_running:
            process.hang_up()

    def _follow_size(self) -> None:
        columns, lines = max(1, self.width), max(1, self.height)
        self.screen.resize(columns, lines)
        if self.process is not None:
            self.process.set_size(columns, lines)
        self._changed()

    def _on_output(self, data: bytes) -> None:
        self.screen.feed(data)
        self._changed()

    def _on_exit(self, status: int) -> None:
        self.screen.respond = None
        self.status = status
        self._changed()
        window = self.parent
        if window is not None and hasattr(window, "command_ended"):
            window.command_ended(status)

    # -- keys ------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        """The program's, but for the window keys; once it has ended, Esc and
        Enter close the window.

        While it runs every key goes to it -- F10, Ctrl+O and Alt+X included,
        as on the console -- except the ones that bring another window
        forward (Alt+Shift+F1 .. F9, Win+digit, Alt+0), which go on up to the
        desktop.  The scrollback keys are kept, as the console keeps them.
        """
        if self.busy and not self.holds_all_keys and event.matches(*window_keys()):
            return False
        if not self.busy and self.selection is None and (event.matches("escape", "enter")):
            window = self.parent
            if window is not None and hasattr(window, "request_close"):
                window.request_close()
                return True
        return await super().on_key(event)
