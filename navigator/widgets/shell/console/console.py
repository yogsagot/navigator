"""The screen a program Navigator started paints on.

Named for what it shows rather than for what drives it: the emulation and the
pty are :mod:`navkit.console` and :mod:`navkit.process`, and what lives here is
the widget that puts one on the desktop and gives it the keyboard.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from navkit.console import ConsoleScreen, seed_from_host
from navkit.events import KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect, reactive
from navkit.screen import Cell

from navigator.lib.system.subshell import RootSubshell, Subshell
from navigator.settings import SETTINGS
from navigator.widgets.shell.console.screen_view import WHEEL_LINES, ScreenView

#: Wider than any row a prompt is typed on; a longer one wraps, and the row it
#: wraps onto is the one the typing happens on.
PROMPT_COLUMNS = 256

__all__ = ["Console", "PROMPT_COLUMNS", "WHEEL_LINES", "prompt_cells"]


def prompt_cells(data: bytes) -> tuple[Cell, ...]:
    """The row a prompt leaves the cursor on, as cells: what the user types after.

    Decoded by the same emulator the console is, on a screen one row tall, so
    every line break scrolls the one before it away and a multi-line prompt
    -- starship's, say -- leaves its last line, with whatever colour the
    lines above it set still in force.  Cut at the cursor rather than at the
    last character, which keeps the space most prompts end in.
    """
    screen = ConsoleScreen(PROMPT_COLUMNS, 1, history=1)
    screen.feed(data)
    surface = screen.written  # the command line lays its own line out
    return tuple(surface.get(x, 0) for x in range(screen.screen.cursor.x))


class Console(ScreenView):
    """The screen a program Navigator started paints on.

    This is what Ctrl+O reveals.  DOS Navigator could show the last command's
    output behind its panels because in DOS there was one screen and the
    output was still in it; a terminal will not give its cells back, so the
    only way to have them is to have received them.  The command line's
    shell (:class:`~navigator.lib.system.subshell.Subshell`) runs on a pty this widget
    owns, its output goes through
    :class:`~navkit.console.ConsoleScreen`, and what arrives is a grid of
    cells like any other -- which is why the menu bar and the key bar can
    stay painted over it, and why it can be scrolled back through.
    """

    #: The shell's last prompt, as :func:`prompt_cells` decodes it, and the
    #: directory it was printed in.  Empty and None until the shell prints one.
    prompt: tuple = reactive(())
    prompt_cwd: Path | None = reactive(None)
    #: Bumped at every prompt, even one identical to the last: a ``cd`` that
    #: failed prints the same prompt in the same place, and is still news.
    prompts: int = reactive(0)

    #: A command the command line sent is running: ``Subshell.busy``, which
    #: is a plain field, mirrored where the reactive layer can see it.
    running: bool = reactive(False)

    #: The shell has the real terminal (``Shell.relay_terminal``): its pty is
    #: then the whole terminal's size, not this widget's.
    relayed: bool = reactive(False)

    def __init__(self, cwd: Path | None = None, **kwargs):
        """*cwd* is optional because a widget markup constructs must be.

        The same rule as :class:`~navigator.widgets.manager.panel.Panel`'s ``path``:
        a child block compiles to ``Console(parent=self)`` and nothing else,
        so a required argument would keep this widget out of a document.
        """
        super().__init__(**kwargs)
        self.cwd = cwd
        #: The shell the command line runs its commands in.  Only the output
        #: and prompt callbacks are set here; what a finished command means is
        #: ``Shell``'s.
        self.subshell = Subshell(
            self.screen, on_output=self._changed, on_prompt=self._prompted,
            on_busy=self._busy_changed,
        )
        self.subshell.feeds_zoxide = lambda: SETTINGS.interface.feed_zoxide
        #: The user's own shell: :attr:`subshell` too, but while the console
        #: is root (:meth:`go_root`), when it waits parked, as it was left.
        self.user_subshell = self.subshell
        #: Called when a root shell ends by itself (``exit`` typed at it),
        #: once the user's shell is back.
        self.on_root_ended = None
        self.seeded = False
        # The pty is told how big it is whenever this widget is, which is the
        # whole of the resize handling: the kernel raises SIGWINCH on the
        # child itself once the size is set.
        effect(self, Console._follow_size)

    def _follow_size(self) -> None:
        columns, lines = self._size()
        self.screen.resize(columns, lines)
        self.subshell.set_size(columns, lines)

    def _size(self) -> tuple[int, int]:
        """What the pty is: this widget, or the whole screen while relayed."""
        source = self.parent if self.relayed and self.parent is not None else self
        return max(1, source.width), max(1, source.height)

    # -- the child -----------------------------------------------------------

    @property
    def process(self):
        """The shell's pty process, or None while no shell is running."""
        return self.subshell.process

    @property
    def busy(self) -> bool:
        """A command is running, so what is typed is the program's."""
        return self.subshell.busy

    def start(self) -> None:
        """Start the shell behind the command line, if it is not running."""
        if self.subshell.is_running:
            return
        if not self.seeded:
            # Whatever was on the real screen before Navigator ran, if this
            # host happens to keep it.  Once only, and before the shell's
            # rc files print anything on top of it.
            self.seeded = True
            seed_from_host(self.screen)
        self.subshell.start(self.cwd, *self._size())

    def run(self, command: str, cwd: Path | None = None) -> None:
        """Run *command* in the shell, in *cwd*."""
        if not self.seeded:
            self.seeded = True
            seed_from_host(self.screen)
        self.subshell.run(command, cwd)

    def stop(self) -> None:
        self.subshell.stop()
        if self.subshell is not self.user_subshell:
            self.user_subshell.stop()

    # -- as root -----------------------------------------------------------------

    @property
    def is_root(self) -> bool:
        """The console's shell is root's (:meth:`go_root`)."""
        return isinstance(self.subshell, RootSubshell)

    async def go_root(self, cwd: Path | None) -> None:
        """Utilities > *Elevate root access*: the console's shell root's, in
        *cwd*, the user's own parked until :meth:`go_user`.  Raises
        ``OSError`` when the helper cannot start one."""
        if self.is_root:
            return
        user = self.user_subshell
        root = RootSubshell(self.screen, on_output=self._changed, on_prompt=self._prompted,
                            on_busy=self._busy_changed)
        root.feeds_zoxide = user.feeds_zoxide
        root.on_finished = user.on_finished
        columns, lines = self._size()
        try:
            pid, fd, name = await asyncio.to_thread(root.open, cwd, columns, lines)
        finally:
            self.screen.respond = user.write
        from navigator.lib.system.elevate import ELEVATION

        if self.is_root or not ELEVATION.running:
            # Another elevation got here first, or root access closed meanwhile.
            import os

            os.close(fd)
            return

        def ended(status: int) -> None:
            if self.subshell is root:
                self.go_user()
                if self.on_root_ended is not None:
                    self.on_root_ended()

        root.on_exit = ended
        root.attach(pid, fd, name, columns, lines)
        user.park()
        self._say(tr("Root shell: commands run as root until root access is closed"))
        self.screen.respond = root.write
        self.subshell = root

    def go_user(self) -> None:
        """The user's own shell back, as it was parked; the root one ended."""
        root = self.subshell
        if root is self.user_subshell:
            return
        self.subshell = self.user_subshell
        self.screen.respond = self.user_subshell.write
        root.on_exit = None
        root.stop()
        self.running = self.user_subshell.busy
        self._say(tr("Back to your own shell"))
        dropped = self.user_subshell.parked_dropped
        if dropped:
            from navigator.lib.system.sysinfo import size_text

            self._say(tr("{size} of what your shell printed meanwhile was not kept: its oldest output").format(
                size=size_text(dropped)))
        self.user_subshell.unpark()
        if self.user_subshell.is_running:
            self._prompted(self.user_subshell.held_prompt, self.user_subshell.cwd)

    def _say(self, text: str) -> None:
        """A line of Navigator's own in the console, between two shells' output."""
        start = "\r\n" if self.screen.cursor[0] else ""
        self.screen.feed(f"{start}\x1b[7m {text} \x1b[0m\r\n".encode())
        self._changed()

    def _on_output(self, data: bytes) -> None:
        """Paint *data* straight onto the screen, past the shell's filter."""
        self.screen.feed(data)
        self._changed()

    def _busy_changed(self, busy: bool) -> None:
        self.running = busy

    def _prompted(self, data: bytes, cwd: Path | None) -> None:
        self.prompt = prompt_cells(data)
        self.prompt_cwd = cwd
        self.prompts += 1

    # -- what the view asks ----------------------------------------------------

    @property
    def alive(self) -> bool:
        return self.subshell.is_running

    def write_child(self, data: bytes) -> None:
        self.subshell.write(data)

    #: The keyboard stays with the command line, as it does for a left click.
    context_focus = False

    def takes_raw_keys(self) -> bool:
        """While a program runs its keys are its own: no chord (Ctrl+J, Ctrl+K)
        is started with them."""
        return self.busy

    async def on_key(self, event: KeyEvent) -> bool:
        """Everything typed while the console has the keyboard.

        The scrollback keys are kept back: Shift+PgUp/PgDn half a page and
        Shift+Up/Down a line (both what xfce4-terminal binds for itself, so
        they reach here only where the terminal leaves them), and while the
        shell is idle the bare PgUp/PgDn a page and Home/End all the way --
        Home and End only with the command line empty, since its table takes
        them first otherwise.  A full-screen program on the alternate screen
        has no scrollback and gets Shift+Up/Down, which editors select with.

        **While a command runs the rest is the program's**, swallowed whether
        or not there is a child to send it to, so a keystroke aimed at ``vim``
        never lands on the panels underneath.  While the shell is idle the
        console is only showing output, and a key goes on up to the shell's
        command line -- which is the prompt the user is looking at.

        The way out is not here.  Ctrl+O and quit are the application's, and
        the application sees every key before the tree does.
        """
        return await super().on_key(event)

    # -- painting ------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        """Where the child program put its cursor, for navkit to place ours.

        This used to be a reversed cell painted here by hand, because the
        terminal's own cursor was hidden for the whole run.  The real one
        blinks the way the user configured it, is the shape they chose, and
        is where a screen reader and the terminal's own copy-mode agree it is.

        None while the shell is idle: the prompt is the command line's then,
        and the caret belongs there.  None while the view is scrolled back: the rows on screen are history
        then, and the live cursor's position means nothing among them.  The
        reversed cell got that wrong, highlighting whatever happened to sit at
        those coordinates in the scrollback.
        """
        return super().cursor_position()
