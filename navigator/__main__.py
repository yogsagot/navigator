#!/usr/bin/env python3
"""Navigator -- a recreation of DOS Navigator for POSIX terminals.

The application entry point: ``python -m navigator``.  What is left here is the
command line, the terminal it hands to navkit, and the application hooks that
hold the keys meaning the same thing wherever the focus is.

Everything it paints lives in :mod:`navigator.widgets`, one module per screen,
and the sheet those screens resolve against in :mod:`navigator.lib.appearance.scheme`.  The
split is not tidiness: this module is what the command runs, so it is already
in ``sys.modules`` as ``__main__`` and importing a widget *from* it would build
a second copy of everything in it.  A widget a document names has to be
importable by its own name, which is what ``manager.nml`` will need.
"""

from __future__ import annotations

import argparse
import contextlib
import configparser
import os
import sqlite3
import sys
from dataclasses import replace
from importlib import metadata
from pathlib import Path

from navkit.application import Application
from navkit.capabilities import VGA_PALETTE, TerminalInfo
from navkit.commands import Command
from navkit.database import DATABASE
from navkit.events import Event, KeyEvent, MouseClickEvent, PasteEvent
from navkit.glyphs import tier_named
from navkit.i18n import tr
from navkit.process import MARKER
from navkit.reactive import effect
from navkit.stylesheet import Stylesheet
from navkit.terminal import Terminal, is_a_tty

from navigator import __version__
from navigator.lib.config import keybindings, language
from navigator.lib.config.associations import seed_all as seed_associations
from navigator.lib.config.bookmarks import seed_bookmarks
from navigator.commands import AsciiTable, Help, OpenSmartpad, Quit, Refresh, ScreenGrab, ShowUserScreen, ToggleConsole
from navigator.lib.system.subshell import CommandFinished, CompletionsReady, HistoryChosen, HistoryReady
from navigator.lib.system.title import window_title
from navml.widgets.menu.commands import OpenMenu
from navigator.lib.appearance.scheme import (
    DEFAULT_THEME, default_scheme, theme_names, theme_path, user_scheme,
)
from navigator.lib.config.file_history import remember_windows
from navigator.lib.system import dirwatch, errorlog
from navigator.settings import SETTINGS, config_path, database_path
from navigator.widgets.manager.commands import HideLeft, HideRight
from navigator.widgets.manager.manager import Manager
from navigator.widgets.shell.commands import (
    CommandLineEnd,
    CommandLineHome,
    CompleteCommandLine,
    EditHistory,
    ExecuteCommandLine,
    QuickRun,
    Game,
    HistoryList,
    NewManager,
    OpenCalendar,
    ViewHistory,
)
from navigator.widgets.shell.console.console import WHEEL_LINES
from navigator.widgets.shell.shell import Shell


class Navigator(Application):
    """The file manager application."""

    def __init__(
        self, left: Path, right: Path, scheme: Stylesheet | None = None, *,
        given: bool = False, theme: str = DEFAULT_THEME, on_error: str | None = None,
        **kwargs
    ):
        """*given*: *left* and *right* came from the command line, so a desktop
        restored at the start puts its first file manager there.  *theme*
        names the theme *scheme* was loaded from, which Options > Colors
        loads again under the palette it edits.  *on_error* is
        ``--on-error``'s word, winning over System Setup's for the session."""
        scheme = scheme or default_scheme()
        self._on_error = on_error
        #: Whether the error box is up: a failure while it is ends Navigator.
        self._error_shown = False
        self._watchdog: errorlog.Watchdog | None = None
        #: The last failure written to ``errors.log``, so the one *Quit*
        #: stops on is not written twice.
        self._last_logged: BaseException | None = None
        self._given = (left, right) if given else None
        #: The directory Navigator started in, DOS's current one at the start.
        self._start = left
        #: When a key, a click or a paste last came: *Inactivity hour exit*.
        self._last_input = 0.0
        #: Whether the pointer was in the top right corner at the last look.
        self._in_corner = False
        kwargs.setdefault("title", window_title(Path(left).absolute()))
        self.shell = Shell(left, right, scheme)
        self.shell.theme = theme
        super().__init__(root=self.shell, **kwargs)

    @property
    def manager(self) -> Manager:
        """The file manager window, whether or not it is still open."""
        return self.shell.manager

    async def on_start(self) -> None:
        # Started now rather than on the first command, because its prompt
        # is what the command line shows -- to somebody looking at a terminal.
        # Headless, nobody is, and the first command starts it as before.
        if self.terminal.is_tty:
            self.shell.console.start()
        await self._restore_desktop()
        if self.manager.parent is not None:
            # The start's own file manager, not one a desktop brought back.
            self.manager.apply_left_panel()
        self._last_input = self._now()
        # System's *stall_report*: a freeze leaves its stacks in errors.log.
        self._watchdog = errorlog.start_watchdog(self, SETTINGS.system.stall_report)
        if self._watchdog is not None:
            effect(self.shell, self._follow_stall_report)
        self.call_every(self.idle_check_every, self._check_idle)
        self.call_every(self.saver_check_every, self._check_saver)
        # Startup's *Auto run User Menu*: DN put ``cmUserMenu`` on the queue
        # once its desktop was in place (``RunMenu``).
        if SETTINGS.startup.auto_user_menu:
            self.shell.spawn(self.shell.user_menu())

    def _follow_stall_report(self, _shell: Shell) -> None:
        """System Setup's *Report a stall after* in force at once: the
        watchdog's thread reads a plain number, never the setting."""
        if self._watchdog is not None:
            self._watchdog.threshold = SETTINGS.system.stall_report

    async def _restore_desktop(self) -> None:
        """Startup's *Autosave desktop*: the desktop saved on the way out last
        time, in place of the file manager this one opened with -- DN read
        ``DN.DSK`` at every start; here only while the box is ticked."""
        from navigator.lib.config import desktop_state
        if not SETTINGS.startup.autosave_desktop:
            return
        data = desktop_state.load()
        if not data or not data.get("windows"):
            return
        desktop = self.shell.desktop
        first = list(desktop.windows())
        made = await desktop_state.restore(desktop, data, dirs=self._given, here=self._start)
        if any(isinstance(window, Manager) for window in made):
            for window in first:
                window.close()

    #: Startup's *Inactivity hour exit*: how long nothing may be typed or
    #: clicked -- DN's ``ElapsedTimeInSecs(IdleSecs) > 3600`` in ``GetEvent``.
    idle_exit_after = 3600.0
    #: How often that is looked at.
    idle_check_every = 60.0

    #: How often the screen savers' *Time* and corners are looked at.
    saver_check_every = 1.0

    async def _check_saver(self) -> None:
        """``InsertIdler``'s callers: *Time* minutes with no key or click
        (``GetEvent``), or with *Use mouse* the pointer coming into the top
        right corner (``EventError``) -- and none while it rests in the
        bottom right.  Not while a command runs on the console, which DN
        was not running to notice."""
        from navigator.lib.appearance.savers import DELAYS

        shell, savers = self.shell, SETTINGS.savers
        if shell.resting or shell.console.busy or not savers.names():
            return
        width, height = shell.width, shell.height
        pointer = self.pointer if savers.mouse else None
        corner = pointer == (width - 1, 0)
        came, self._in_corner = corner and not self._in_corner, corner
        if pointer == (width - 1, height - 1):
            return
        delay = DELAYS.get(savers.time)
        if came or (delay is not None and self._now() - self._last_input >= delay):
            self._last_input = self._now()
            self.spawn(shell.rest())

    async def on_event(self, event: Event) -> bool:
        if isinstance(event, (KeyEvent, MouseClickEvent, PasteEvent)):
            self._last_input = self._now()
        return False

    async def _check_idle(self) -> None:
        """``ExecExit`` after an idle hour, or ``$DNIDLE`` run in its place.

        Not while a command runs on the console -- DN was not running then,
        so its hour started when the program ended -- and, a departure, not
        while an editor holds a changed text: ``ExecExit`` went through
        ``Done`` without asking, and the text would be lost.
        """
        if not SETTINGS.startup.inactivity_exit:
            return
        shell = self.shell
        if shell.console.busy:
            self._last_input = self._now()
            return
        if self._now() - self._last_input <= self.idle_exit_after:
            return
        if any(window.must_ask() for window in shell.desktop.windows()):
            return
        self._last_input = self._now()
        command = os.environ.get("DNIDLE", "")
        if command:
            shell.run_command(command, typed=False)
        else:
            self.exit()

    # -- failures -------------------------------------------------------------

    @property
    def on_error(self) -> str:
        """``dialog`` or ``crash``: the flag's, else System Setup's."""
        return self._on_error or SETTINGS.system.on_error

    def log_error(self, error: BaseException) -> None:
        if error is not self._last_logged:
            self._last_logged = error
            errorlog.append(error)

    def report_error(self, error: BaseException) -> bool:
        """The error box, unless *On error* says quit -- or the box is
        already up, when a second failure means the first left things broken."""
        if self.on_error != "dialog" or self._error_shown or self.root is None:
            return False
        self._error_shown = True
        self.spawn(self._show_error(error))
        return True

    async def _show_error(self, error: BaseException) -> None:
        from navigator.widgets.shell.error_dialog import ErrorDialog

        try:
            answer = await ErrorDialog(error, errorlog.PATH).execute(self)
        except Exception as during:
            # The box itself failed: no way left to show it, so stop on it.
            self.log_error(during)
            answer = "quit"
        finally:
            self._error_shown = False
        if answer == "quit":
            self.fail(error, fatal=True)

    async def on_stop(self) -> None:
        if self._watchdog is not None:
            self._watchdog.stop()
        # Startup's *Autosave desktop*: ``SaveRealDsk`` on the way out.
        if SETTINGS.startup.autosave_desktop:
            from navigator.lib.config import desktop_state
            desktop_state.save(self.shell.desktop)
        # Every viewer and editor still open is recorded, as ``cmQuit`` went
        # through each window's ``Valid`` -- whatever way Navigator is left.
        remember_windows(self.shell.desktop)
        # The shell would otherwise outlive the terminal it was talking to.
        self.shell.console.stop()
        # Auto refresh's observer: nothing is left to tell of a change.
        dirwatch.shutdown()

    #: Only the keys that mean the same thing wherever the focus is.
    #:
    #: The application's table is consulted before any widget's, which is
    #: what makes it the right place for exactly these and the wrong place for
    #: anything else: whatever is bound here is kept from the console, from
    #: the panels and from every dialog not yet written.  Ctrl+O is the way in
    #: and out of the console, and F10 is DOS Navigator's ``cmMenu``.
    #: **While a program holds the keyboard every one of them is disabled**
    #: (``Shell.program_has_keys``), so each falls through to it -- F10 is how
    #: ``htop`` and ``mc`` are left, and Ctrl+O is ``mc``'s own panel toggle
    #: and ``nano``'s Write Out.  DOS Navigator was not running at all while a
    #: program was, so nothing was kept back then either; the way out of a
    #: program is the program's own, or Ctrl+C.  F1
    #: is here because Help is not a panel's; it has no handler yet, so it is
    #: disabled, and a disabled command's key is left for whoever is next --
    #: the console's child gets F1 while Ctrl+O is showing it.  Ctrl+Q is not
    #: here: it is DOS Navigator's Quick view, and quitting is Alt+X.  Ctrl+F3
    #: (Manager > New) is, because it has to work with no file manager open --
    #: from the console, after the last one was closed.  Ctrl+F1 and Ctrl+F2
    #: (show/hide a side) are, because DOS Navigator's user screen took them
    #: too: from the console they bring the file manager back with that side
    #: alone.  ``Manager`` handles them first while it holds the keyboard.
    #:
    #: **Alt+X is here because a window can be closed.**  It lived on
    #: ``Manager`` once, and closing the file manager took the key with it.  It is still a desktop key rather than a global
    #: one, which is what ``Quit(desktop=True)`` and :meth:`enables` say: while
    #: a running program is over the windows it is Meta+X for the child.
    #:
    #: **Enter, Home and End are the command line's while it has text on it**,
    #: and the panel's otherwise -- ``FLPANELX.PAS`` sent ``cmExecCommandLine``
    #: from the panel's own Enter and fell back when the line was blank.  They
    #: are here because this table is asked before the panel is, and the
    #: command is disabled while the line is empty, which lets the key fall
    #: through to the list.
    #:
    #: **Tab completes while the command line has text**, by the same rule,
    #: and switches panels otherwise -- which is all it did in DOS Navigator.
    #:
    #: **Nothing here reaches past a modal**, and nothing here has to say so:
    #: navkit stands the application's table aside while one is up.
    keys = {
        "ctrl+o": ToggleConsole,
        "alt+f5": ShowUserScreen,
        "alt+shift+insert": ScreenGrab,
        "alt+f8": HistoryList,
        "ctrl+f3": NewManager,
        "alt+pageup": EditHistory,
        "alt+pagedown": ViewHistory,
        "ctrl+f1": HideLeft,
        "ctrl+f2": HideRight,
        "f1": Help,
        "f10": OpenMenu,
        #: Utilities > *Character table*, DN's ``kbCtrlB``.  An editor's ^B^V
        #: chord keeps Ctrl+B for itself, as DN's editor table did.
        "ctrl+b": AsciiTable,
        #: ≡ > *SmartPad (TM)*, DN's ``kbAltQ`` -- from anywhere the desktop is.
        "alt+q": OpenSmartpad,
        #: ≡ > *Game*, DN's ``kbAltF9`` -- *Navigator's game*, from anywhere.
        "alt+f9": Game,
        #: Utilities > *Calendar*, TVDEMO's calendar -- a departure, so a key
        #: of its own rather than DN's: nothing in Navigator binds F12.
        "ctrl+f12": OpenCalendar,
        "alt+x": Quit(desktop=True),
        "enter": ExecuteCommandLine,
        "home": CommandLineHome,
        "end": CommandLineEnd,
        "tab": CompleteCommandLine,
        #: *Quick run*, DN's Ctrl+Shift+F1 .. F10 (``QuickExecExternal``):
        #: ``quickrun.ini``'s ``[F1]`` .. ``[F10]``.
        **{f"ctrl+shift+f{number}": QuickRun(number) for number in range(1, 11)},
    }

    def enables(self, command: Command) -> bool:
        if self.shell.program_has_keys:
            return False
        if isinstance(command, Quit) and command.desktop:
            return not self._console_over_windows()
        return True

    async def on_toggle_console(self, event: ToggleConsole) -> bool:
        self.shell.toggle_console()
        return True

    async def on_refresh(self, event: Refresh) -> bool:
        """≡ > Refresh display: ``cmRefresh``, every cell sent again."""
        self.redraw()
        return True

    async def on_quit(self, event: Quit) -> bool:
        """Leave -- once asked, and once every editor with a changed text has been.

        ``cmQuit`` asked ``dlQueryExit`` first while *Exit confirmation* was
        ticked in Confirmations (``cfExitConfirm``), then went through every
        window's ``Valid`` as ``cmClose`` did, so one No or Cancel keeps
        Navigator running.  Asked from a task, for the reason every dialog is.
        """
        desktop = self.shell.desktop
        if SETTINGS.confirmations.exit or any(window.must_ask() for window in desktop.windows()):
            self.spawn(self._quit_asking())
            return True
        self.exit()
        return True

    async def _quit_asking(self) -> None:
        if SETTINGS.confirmations.exit:
            from navigator.widgets.shell.exit_dialog import ExitDialog

            answer = await ExitDialog().execute(self)
            if not answer:
                return
            if not answer["ask_again"]:
                # *Don't ask again*: Confirmations' *Exit confirmation* off,
                # and saved -- a file that cannot be written only means the
                # question comes back next time.
                SETTINGS.confirmations.exit = False
                with contextlib.suppress(OSError):
                    SETTINGS.save(section="confirmations")
        desktop = self.shell.desktop
        for window in reversed(desktop.windows()):
            if window.parent is not desktop or not window.must_ask():
                continue
            desktop.activate(window)
            if not await window.ask_to_close():
                return
        self.exit()

    def _console_over_windows(self) -> bool:
        """Whether a program on the console has the keys, over the windows.

        Only while a command runs: an idle console is showing output, and
        what is typed at it goes to the command line, as it would over the
        panels.
        """
        shell = self.shell
        return (
            shell.console_visible
            and shell.console.busy
            and shell.desktop.active_window is not None
        )

    async def on_completions_ready(self, event: CompletionsReady) -> bool:
        """The shell's answer to Tab: posted from the pty's reader."""
        self.shell.completions_ready(event)
        return True

    async def on_history_ready(self, event: HistoryReady) -> bool:
        """The shell's history, for Up on the console: posted from the pty's reader."""
        self.shell.history_ready(event.entries)
        return True

    async def on_history_chosen(self, event: HistoryChosen) -> bool:
        """What atuin's search chose: posted from the pty's reader."""
        self.shell.history_chosen(event.text)
        return True

    async def on_command_finished(self, event: CommandFinished) -> bool:
        """The command line's command is done: posted from the pty's reader."""
        self.shell.command_finished(event.status, event.cwd)
        return True

    def clipboard_unavailable(self) -> None:
        """Say, once, that a paste had to use Navigator's own copy."""
        from navml.widgets.dialog.dialog import Dialog

        prompt = tr(
            "The desktop's clipboard could not be read, so Navigator pasted its own last copy. "
            "Install xclip or xsel (X11), or wl-clipboard (Wayland), to share the clipboard "
            "with other programs."
        )
        self.spawn(Dialog(title=tr("Clipboard"), prompt=prompt, buttons="ok").execute(self))

    async def on_paste(self, event: PasteEvent) -> bool:
        """A paste goes where typing would: the running program, or the command line.

        Under a dialog it is the dialog's, and goes to its focused line; with
        an editor holding the keyboard it is the editor's.
        """
        if self.modal is not None:
            return False
        console = self.shell.console
        if console.busy:
            console.subshell.paste(event.text)
            return True
        if self.shell._editor_has_keys():
            return False  # an editor takes it, line breaks and all
        text = " ".join(event.text.splitlines())
        if text:
            self.shell.command_line.insert(text)
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """The console's scrollback, and nothing else.

        This used to hold the panels' mouse too -- hit-testing both of them,
        switching the active one, moving the cursor to the clicked row and
        scrolling on the wheel.  All four went away with the widget library
        rather than being moved: ``Control.on_mouse_click`` takes the keyboard
        on a press, which *is* switching now that the active panel is the
        focused one, and ``ListViewer`` owns the row click and the wheel.
        Routing by position is what puts them in the right panel.

        What is left genuinely needs the desktop: a wheel over the console
        scrolls its history, and the console is not a list.
        """
        if self.modal is not None:
            return False
        console = self.shell.console
        if not self.shell.console_visible or not event.is_wheel:
            return False
        if console.tracks_mouse:
            # The program turned the mouse on: the wheel is its to scroll.
            return False
        if not console.contains(event.x, event.y):
            return False
        console.scroll_lines(-WHEEL_LINES if event.button == "wheel_up" else WHEEL_LINES)
        return True


class PrintVersion(argparse.Action):
    """``--version``, printed verbatim.

    argparse's own ``version`` action runs the string through the help
    formatter, which word-wraps it to the terminal -- and the banner is mostly
    one long path, so on a narrow window it comes back broken across lines and
    cannot be copied out of a bug report.  Printing it directly is the whole
    of the difference.
    """

    def __init__(self, option_strings, dest, help=None):
        super().__init__(option_strings, dest, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        print(version_banner())
        parser.exit()


def version_banner() -> str:
    """What ``--version`` prints: the version, and *which copy* is running.

    The second half is the useful half.  Navigator can be installed three ways
    at once -- a system package under ``/usr/lib``, a pipx or ``pip --user``
    copy under ``~/.local``, and a checkout -- and ``~/.local/bin`` comes
    before ``/usr/bin`` on nearly every PATH, so the one that runs is often not
    the one that was just installed.  Printing the path turns that from a
    mystery into a glance, which is why ``pip --version`` has done it for
    years and why the format here follows it.

    The version itself prefers the distribution metadata over ``__version__``:
    they differ exactly when a checkout has been edited since it was
    installed, and metadata is absent precisely in the case where the source
    tree is the honest answer.
    """
    try:
        version = metadata.version("navigator-fm")
    except metadata.PackageNotFoundError:
        version = __version__
    here = Path(__file__).resolve().parent
    python = ".".join(str(n) for n in sys.version_info[:3])
    return f"nav {version} from {here} (python {python})"


def load_keybindings() -> None:
    """``keybindings.ini`` beside ``navigator.ini``: written with every
    default when missing, then read over the key tables.  A line that will
    not do is a warning before the screen is taken, and keeps its default."""
    try:
        keybindings.seed(Navigator)
    except OSError as error:
        print(f"nav: {keybindings.path()}: {error.strerror or error}", file=sys.stderr)
    for warning in keybindings.load(Navigator):
        print(f"nav: {warning}", file=sys.stderr)


def load_settings(path: Path | None = None) -> None:
    """Read the settings file into :data:`SETTINGS`, writing the defaults first if it is missing.

    Here rather than in :class:`Navigator`, so an application built by a test
    never touches the disk.  Every complaint goes to stderr before the screen
    is taken, and none of them stops Navigator starting: a setting it cannot
    read keeps its default, and a file it cannot write is simply not written.
    """
    path = path if path is not None else config_path()
    try:
        if not path.exists():
            SETTINGS.save(path)
        for warning in SETTINGS.load(path):
            print(f"nav: {warning}", file=sys.stderr)
    except (OSError, configparser.Error) as error:
        print(f"nav: {path}: {error}; using the default settings", file=sys.stderr)
        SETTINGS.reset()
        SETTINGS.path = path


def clear_histories() -> None:
    """``ClearHistories``: every unpinned entry gone -- each input line's
    list, the commands, the directories, and the files viewed and edited.
    What is pinned stays, as DN kept an entry flagged ``'+'``."""
    from navigator.models.edit_record import EditRecord
    from navigator.models.view_record import ViewRecord
    from navml.models.history_entry import HistoryEntry

    with DATABASE.transaction():
        for model in (HistoryEntry, ViewRecord, EditRecord):
            model.delete_where(pinned=False)


def open_database(path: Path | None = None) -> None:
    """Open the database every model uses, or carry on in memory.

    Beside :func:`load_settings` and for its reason: an application a test
    builds never opens a file.  A file that cannot be opened -- unwritable,
    locked, not a database -- costs this session its histories, not its start.
    """
    path = path if path is not None else database_path()
    try:
        DATABASE.open(path)
    except (OSError, sqlite3.Error) as error:
        print(f"nav: {path}: {error}; remembering nothing this session", file=sys.stderr)
        DATABASE.open()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nav", description=__doc__)
    parser.add_argument("left", nargs="?", help="the directory the left panel opens")
    parser.add_argument("right", nargs="?", help="the directory the right panel opens")
    parser.add_argument(
        "--version", action=PrintVersion,
        help="print the version, and which copy of Navigator is running",
    )
    parser.add_argument(
        "--theme", default=None, metavar="NAME",
        help="a colour scheme from navigator/styles/themes (default: the "
             f"settings file's, else {DEFAULT_THEME})",
    )
    parser.add_argument(
        "--list-themes", action="store_true", help="print the theme names and exit",
    )
    parser.add_argument(
        "--palette", choices=("dos", "terminal"), default=None,
        help="what a colour name in a theme means: the VGA register value DOS "
             "Navigator asked for (default), or whatever the terminal's own "
             "scheme paints for it (default: the settings file's)",
    )
    parser.add_argument(
        "--glyphs", choices=("auto", "ascii", "unicode", "nerd"), default=None,
        help="which characters the terminal's font can draw: `ascii' for plain "
             "+-| frames, `unicode' for box drawing, `nerd' to add a Nerd Font "
             "icon beside each name (default: the settings file's, else detect)",
    )
    parser.add_argument(
        "--language", default=None, metavar="CODE",
        help="the language to speak: a catalogue's code such as `lv', `en' "
             "(default: the settings file's, else $LANG)",
    )
    parser.add_argument(
        "--reprogram-palette", action="store_true",
        help="rewrite the terminal's sixteen colour registers to the DOS "
             "palette for as long as Navigator runs -- the only thing that "
             "helps on a terminal that names no other colours",
    )
    parser.add_argument(
        "--dim-modal", action=argparse.BooleanOptionalAction, default=None,
        help="paint what lies behind a dialog faint while the dialog is open "
             "(default: the settings file's, else on; experimental)",
    )
    parser.add_argument(
        "--on-error", choices=("dialog", "crash"), default=None,
        help="what an unexpected error does: show a box with its traceback, "
             "or quit printing it (default: the settings file's, else dialog); "
             "either way it is appended to errors.log beside the database",
    )
    parser.add_argument(
        "--config", metavar="PATH", type=Path, default=None,
        help=f"the settings file to read and save (default: {config_path()})",
    )
    parser.add_argument(
        "--database", metavar="PATH", type=Path, default=None,
        help=f"the database histories are kept in (default: {database_path()})",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    if args.list_themes:
        print("\n".join(theme_names()))
        return 0
    # Every program the console starts carries MARKER, so finding it means this
    # is a command typed inside a running Navigator; another terminal never has
    # it, which keeps this per session rather than a lock.  A departure: DN's
    # loader numbered nested copies (DNNumber) and let them run, but here one
    # would only draw itself inside the other's console.  `NAVIGATOR= nav'
    # still forces it.
    if os.environ.get(MARKER):
        print(
            "nav: Navigator is already running in this terminal; "
            "press Ctrl+O to return to it",
            file=sys.stderr,
        )
        return 1
    load_settings(args.config)
    # First, so a failure from here on -- and a hard crash, through
    # faulthandler -- leaves a record even when the screen it was on is gone.
    errorlog.open_log()
    # extensions.ini, viewers.ini, editors.ini, quickrun.ini, highlight.ini and
    # menu.ini beside it, written from their templates when missing, as
    # navigator.ini is.
    for problem in seed_associations():
        print(f"nav: {problem}", file=sys.stderr)
    load_keybindings()
    open_database(args.database)
    try:
        seed_bookmarks()
    except sqlite3.Error as error:
        print(f"nav: bookmarks: {error}", file=sys.stderr)
    # Startup's *Clear history*, as DN cleared its at the first start.
    if SETTINGS.startup.clear_history:
        try:
            clear_histories()
        except sqlite3.Error as error:
            print(f"nav: histories: {error}", file=sys.stderr)
    # A flag is this session's alone: it wins over the settings file and is
    # never written back to it.
    language.install((SETTINGS.path or config_path()).parent)
    language.apply(args.language if args.language is not None else SETTINGS.interface.language)
    appearance = SETTINGS.appearance
    if args.theme is not None:
        theme = args.theme
        try:
            theme_path(theme)
        except LookupError as exc:
            parser.error(str(exc))
    else:
        theme = appearance.theme
        try:
            theme_path(theme)
        except LookupError as exc:
            print(f"nav: {SETTINGS.path}: {exc}; using {DEFAULT_THEME}", file=sys.stderr)
            theme = DEFAULT_THEME
    # The user's palette (Options > Colors) goes over whichever theme it is.
    scheme, problem = user_scheme(theme)
    if problem is not None:
        print(f"nav: {problem}; the palette is left out", file=sys.stderr)

    # A theme that names its colours is transcribing a palette that left the
    # VGA registers alone, so `blue' means the value that adapter held and not
    # whatever this terminal calls blue -- which is why Navigator pins by
    # default where navkit, knowing nothing of DOS, does not.  Precedence runs
    # flag, then NAVKIT_PALETTE, then the settings file, then that default;
    # `detect' weighs the environment against the file's answer, and an
    # explicit flag is applied over what it decides.
    info = TerminalInfo.detect(
        is_tty=is_a_tty(sys.stdin, sys.stdout),
        palette=VGA_PALETTE if appearance.palette == "dos" else None,
        glyphs=tier_named(appearance.glyphs),
    )
    if args.palette is not None:
        info = replace(
            info, palette=VGA_PALETTE if args.palette == "dos" else None
        )
    # Same three-step precedence for the character repertoire, and the same
    # reason for spelling it out: `detect' has already weighed NAVKIT_GLYPHS
    # against what it found, so the flag is applied over that answer.
    if args.glyphs is not None and args.glyphs != "auto":
        info = replace(info, glyphs=tier_named(args.glyphs, info.glyphs))
    terminal = Terminal(info=info, reprogram_palette=args.reprogram_palette)

    left = Path(args.left).expanduser().resolve() if args.left else Path.cwd()
    right = Path(args.right).expanduser().resolve() if args.right else left
    dim_modal = appearance.dim_modal if args.dim_modal is None else args.dim_modal
    Navigator(left, right, scheme, terminal=terminal, dim_modal=dim_modal,
              given=bool(args.left), theme=theme, on_error=args.on_error).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
