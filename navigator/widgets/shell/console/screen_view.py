"""A program's screen as a widget: what the console and a terminal window share.

The emulation is :class:`~navkit.console.ConsoleScreen`; what lives here is
showing one -- painting it, scrolling back through it, selecting from it, and
passing keys and the mouse on to the program behind it.  Which program that is,
and how it is started, is a subclass's: :class:`~navigator.widgets.shell.console.Console`
drives the command line's shell, a :class:`~navigator.widgets.shell.terminal_view.TerminalView`
one command on a pty of its own.
"""

from __future__ import annotations

from typing import Any

from navkit.console import ConsoleScreen
from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.terminal import encode_key, encode_mouse
from navkit.widget import Widget
from navml.widgets.dialog.commands import Clear, ClipboardCopy, ClipboardPaste
from navml.widgets.menu.context_menu import ContextMenu, ContextMenuHost

#: Rows one notch of the wheel scrolls the console, as most terminals do.
WHEEL_LINES = 3


class ScreenView(ContextMenuHost, Widget):
    """A :class:`~navkit.console.ConsoleScreen` on the desktop.

    A subclass says three things: :attr:`busy` (a program is running and has
    the keys), :attr:`alive` (there is a child to write to) and
    :meth:`write_child`.
    """

    #: Bumped whenever the child writes, so the reactive layer knows the cells
    #: moved.  The screen behind it is not observable -- it is a great deal of
    #: mutable state that changes together -- so one counter stands for it.
    revision: int = reactive(0)

    #: What the mouse has selected: the cell it started on and the cell it
    #: is on now, both ``(x, y)`` in the view, or None.  Cleared whenever the
    #: view moves under it -- new output, a scroll -- since the cells it
    #: named are then somewhere else.
    selection: Any = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # It has the screen, so it should have the keyboard: the application
        # asks whichever widget the keys are going to where its caret belongs,
        # which is what gets the child's own cursor drawn.
        self.can_focus = True
        self.screen = ConsoleScreen(80, 24)
        #: Where a left-button drag started, while one is selecting.
        self._drag_from: tuple[int, int] | None = None

    # -- what a subclass says --------------------------------------------------

    @property
    def busy(self) -> bool:
        """A program is running, so what is typed is the program's."""
        return False

    @property
    def alive(self) -> bool:
        """There is a child to write to."""
        return False

    def write_child(self, data: bytes) -> None:
        """Send *data* to the child."""

    # -- output ------------------------------------------------------------------

    def _changed(self) -> None:
        self.revision += 1
        self.clear_selection()

    # -- input ---------------------------------------------------------------

    def send(self, event: KeyEvent) -> bool:
        """Type *event* at the child; ``False`` if there is nobody to type at."""
        if not self.alive:
            return False
        data = encode_key(event, application_cursor=self.screen.application_cursor)
        if not data:
            return False
        self.write_child(data)
        return True

    @property
    def tracks_mouse(self) -> bool:
        """A running program asked for the mouse, so the view passes it on."""
        return self.busy and bool(self.screen.mouse_tracking)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """Clicks, drags and the wheel, for a program that turned the mouse on.

        ``mc`` and ``htop`` both do, and a console that kept the mouse for
        itself left them with a pointer that did nothing.  The position is
        already the view's own -- ``dispatch_mouse`` shifted it on the way
        down -- which is the program's screen, cell for cell.

        Otherwise the mouse selects, as a terminal's does -- the terminal's
        own selection is out of reach while Navigator tracks the mouse.
        """
        if not self.tracks_mouse or not self.alive:
            return self._select(event)
        data = encode_mouse(
            event, tracking=self.screen.mouse_tracking, sgr=self.screen.mouse_sgr
        )
        if data:
            self.write_child(data)
        return True

    # -- selection -------------------------------------------------------------

    def _cell(self, event: MouseClickEvent) -> tuple[int, int]:
        """The cell under *event*, held inside the view while a drag outruns it."""
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
        if event.button != "left" or (self.tracks_mouse and self.alive):
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

    # -- the context menu --------------------------------------------------------

    def context_menu(self) -> ContextMenu | None:
        """Copy, Paste and Clear selection -- or nothing while a program has
        the mouse, which has the right click too."""
        if self.tracks_mouse and self.alive:
            return None
        menu = ContextMenu()
        menu.add_item(tr("~C~opy"), ClipboardCopy, "Ctrl-Ins")
        menu.add_item(tr("~P~aste"), ClipboardPaste)
        menu.add_line()
        menu.add_item(tr("C~l~ear selection"), Clear, "Esc")
        return menu

    def refusal(self, command: Any) -> str:
        if isinstance(command, (ClipboardCopy, Clear)):
            return "" if self.selection is not None else tr("Nothing is selected")
        return super().refusal(command)

    async def on_clipboard_copy(self, command: ClipboardCopy) -> bool:
        self._copy_selection()
        return True

    async def on_clipboard_paste(self, command: ClipboardPaste) -> bool:
        """Ask for the clipboard: it arrives as a paste, and goes wherever the
        terminal's own paste would -- to the program, or the command line."""
        app = self.application
        if app is not None:
            app.request_clipboard()
        return True

    async def on_clear(self, command: Clear) -> bool:
        self.clear_selection()
        return True

    def copy_key(self, event: KeyEvent) -> bool:
        """Ctrl+Ins copies what is selected here; so does Ctrl+C, unless a program runs.

        Ctrl+C belongs to a running program -- it is how one is interrupted --
        and is only a copy while nothing is.
        """
        if self.selection is None:
            return False
        if event.matches("ctrl+insert") or (event.matches("ctrl+c") and not self.busy):
            return self._copy_selection()
        return False

    async def on_key(self, event: KeyEvent) -> bool:
        """The scrollback keys, a copy, and -- while a program runs -- the rest.

        Shift+PgUp/PgDn half a page and Shift+Up/Down a line (both what
        xfce4-terminal binds for itself, so they reach here only where the
        terminal leaves them), and while nothing runs the bare PgUp/PgDn a page
        and Home/End all the way.  A full-screen program on the alternate
        screen has no scrollback and gets Shift+Up/Down, which editors select
        with.

        **While a program runs the rest is the program's**, swallowed whether
        or not there is a child to send it to, so a keystroke aimed at ``vim``
        never lands on whatever is underneath.  Otherwise a key is declined.
        """
        page = self.screen.lines
        idle = not self.busy
        half = (page + 1) // 2
        if event.matches("shift+pageup"):
            self.scroll_lines(-half)
        elif event.matches("shift+pagedown"):
            self.scroll_lines(half)
        elif idle and event.matches("pageup"):
            self.scroll_lines(-page)
        elif idle and event.matches("pagedown"):
            self.scroll_lines(page)
        elif event.matches("shift+up") and not (self.busy and self.screen.alternate):
            self.scroll_lines(-1)
        elif event.matches("shift+down") and not (self.busy and self.screen.alternate):
            self.scroll_lines(1)
        elif idle and event.matches("home"):
            self.screen.scroll_to_top()
            self._changed()
        elif idle and event.matches("end"):
            self.screen.scroll_to_bottom()
            self._changed()
        elif self.copy_key(event):
            pass
        elif event.matches("escape") and self.selection is not None and not self.busy:
            self.clear_selection()
        elif self.busy:
            self.send(event)
        else:
            return False
        return True

    def scroll_lines(self, lines: int) -> None:
        """*lines* rows back (negative) or forward (positive) through the scrollback."""
        self.screen.scroll(lines)
        self._changed()

    # -- painting ------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        """Where the child program put its cursor, for navkit to place ours.

        None while nothing runs, and while the view is scrolled back: the rows
        on screen are history then, and the live cursor's position means
        nothing among them.
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
