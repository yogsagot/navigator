"""The screen a program Navigator started paints on.

Named for what it shows rather than for what drives it: the emulation and the
pty are :mod:`navkit.console` and :mod:`navkit.process`, and what lives here is
the widget that puts one on the desktop and gives it the keyboard.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.console import ConsoleScreen, seed_from_host
from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent
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
    #: Bumped at every prompt, even one identical to the last: a ``cd`` that
    #: failed prints the same prompt in the same place, and is still news.
    prompts: int = reactive(0)

    #: What the mouse has selected: the cell it started on and the cell it
    #: is on now, both ``(x, y)`` in the view, or None.  Cleared whenever the
    #: view moves under it -- new output, a scroll -- since the cells it
    #: named are then somewhere else.
    selection: Any = reactive(None)

    def __init__(self, cwd: Path | None = None, **kwargs):
        """*cwd* is optional because a widget markup constructs must be.

        The same rule as :class:`~navigator.widgets.manager.panel.Panel`'s ``path``:
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
        #: Where a left-button drag started, while one is selecting.
        self._drag_from: tuple[int, int] | None = None
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
        self._changed()

    def _changed(self) -> None:
        self.revision += 1
        self.clear_selection()

    def _prompted(self, data: bytes, cwd: Path | None) -> None:
        self.prompt = prompt_cells(data)
        self.prompt_cwd = cwd
        self.prompts += 1

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

        Otherwise the mouse selects, as a terminal's does -- the terminal's
        own selection is out of reach while Navigator tracks the mouse.
        """
        if not self.tracks_mouse or not self.subshell.is_running:
            return self._select(event)
        data = encode_mouse(
            event, tracking=self.screen.mouse_tracking, sgr=self.screen.mouse_sgr
        )
        if data:
            self.subshell.write(data)
        return True

    # -- selection -------------------------------------------------------------

    def _cell(self, event: MouseClickEvent) -> tuple[int, int]:
        """The cell under *event*, held inside the console while a drag outruns it."""
        return (
            min(max(event.x, 0), max(0, self.width - 1)),
            min(max(event.y, 0), max(0, self.height - 1)),
        )

    def _select(self, event: MouseClickEvent) -> bool:
        """A left drag selects; a middle click pastes the primary selection."""
        app = self.application
        if event.button == "middle" and event.action == "press":
            if app is not None:
                app.request_clipboard(primary=True)
            return True
        if event.button != "left":
            return False
        if event.action == "press":
            self.clear_selection()
            self._drag_from = self._cell(event)
            if app is not None:
                app.capture_mouse(self)
        elif event.action == "move" and self._drag_from is not None:
            self.selection = (self._drag_from, self._cell(event))
        elif event.action == "release" and self._drag_from is not None:
            self._drag_from = None
            self._copy_selection(primary=True)
        else:
            return False
        return True

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        """The word under the pointer: the run of non-blank cells around it."""
        if event.button != "left" or (self.tracks_mouse and self.subshell.is_running):
            return False
        x, y = self._cell(event)
        surface = self.screen.surface
        if not surface.get(x, y)[0].strip():
            return True
        start = x
        while start and surface.get(start - 1, y)[0].strip():
            start -= 1
        stop = x
        while stop + 1 < self.screen.columns and surface.get(stop + 1, y)[0] != " ":
            stop += 1
        self._drag_from = None
        self.selection = ((start, y), (stop, y))
        self._copy_selection(primary=True)
        return True

    @property
    def selected_text(self) -> str:
        if self.selection is None:
            return ""
        start, end = self.selection
        return self.screen.text(start, end)

    def clear_selection(self) -> None:
        if self.selection is not None:
            self.selection = None

    def _copy_selection(self, *, primary: bool = False) -> bool:
        text, app = self.selected_text, self.application
        if not text or app is None:
            return False
        app.copy_to_clipboard(text, primary=primary)
        return True

    def copy_key(self, event: KeyEvent) -> bool:
        """Ctrl+Ins copies what is selected here; so does Ctrl+C, unless a program runs.

        Asked by ``Shell`` before the command line is offered the key, since
        the console holds no keyboard while the windows are up and declines
        it while idle.  Ctrl+C belongs to a running program -- it is how one
        is interrupted -- and is only a copy while the shell is at its prompt.
        """
        if self.selection is None:
            return False
        if event.matches("ctrl+insert") or (event.matches("ctrl+c") and not self.busy):
            return self._copy_selection()
        return False

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
        elif self.copy_key(event):
            pass
        elif event.matches("escape") and self.selection is not None and not self.busy:
            self.clear_selection()
        elif self.busy:
            self.send(event)
        else:
            return False
        return True

    def scroll_back(self) -> None:
        self.screen.prev_page()
        self._changed()

    def scroll_forward(self) -> None:
        self.screen.next_page()
        self._changed()

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
        if self.selection is not None:
            self._render_selection(surface)

    def _render_selection(self, surface: Surface) -> None:
        """The selected cells reversed, as a terminal shows its own selection."""
        (sx, sy), (ex, ey) = sorted(self.selection, key=lambda cell: (cell[1], cell[0]))
        cells = self.screen.surface
        columns = self.screen.columns
        for y in range(sy, ey + 1):
            left = sx if y == sy else 0
            right = ex + 1 if y == ey else columns
            for x in range(left, min(right, columns)):
                char, style = cells.get(x, y)
                if char:
                    surface.set_cell(x, y, char, style.derive(reverse=not style.reverse))
