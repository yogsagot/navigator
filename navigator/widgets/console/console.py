"""The screen a program Navigator started paints on.

Named for what it shows rather than for what drives it: the emulation and the
pty are :mod:`navkit.console` and :mod:`navkit.process`, and what lives here is
the widget that puts one on the desktop and gives it the keyboard.
"""

from __future__ import annotations

import os
from pathlib import Path

from navkit.console import ConsoleScreen, seed_from_host
from navkit.events import KeyEvent
from navkit.process import PtyProcess
from navkit.reactive import effect, reactive
from navkit.screen import Surface
from navkit.terminal import encode_key
from navkit.widget import Widget


class Console(Widget):
    """The screen a program Navigator started paints on.

    This is what Ctrl+O reveals.  DOS Navigator could show the last command's
    output behind its panels because in DOS there was one screen and the
    output was still in it; a terminal will not give its cells back, so the
    only way to have them is to have received them.  A shell runs on a pty
    this widget owns, its output goes through
    :class:`~navkit.console.ConsoleScreen`, and what arrives is a grid of
    cells like any other -- which is why the menu bar and the key bar can
    stay painted over it, and why it can be scrolled back through.
    """

    #: Bumped whenever the child writes, so the reactive layer knows the cells
    #: moved.  The screen behind it is not observable -- it is a great deal of
    #: mutable state that changes together -- so one counter stands for it.
    revision: int = reactive(0)

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
        self.process: PtyProcess | None = None
        self.seeded = False
        # The pty is told how big it is whenever this widget is, which is the
        # whole of the resize handling: the kernel raises SIGWINCH on the
        # child itself once the size is set.
        effect(self, Console._follow_size)

    def _follow_size(self) -> None:
        columns, lines = max(1, self.width), max(1, self.height)
        self.screen.resize(columns, lines)
        if self.process is not None:
            self.process.set_size(columns, lines)

    # -- the child -----------------------------------------------------------

    def start(self, argv: list[str] | None = None) -> None:
        """Start a program on the console, replacing any already running."""
        if self.process is not None and self.process.is_running:
            return
        if not self.seeded:
            # Whatever was on the real screen before Navigator ran, if this
            # host happens to keep it.  Once only, and before the shell's
            # first prompt lands on top of it.
            self.seeded = True
            seed_from_host(self.screen)
        shell = argv or [os.environ.get("SHELL") or "/bin/sh"]
        self.process = PtyProcess(
            shell,
            cwd=self.cwd,
            columns=max(1, self.width),
            lines=max(1, self.height),
            on_output=self._on_output,
            on_exit=self._on_exit,
        )
        try:
            self.process.start()
        except OSError:
            self.process = None

    def stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            self.process.close()
            self.process = None

    def _on_output(self, data: bytes) -> None:
        self.screen.feed(data)
        self.revision += 1

    def _on_exit(self, status: int) -> None:
        self.process = None
        self.revision += 1

    # -- input ---------------------------------------------------------------

    def send(self, event: KeyEvent) -> bool:
        """Type *event* at the child; ``False`` if there is nobody to type at."""
        if self.process is None or not self.process.is_running:
            return False
        data = encode_key(event)
        if not data:
            return False
        self.process.write(data)
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        """Everything typed while the console has the keyboard.

        It has the screen, so it has the keys: the two scrollback bindings are
        kept back and the rest goes to the child.  **Including the keys it has
        nobody to send to** -- a console with no child still swallows them
        rather than letting them fall through to the desktop underneath, which
        is showing nothing and would act on keys the user aimed at a shell.

        The way out is not here.  Ctrl+O and quit are the application's, and
        the application sees every key before the tree does.
        """
        if event.matches("shift+pageup"):
            self.scroll_back()
        elif event.matches("shift+pagedown"):
            self.scroll_forward()
        else:
            self.send(event)
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

        None while the view is scrolled back: the rows on screen are history
        then, and the live cursor's position means nothing among them.  The
        reversed cell got that wrong, highlighting whatever happened to sit at
        those coordinates in the scrollback.
        """
        if self.screen.scrolled_back:
            return None
        column, row, hidden = self.screen.cursor
        return None if hidden else (column, row)

    def render(self, surface: Surface) -> None:
        _ = self.revision  # read for the dependency: this is what output moves
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        self.screen.blit_into(surface)
