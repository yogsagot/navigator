"""The screen a program Navigator started paints on.

Named for what it shows rather than for what drives it: the emulation and the
pty are :mod:`navkit.console` and :mod:`navkit.process`, and what lives here is
the widget that puts one on the desktop and gives it the keyboard.
"""

from __future__ import annotations

from pathlib import Path

from navkit.console import ConsoleScreen, seed_from_host
from navkit.events import KeyEvent
from navkit.reactive import effect, reactive
from navkit.screen import Cell

from navigator.lib.system.subshell import Subshell
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
