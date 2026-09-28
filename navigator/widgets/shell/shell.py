"""The handlers behind ``shell.nml``.

What the document says is the two bars, the command line and the two layers
between them; what is left here is opening the file manager on the desktop,
Ctrl+O, and running what is typed on the command line.

This file never names the generated class.  ``class Shell(DockLayout)`` is
what a Python-only widget would say too, and it is the base the markup's
``Shell(DockLayout):`` head names.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.commands import Command
from navkit.events import Event, KeyEvent
from navkit.reactive import computed
from navkit.screen import Surface
from navkit.stylesheet import Stylesheet
from navml.commands import OpenMenu
from navml.history import HISTORY

from navigator.commands import About, CommandLineEnd, CommandLineHome
from navigator.commands import ExecuteCommandLine, NewManager, OpenTreeWindow
from navigator.subshell import CommandFinished
from navigator.widgets.command_line.command_line import HISTORY_ID
from navml.widgets.layout.dock_layout import DockLayout

from navigator.scheme import default_scheme
from navigator.widgets.manager import Manager


class Shell(DockLayout):
    """The Navigator screen: menu bar, console, desktop and key bar."""

    def __init__(
        self,
        left: Path,
        right: Path,
        scheme: Stylesheet | None = None,
        **kwargs,
    ):
        """Build the screen, and open the file manager on its desktop.

        ``stylesheet`` is a keyword rather than a markup line because a
        default that depends on whether the caller supplied one is logic.  The
        screen brings its own look either way, so the tree is styled with or
        without an application around it.

        **The console's working directory is seeded, not bound**, for the
        reason ``Panel.path`` is: the shell inside it navigates it.
        """
        super().__init__(stylesheet=scheme or default_scheme(), **kwargs)
        self.console.cwd = left
        self.console.subshell.on_finished = self._command_finished
        #: Whether the console was put up by a command rather than by Ctrl+O,
        #: and so is to be taken down again when the command is done.
        self._shown_for_command = False
        #: The file manager window.  Kept after it is closed, for whoever asks
        #: what it was; whether it is still on the desktop is
        #: ``manager.parent is not None``.
        self.manager = self.desktop.open(Manager(left, right))

    def toggle_console(self) -> None:
        """Put the windows away to show the console, or bring them back.

        The console starts its shell the first time it is shown.  The focus
        moves with the flag, and **in the same call rather than from an
        effect**.  An effect runs at the next flush, which is after the whole
        batch of events has been dispatched -- so a Ctrl+O and the keystroke
        behind it, arriving together as a paste or fast typing do, would be
        routed by a focus that had not moved yet and the second key would go
        to the wrong place.

        Bringing the windows back hands the keyboard to exactly the widget
        that had it, because that is what activating a window does.  With no
        window left there is nothing to go back to, and the console stays.
        """
        desktop = self.desktop
        showing = not self.console_visible
        if not showing and desktop.active_window is None:
            return
        if showing:
            self.console.start()
            window = desktop.active_window
            app = self.application
            if window is not None and app is not None and window._holds(app.focused):
                window._saved_focus = app.focused
        self.console_visible = showing
        if showing:
            self.console.focus()
        else:
            desktop.activate(desktop.active_window)

    def show_console(self) -> None:
        """Show the console if it is not showing already."""
        if not self.console_visible:
            self.console.start()
            self.console_visible = True
        self.console.focus()

    # -- the menu ---------------------------------------------------------------

    async def on_open_menu(self, event: OpenMenu) -> bool:
        """F10: the menu bar is this screen's, so the command stops here.

        The bar is nowhere near the focus -- it is a sibling of the desktop --
        so the command, which starts from the focus and walks up, reaches it
        only through the screen that holds both.
        """
        self.menu.open(0)
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        """Alt+letter drops a menu; anything else is typed on the command line.

        Reached only by a key that everything nearer the keyboard declined,
        so a dialog's Alt+letter walk and a running program both come first:
        the console sends Meta+F to its program, as DOS Navigator's user
        screen would have.  What is left once the menu has passed is what
        ``TCommandLine`` got by being ``ofPostProcess`` -- the printable
        characters and the editing keys a panel has no use for.
        """
        if await self.menu.open_hotkey(event):
            return True
        return await self.command_line.on_key(event)

    # -- the command line ------------------------------------------------------

    @computed
    def command_prompt(self) -> str:
        """``<directory>>``: where the file manager in front is, as ``GetDir`` said.

        DOS Navigator's prompt was the process's current directory, which a
        focused panel kept equal to its own.  A command runs in the active
        panel's directory here, so the prompt says that one.  With no file
        manager open it is where the shell last was.
        """
        window = self.desktop.active_window
        manager = window if isinstance(window, Manager) else self.active_manager
        if manager is not None:
            return f"{manager.active_panel.path}>"
        where = self.console.subshell.cwd or self.console.cwd
        return f"{where}>" if where is not None else ">"

    def _command_directory(self) -> Path | None:
        manager = self.active_manager
        if manager is not None:
            return manager.active_panel.path
        return self.console.subshell.cwd or self.console.cwd

    @property
    def program_has_keys(self) -> bool:
        """A command is running on the console and the console holds the keyboard.

        DOS Navigator was not running at all while a command was: the program
        had every key.  So every command this screen handles steps aside --
        F10 is ``htop``'s and ``mc``'s way out, Enter, Home and End are the
        program's -- and a disabled command's key falls through to the
        console, which sends it on.  The application asks the same question,
        so Ctrl+O -- ``mc``'s panel toggle, ``nano``'s Write Out -- goes to the
        program as well, and the way back to the panels is to leave it.
        """
        return self.console.busy and self.console.focused

    def enables(self, command: Command) -> bool:
        """Enter, Home and End are the command line's only while it has text.

        And Enter only while no command is running: the program has the keys
        then, and a second command would be typed at it.  Nothing here runs
        while a program holds the keyboard (:attr:`program_has_keys`).
        """
        if self.program_has_keys:
            return False
        if isinstance(command, (ExecuteCommandLine, CommandLineHome, CommandLineEnd)):
            if not self.command_line.value.strip():
                return False
            if isinstance(command, ExecuteCommandLine):
                return not self.console.busy
        return super().enables(command)

    async def on_command_line_home(self, event: CommandLineHome) -> bool:
        self.command_line.home()
        return True

    async def on_command_line_end(self, event: CommandLineEnd) -> bool:
        self.command_line.end()
        return True

    async def on_execute_command_line(self, event: ExecuteCommandLine) -> bool:
        """Enter: run the line in the shell, with the console up while it runs.

        The console takes the keyboard for the length of the command, so a
        program that reads the terminal -- an editor, a pager, a password
        prompt -- gets what is typed.  The windows come back when the shell
        reports its prompt, in :meth:`command_finished`.
        """
        self.run_command(self.command_line.value)
        return True

    def run_command(self, command: str) -> None:
        """Run *command* as though it had been typed on the command line."""
        if not command.strip():
            return
        HISTORY.add(HISTORY_ID, command)
        self.command_line.clear()
        cwd = self._command_directory()
        self._shown_for_command = not self.console_visible
        if not self.console_visible:
            self.toggle_console()
        self.console.focus()
        self.console.run(command, cwd)

    def _command_finished(self, status: int, cwd: Path | None) -> None:
        """The shell is back at its prompt: finish in a batch, not in the pty's reader."""
        app = self.application
        if app is not None and app.is_running:
            app.post_event(CommandFinished(status, cwd))
        else:
            self.command_finished(status, cwd)

    def command_finished(self, status: int, cwd: Path | None) -> None:
        """Bring the windows back, and send the panel wherever the shell went.

        DOS Navigator restarted into its panels the moment the command
        returned and re-read them, and the directory it came back to was the
        one DOS had kept -- so a ``cd`` on the command line moved the panel.
        """
        if self._shown_for_command and self.console_visible:
            self._shown_for_command = False
            self.toggle_console()
        elif self.console_visible:
            # Still up by Ctrl+O: the keys go back to the command line.
            self.console.focus()
        manager = self.active_manager
        if manager is None:
            return
        panel = manager.active_panel
        if cwd is not None and cwd != panel.path and cwd.is_dir():
            panel.path = cwd
        for each in (manager.left, manager.right):
            each.reload()

    def cursor_position(self) -> tuple[int, int] | None:
        """The command line's caret, when the keys that fell this far go there.

        Asked because the widget holding the keyboard -- a panel, the idle
        console -- has no caret of its own, and what it declines is what
        reaches :meth:`on_key` and so the command line.
        """
        line = self.command_line
        if not line.visible:
            return None
        if self.console.busy and self.console.focused:
            # A program has the keys, and has hidden its cursor or been
            # scrolled away from: nothing typed now reaches the line.
            return None
        position = line.cursor_position()
        if position is None:
            return None
        x, y = position
        return line.x + x, line.y + y

    # -- file managers --------------------------------------------------------

    @property
    def active_manager(self) -> Manager | None:
        """The file manager nearest the top of the desktop, or None if none is open.

        What a command meaning "the file manager" asks for, now that Manager >
        New can open several: the one the user last had in front, whatever
        other window -- a tree window, say -- is in front of it.
        ``manager`` stays the first one, kept for whoever asks what it was.
        """
        for window in reversed(self.desktop.windows()):
            if isinstance(window, Manager):
                return window
        return None

    async def on_new_manager(self, event: NewManager) -> bool:
        """Ctrl+F3: ``OpenWindow``.  Another file manager, filling the desktop.

        DOS Navigator asked for a drive first and opened both panels on that
        drive's current directory.  One root has no drive to ask for, so both
        panels open where the file manager in front is -- or where Navigator was
        started, with none open.
        """
        current = self.active_manager
        start = current.active_panel.path if current is not None else Path.cwd()
        self.desktop.open(Manager(start, start))
        return True

    async def on_about(self, event: About) -> bool:
        """≡ > About: started, not awaited -- a handler never waits on a dialog."""
        from navigator.widgets.about_dialog import AboutDialog

        self.spawn(AboutDialog().execute(self.application))
        return True

    # -- the directory tree window --------------------------------------------

    async def on_open_tree_window(self, event: OpenTreeWindow) -> bool:
        """Disk > Directory tree: a tree window, opened on the active panel's directory."""
        from navigator.widgets.tree_window import TreeWindow

        manager = self.active_manager
        start = manager.active_panel.path if manager is not None else None
        self.desktop.open(TreeWindow(start=start))
        return True

    async def on_chosen(self, event: Any) -> bool:
        """Enter in a tree nobody nearer claimed: the file manager's panel goes there.

        The tree window's, in practice -- the manager's own tree and a dialog's
        both answer their tree themselves -- and this screen is the one thing
        that knows where the file manager is.  The keyboard stays in the tree,
        as ``SendLocated`` left it.
        """
        manager = self.active_manager
        if manager is None or event.node is None:
            return False
        manager.active_panel.path = Path(event.node.data)
        return True

    async def on_desktop_opened(self, event: Event) -> bool:
        """A window was opened on ``desktop``: if Ctrl+O had put the windows away, bring them back.

        Here rather than in each command that opens one, which is what used to
        let Disk > Directory tree open a window nobody could see: opening *is*
        the request to show it, whatever the window and whoever opened it.
        """
        if self.console_visible:
            self.toggle_console()
        return True

    async def on_desktop_emptied(self, event: Event) -> bool:
        """The last window on ``desktop`` closed: the console is all there is.

        Named by the generator's ``on_<id>_<event>`` convention, so the stub it
        writes is what this overrides.
        """
        self.show_console()
        return True

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
