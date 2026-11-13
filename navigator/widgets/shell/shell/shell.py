"""The handlers behind ``shell.nml``.

What the document says is the two bars, the command line and the two layers
between them; what is left here is opening the file manager on the desktop,
Ctrl+O, and running what is typed on the command line.

This file never names the generated class.  ``class Shell(..., DockLayout)``
is what a Python-only widget would say too, and its last base is the one the
markup's ``Shell(DockLayout):`` head names.  The methods are split by feature
into mixins (``navkit.widget.Mixin``), one module each beside this one --
``command_line``, ``running``, ``associations``, ``links``, ``utilities`` and
the rest; what stays here is the state, the constructor, ``checks``/``refusal``,
the prompt and the toasts.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Callable

from navkit.commands import Command
from navkit.events import Event, KeyEvent
from navkit.i18n import tr
from navkit.reactive import bind, computed, effect, reactive
from navkit.screen import Surface
from navkit.widget import Widget
from navkit.stylesheet import Stylesheet

from navml.widgets.dialog.dialog import Dialog

from navigator.commands import AsciiTable
from navigator.lib.system.subshell import CompletionsReady
from navigator.widgets.manager.commands import HideLeft, HideRight, ToggleMark
from navigator.widgets.shell.commands import (
    S3Link,
    GvfsLink,
    DockerLink,
    PodmanLink,
    AdbLink,
    RcloneLink,
    DockerShell,
    PodmanShell,
    AdbShell,
    FtpLink,
    HangUp,
    Terminal,
    CloseRootAccess,
    ToggleRootAccess,
    ShowBackground,
    NavyLink,
    SmbLink,
    ToggleTrashCan,
    OpenTrash,
    EmptyTrash,
    CommandLineEnd,
    CommandLineHome,
    CompleteCommandLine,
    ExecuteCommandLine,
    ExecuteCommandLineInWindow,
    SaveDesktop,
    FuzzyHistory,
    InsertName,
    InsertPath,
    OpenProcessWindow,
    OpenServiceWindow,
    OpenMonitorWindow,
    ToggleMarkBySpace,
)

from navml.widgets.dialog.date_button import CalendarView
from navml.widgets.dialog.file_list import FileInfoPane
from navml.widgets.layout.dock_layout import DockLayout

from navigator.lib.config import country
from navigator.lib.appearance.scheme import DEFAULT_THEME, default_scheme
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager

from navigator.widgets.shell.shell.colors import Colors
from navigator.widgets.shell.shell.console_keys import ConsoleMixin
from navigator.widgets.shell.shell.fuzzy import Fuzzy
from navigator.widgets.shell.shell.command_line import CommandLineMixin
from navigator.widgets.shell.shell.completion import Completion
from navigator.widgets.shell.shell.running import Running
from navigator.widgets.shell.shell.user_menu import UserMenu
from navigator.widgets.shell.shell.associations import Associations
from navigator.widgets.shell.shell.links import Links
from navigator.widgets.shell.shell.utilities import Utilities


class _Toasts:
    """The toasts up, oldest first: where each stands, the newest lowest."""

    items: tuple[Any, ...] = reactive(())

    def above(self, toast: Any) -> int:
        """How many toasts high *toast*'s bottom is: itself and every newer one."""
        items = self.items
        return len(items) - items.index(toast) if toast in items else 1

    def drop(self, toast: Any) -> None:
        self.items = tuple(item for item in self.items if item is not toast)


class Shell(Colors, ConsoleMixin, Fuzzy, CommandLineMixin, Completion, Running, UserMenu, Associations, Links,
            Utilities, DockLayout):
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
        #: The theme the sheet was loaded from: what Options > Colors loads
        #: again beneath the palette it edits.
        self.theme = DEFAULT_THEME
        #: *Highlight groups*' masks as this shell last saw them (``_use_highlight_groups``).
        self._highlight_masks: dict[str, str] | None = None
        #: ``.root`` on the whole screen while Navigator runs as root, so a
        #: sheet can mark every window and dialog under it.
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.add_class("root")
        self.console.cwd = left
        self.console.subshell.on_finished = self._command_finished
        # A shell that exits while it has the real terminal -- ``exit`` typed
        # at it -- can no longer hand it back, so Navigator takes it.
        self.console.subshell.on_exit = lambda status: self.end_relay()
        # navml's file dialogs know no country, so they are told from here;
        # ``country.stamp`` reads the settings at each paint.
        FileInfoPane.stamp = staticmethod(country.stamp)
        # The same for the week a dropped calendar starts on.
        CalendarView.default_first_weekday = staticmethod(country.first_weekday)
        #: The toasts up now, the newest at the bottom (:meth:`toast`).
        self._toasts = _Toasts()
        self.keybar.menu = self.menu
        #: Up and Down through the shell's history: the entries, where the walk
        #: is, what was typed before it began, and what it last put on the line.
        self._walk: tuple[list[str], int, str, str] | None = None
        #: The completions drop-down, the answer it is showing, and the
        #: candidates that answer held before typing narrowed them.
        self._completion_list: Any = None
        self._completing: CompletionsReady | None = None
        self._candidates: list[str] = []
        #: Whether the console was put up by a command rather than by Ctrl+O,
        #: and so is to be taken down again when the command is done.
        self._shown_for_command = False
        #: An fzf pick running on the console (:meth:`pick`): what its choice
        #: is for, and whether the console was put up for it.
        self._picking: tuple[Callable[[list[str]], None], bool] | None = None
        #: A screen saver is up (``SSaver <> nil``): no second one comes.
        self.resting = False
        #: Whether the real terminal was handed to the shell for a command
        #: rather than by Ctrl+O, and so is to be taken back when it is done.
        self._relayed_for_command = False
        #: When a command run on the Timer line started (``monotonic``), or None.
        self._timer_started: float | None = None
        #: Files fetched from another drive for the command running
        #: (``UseFile``), offered back once it is done; and the shell's
        #: directory when it started, which tells a ``cd`` in it.
        self._command_uses: list[Any] = []
        self._command_started_in: Path | None = None
        #: One lock per site being connected to, so two panels going to the
        #: same server ask its questions once.
        self._reaching: dict[Any, asyncio.Lock] = {}
        #: The file manager window.  Kept after it is closed, for whoever asks
        #: what it was; whether it is still on the desktop is
        #: ``manager.parent is not None``.
        self.manager = self.desktop.open(Manager(left, right))

    async def on_save_desktop(self, event: SaveDesktop) -> bool:
        """Options > Save desktop: ``SaveRealDsk`` (``navigator.lib.config.desktop_state``)."""
        from navigator.lib.config import desktop_state
        desktop_state.save(self.desktop)
        return True

    async def load_desktop(self) -> None:
        """Options > Load desktop: ``RetrieveDesktop`` -- every window closed,
        asked as Close all asks, and the saved ones put in their place.  A
        Cancel keeps the desktop as it is; none saved says so."""
        from navigator.lib.config import desktop_state
        data = desktop_state.load()
        if data is None:
            await Dialog(title=tr("Error"), prompt=tr("No desktop has been saved"), buttons="ok"
                         ).execute(self.application)
            return
        here = self._command_directory()
        if not await self.desktop.close_all_asking():
            return
        await desktop_state.restore(self.desktop, data, here=here)

    #: Whether the grabber has said how it works this session (DN's ``NotMessage``).
    _grabber_told = False

    # -- the command line ------------------------------------------------------

    def mounted(self) -> None:
        super().mounted()
        effect(self, Shell._follow_panel)
        effect(self, Shell._name_window)
        effect(self, Shell._size_histories)
        effect(self, Shell._choose_clipboard)
        effect(self, Shell._use_highlight_groups)
        effect(self, Shell._name_root_access)
        from navigator.lib.drives.sessions import SESSIONS

        SESSIONS.add_listener(self._heard_closed)

    def unmounting(self) -> None:
        from navigator.lib.drives.sessions import SESSIONS

        SESSIONS.remove_listener(self._heard_closed)
        super().unmounting()

    @computed
    def command_prompt(self) -> str:
        """``<directory>$``: where the file manager in front is, as ``GetDir`` said.

        DOS Navigator's prompt was the process's current directory, which a
        focused panel kept equal to its own.  A command runs in the active
        panel's directory here, so the prompt says that one.  With no file
        manager open it is where the shell last was.  Shown only until the
        shell's own prompt arrives (:attr:`command_prompt_cells`).  It ends in
        a POSIX shell's ``$`` -- root's ``#`` while the console is root's --
        not DOS's ``PROMPT $P$G`` ``>``.  Blank while a
        command runs, as :attr:`command_prompt_cells` is.
        """
        if self.console.running:
            return ""
        remote = self._front_remote()
        if remote is not None:
            # The panel's place, though a command still runs in the last local
            # directory: what the user is looking at is what the prompt names.
            return f"{self._remote_name(remote)}{'#' if self.console.root else '$'}"
        where = self._front_directory()
        if where is None:
            where = self.console.subshell.cwd or self.console.cwd
        # Root's ``#``, as a shell's ``\$`` says it: a root console, or Navigator run as root.
        mark = "#" if self.console.root or (hasattr(os, "geteuid") and os.geteuid() == 0) else "$"
        return f"{where}{mark}" if where is not None else mark

    @computed
    def command_prompt_cells(self) -> tuple:
        """The shell's own prompt, if it was printed where the command would run.

        A prompt printed somewhere else names the wrong directory, so it is
        never shown for long: while the silent ``cd`` that follows a panel is
        on its way the last prompt stays, as a terminal's would, rather than
        ``<dir>>`` flashing up for the frame before the new one arrives.  If
        the shell cannot get there, ``<dir>>`` stands in.  With no file
        manager open, the shell is where the command would run, and its
        prompt is always right.

        **None while a command runs** -- a departure: DN's line stayed under
        the program's output.  A terminal shows no prompt until the command
        has finished, so its coming back is the sign that it has, and an
        empty row says the program is still going.  The row itself stays:
        giving it to the console would resize the pty under the program.
        """
        console = self.console
        if console.running:
            return ()
        if self._front_remote() is not None:
            # The shell's own prompt names a local directory: the stand-in
            # names the panel's place instead.
            return ()
        where = self._front_directory()
        if where is not None and console.prompt_cwd != where:
            # Read so the next prompt re-decides, whatever it says.
            console.prompts
            if console.subshell.catching_up:
                return console.prompt
            return ()
        return console.prompt

    def refusal(self, command: Command) -> str:
        """Enter, Home and End are the command line's only while it has text.

        And Enter only while no command is running: the program has the keys
        then, and a second command would be typed at it.  Nothing here runs
        while a program holds the keyboard (:attr:`program_has_keys`).
        """
        if self.program_has_keys:
            return tr("A program in the console has the keys")
        from navigator.commands import NewView

        if isinstance(command, NewView):
            # Window > *New view*: an editor's own (EditWindow.on_new_view).
            from navigator.widgets.editor.edit_window import EditWindow

            return "" if isinstance(self.desktop.active_window, EditWindow) else tr("Only an editor has views")
        hidden = tr("Interface Setup hides the command line")
        no_manager = tr("No file panels are open")
        if isinstance(command, OpenProcessWindow):
            from navigator.lib.system import processes

            return "" if processes.available() else tr("There is no /proc to read processes from")
        if isinstance(command, OpenServiceWindow):
            from navigator.lib.system import services

            return services.refusal_reason()
        if isinstance(command, OpenMonitorWindow):
            from navigator.lib.system import monitor

            return "" if monitor.available() else tr("There is no /proc/stat to read the processors from")
        if isinstance(command, AsciiTable):
            # ``ouiHideCmdline``: a hidden line takes no character either.
            return hidden if SETTINGS.interface.hide_command_line else ""
        if isinstance(
            command,
            (ExecuteCommandLine, ExecuteCommandLineInWindow, CommandLineHome, CommandLineEnd,
             CompleteCommandLine, InsertName, InsertPath),
        ):
            # A hidden command line runs and takes nothing: DN's
            # ``cmExecCommandLine`` and ``cmInsertName`` did nothing under
            # ``ouiHideCmdline``, and the keys fall through to the panel.
            if SETTINGS.interface.hide_command_line:
                return hidden
            if self._editor_has_keys():
                return tr("The editor has the keys")
        if isinstance(command, (InsertName, InsertPath)):
            return "" if self._panel_entry() is not None else tr("The cursor is on no file")
        if isinstance(command, FuzzyHistory):
            return hidden if SETTINGS.interface.hide_command_line else self.fuzzy_refusal()
        if isinstance(command, HangUp):
            from navigator.lib.drives import mounted, sessions

            # Connections only: a panel browsing ``root:`` mounts a drive too.
            if any(sessions.is_connection(drive.site.scheme) for drive in mounted()):
                return ""
            return tr("No connection is open")
        if isinstance(command, (Terminal, DockerShell, PodmanShell, AdbShell)):
            from navigator.lib.drives import remote_shell

            if remote_shell.program(command.scheme) is not None:
                return ""
            return tr("The {command} command is not installed").format(
                command=remote_shell.PROGRAMS[command.scheme])
        if isinstance(command, CloseRootAccess):
            return "" if self.root_mark.open else tr("No root access is open")
        if isinstance(command, ToggleRootAccess):
            if self.root_mark.open or self._root_reachable():
                return ""
            if os.geteuid() == 0:
                return tr("Navigator runs as root already")
            return tr("No way to root: System Setup's Root access says Never offer, or there is no sudo or pkexec")
        if isinstance(command, ShowBackground):
            from navigator.lib.system.background import BACKGROUND

            return "" if BACKGROUND.jobs else tr("Nothing is running in the background")
        if isinstance(command, (NavyLink, FtpLink, SmbLink, S3Link, OpenTrash, EmptyTrash)):
            return "" if self.active_manager is not None else no_manager
        if isinstance(command, (DockerLink, PodmanLink, AdbLink, RcloneLink)):
            from navigator.lib.drives import sessions

            if self.active_manager is None:
                return no_manager
            return sessions.available(command.scheme) or ""
        if isinstance(command, GvfsLink):
            from navigator.lib.system import desktop

            if self.active_manager is None:
                return no_manager
            return "" if desktop.program() is not None else tr("Neither GIO nor KIO is installed")
        if isinstance(command, (HideLeft, HideRight)):
            # Reached here only from outside a file manager: from the
            # console, DN's user screen, and not from a viewer or an editor.
            if self.active_manager is None:
                return no_manager
            return "" if self.console_visible else tr("Only in a file panel or the console")
        if isinstance(command, ToggleMarkBySpace):
            # ``CmdLine.Str <> ''``: once anything is on the line -- a blank
            # included -- Space types.  Otherwise it is Insert, wherever the
            # file manager would take Insert.
            # File Manager Setup's *Space toggles* off, it always types.
            manager = self.active_manager
            if not SETTINGS.file_manager.space_toggles_selection:
                return tr("File Manager Setup's Space toggles is off")
            if self.command_line.value and not SETTINGS.interface.hide_command_line:
                # A hidden line's text takes nothing: DN's hidden line took no keys.
                return tr("The command line holds text: the key edits it")
            if manager is None:
                return no_manager
            return manager.refusal(ToggleMark())
        if isinstance(
            command,
            (ExecuteCommandLine, ExecuteCommandLineInWindow, CommandLineHome, CommandLineEnd,
             CompleteCommandLine),
        ):
            if not self.command_line.value.strip():
                return tr("The command line is empty")
            if isinstance(command, (CommandLineHome, CommandLineEnd)) and not SETTINGS.file_manager.use_arrows:
                # *Use arrows* off: Home and End are the panel's, Shift+Home and
                # Shift+End the line's (``fmoUseArrows``).
                return tr("File Manager Setup's Use arrows is off")
            busy = tr("A command is still running")
            if isinstance(command, ExecuteCommandLine):
                return busy if self.console.busy else ""
            if isinstance(command, CompleteCommandLine):
                subshell = self.console.subshell
                if not (subshell.is_running and subshell.can_complete):
                    return tr("The shell cannot complete")
                return busy if self.console.busy else ""
        return super().refusal(command)

    @computed
    def block_insert(self) -> bool:
        """The ``:block_insert`` state: Interface's *Block Insert Cursor*.

        ``ouiBlockInsertCursor`` swapped ``TCommandLine``'s two cursors:
        ``Overwrite xor ouiBlockInsertCursor`` is the block (``CMDLINE.PAS:234``),
        so overwrite shows the block unless the setting swaps it.  It is this
        screen's rather than the line's because the caret is answered from here
        (:meth:`cursor_position`), and the application takes its shape from
        whoever answers.
        """
        return SETTINGS.interface.block_insert_cursor != self.command_line.overwrite

    def strip_start(self) -> int:
        """The column the window strip's chips begin at -- or its ``+k``
        alone, which keeps to its right end too -- and the strip's end
        when it shows none: where the mark of work in the background ends."""
        strip = self.window_strip
        end = strip.x + strip.width
        if not strip.visible:
            return end
        chips = strip.chips()
        if chips:
            return strip.x + chips[0][0]
        hidden = strip.hidden()
        return end - len(f"+{hidden}") if hidden else end

    def toast(self, text: str, *, title: str = "", seconds: float | None = None) -> Any:
        """*text* in a passing box at the desktop's bottom right, over the
        windows (and the console), stacked above any still up; gone after
        *seconds* (``TOAST_SECONDS``) or a click."""
        from navml.widgets.toast import TOAST_SECONDS, Toast

        toasts = self._toasts
        desktop = self.desktop
        toast = self.add(Toast(text, title=title, seconds=TOAST_SECONDS if seconds is None else seconds))
        toast.merge_style("dock: none")
        toast.height = bind(lambda w: 3)
        toast.width = bind(lambda w: max(0, min(w.natural_width, desktop.width - 2)))
        toast.x = bind(lambda w: max(0, desktop.x + desktop.width - w.width - 1))
        toast.y = bind(lambda w: max(0, desktop.y + desktop.height - w.height * toasts.above(w)))
        toast.gone = toasts.drop
        toasts.items = (*toasts.items, toast)
        return toast

    def notify_away(self, title: str, text: str) -> bool:
        """*text* under *title* as a desktop notification -- but only while
        the terminal has said it is in the background, and ``[system]
        notifications`` is not off (:mod:`navigator.lib.system.notify`).
        A terminal that never reports its focus is never notified from:
        nobody can tell whether it is watched.  Whether one went out."""
        from navigator.lib.system import notify

        app = self.application
        if app is None or getattr(app, "terminal_focused", None) is not False:
            return False
        way = notify.method(SETTINGS.system.notifications, app.terminal.info.notifications)
        return bool(app.notify(title, text, way, app_name="Navigator"))

    #: ``ELEVATION.available()`` by System Setup's *Elevate*: its ``which``
    #: of sudo or pkexec asked once, not each time a menu is painted.
    _reachable: dict[str, bool] = {}

    def checks(self, command: Command) -> bool | None:
        """≡ > Trashcan on/off is ticked while the trash can shows."""
        if isinstance(command, ToggleTrashCan):
            return self.trash.shown
        return super().checks(command)

    async def on_chosen(self, event: Any) -> bool:
        """Enter in a tree or the volume list nobody nearer claimed: the file
        manager's panel goes there.

        The tree window's and the Volumes window's, in practice -- the
        manager's own tree and a dialog's both answer their tree themselves --
        and this screen is the one thing that knows where the file manager is.
        The keyboard stays where it was, as ``SendLocated`` left it.
        """
        from navigator.lib.system.volumes import Volume

        manager = self.active_manager
        if manager is None or event.node is None:
            return False
        if isinstance(event.node, Volume):
            manager.active_panel.path = Path(event.node.mount)
        else:
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

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)


class UserScreenPeek(Widget):
    """The user screen over the whole screen until the next key or click: DN's
    ``ShowUserScreen``, a ``TBackground`` the size of the application
    (``DNAPP.PAS:1027-1046``), the menu bar and status line covered too.
    Modal, so the console is shown and not typed into.  The live console's
    rows are at the bottom, its history filling the rows above, as a
    terminal's last screenful reads."""

    def __init__(self, console: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._console = console
        self.modal = True
        self.can_focus = True
        self.dims_behind = False
        self.fill_parent()
        self._done: Any = None

    async def execute(self, app: Any) -> None:
        import asyncio

        self._done = asyncio.get_running_loop().create_future()
        app.overlay(self)
        self.focus()
        try:
            await self._done
        finally:
            if self.parent is not None:
                self.parent.remove(self)

    def _end(self) -> None:
        if self._done is not None and not self._done.done():
            self._done.set_result(None)

    async def on_key(self, event: KeyEvent) -> bool:
        self._end()
        return True

    async def on_mouse_click(self, event: Any) -> bool:
        if event.action == "press" and not event.is_wheel:
            self._end()
        return True

    def render(self, surface: Surface) -> None:
        """The console's last screenful over every row: its live rows at the
        bottom, history above them, blanks where there is none."""
        console = self._console
        if console is None:
            return
        screen = console.screen
        surface.fill(0, 0, self.width, self.height, " ", console.style)
        top = max(0, self.height - screen.lines)
        rows = screen.history_rows(top)
        for offset, row in enumerate(rows):
            y = top - len(rows) + offset
            for x, (char, style) in enumerate(row[: self.width]):
                if char:
                    surface.set_cell(x, y, char, style)
        screen.blit_into(surface, 0, top)
