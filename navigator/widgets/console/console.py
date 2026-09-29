"""The screen a program Navigator started paints on.

Named for what it shows rather than for what drives it: the emulation and the
pty are :mod:`navkit.console` and :mod:`navkit.process`, and what lives here is
the widget that puts one on the desktop and gives it the keyboard.
"""

from __future__ import annotations

from pathlib import Path

from navkit.console import ConsoleScreen, seed_from_host
from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import effect, reactive
from navkit.screen import Cell, Surface
from navkit.terminal import encode_key, encode_mouse
from navkit.widget import Widget

from navigator.subshell import Subshell

#: Wider than any row a prompt is typed on; a longer one wraps, and the row it
#: wraps onto is the one the typing happens on.
PROMPT_COLUMNS = 256


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
    surface = screen.surface
    return tuple(surface.get(x, 0) for x in range(screen.screen.cursor.x))


class Console(Widget):
    """The screen a program Navigator started paints on.

    This is what Ctrl+O reveals.  DOS Navigator could show the last command's
    output behind its panels because in DOS there was one screen and the
    output was still in it; a terminal will not give its cells back, so the
    only way to have them is to have received them.  The command line's
    shell (:class:`~navigator.subshell.Subshell`) runs on a pty this widget
    owns, its output goes through
    :class:`~navkit.console.ConsoleScreen`, and what arrives is a grid of
    cells like any other -- which is why the menu bar and the key bar can
    stay painted over it, and why it can be scrolled back through.
    """

    #: Bumped whenever the child writes, so the reactive layer knows the cells
    #: moved.  The screen behind it is not observable -- it is a great deal of
    #: mutable state that changes together -- so one counter stands for it.
    revision: int = reactive(0)

    #: The shell's last prompt, as :func:`prompt_cells` decodes it, and the
    #: directory it was printed in.  Empty and None until the shell prints one.
    prompt: tuple = reactive(())
    prompt_cwd: Path | None = reactive(None)

    def __init__(self, cwd: Path | None = None, **kwargs):
        """*cwd* is optional because a widget markup constructs must be.

        The same rule as :class:`~navigator.widgets.panel.Panel`'s ``path``:
        a child block compiles to ``Console(parent=self)`` and nothing else,
        so a required argument would keep this widget out of a document.
        """
        super().__init__(**kwargs)
        self.cwd = cwd
        # It has the screen, so it should have the keyboard -- which is what
        # `Navigator.on_key' has always said in words.  Saying it to navkit
        # as well is what gets the child's own cursor drawn: the application
        # asks whichever widget the keys are going to where its caret belongs.
        self.can_focus = True
        self.screen = ConsoleScreen(80, 24)
        #: The shell the command line runs its commands in.  Only the output
        #: and prompt callbacks are set here; what a finished command means is
        #: ``Shell``'s.
        self.subshell = Subshell(
            self.screen, on_output=self._changed, on_prompt=self._prompted
        )
        self.seeded = False
        # The pty is told how big it is whenever this widget is, which is the
        # whole of the resize handling: the kernel raises SIGWINCH on the
        # child itself once the size is set.
        effect(self, Console._follow_size)

    def _follow_size(self) -> None:
        columns, lines = max(1, self.width), max(1, self.height)
        self.screen.resize(columns, lines)
        self.subshell.set_size(columns, lines)

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
        self.subshell.start(self.cwd, max(1, self.width), max(1, self.height))

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
        self.revision += 1

    def _changed(self) -> None:
        self.revision += 1

    def _prompted(self, data: bytes, cwd: Path | None) -> None:
        self.prompt = prompt_cells(data)
        self.prompt_cwd = cwd

    # -- input ---------------------------------------------------------------

    def send(self, event: KeyEvent) -> bool:
        """Type *event* at the child; ``False`` if there is nobody to type at."""
        if not self.subshell.is_running:
            return False
        data = encode_key(event, application_cursor=self.screen.application_cursor)
        if not data:
            return False
        self.subshell.write(data)
        return True

    @property
    def tracks_mouse(self) -> bool:
        """A running program asked for the mouse, so the console passes it on."""
        return self.busy and bool(self.screen.mouse_tracking)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """Clicks, drags and the wheel, for a program that turned the mouse on.

        ``mc`` and ``htop`` both do, and a console that kept the mouse for
        itself left them with a pointer that did nothing.  The position is
        already the console's own -- ``dispatch_mouse`` shifted it on the way
        down -- which is the program's screen, cell for cell.
        """
        if not self.tracks_mouse or not self.subshell.is_running:
            return False
        data = encode_mouse(
            event, tracking=self.screen.mouse_tracking, sgr=self.screen.mouse_sgr
        )
        if data:
            self.subshell.write(data)
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        """Everything typed while the console has the keyboard.

        The two scrollback bindings are kept back.  **While a command runs the
        rest is the program's**, swallowed whether or not there is a child to
        send it to, so a keystroke aimed at ``vim`` never lands on the panels
        underneath.  While the shell is idle the console is only showing
        output, and a key goes on up to the shell's command line -- which is
        the prompt the user is looking at.

        The way out is not here.  Ctrl+O and quit are the application's, and
        the application sees every key before the tree does.
        """
        if event.matches("shift+pageup"):
            self.scroll_back()
        elif event.matches("shift+pagedown"):
            self.scroll_forward()
        elif self.busy:
            self.send(event)
        else:
            return False
        return True

    def scroll_back(self) -> None:
        self.screen.prev_page()
        self.revision += 1

    def scroll_forward(self) -> None:
        self.screen.next_page()
        self.revision += 1

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
        if not self.busy or self.screen.scrolled_back:
            return None
        column, row, hidden = self.screen.cursor
        return None if hidden else (column, row)

    def render(self, surface: Surface) -> None:
        _ = self.revision  # read for the dependency: this is what output moves
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        self.screen.blit_into(surface)
