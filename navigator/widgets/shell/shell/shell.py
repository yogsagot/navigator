"""The handlers behind ``shell.nml``.

What the document says is the two bars, the command line and the two layers
between them; what is left here is opening the file manager on the desktop,
Ctrl+O, and running what is typed on the command line.

This file never names the generated class.  ``class Shell(DockLayout)`` is
what a Python-only widget would say too, and it is the base the markup's
``Shell(DockLayout):`` head names.
"""

from __future__ import annotations

import asyncio
import os
import random
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Callable

from navkit.commands import Command
from navkit.events import Event, KeyEvent
from navkit.i18n import tr
from navkit.reactive import bind, computed, effect, reactive, untracked
from navkit.screen import Surface
from navkit.widget import Widget
from navkit.stylesheet import Stylesheet, StylesheetError
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.menu.commands import OpenMenu
from navml.history import HISTORY

from navigator.commands import AsciiTable, OpenSmartpad, ScreenGrab, ShowUserScreen
from navigator.lib.drives import DriveGone, Location, Site, drive_of
from navigator.lib.system import fuzzy
from navigator.lib.system.subshell import CommandFinished, CompletionsReady, HistoryChosen, HistoryReady, PickChosen
from navigator.lib.system.title import window_title
from navigator.widgets.manager.commands import Calculator, HideLeft, HideRight, ToggleMark, UserMenu
from navigator.widgets.shell.commands import (
    EditLinks,
    Game,
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
    SetupLink,
    OpenCalendar,
    ToggleTrashCan,
    OpenTrash,
    EmptyTrash,
    SaversSetup,
    CountrySetup,
    ScreenRest,
    About,
    ChangeColors,
    DriveInfoSetup,
    ColumnDefaults,
    HighlightGroups,
    EditQuickRun,
    ExtFileEdit,
    EditHGL,
    EditMacros,
    ExternalViewers,
    ExternalEditors,
    QuickRun,
    CommandLineEnd,
    CommandLineHome,
    CompleteCommandLine,
    EditHistory,
    EditorDefaults,
    ExecuteCommandLine,
    ExecuteCommandLineInWindow,
    FileManagerDefaults,
    EnvEdit,
    ExecuteOsCommand,
    LoadColors,
    LoadDesktop,
    SaveDesktop,
    StoreColors,
    SystemInfo,
    FileManagerSetup,
    HistoryList,
    FuzzyHistory,
    InsertName,
    OpenCommandPalette,
    InsertPath,
    InterfaceSetup,
    KeyBindingsSetup,
    LocalMenuFileEdit,
    MenuFileEdit,
    NewManager,
    OpenEdit,
    OpenTreeWindow,
    OpenView,
    OpenUsageWindow,
    OpenVolumesWindow,
    OpenProcessWindow,
    OpenServiceWindow,
    OpenMonitorWindow,
    SetupConfirmation,
    Settings,
    StartupSetup,
    SystemSetup,
    ToggleMarkBySpace,
    ViewHistory,
)
from navigator.widgets.shell.command_line.command_line import HISTORY_ID
from navml.widgets.dialog.date_button import CalendarView
from navml.widgets.dialog.file_list import FileInfoPane
from navml.widgets.layout.dock_layout import DockLayout

from navigator.lib.appearance import filetypes
from navigator.lib.config import country
from navigator.lib.config.associations import EDITORS, EXTENSIONS, HIGHLIGHT, QUICK_RUN, VIEWERS
from navigator.lib.appearance.scheme import DEFAULT_THEME, default_scheme
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager

if TYPE_CHECKING:
    from navigator.widgets.editor.edit_window import FileSaved

#: The most candidates a Tab puts in its list; ``compgen -c`` on one letter
#: can be thousands.
MAX_COMPLETIONS = 500

#: What a file name has to have escaped to reach a command as one word.
_SHELL_SPECIAL = set(" \t'\"\\$&;|<>()*?[]!#{}`")


class _Toasts:
    """The toasts up, oldest first: where each stands, the newest lowest."""

    items: tuple[Any, ...] = reactive(())

    def above(self, toast: Any) -> int:
        """How many toasts high *toast*'s bottom is: itself and every newer one."""
        items = self.items
        return len(items) - items.index(toast) if toast in items else 1

    def drop(self, toast: Any) -> None:
        self.items = tuple(item for item in self.items if item is not toast)


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

    async def on_load_desktop(self, event: LoadDesktop) -> bool:
        self.spawn(self.load_desktop())
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

    # -- the palette ------------------------------------------------------------------

    async def _palette_base(self) -> tuple[list[tuple[str, str]], dict[str, str]] | None:
        """The theme's sheets, read on a thread, and every entry's variables
        as the theme alone gives them -- what a palette is the difference
        from.  None, said so, if the theme cannot be read."""
        import asyncio

        from navigator.lib.appearance.palette import entry_values
        from navigator.lib.appearance.scheme import scheme_from, theme_sources

        try:
            sources = await asyncio.to_thread(theme_sources, self.theme)
        except (OSError, LookupError) as error:
            await self._palette_failed(tr("Cannot read the theme: {error}").format(error=getattr(error, 'strerror', None) or error))
            return None
        return sources, entry_values(scheme_from(sources).variables)

    async def _palette_failed(self, prompt: str) -> None:
        await Dialog(title=tr("Error"), prompt=prompt, buttons="ok").execute(self.application)

    async def _keep_palette(self, sources: list[tuple[str, str]], palette: dict[str, str]) -> None:
        """*palette* (what differs from the theme) painted and kept as
        ``palette.nss`` -- DN's ``cmUpdateConfig`` after its palette changed."""
        import asyncio

        from navigator.lib.appearance.palette import render_palette, save_palette
        from navigator.lib.appearance.scheme import palette_source, scheme_from

        self.stylesheet = scheme_from(sources, palette_source(render_palette(palette, "palette")))
        try:
            await asyncio.to_thread(save_palette, palette, self.theme)
        except OSError as error:
            await self._palette_failed(tr("Cannot save the palette: {error}").format(error=error.strerror or error))

    async def on_change_colors(self, event: ChangeColors) -> bool:
        self.spawn(self.change_colors())
        return True

    async def change_colors(self) -> None:
        """Options > Colors: ``ChangeColors`` -- the dialog over the palette as
        it is, every change painted as it is made; OK keeps it, Cancel puts
        the screen back as it was."""
        from navigator.lib.appearance.palette import differences, entry_values, render_palette
        from navigator.lib.appearance.scheme import palette_source, scheme_from
        from navigator.widgets.setup.colors_dialog import ColorsDialog

        base = await self._palette_base()
        if base is None:
            return
        sources, theme = base
        before = self.stylesheet

        def apply(values: dict[str, str]) -> None:
            text = render_palette(differences(theme, values), "palette")
            try:
                self.stylesheet = scheme_from(sources, palette_source(text))
            except StylesheetError:
                pass  # a value the sheet refuses: the screen stays as it was

        answer = await ColorsDialog(entry_values(before.variables), apply).execute(self.application)
        if answer is None:
            self.stylesheet = before
            return
        await self._keep_palette(sources, differences(theme, answer))

    async def on_store_colors(self, event: StoreColors) -> bool:
        self.spawn(self.store_colors())
        return True

    async def store_colors(self) -> None:
        """Options > Store palette: ``StoreColors`` -- every entry's colours
        and attributes written as a sheet, named in a file box opened on the
        user's themes (DN's ``COLORS\\*.PAL``), whose name ``--theme`` then
        takes.  A file that is there is asked about first."""
        import asyncio

        from navml.widgets.dialog.file_dialog import FileDialog

        from navigator.lib.appearance.palette import entry_values, render_palette, user_themes, write_sheet

        directory = user_themes()
        try:
            await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        except OSError as error:
            await self._palette_failed(tr("Cannot make {path}: {error}").format(path=directory, error=error.strerror or error))
            return
        name = await FileDialog(title=tr("Store Color Palette"), label=tr("~F~ile name"), history_id="colors",
                                directory=directory, wildcard="*.nss").execute(self.application)
        if not name:
            return
        path = Path(name)
        if not path.suffix:
            path = path.with_suffix(".nss")
        if await asyncio.to_thread(path.exists):
            answer = await Dialog(title=tr("Warning"),
                                  prompt=tr("File {name}\nalready exists.\nOK to overwrite it?").format(name=path.name),
                                  buttons="yes-no").execute(self.application)
            if answer is not True:
                return
        text = render_palette(entry_values(self.stylesheet.variables), f"{path.stem} -- a palette stored by Navigator")
        try:
            await asyncio.to_thread(write_sheet, path, text)
        except OSError as error:
            await self._palette_failed(tr("Cannot write {path}: {error}").format(path=path, error=error.strerror or error))

    async def on_load_colors(self, event: LoadColors) -> bool:
        self.spawn(self.load_colors())
        return True

    async def load_colors(self) -> None:
        """Options > Load palette: ``LoadColors`` -- a sheet picked in a file
        box (the user's themes if there are any, else the ones Navigator
        ships), its colours put over the theme and kept as the palette, as
        DN's ``LoadPalFromFile`` replaced the one in ``DN.CFG``.  One that does
        not parse is said so and changes nothing.  With *Preview palette*
        ticked the box paints each file the cursor stops on; cancelling it
        puts the screen back as it was."""
        import asyncio

        from navigator.lib.appearance.palette import differences, entry_values, user_themes
        from navigator.lib.appearance.scheme import THEMES, scheme_from
        from navigator.widgets.setup.palette_file_dialog import PaletteFileDialog

        def start() -> Path:
            mine = user_themes()
            return mine if any(mine.glob("*.nss")) else THEMES

        base = await self._palette_base()
        if base is None:
            return
        sources, theme = base
        before = self.stylesheet

        def preview(shown: tuple[Path, str] | None) -> None:
            if shown is None:
                self.stylesheet = before
                return
            path, text = shown
            try:
                self.stylesheet = scheme_from(sources, (str(path), text))
            except StylesheetError:
                pass  # not a palette: the screen stays as it was

        directory = await asyncio.to_thread(start)
        name = await PaletteFileDialog(title=tr("Load Color Palette"), label=tr("~F~ile name"), history_id="colors",
                                       directory=directory, wildcard="*.nss", ok_text=tr("~O~pen"),
                                       preview=preview).execute(self.application)
        self.stylesheet = before
        if not name:
            return
        path = Path(name)
        try:
            text = await asyncio.to_thread(path.read_text, encoding="utf-8")
        except (OSError, UnicodeError) as error:
            await self._palette_failed(tr("Cannot read {path}: {error}").format(path=path, error=getattr(error, 'strerror', None) or error))
            return
        try:
            loaded = scheme_from(sources, (str(path), text))
        except StylesheetError as error:
            await self._palette_failed(tr("Not a palette:\n{error}").format(error=error))
            return
        await self._keep_palette(sources, differences(theme, entry_values(loaded.variables)))

    async def on_execute_os_command(self, event: ExecuteOsCommand) -> bool:
        self.spawn(self.execute_os_command())
        return True

    async def execute_os_command(self) -> None:
        """File > Execute OS command: ``ExecDOSCmd`` -- DN's ``InputBox``, opened
        on the file at the active panel's cursor if it is one to run (followed
        by a blank, for its arguments), in the command line's history; OK runs
        it as though it had been typed there.  *OS* where DN's title said *DOS*.
        *In a window* (not DN's) runs it in a window of its own instead, opened
        *Zoomed* and *Modal* as ticked."""
        from navigator.widgets.shell.execute_command_dialog import ExecuteCommandDialog

        text = ""
        manager = self.active_manager
        entry = manager.active_panel.selected if manager is not None else None
        if entry is not None and entry.is_executable:
            name = str(entry.path_in(manager.active_panel.path)) if entry.directory is not None else entry.name
            text = _escape(name) + " "
        box = ExecuteCommandDialog(text, zoomed=SETTINGS.system.command_window_zoomed,
                                   modal=SETTINGS.system.command_window_modal)
        choice = await box.execute(self.application)
        if choice is None or not choice.command.strip():
            return
        if choice.in_window:
            HISTORY.add(HISTORY_ID, choice.command)
            self.run_in_window(choice.command, zoomed=choice.zoomed, modal=choice.modal)
        else:
            self.run_command(choice.command)

    async def on_system_info(self, event: SystemInfo) -> bool:
        self.spawn(self.system_info())
        return True

    async def system_info(self) -> None:
        """Utilities > System Information: the machine read on a thread
        (:func:`navigator.lib.system.sysinfo.gather`), then DN's dialog."""
        import asyncio

        from navigator.lib.system.sysinfo import gather
        from navigator.widgets.shell.system_info_dialog import SystemInfoDialog

        facts = await asyncio.to_thread(gather)
        await SystemInfoDialog(facts).execute(self.application)

    async def on_env_edit(self, event: EnvEdit) -> bool:
        self.spawn(self.edit_environment())
        return True

    async def edit_environment(self) -> None:
        """Utilities > Edit environment: ``EditDOSEvironment`` over Navigator's
        own variables; OK makes what changed so there (``navigator.lib.system.environ``)
        and in the console's shell, unseen (``Subshell.set_environment``)."""
        import os

        from navigator.lib.system.environ import apply, changes
        from navigator.widgets.shell.environment_dialog import EnvironmentDialog

        before = dict(os.environ)
        after = await EnvironmentDialog(before).execute(self.application)
        if after is None:
            return
        found = changes(before, after)
        apply(found)
        self.console.subshell.set_environment(found)

    async def on_fuzzy_history(self, event: FuzzyHistory) -> bool:
        self.fuzzy_history()
        return True

    async def on_open_command_palette(self, event: OpenCommandPalette) -> bool:
        self.spawn(self.command_palette())
        return True

    async def command_palette(self) -> None:
        """Alt+Shift+P: the command chosen in ``CommandPalette``, run from
        where the keyboard was before the box opened -- its enabled state and
        keys were asked from there too."""
        from navigator.widgets.shell.command_palette import CommandPalette

        app = self.application
        if app is None:
            return
        behind = app.focused
        chosen = await CommandPalette(behind=behind).execute(app)
        if chosen is not None:
            await app.run_command(chosen, start=behind)

    async def on_history_list(self, event: HistoryList) -> bool:
        self.spawn(self.command_history())
        return True

    async def command_history(self) -> None:
        """Alt+F8: ``CmdHistory`` -- *Run* puts the command on the line and runs
        it, *Drop* puts it there alone, the cursor at its end."""
        from navigator.widgets.shell.command_history_dialog import CommandHistoryDialog

        answer = await CommandHistoryDialog().execute(self.application)
        if answer is None:
            return
        how, command = answer
        if how == "run":
            self.run_command(command)
        else:
            self.command_line.set_text(command)

    #: Whether the grabber has said how it works this session (DN's ``NotMessage``).
    _grabber_told = False

    async def on_screen_grab(self, event: ScreenGrab) -> bool:
        self.spawn(self.screen_grab())
        return True

    async def screen_grab(self) -> None:
        """Shift+Alt+Ins: ``ScreenGrabber`` -- DN's ``dlGrabWelcome`` the first
        time, then the rectangle (:mod:`navigator.widgets.shell.grabber`), and
        what Enter took on the clipboard, a line a row."""
        from navigator.widgets.shell.grabber import ScreenGrabber

        app = self.application
        if app is None or any(isinstance(child, ScreenGrabber) for child in app.root.children):
            return  # DN's ``Here``: one at a time
        if not type(self)._grabber_told:
            type(self)._grabber_told = True
            await Dialog(
                title=tr("Information"),
                prompt=tr("Use arrows to move area\nUse Shift-Arrows to change area size\n\n"
                          "After selecting press Enter to place\narea image into the clipboard"),
                buttons="ok",
            ).execute(app)
        rows = await ScreenGrabber().execute(app)
        if rows:
            app.copy_to_clipboard("\n".join(rows))

    async def on_show_user_screen(self, event: ShowUserScreen) -> bool:
        """Alt+F5, ≡ > *User screen*: ``ShowUserScreen`` -- the console, until
        any key or click, which then goes nowhere else and the windows come
        back.  Already showing, it stays; with *Use internal terminal* off it
        is Ctrl+O's handing over of the real terminal."""
        if self.console_visible:
            return True
        if not SETTINGS.system.internal_terminal:
            self.toggle_console()
            return True
        app = self.application
        if app is None:
            return True
        self.toggle_console()
        if not self.console_visible:
            return True
        self.spawn(self._peek(app))
        return True

    async def _peek(self, app: Any) -> None:
        await UserScreenPeek().execute(app)
        if self.console_visible:
            self.toggle_console()

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
        if showing and not SETTINGS.system.internal_terminal and self.relay_terminal():
            return
        if not showing and desktop.active_window is None:
            return
        if showing:
            self._show_console()
        else:
            self.console_visible = False
            desktop.activate(desktop.active_window)

    def _show_console(self) -> None:
        """The console up, holding the keyboard: always this one, never the
        real terminal lent (System Setup's *Internal terminal* off)."""
        self.console.start()
        window = self.desktop.active_window
        app = self.application
        if window is not None and app is not None and window._holds(app.focused):
            window._saved_focus = app.focused
        self.console_visible = True
        self.console.focus()

    # -- the real terminal, Midnight Commander's way ---------------------------------

    def relay_terminal(self) -> bool:
        """Hand the real terminal to the shell: System Setup's *Use internal terminal* off.

        Midnight Commander's Ctrl+O, a departure from DN's for whoever wants
        it.  Navigator leaves full-screen mode, so the terminal shows what it
        showed before Navigator started and everything the shell printed on
        it since; the shell's output goes straight there and every key
        straight to the shell, until Ctrl+O comes back
        (:meth:`_relayed_input`).  False, and nothing done, without a real
        terminal to hand over.
        """
        app = self.application
        if app is None or app.released or not app.terminal.is_tty:
            return False
        console = self.console
        console.relayed = True
        # Now rather than at the next flush: the shell is about to draw its
        # prompt, and should draw it at the terminal's width.
        console._follow_size()
        console.start()
        app.release_terminal(self._relayed_input)
        console.subshell.start_relay(app.terminal.write_bytes)
        return True

    def _relayed_input(self, data: bytes) -> bytes:
        """What is typed while the shell has the real terminal.

        Ctrl+O takes it back -- as the plain control byte, or as the kitty
        protocol spells it if a program turned that on -- unless a command
        the command line sent is running: that has every key, Ctrl+O
        included, as it does on the console.  What follows Ctrl+O is
        Navigator's again.
        """
        subshell = self.console.subshell
        if not subshell.busy:
            for key in (b"\x0f", b"\x1b[111;5u"):
                cut = data.find(key)
                if cut != -1:
                    if cut:
                        subshell.relay_input(data[:cut])
                    self.end_relay()
                    return data[cut + len(key):]
        subshell.relay_input(data)
        return b""

    def end_relay(self, *, follow: bool = True) -> None:
        """Take the real terminal back, and repaint; *follow* moves the panel after the shell.

        A ``cd`` typed at the shell moves the active panel, and both re-read
        whatever the shell did to them -- what a finished command does.
        """
        app = self.application
        if app is None or not app.released:
            return
        console = self.console
        console.subshell.stop_relay()
        console.relayed = False
        console._follow_size()
        app.reclaim_terminal()
        if follow:
            self._follow_shell(console.subshell.cwd)

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
        # Ctrl+Ins over a selection in the console copies that, not the line.
        if self.console.copy_key(event):
            return True
        # ``ouiHideCmdline``: a hidden line takes no keys at all, as
        # ``TCommandLine.HandleEvent`` took none.
        if SETTINGS.interface.hide_command_line:
            return False
        if self._console_is_the_terminal() and await self._terminal_key(event):
            return True
        if self._panel_keeps(event):
            return False
        if await self.command_line.on_key(event):
            return True
        # *ESC for user screen* (``ouiEsc``): Esc with nothing on the line
        # sends ``cmShowUserScreen`` -- here Ctrl+O's console, which Esc
        # puts away again as any key closed DN's user screen.  A line with
        # text was cleared by the Esc above instead.
        if event.matches("escape") and SETTINGS.interface.esc_user_screen:
            self.toggle_console()
            return True
        return False

    def _panel_keeps(self, event: KeyEvent) -> bool:
        """A plain arrow, Home or End a panel declined, with *Use arrows* off:
        not the line's either -- DN's ``TSpecScroll`` let it go nowhere."""
        from navigator.widgets.manager.panel import Panel

        app = self.application
        return (
            not SETTINGS.file_manager.use_arrows
            and event.key in Panel.LINE_KEYS
            and not (event.shift or event.ctrl or event.alt)
            and app is not None
            and isinstance(app.focused, Panel)
        )

    # -- the console's history keys --------------------------------------------

    def _console_is_the_terminal(self) -> bool:
        """The console is up, idle and holding the keyboard: it stands for the terminal.

        Then Up, Down and Ctrl+R mean what they mean at a shell prompt.  With
        the panels up Up is the panel's, and Ctrl+R re-reads it, as in DOS
        Navigator.
        """
        console = self.console
        return self.console_visible and console.focused and not console.busy

    async def _terminal_key(self, event: KeyEvent) -> bool:
        subshell = self.console.subshell
        if event.matches("up"):
            if subshell.up_binding == "atuin":
                return self._search_history(["--shell-up-key-binding", "--keymap-mode=emacs"])
            self._walk_history(+1)
            return True
        if event.matches("down"):
            self._walk_history(-1)
            return True
        if event.matches("ctrl+r") and subshell.search_binding == "atuin":
            return self._search_history(["--keymap-mode=emacs"])
        if event.matches("ctrl+r") and subshell.search_binding == "fzf":
            self.fuzzy_history()
            return True
        if event.matches("alt+c") and subshell.cd_binding == "fzf":
            self.spawn(self.pick("cd", "", (), self._cd_chosen))
            return True
        if event.matches("ctrl+t") and subshell.file_binding == "fzf":
            self.spawn(self.pick("files", "", (), self._files_chosen))
            return True
        return False

    def _search_history(self, args: list[str]) -> bool:
        """Run atuin on the console, as the user's own Up or Ctrl+R would."""
        app = self.application

        def chosen(text: str) -> None:
            if app is not None and app.is_running:
                app.post_event(HistoryChosen(text))
            else:
                self.history_chosen(text)

        self._walk = None
        return self.console.subshell.search_history(self.command_line.value, args, chosen)

    def history_chosen(self, text: str) -> None:
        """atuin's answer: onto the line, or run at once if it said so (Tab vs Enter)."""
        accept = "__atuin_accept__:"
        if text.startswith(accept):
            self.run_command(text[len(accept) :])
        elif text:
            self.command_line.set_text(text)

    # -- fzf and zoxide (a departure: DOS Navigator had neither) --------------

    def fuzzy_refusal(self) -> str:
        """Why fzf cannot be run on the console now, ``""`` when it can."""
        subshell = self.console.subshell
        if self.console.busy or self._picking is not None:
            return tr("A program in the console has the keys")
        if not subshell.has_fzf:
            # Asked of the shell, whose rc may put it on PATH; before the
            # shell is up, of Navigator's own.
            if subshell.is_running or fuzzy.program("fzf") is None:
                return tr("fzf is not installed, or the shell is not bash or zsh")
        return ""

    def fuzzy_history(self) -> None:
        """Alt+Shift+F8, and the console's Ctrl+R where the rc binds it to fzf:
        the command line's history and the shell's, newest first, searched by
        fzf for what is on the line; the one chosen replaces it, as fzf's
        Ctrl+R leaves it to be run."""
        self.spawn(self.pick("history", self.command_line.value, HISTORY.entries(HISTORY_ID),
                             lambda lines: self.command_line.set_text(lines[0])))

    async def jump_directory(self, then: Callable[[str], None]) -> None:
        """Alt+J: zoxide's directories by frecency, then the panels' history
        (Alt+Backspace), searched by fzf; *then* gets the one chosen."""
        await self.pick("directories", "", HISTORY.entries("directories"), lambda lines: then(lines[0]))

    async def pick(self, kind: str, line: str, entries: Any,
                   then: Callable[[list[str]], None]) -> None:
        """Run fzf on the console over *kind* (``Subshell.PICKS``), *line* its
        query and *entries* Navigator's own list for it, and *then* what was
        chosen -- not called if nothing was.  The console comes up for it, and
        goes again after, if it was not up."""
        subshell = self.console.subshell
        if self.fuzzy_refusal():
            return
        if not self.console_visible:
            # Started now if it was not: the pick needs its prompt.
            self.console.start()
        listing = subshell.scratch(f"{kind}.list")
        entries = [entry for entry in entries if entry and "\n" not in entry]
        if listing is not None and entries:
            try:
                await asyncio.to_thread(listing.write_text, "".join(entry + "\n" for entry in entries))
            except OSError:
                listing = None
        else:
            listing = None
        app = self.application

        def chosen(text: str) -> None:
            if app is not None and app.is_running:
                app.post_event(PickChosen(text))
            else:
                self.pick_chosen(text)

        shown = not self.console_visible
        if shown:
            self._show_console()
        self._walk = None
        self._picking = (then, shown)
        if not subshell.pick(kind, line, chosen, listing):
            self._picking = None
            if shown:
                self.toggle_console()

    def pick_chosen(self, text: str) -> None:
        """fzf's answer: the console goes if it came up for the pick, and the
        choice -- a line each -- to whoever asked."""
        picking, self._picking = self._picking, None
        if picking is None:
            return
        then, shown = picking
        if shown and self.console_visible:
            self.toggle_console()
        elif self.console_visible:
            self.console.focus()
        lines = [line for line in text.splitlines() if line.strip()]
        if lines:
            then(lines)

    def _cd_chosen(self, lines: list[str]) -> None:
        """The console's Alt+C: the active panel goes where fzf's ``cd`` would
        have taken the shell -- and the shell follows it there, silently."""
        manager = self.active_manager
        if manager is None:
            return
        place = Path(os.path.expanduser(lines[0]))
        if not place.is_absolute():
            base = self.console.subshell.cwd or self._command_directory()
            if base is None:
                return
            place = base / place

        async def go() -> None:
            await manager._go_to(manager.active_panel, os.path.normpath(place))
            if self.console_visible:
                # Going focuses the panel; the console it is behind keeps the keys.
                self.console.focus()

        self.spawn(go())

    def _files_chosen(self, lines: list[str]) -> None:
        """The console's Ctrl+T: the files chosen onto the line, as Ctrl+Enter puts a name."""
        for line in lines:
            self.command_line.insert_name(_escape(line))

    def _walk_history(self, step: int) -> None:
        """Up and Down through the shell's history, as readline walks it.

        The history is the shell's, so it holds what was typed in the user's
        other terminals as well; it is asked for afresh at the first Up of a
        walk, and a walk ends when the line is edited.  A shell that cannot be
        asked -- ``sh``, or none running -- walks the command line's own.
        """
        line = self.command_line
        if self._walk is not None and line.value != self._walk[3]:
            self._walk = None
        if self._walk is not None:
            self._step_history(step)
            return
        if step < 0:
            return
        app = self.application

        def ready(entries: list[str]) -> None:
            if app is not None and app.is_running:
                app.post_event(HistoryReady(tuple(entries)))
            else:
                self.history_ready(tuple(entries))

        if not self.console.subshell.history(ready):
            self.history_ready(tuple(HISTORY.entries(HISTORY_ID)))

    def history_ready(self, entries: tuple[str, ...]) -> None:
        """The history arrived: the walk starts, one step back."""
        line = self.command_line
        self._walk = (list(entries), -1, line.value, line.value)
        self._step_history(+1)

    def _step_history(self, step: int) -> None:
        entries, index, typed, _ = self._walk
        index = min(max(index + step, -1), len(entries) - 1)
        value = entries[index] if index >= 0 else typed
        self.command_line.set_text(value)
        self._walk = (entries, index, typed, value)

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

    def _size_histories(self) -> None:
        """Interface's *History size* is how long every input-line list grows.

        navml's store keeps DN's 20 unless told otherwise, and knows nothing of
        Navigator's settings, so it is told from here.
        """
        HISTORY.limit = max(1, SETTINGS.interface.history_size)

    def _use_highlight_groups(self) -> None:
        """*Highlight groups*' masks put in force, and every panel read again
        when they changed: ``SetHighlightGroups``' ``cmPanelReread``, since a
        row's colour and its place under *Group* both come from them.

        ``filetypes`` knows nothing of Navigator's settings, so it is told from here.
        """
        section = SETTINGS.highlight_groups
        masks = {key: getattr(section, key) for key in filetypes.CUSTOM}
        # What this shell last saw rather than what ``use_masks`` answers: the
        # masks are the process's, and another shell may have put them in force.
        seen, self._highlight_masks = self._highlight_masks, masks
        filetypes.use_masks(masks)
        with untracked():
            if seen is not None and seen != masks and self.desktop is not None:
                for window in self.desktop.windows():
                    if isinstance(window, Manager):
                        for panel in window.all_panels:
                            panel.reload()

    def _choose_clipboard(self) -> None:
        """System Setup's *Use system clipboard*: the desktop's, or Navigator's own.

        navkit's application knows nothing of Navigator's settings either.
        """
        app = self.application
        if app is not None:
            app.system_clipboard = SETTINGS.system.system_clipboard

    def _front_location(self) -> Location | None:
        """Where the active panel is in the file manager in front, if one is open."""
        window = self.desktop.active_window
        manager = window if isinstance(window, Manager) else self.active_manager
        return manager.active_panel.location if manager is not None else None

    def _front_directory(self) -> Path | None:
        """The active panel's directory in the file manager in front, if one is
        open and it is on the local disk: the shell cannot follow a panel onto
        another drive, and stays in the last local directory it was in."""
        where = self._as_the_shell_sees(self._front_location())
        return where.local if where is not None and where.is_local else None

    def _front_remote(self) -> Location | None:
        """The active panel's place in front when it is on another drive."""
        where = self._as_the_shell_sees(self._front_location())
        return where if where is not None and not where.is_local else None

    def _as_the_shell_sees(self, where: Location | None) -> Location | None:
        """*where*, or its own place on the disk if it is ``root:`` and the
        console's shell is root's: that shell can be there, so the command
        line shows its prompt, follows the panel there and runs there."""
        if where is not None and self.console.root:
            from navigator.lib.drives import root

            return root.on_disk(where)
        return where

    @staticmethod
    def _remote_name(where: Location) -> str:
        """What the prompt and the title call a place on another drive: its
        drive's ``GetDir``."""
        try:
            return drive_of(where).get_dir(where)
        except DriveGone:
            return str(where)

    def _follow_panel(self) -> None:
        """Keep the idle shell where the panel is, so its prompt names that directory."""
        where = self._front_directory()
        if where is not None:
            self.console.subshell.sync(where)

    def _name_window(self) -> None:
        """Keep the terminal's title on the directory the prompt names."""
        remote = self._front_remote()
        if remote is not None:
            application = self.application
            if application is not None:
                application.title = window_title(None, self.console.root).replace(
                    " — ", f" {self._remote_name(remote)} — ", 1)
            return
        where = self._front_directory()
        if where is None:
            where = self.console.subshell.cwd or self.console.cwd
        title = window_title(Path(where) if where is not None else None, self.console.root)
        application = self.application
        if application is not None:
            application.title = title

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

    def _command_directory(self) -> Path | None:
        """Where a command runs: the active panel's directory -- or, with the
        panel on another drive, where the shell last was on the disk."""
        manager = self.active_manager
        if manager is not None:
            where = self._as_the_shell_sees(manager.active_panel.location)
            if where is not None and where.is_local:
                return where.local
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

        Or a command in a window of its own is running and has the keyboard
        (``TerminalView``): it gets every key the same way, but for the ones
        that bring another window forward, which it declines itself.
        """
        if self.console.busy and self.console.focused:
            return True
        from navigator.widgets.shell.terminal_view import TerminalView

        app = self.application
        focused = app.focused if app is not None else None
        return isinstance(focused, TerminalView) and focused.busy

    def refusal(self, command: Command) -> str:
        """Enter, Home and End are the command line's only while it has text.

        And Enter only while no command is running: the program has the keys
        then, and a second command would be typed at it.  Nothing here runs
        while a program holds the keyboard (:attr:`program_has_keys`).
        """
        if self.program_has_keys:
            return tr("A program in the console has the keys")
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
            if self.command_line.value:
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

    def _editor_has_keys(self) -> bool:
        """Whether the keyboard is with a widget that edits text of its own.

        An editor wants Enter, Home, End and Tab for itself, and would lose
        them to a command line with text on it -- the application's table is
        asked before the tree.  DN's command line lived in the file panel's
        window and never met the editor's keys.
        """
        app = self.application
        if app is None or app.focused is None:
            return False
        widget = app.focused
        while widget is not None:
            if widget.edits_text:
                return True
            widget = widget.parent
        return False

    async def on_file_saved(self, event: FileSaved) -> bool:
        """``FileChanged``: every panel showing the saved file's directory re-reads.

        ``highlight.ini`` saved colours every open text again by its new rules.
        """
        from navigator.lib.config import associations
        from navigator.widgets.editor.file_editor import FileEditor
        from navigator.widgets.viewer.file_viewer import FileViewer

        directory = event.path.parent
        rules = event.path == associations.path_of(HIGHLIGHT)
        for window in self.desktop.windows():
            if isinstance(window, Manager):
                for panel in window.all_panels:
                    if panel.location == Location.of(directory):
                        panel.reload()
        for window in self.desktop.windows():
            # Utilities > Services: a unit file it opened, saved -- daemon-reload.
            saved = getattr(window, "unit_file_saved", None)
            if saved is not None:
                saved(event.path)
        if rules:
            pending = [self.desktop]
            while pending:
                widget = pending.pop()
                if isinstance(widget, (FileEditor, FileViewer)):
                    widget.rehighlight()
                pending.extend(widget.children)
        return True

    async def on_command_line_home(self, event: CommandLineHome) -> bool:
        self.command_line.home()
        return True

    async def on_command_line_end(self, event: CommandLineEnd) -> bool:
        self.command_line.end()
        return True

    # -- completion ------------------------------------------------------------

    async def on_complete_command_line(self, event: CompleteCommandLine) -> bool:
        """Tab: ask the shell what the word at the caret could become.

        The answer comes back later, posted from the pty's reader, and is
        applied by :meth:`completions_ready` -- only if the line is still what
        it was asked about.
        """
        self._ask_completions()
        return True

    def _ask_completions(self) -> None:
        """Ask the shell about the word at the caret; the answer is posted back."""
        line = self.command_line
        value, point = line.value, line.cursor
        app = self.application

        def answered(start: int, candidates: list[str]) -> None:
            ready = CompletionsReady(value, point, start, tuple(candidates))
            if app is not None and app.is_running:
                app.post_event(ready)
            else:
                self.completions_ready(ready)

        self.console.subshell.complete(value, point, self._command_directory(), answered)

    @property
    def completion_list(self) -> Any:
        """The completions drop-down, while it is open."""
        window = self._completion_list
        return window if window is not None and window.parent is not None else None

    def completions_ready(self, event: CompletionsReady) -> None:
        """Apply the shell's answer as readline would: complete, extend, or list.

        One candidate replaces the word and ends it -- with ``/`` for a
        directory and a space for anything else.  Several that agree on more
        than the word already says extend it that far.  Otherwise the choice
        is the user's, in a drop-down over the line.

        **While that drop-down is open the answer only refills it**: it is an
        answer to typing, and completing or extending the word under the
        user's fingers would fight them.  An empty one closes it.
        """
        line = self.command_line
        if line.value != event.line or line.cursor != event.point:
            return
        word = event.line[event.start : event.point]
        candidates = list(dict.fromkeys(event.candidates))[:MAX_COMPLETIONS]
        if self.completion_list is not None:
            if candidates:
                self._completing, self._candidates = event, candidates
                self._show_completions(event.start, candidates)
            else:
                self._close_completions()
            return
        if not candidates:
            return
        if len(candidates) == 1:
            self._complete_word(event, candidates[0], final=True)
            return
        prefix = os.path.commonprefix(candidates)
        if len(prefix) > len(word):
            self._complete_word(event, prefix, final=False)
            return
        self._open_completions(event, candidates)

    def _complete_word(self, event: CompletionsReady, text: str, *, final: bool) -> None:
        line = self.command_line
        suffix = ""
        if final and not text.endswith(("/", " ", "=")):
            suffix = "/" if self._is_directory(text) else " "
        if not text.endswith(" "):
            text = _escape(text)
        value = event.line[: event.start] + text + suffix + event.line[event.point :]
        line.value = value
        line.anchor = None
        line.cursor = event.start + len(text) + len(suffix)

    def _is_directory(self, text: str) -> bool:
        path = Path(os.path.expanduser(text))
        if not path.is_absolute():
            base = self._command_directory()
            if base is None:
                return False
            path = base / path
        try:
            return path.is_dir()
        except OSError:
            return False

    def _open_completions(self, event: CompletionsReady, candidates: list[str]) -> None:
        """The list over the command line, its left edge under the word."""
        from navigator.widgets.shell.completion_list import CompletionList

        app = self.application
        if app is None:
            return
        self._completing, self._candidates = event, candidates
        window = CompletionList(
            lambda text: self._complete_word(self._completing, text, final=True),
            self._type_in_completions,
        )
        self._completion_list = window
        self._show_completions(event.start, candidates)
        app.overlay(window)

    def _show_completions(self, start: int, candidates: list[str]) -> None:
        """Fill the list with *candidates* and fit it to them, above the line."""
        window, line = self._completion_list, self.command_line
        shown = candidates or [""]
        width = min(self.width, max(len(c) for c in shown) + 4)
        height = min(len(shown) + 2, max(3, line.y - 1))
        column = line.x + line.text_origin + start - line.first - 1
        x = max(0, min(column, self.width - width))
        y = max(0, line.y - height)
        window.items = candidates
        window.cursor = 0
        window.x = bind(lambda o, v=x: v)
        window.y = bind(lambda o, v=y: v)
        window.width = bind(lambda o, v=width: v)
        window.height = bind(lambda o, v=height: v)

    def _close_completions(self) -> None:
        window = self.completion_list
        if window is not None:
            window.close()

    async def _type_in_completions(self, event: KeyEvent) -> None:
        """A key typed with the list open: onto the line, and the list follows.

        Narrowed at once to what still starts with the word, so the list
        keeps up with the keyboard, and then refilled by the shell's own
        answer -- which is what makes a ``/`` descend into the directory.  A
        blank ends the word and Backspace past its start leaves it; either
        closes the list.
        """
        line, state = self.command_line, self._completing
        await line.on_key(event)
        if state is None or line.cursor < state.start or (event.char or "x").isspace():
            self._close_completions()
            return
        word = line.value[state.start : line.cursor]
        narrowed = [c for c in self._candidates if c.startswith(word)]
        self._completing = CompletionsReady(line.value, line.cursor, state.start, tuple(narrowed))
        self._show_completions(state.start, narrowed)
        self._ask_completions()

    # -- the panel and the command line ----------------------------------------

    def _panel_entry(self) -> tuple[Location, Any] | None:
        """The active panel's directory and the entry under its cursor, if any."""
        manager = self.active_manager
        if manager is None:
            return None
        panel = manager.active_panel
        entry = panel.selected
        return (panel.location, entry) if entry is not None else None

    def _insert_entry(self, *, whole: bool) -> None:
        """``_CtrlEnter``: the entry's name -- or path -- onto the command line.

        On ``..`` it is the directory the panel shows, whole and ending in
        ``/``, as DOS Navigator's ended in a backslash.
        """
        found = self._panel_entry()
        if found is None:
            return
        directory, entry = found
        if entry.name == "..":
            text = _escape(str(directory).rstrip("/")) + "/"
        elif whole:
            text = _escape(str(entry.path_in(directory)))
        else:
            text = _escape(entry.name)
        self.command_line.insert_name(text)

    async def on_toggle_mark_by_space(self, event: ToggleMarkBySpace) -> bool:
        self.active_manager.active_panel.toggle_mark()
        return True

    async def on_open_smartpad(self, event: OpenSmartpad) -> bool:
        """Alt+Q, ≡ > *SmartPad (TM)*: ``OpenSmartpad`` (``navigator.lib.utilities.smartpad``)."""
        from navigator.lib.utilities.smartpad import open_smartpad

        if self.console_visible:
            self.toggle_console()
        self.spawn(open_smartpad(self.desktop))
        return True

    # -- Ctrl+F6: the calculator ----------------------------------------------------

    async def on_calculator(self, event: Calculator) -> bool:
        """Ctrl+F6, Utilities > *Calculator*: ``InsertCalc`` -- the one calculator
        window, brought forward if it is open, else opened where DN put it, in
        the face it last had.  Already in front, the next face: a departure,
        for terminals that send no Ctrl+digit."""
        from navigator.widgets.shell.calculator_window import CalculatorWindow
        from navigator.widgets.shell.calculator_window.calculator_window import X, Y

        if self.console_visible:
            self.toggle_console()
        desktop = self.desktop
        for window in desktop.windows():
            if isinstance(window, CalculatorWindow):
                if window is desktop.active_window:
                    window.cycle_mode()
                else:
                    desktop.activate(window)
                return True
        window = desktop.open(CalculatorWindow())
        window.x, window.y = X, Y
        window.place()
        window.take_keyboard()
        window.line.focus()
        return True

    # -- Utilities > Calendar --------------------------------------------------------

    async def on_open_calendar(self, event: OpenCalendar) -> bool:
        """Utilities > *Calendar*: TVDEMO's calendar window, a departure (DN had
        none) -- the one window, brought forward if it is open, else opened in
        the middle of the desktop on today.  From a click on the clock it goes
        to the top right corner, its top edge on the screen's second row, just
        under the clock; a click on the clock while it is open closes it."""
        from navigator.widgets.shell.calendar_window import CalendarWindow

        if self.console_visible:
            self.toggle_console()
        desktop = self.desktop
        for window in desktop.windows():
            if isinstance(window, CalendarWindow):
                if event.under_clock:
                    window.close()
                else:
                    desktop.activate(window)
                return True
        window = desktop.open(CalendarWindow())
        # As wide as the months its *View* shows.
        width, height = window.size()
        width, height = min(width, desktop.width), min(height, desktop.height)
        if event.under_clock:
            # Screen row 1 in the desktop's rows: 0 under a docked menu bar,
            # 1 when the desktop has the top row too.
            top = desktop.offset()[1] + desktop.y
            x, y = desktop.width - width, max(0, 1 - top)
        else:
            x, y = (desktop.width - width) // 2, (desktop.height - height) // 2
        x, y = max(0, x), max(0, min(y, desktop.height - height))
        window.locate(x, y, width, height)
        window.take_keyboard()
        return True

    # -- F2: the user menu (navigator.lib.config.usermenu) ------------------------------------

    async def on_user_menu(self, event: UserMenu) -> bool:
        """F2, Utilities > *User menu*: ``cmUserMenu``, DN's ``ExecUserMenu``."""
        self.spawn(self.user_menu())
        return True

    async def on_menu_file_edit(self, event: MenuFileEdit) -> bool:
        from navigator.lib.config.associations import MENU

        self.spawn(self.edit_associations(MENU))
        return True

    async def on_local_menu_file_edit(self, event: LocalMenuFileEdit) -> bool:
        from navigator.lib.config.usermenu import LOCAL_NAME

        self.spawn(self.edit_menu_file(self._menu_directory() / LOCAL_NAME))
        return True

    def _menu_directory(self) -> Path:
        """Where a local menu is looked for from: the active panel's directory."""
        return Path(self._command_directory() or Path.cwd())

    def _menu_panels(self) -> tuple[Any, Any]:
        """The active panel and the passive one if it is showing, as ``cmGetUserParams``."""
        manager = self.active_manager
        if manager is None:
            return None, None
        active, passive = manager.active_panel, manager.passive_panel
        # In Miller columns the passive panel is the active one: there is none.
        return active, (passive if passive.visible and passive is not active else None)

    @staticmethod
    def _menu_side(panel: Any, list_file: str = "-", use: Any = None) -> Any:
        """*panel* as the macros see it.  On another drive the directory is
        the one its files were fetched into (*use*, ``UseFile``), or -- for a
        caption, before anything is fetched -- the place's own name."""
        from navigator.lib.config.usermenu import Side

        if panel is None:
            return Side()
        entry = panel.selected
        if not panel.location.is_local:
            name = entry.name if entry is not None and not entry.is_dir else None
            if use is not None:
                return Side.of(use.directory, name, list_file)
            return Side.of(str(panel.location), name, list_file)
        if entry is None:
            return Side.of(Path(panel.path), None, list_file)
        # A *Find:* listing's entry is in a directory of its own.
        path = entry.path_in(Path(panel.path))
        return Side.of(path.parent, entry.name, list_file)

    async def edit_menu_file(self, path: Path) -> None:
        """A menu or ``.ini`` file in an editor, made by saving if it is not there yet."""
        from navigator.lib.config.file_history import open_editor

        if self.console_visible:
            self.toggle_console()
        try:
            await open_editor(self.desktop, path, new=True)
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot edit {path}: {error}").format(path=path, error=error.strerror or error),
                         buttons="ok").execute(self.application)

    async def user_menu(self, want_global: bool = False) -> None:
        """``ExecUserMenu``: the menu in a box in the middle of the screen, and
        the item chosen run in the console.

        The local ``.navigator-menu.ini`` -- the active panel's directory's, or
        the nearest above it -- else the global ``menu.ini``; F2 in the box changes between them,
        F4 edits the one shown, and a caption's own F-key, which outranks
        both, chooses its item.  Neither file: ``dlMNUNotFound``.
        """
        import asyncio

        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.config.usermenu import caption, find_menu, global_menu, parse, preview

        app = self.application
        if app is None:
            return
        # A panel on another drive has no local menu to look for.
        remote = self._front_remote() is not None
        while True:
            found = await asyncio.to_thread(find_menu, self._menu_directory(), want_global or remote)
            if found is None:
                await Dialog(title=tr("Error"), prompt=tr("File {name} not found").format(name=global_menu()),
                             buttons="ok").execute(app)
                return
            path, is_global = found
            try:
                text = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="replace")
                menu = parse(text, path, is_global)
            except (OSError, ValueError) as error:
                reason = error.strerror if isinstance(error, OSError) and error.strerror else error
                await Dialog(title=tr("Error"), prompt=tr("Cannot read {path}: {error}").format(path=path, error=reason),
                             buttons="ok").execute(app)
                return
            active, passive = (self._menu_side(panel) for panel in self._menu_panels())
            box_menu = SubMenu()
            items: dict[int, Any] = {}
            fkeys: dict[str, Any] = {}

            def fill(into: Any, entries: list[Any]) -> None:
                for entry in entries:
                    if entry.children:
                        fill(into.add_submenu(caption(entry, active, passive)), entry.children)
                    elif entry.is_line:
                        into.add_line()
                    else:
                        item = into.add_item(caption(entry, active, passive))
                        # What it will run, the panels' macros in (``preview``).
                        item.tooltip = preview(menu.commands(entry), active, passive)
                        items[id(item)] = entry
                        if entry.fkey:
                            fkeys.setdefault(entry.fkey, entry)

            fill(box_menu, menu.items)
            if not items:
                return
            # Which menu this is -- a departure, asked for: DN told the two
            # apart by its status line -- and that status line's two items
            # (``hcLUserMenu``/``hcGUserMenu``) on the key bar.
            if is_global:
                title, other = tr("User menu (global)"), tr("Local menu")
            else:
                title, other = tr("User menu (local)"), tr("Global menu")
            box = PopupMenu(box_menu, behind=self, keys=tuple(dict.fromkeys([*fkeys, "f2", "f4"])),
                            title=title, hints=(("F2", other), ("F4", tr("Edit"))))
            width, height = PopupMenu.measure(box_menu, app, self, title)
            box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
            chosen = await box.execute(app)
            pressed = box.pressed
            if pressed in fkeys:
                entry = fkeys[pressed]
            elif pressed == "f2":
                want_global = not is_global
                continue
            elif pressed == "f4":
                await self.edit_menu_file(path)
                return
            elif chosen is None:
                return
            else:
                entry = items.get(id(chosen))
                if entry is None:
                    return
            await self.run_menu_item(menu, entry)
            return

    async def run_menu_item(self, menu: Any, entry: Any) -> None:
        """An item's lines, run as :meth:`run_commands` runs them."""
        await self.run_commands(menu.commands(entry))

    async def run_commands(self, commands: Any, *, cwd: Path | None = None, uses: list[Any] = ()) -> None:
        """A user menu item's lines -- or an ``.ini`` entry's
        (:mod:`navigator.lib.config.associations`) -- its parameters asked first if it
        wants them, run in the console as a script the shell sources.

        ``%1`` and ``%2`` are files listing each panel's tagged names, or the
        one at its cursor (``GetUserParams``); they, and the script, are kept
        under fixed names in Navigator's own temporary directory
        (:func:`navigator.lib.system.tempdir.private_dir`), as DN's ``$DN$.BAT`` and
        ``$$$DN$$.LST`` were in its swap directory.
        """
        import asyncio
        import shlex

        from navigator.lib.system.tempdir import private_dir
        from navigator.lib.config.usermenu import script_text
        from navigator.widgets.shell.menu_params_dialog import MenuParamsDialog

        app = self.application
        params = ""
        if commands.asks:
            answer = await MenuParamsDialog(commands.title, commands.default).execute(app)
            if answer is None:
                return
            params = answer
        if not commands.lines:
            return
        active_panel, passive_panel = self._menu_panels()

        def names(panel: Any) -> list[str] | None:
            if panel is None:
                return None
            marked = panel.marked_entries
            if marked:
                return [entry.name for entry in marked]
            return [panel.selected.name] if panel.selected is not None else []

        lists = (names(active_panel), names(passive_panel))
        given, uses = list(uses), []
        for panel in (active_panel, passive_panel):
            use = None
            if panel is not None and not panel.location.is_local:
                use = await self._use_panel_files(panel)
                if use is False:
                    return
            uses.append(use)

        # A window's script and lists are its own (``-N``), as it may still
        # be reading them when the next item writes the console's.
        window = commands.window if not commands.panelize else None
        written: list[Path] = []
        shown: list[str] = []

        def write() -> Path:
            directory = private_dir()
            suffix = ""
            if window is not None:
                number = 1
                while (directory / f"usermenu-{number}.sh").exists():
                    number += 1
                suffix = f"-{number}"
            files = []
            for name, listed in zip((f"active{suffix}.lst", f"passive{suffix}.lst"), lists):
                if listed is None:
                    files.append("-")
                    continue
                target = directory / name
                written.append(target)
                target.write_text("".join(f"{line}\n" for line in listed), encoding="utf-8",
                                  errors="surrogateescape")
                files.append(str(target))
            script = directory / f"usermenu{suffix}.sh"
            written.append(script)
            active = self._menu_side(active_panel, files[0], uses[0])
            passive = self._menu_side(passive_panel, files[1], uses[1])
            text = script_text(commands, active, passive, str(script), params)
            shown.append("; ".join(text.splitlines()))
            script.write_text(text, encoding="utf-8", errors="surrogateescape")
            return script

        try:
            script = await asyncio.to_thread(write)
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot write the menu's script: {error}").format(error=error.strerror or error),
                         buttons="ok").execute(app)
            return
        fetched = [*given, *(use for use in uses if use is not None)]
        if cwd is None and uses and uses[0] is not None:
            cwd = uses[0].directory
        if commands.panelize:
            # ``<|``: the script's output is the active panel's listing.
            await self._panelize(f". {shlex.quote(str(script))}", fetched)
            return
        if window is not None:
            self.run_in_window(f". {shlex.quote(str(script))}", cwd=cwd, zoomed=window.zoomed,
                               modal=window.modal, closes=window.closes, uses=fetched, cleanup=written,
                               title=shown[0] if shown else None)
            return
        elsewhere = {"cwd": cwd, "uses": fetched} if cwd is not None or fetched else {}
        self.run_command(f". {shlex.quote(str(script))}", typed=False, **elsewhere)

    async def _use_panel_files(self, panel: Any) -> Any:
        """``UseFile`` for *panel* on another drive: its tagged files -- or
        the one at its cursor -- fetched into a directory of their own.  None
        with no file to fetch, False when the fetch failed or was stopped."""
        from navigator.widgets.drives.use_file import materialize

        entries = panel.marked_entries or ([panel.selected] if panel.selected is not None else [])
        files = [panel.entry_location(entry) for entry in entries if not entry.is_dir]
        if not files:
            return None
        use = await materialize(self.application, files)
        return use if use is not None else False

    # -- extensions.ini, viewers.ini, editors.ini, quickrun.ini ----------------

    async def on_open_file(self, event: Any) -> bool:
        """Enter on a file that is not itself a program: ``ExecFile`` -- what
        ``extensions.ini`` says for its name (DN's ``DN.EXT``), else the
        desktop's application for it (:meth:`open_on_desktop`), else nothing."""
        if self.console.busy:
            return True
        if isinstance(event.path, Location) and not event.path.is_local:
            self.spawn(self._open_elsewhere(event.path))
        else:
            self.spawn(self._open_here(Path(event.path)))
        return True

    async def _open_here(self, path: Path) -> None:
        if not await self.run_associated(EXTENSIONS, path.name):
            await self.open_on_desktop(path)

    @staticmethod
    def desktop_opens() -> bool:
        """Whether Enter on a file ``extensions.ini`` has nothing for opens it
        in the desktop's application: *Pass other files to desktop* on, and
        ``gio``, KIO or ``xdg-open`` and a display to open it on."""
        from navigator.lib.system import desktop

        return SETTINGS.file_manager.open_unassociated and desktop.opener() is not None and desktop.graphical()

    async def open_on_desktop(self, path: Path) -> bool:
        """*path* opened in the desktop's default application for its type
        (``gio open``, ``kioclient exec``, else ``xdg-open``) -- not DN's, where a file
        ``DN.EXT`` had no line for did nothing; nor here with *Pass other
        files to desktop* off.  A failure is said.  True when it was handed over."""
        from navigator.lib.system import desktop
        from navml.widgets.dialog.control import escape_caption

        if not self.desktop_opens():
            return False
        try:
            await asyncio.to_thread(desktop.open_file, path)
        except OSError as error:
            await Dialog(title=tr("Error"), buttons="ok", prompt=tr("Cannot open {path}: {error}").format(
                path=escape_caption(str(path)), error=escape_caption(error.strerror or str(error)),
            )).execute(self.application)
            return False
        return True

    async def open_with(self, origin: Location) -> None:
        """File > *Open with*: the applications the desktop has for *origin*'s
        type, in a box, the default first and marked, and the file opened in
        the one chosen (``gio launch``, ``kstart``).  Under them, as GNOME's
        and Xfce's have it, *Other applications* (every other installed one,
        :func:`~navigator.lib.system.desktop.other_applications`), *Set
        default* (the same two layers again: the one chosen becomes what the
        type opens in, and nothing is opened) and *Command...*: a command line
        of the user's own (:meth:`open_with_command`).  Not DN's.

        A file on another drive is typed by its name, and fetched
        (``UseFile``) only once an application is chosen: nothing waits for a
        desktop application, so what it changes is not sent back.
        """
        import mimetypes

        from navigator.lib.system import desktop
        from navml.widgets.dialog.control import escape_caption
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        app = self.application
        try:
            if origin.is_local:
                mime = await asyncio.to_thread(desktop.content_type, Path(origin.local))
            else:
                mime = mimetypes.guess_type(origin.name)[0] or ""
            apps = await asyncio.to_thread(desktop.applications, mime)
            others = await asyncio.to_thread(desktop.other_applications, apps)
        except OSError as error:
            await Dialog(title=tr("Open with"), buttons="ok",
                         prompt=escape_caption(error.strerror or str(error))).execute(app)
            return
        box_menu = SubMenu()
        #: Each application's item: the application, and whether it is set as the default.
        chosen_of: dict[int, tuple[Any, bool]] = {}
        self._fill_open_with(box_menu, apps, others, chosen_of, setting=False)
        if apps or others:
            box_menu.add_line()
        defaults = box_menu.add_submenu(tr("Set ~d~efault"))
        self._fill_open_with(defaults, apps, others, chosen_of, setting=True)
        defaults.disabled = not mime or not (apps or others)
        command = box_menu.add_item(tr("~C~ommand..."))
        title = tr("Open with ({type})").format(type=mime) if mime else tr("Open with")
        box = PopupMenu(box_menu, behind=self, title=title)
        width, height = PopupMenu.measure(box_menu, app, self, title)
        box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
        chosen = await box.execute(app)
        if chosen is command:
            await self.open_with_command(origin)
            return
        if chosen is None or id(chosen) not in chosen_of:
            return
        application, setting = chosen_of[id(chosen)]
        if setting:
            try:
                await asyncio.to_thread(desktop.set_default, mime, application)
            except OSError as error:
                await Dialog(title=tr("Set default"), buttons="ok",
                             prompt=escape_caption(error.strerror or str(error))).execute(app)
                return
            self.toast(tr("{name} now opens {type}").format(name=application.name, type=mime),
                       title=tr("Set default"))
            return
        path: Path
        if origin.is_local:
            path = Path(origin.local)
        else:
            from navigator.widgets.drives.use_file import materialize

            use = await materialize(app, [origin])
            if use is None:
                return
            path = use.local_for(origin) or use.directory / origin.name
        try:
            await asyncio.to_thread(desktop.launch, application, path)
        except OSError as error:
            await Dialog(title=tr("Open with"), buttons="ok",
                         prompt=escape_caption(error.strerror or str(error))).execute(app)

    @staticmethod
    def _fill_open_with(menu: Any, apps: list[Any], others: list[Any],
                        chosen_of: dict[int, tuple[Any, bool]], *, setting: bool) -> None:
        """*Open with*'s layers into *menu*: the type's own applications (the
        default marked), then *Other applications* in a box of their own;
        each item recorded in *chosen_of* with *setting*."""
        from navml.widgets.dialog.control import escape_caption

        for each in apps:
            name = escape_caption(each.name)
            caption = tr("{name} (default)").format(name=name) if each.default else name
            chosen_of[id(menu.add_item(caption))] = (each, setting)
        if not others:
            return
        if apps:
            menu.add_line()
        other = menu.add_submenu(tr("~O~ther applications"))
        other.filterable = True
        other.centred = True
        other.footer = tr("Type to filter")
        for each in others:
            chosen_of[id(other.add_item(escape_caption(each.name)))] = (each, setting)

    @staticmethod
    def open_with_history(name: str) -> str:
        """The history *Open with*'s command line keeps for a file called
        *name*: one per extension, case aside (``open_with.png``), and one
        for the names that have none (``open_with``)."""
        extension = Path(name).suffix.lower().lstrip(".")
        return f"open_with.{extension}" if extension else "open_with"

    @staticmethod
    def open_with_line(text: str) -> str:
        """*text* as the line that runs: the user menu's language, so ``!.!``
        and the rest are put in; with no ``!`` macro in it, the file's name
        goes on the end (``gimp`` runs ``gimp !.!``)."""
        return text if "!" in text else f"{text} !.!"

    async def open_with_command(self, origin: Location) -> bool:
        """*Open with*'s *Command...*: a command line asked -- its history the
        file's extension's own (:meth:`open_with_history`) -- and run in the
        console as an ``extensions.ini`` entry is (:meth:`run_commands`):
        the user menu's macros work, and a file on another drive is fetched
        first and sent back once the command ends.  True once it ran."""
        from navigator.lib.config.usermenu import commands_of
        from navigator.widgets.shell.edit_line_dialog import EditLineDialog

        box = EditLineDialog("", history=self.open_with_history(origin.name),
                             caption=tr("~C~ommand (!.! is the file; else it goes at the end)"))
        # After construction: the markup's own *Edit History* is bound in ``__init__``.
        box.title = tr("Open with")
        text = await box.execute(self.application)
        text = (text or "").strip()
        if not text or self.console.busy:
            return False
        await self.run_commands(commands_of([self.open_with_line(text)]))
        return True

    async def _open_elsewhere(self, origin: Location) -> None:
        """Enter on a file on another drive: ``UseFile``, then what
        ``extensions.ini`` says for it, run beside the local copy -- which
        goes back up if the program changed it."""
        from navigator.lib.drives import usefile
        from navigator.widgets.drives.use_file import materialize

        use = await materialize(self.application, [origin])
        if use is None:
            return
        if await self.run_associated(EXTENSIONS, origin.name, cwd=use.directory, uses=[use]):
            return
        # The desktop's application on the copy, which stays: nothing waits
        # for it to be done, so nothing is sent back either.
        if not await self.open_on_desktop(use.local_for(origin) or use.directory / origin.name):
            await asyncio.to_thread(usefile.discard, use)

    async def on_quick_run(self, event: QuickRun) -> bool:
        """Ctrl+Shift+F1 .. F10: ``QuickExecExternal`` -- ``quickrun.ini``'s
        ``[F1]`` .. ``[F10]`` (DN's ``DN.XRN``); a key with no section does nothing."""
        if not self.console.busy:
            self.spawn(self.run_associated(QUICK_RUN, key=f"F{event.number}"))
        return True

    async def run_associated(self, file_name: str, name: str | None = None, *,
                             key: str | None = None, cwd: Path | None = None,
                             uses: list[Any] = ()) -> bool:
        """Run what *file_name* (one of :mod:`navigator.lib.config.associations`' four)
        has for the file called *name*, or for *key*; False when it has
        nothing, so the caller does what it did without one.

        One entry runs at once; several are offered in a menu in the middle
        of the screen, their captions' macros put in, and Esc runs none (and
        still answers True: the file had something).  A file that will not
        read, or is not an ``.ini``, is said so.
        """
        import asyncio

        from navigator.lib.config import associations
        app = self.application
        if app is None:
            return False
        try:
            groups = await asyncio.to_thread(associations.read, file_name)
        except (OSError, ValueError) as error:
            reason = error.strerror if isinstance(error, OSError) and error.strerror else error
            await Dialog(title=tr("Error"), prompt=tr("Cannot read {path}: {error}").format(path=file_name, error=reason),
                         buttons="ok").execute(app)
            return True
        group = (associations.for_key(groups, key) if key is not None
                 else associations.for_file(groups, name or ""))
        if group is None:
            return False
        action = group.actions[0]
        if len(group.actions) > 1:
            action = await self.choose_action(group.actions)
            if action is None:
                return True
        elsewhere = {"cwd": cwd, "uses": uses} if cwd is not None or uses else {}
        await self.run_commands(action.commands, **elsewhere)
        return True

    async def choose_action(self, actions: Any, title: str | None = None) -> Any:
        """A ``PopupMenu`` of *actions*' captions, as F2's box is shown: the one chosen, or None.

        *title* is the box's, "Choose action" unless given."""
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.config.usermenu import expand

        app = self.application
        active, passive = (self._menu_side(panel) for panel in self._menu_panels())
        box_menu = SubMenu()
        chosen_of = {id(box_menu.add_item(expand(action.caption, active, passive, quote=False))): action
                     for action in actions}
        title = title or tr("Choose action")
        box = PopupMenu(box_menu, behind=self, title=title)
        width, height = PopupMenu.measure(box_menu, app, self, title)
        box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
        chosen = await box.execute(app)
        return chosen_of.get(id(chosen)) if chosen is not None else None

    async def on_edit_quick_run(self, event: EditQuickRun) -> bool:
        self.spawn(self.edit_associations(QUICK_RUN))
        return True

    async def on_ext_file_edit(self, event: ExtFileEdit) -> bool:
        self.spawn(self.edit_associations(EXTENSIONS))
        return True

    async def on_edit_hgl(self, event: EditHGL) -> bool:
        self.spawn(self.edit_associations(HIGHLIGHT))
        return True

    async def on_edit_macros(self, event: EditMacros) -> bool:
        from navigator.lib.config.associations import MACROS

        self.spawn(self.edit_associations(MACROS))
        return True

    async def on_external_viewers(self, event: ExternalViewers) -> bool:
        self.spawn(self.edit_associations(VIEWERS))
        return True

    async def on_external_editors(self, event: ExternalEditors) -> bool:
        self.spawn(self.edit_associations(EDITORS))
        return True

    async def edit_associations(self, file_name: str) -> None:
        """Options > Quick run file edit, Extension file edit, Viewers or
        Editors: the file in an editor, written first from its template
        (:func:`navigator.lib.config.associations.seed`) should it have gone since
        Navigator started."""
        import asyncio

        from navigator.lib.config import associations
        path = associations.path_of(file_name)
        try:
            await asyncio.to_thread(associations.seed, file_name)
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot write {path}: {error}").format(path=path, error=error.strerror or error),
                         buttons="ok").execute(self.application)
            return
        await self.edit_menu_file(path)

    async def on_ascii_table(self, event: AsciiTable) -> bool:
        """Ctrl+B, Utilities > *Character table*: DN's ``ASCIITable``."""
        self.spawn(self.ascii_table())
        return True

    async def ascii_table(self) -> None:
        """The character table, then the character picked on the command line.

        *ASCII Chart* in the ASCII glyph tier, the *Character Table* in any
        other (:func:`~navigator.widgets.shell.unicode_chart.pick_character`).
        DN put it back as a key press (``PutEvent``), which reached the
        command line wherever the panels had the keyboard; here it goes into
        the line directly.  A NUL is no key, and nothing.  The character is
        the one the chart shows (``│`` for 179), the line being Unicode.
        """
        from navigator.widgets.shell.unicode_chart import pick_character

        char = await pick_character(self.application, self.glyphs)
        if char and char != "\x00":
            self.command_line.insert(char)

    async def on_insert_name(self, event: InsertName) -> bool:
        self._insert_entry(whole=False)
        return True

    async def on_insert_path(self, event: InsertPath) -> bool:
        self._insert_entry(whole=True)
        return True

    async def on_execute_file(self, event: Any) -> bool:
        """Enter on an executable in a panel: run it, as though typed.

        ``./name`` in the panel's directory, which is where a command runs --
        so the console log shows ``prompt$ ./name``, what a user would have
        typed, and the history gets it too.  Not while a program is running:
        the panels are not showing then, and nothing typed would reach them.
        """
        if self.console.busy:
            return True
        self.run_command("./" + _escape(event.path.name))
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

    async def on_execute_command_line_in_window(self, event: ExecuteCommandLineInWindow) -> bool:
        """Shift+Enter: the line run in a window of its own, as ``&`` before it would."""
        line = self.command_line.value
        self.run_command(line if line.lstrip().startswith("&") else "&" + line.lstrip())
        return True

    def run_command(self, command: str, *, typed: bool = True, cwd: Path | None = None,
                    uses: list[Any] = ()) -> None:
        """Run *command* as though it had been typed on the command line.

        *typed* off is for a command the line did not hold -- a user menu
        item's -- which leaves the line and its history alone.  *cwd* is where
        it runs, the active panel's directory unless given; *uses* are the
        files fetched from another drive for it (``UseFile``), offered back up
        once it is done.
        """
        if not command.strip():
            if uses:
                self.spawn(self._put_back(list(uses)))
            return
        if typed:
            HISTORY.add(HISTORY_ID, command)
            self.command_line.clear()
            self._walk = None
            if command.lstrip().startswith("|"):
                # ``|cmd``: its output panelized rather than shown (a
                # departure, :mod:`navigator.lib.file_ops.panelize`); a line
                # starting with a pipe is no shell command.
                self.spawn(self._panelize(command.lstrip()[1:].strip(), uses))
                return
            if command.lstrip().startswith("&"):
                # ``&cmd``: run in a window of its own (a departure,
                # ``TerminalWindow``); a line starting with ``&`` is no shell
                # command either.
                self.run_in_window(command.lstrip()[1:].strip(), cwd=cwd, uses=uses)
                return
        if cwd is None:
            cwd = self._command_directory()
        self._command_uses = [*self._command_uses, *uses]
        self._command_started_in = self.console.subshell.cwd
        if not self.console_visible and not SETTINGS.system.internal_terminal:
            # mc's way: the command runs on the real terminal, and Navigator
            # comes back when it is done.
            self._relayed_for_command = self.relay_terminal()
            if self._relayed_for_command:
                self.console.run(command, cwd)
                return
        self._shown_for_command = not self.console_visible
        if not self.console_visible:
            self.toggle_console()
        self.console.focus()
        self.console.run(command, cwd)

    def run_in_window(self, command: str, *, cwd: Path | None = None, zoomed: bool | None = None,
                      modal: bool | None = None, closes: bool | Callable[[int], bool] = False, uses: list[Any] = (),
                      cleanup: list[Path] = (), title: str | None = None) -> Any:
        """Run *command* in a window of its own (``TerminalWindow``), not on the console.

        *cwd* is where, the active panel's directory unless given; *zoomed*
        and *modal* how the window opens, System Setup's *Command windows*
        unless given; *closes*, that the window goes as soon as the command
        ends with status 0 rather than staying with its output -- or a test
        of the wait status saying which ends take it.  *uses* are files fetched from another drive for it,
        offered back up once the window is closed; *cleanup* are files written
        for it alone (a user menu item's script), removed then.  *title* is
        what the window calls it, the command unless given.  Returns the
        window, or None for a blank command.
        """
        from navigator.widgets.shell.terminal_window import open_terminal

        uses, cleanup = list(uses), list(cleanup)
        if not command.strip():
            self._closed_terminal(uses, cleanup)
            return None
        if cwd is None:
            cwd = self._command_directory()
        if self.console_visible:
            self.toggle_console()
        return open_terminal(
            self.desktop, command, cwd,
            zoomed=SETTINGS.system.command_window_zoomed if zoomed is None else zoomed,
            modal=SETTINGS.system.command_window_modal if modal is None else modal,
            shell=self.console.subshell.shell, title=title, closes=closes,
            on_close=lambda: self._closed_terminal(uses, cleanup),
        )

    def _closed_terminal(self, uses: list[Any], cleanup: list[Path]) -> None:
        """A command window has gone: what it fetched put back, what it wrote removed."""
        for path in cleanup:
            try:
                path.unlink()
            except OSError:
                pass
        if uses:
            self.spawn(self._put_back(uses))

    async def _panelize(self, command: str, uses: list[Any] = ()) -> None:
        """*command*'s output as the active panel's listing
        (:meth:`Manager.panelize`); with no file manager open, says so."""
        manager = self.active_manager
        try:
            if not command:
                return
            if manager is None:
                await Dialog(title=tr("Error"), prompt=tr("No file manager is open to panelize into"),
                             buttons="ok").execute(self.application)
                return
            await manager.panelize(manager.active_panel, command)
        finally:
            if uses:
                await self._put_back(list(uses))

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
        if self._relayed_for_command:
            self._relayed_for_command = False
            self.end_relay(follow=False)
        elif self._shown_for_command and self.console_visible:
            self._shown_for_command = False
            self.toggle_console()
        elif self.console_visible:
            # Still up by Ctrl+O: the keys go back to the command line.
            self.console.focus()
        self._follow_shell(cwd)
        if self._command_uses:
            uses, self._command_uses = self._command_uses, []
            self.spawn(self._put_back(uses))

    async def _put_back(self, uses: list[Any]) -> None:
        """What a command changed of the files fetched for it, offered back to
        their drive; then the copies go."""
        from navigator.lib.drives import usefile
        from navigator.widgets.drives.use_file import put_back

        for use in uses:
            try:
                await put_back(self.application, use)
            finally:
                await asyncio.to_thread(usefile.discard, use)
        manager = self.active_manager
        if manager is not None:
            for panel in manager.all_panels:
                if not panel.location.is_local:
                    panel.reload()

    @staticmethod
    def _is_use_directory(path: Path) -> bool:
        """Whether *path* is one a command on fetched files ran in: the shell
        coming back from there is not a ``cd`` for the panel to follow."""
        from navigator.lib.drives.usefile import REMOTE
        from navigator.lib.system.tempdir import temp_root

        try:
            path.relative_to(temp_root())
        except ValueError:
            return False
        return REMOTE in path.parts

    def _follow_shell(self, cwd: Path | None) -> None:
        """Send the active panel wherever the shell went, and re-read both.

        Not with Startup's *Preserve directory*: DN stored the active panel's
        drive across a command only then (``TFilePanelRoot.Store``), and
        otherwise let it take the directory DOS came back with.
        """
        manager = self.active_manager
        if manager is None:
            return
        panel = manager.active_panel
        started, self._command_started_in = self._command_started_in, None
        if not panel.location.is_local:
            # The shell never went where the panel is: only a ``cd`` typed in
            # the command takes the panel back to the disk.
            moved = cwd is not None and started is not None and cwd != started
            if moved and not SETTINGS.startup.preserve_directory and not self._is_use_directory(cwd):
                self._panel_to_shell(panel, cwd)
        elif (cwd is not None and cwd != panel.path and not SETTINGS.startup.preserve_directory
                and not self._is_use_directory(cwd)):
            self._panel_to_shell(panel, cwd)
        for each in manager.all_panels:
            each.reload()

    def _panel_to_shell(self, panel: Any, cwd: Path) -> None:
        """*panel* where the shell went: a directory the user can see is, or
        -- the console being root's -- ``root:`` there, for one under a
        directory the user may not even look into (``/root/sub``)."""
        try:
            seen = cwd.is_dir()
        except OSError:  # EACCES under a directory the user may not look into
            seen = False
        if seen:
            panel.path = cwd
        elif self.console.root and cwd.is_absolute():
            from navigator.lib.drives import root

            panel.location = root.root_location(cwd)

    @computed
    def block_insert(self) -> bool:
        """The ``:block_insert`` state: Interface's *Block Insert Cursor*.

        ``ouiBlockInsertCursor`` swapped ``TCommandLine``'s two cursors, so
        inserting showed DN's block.  The line only inserts -- it has no
        overwrite mode for the other half of the swap -- so the state is the
        setting.  It is this screen's rather than the line's because the caret
        is answered from here (:meth:`cursor_position`), and the application
        takes its shape from whoever answers.
        """
        return SETTINGS.interface.block_insert_cursor

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
        start = current.active_panel.location if current is not None else Path.cwd()
        self.desktop.open(Manager(start, start)).apply_left_panel()
        return True

    async def on_hide_left(self, event: HideLeft) -> bool:
        self.show_manager_side("left")
        return True

    async def on_hide_right(self, event: HideRight) -> bool:
        self.show_manager_side("right")
        return True

    def show_manager_side(self, side: str) -> None:
        """Ctrl+F1 / Ctrl+F2 from the console: the file manager back, *side* alone.

        DOS Navigator's user screen turned ``cmHideLeft`` into
        ``cmPostHideLeft`` and closed: the double window then showed the left
        side and hid the right.  So Ctrl+F1 from a left-only file manager shows
        the console, and Ctrl+F1 again brings the left side back as it was.
        """
        manager = self.active_manager
        manager.show_only(side)
        if self.console_visible:
            self.toggle_console()
        self.desktop.activate(manager)

    async def on_about(self, event: About) -> bool:
        """≡ > About: started, not awaited -- a handler never waits on a dialog."""
        from navigator.widgets.about_dialog import AboutDialog

        self.spawn(AboutDialog().execute(self.application))
        return True

    # -- Options: the setup dialogs ------------------------------------------------

    async def on_settings(self, event: Settings) -> bool:
        self.spawn(self.settings())
        return True

    async def on_system_setup(self, event: SystemSetup) -> bool:
        self.spawn(self.settings("system"))
        return True

    async def on_startup_setup(self, event: StartupSetup) -> bool:
        self.spawn(self.settings("startup"))
        return True

    async def on_interface_setup(self, event: InterfaceSetup) -> bool:
        self.spawn(self.settings("interface"))
        return True

    async def settings(self, tab: str = "system") -> None:
        """Options > Settings, opened on page *tab*: every section it shows
        that OK changed is applied and saved, as :meth:`setup` does."""
        from navigator.lib.config import language
        from navigator.widgets.setup.settings_dialog import SettingsDialog
        from navigator.widgets.setup.settings_dialog.settings_dialog import SECTIONS

        before = SETTINGS.interface.language
        direction = SETTINGS.interface.direction
        depth = SETTINGS.appearance.colors
        glyphs = SETTINGS.appearance.glyphs
        marks = SETTINGS.appearance.marks
        await self.setup(SettingsDialog(tab=tab), *SECTIONS)
        # The same for the colour depth, over a session's --colors.
        if SETTINGS.appearance.colors != depth:
            self.application.use_color_depth(SETTINGS.appearance.colors)
        # And the glyph tier, over a session's --glyphs: frames, marks, arrows
        # and the panels' icon gutter change on the next frame.
        if SETTINGS.appearance.glyphs != glyphs:
            self.application.use_glyphs(SETTINGS.appearance.glyphs)
        # And the check marks, over a session's --marks; every cluster on the
        # screen redraws, as it reads the application's choice.
        if SETTINGS.appearance.marks != marks:
            self.application.marks = SETTINGS.appearance.marks
            self.application.invalidate()
        # Only a change: Cancel, or OK on the same choice, leaves a session's
        # --language standing.  Every caption bound to it follows this batch.
        if SETTINGS.interface.language != before:
            language.apply(SETTINGS.interface.language)
            self.application.invalidate()
        # And the direction, over a session's --direction: the screen mirrors
        # or stops mirroring on the next frame.
        if SETTINGS.interface.direction != direction:
            self.application.direction = SETTINGS.interface.direction

    async def on_setup_link(self, event: SetupLink) -> bool:
        self.spawn(self.settings("remote"))
        return True

    # -- other drives: Navigator Link ------------------------------------------

    async def on_navy_link(self, event: NavyLink) -> bool:
        return self._link_command("sftp")

    async def on_ftp_link(self, event: FtpLink) -> bool:
        return self._link_command("ftp")

    async def on_smb_link(self, event: SmbLink) -> bool:
        return self._link_command("smb")

    async def on_s3_link(self, event: S3Link) -> bool:
        return self._link_command("s3")

    async def on_gvfs_link(self, event: GvfsLink) -> bool:
        return self._link_command("gvfs")

    async def on_docker_link(self, event: DockerLink) -> bool:
        return self._link_command("docker")

    async def on_podman_link(self, event: PodmanLink) -> bool:
        return self._link_command("podman")

    async def on_adb_link(self, event: AdbLink) -> bool:
        return self._link_command("adb")

    async def on_rclone_link(self, event: RcloneLink) -> bool:
        return self._link_command("rclone")

    def _link_command(self, scheme: str) -> bool:
        manager = self.active_manager
        if manager is not None:
            self.spawn(self.navy_link(manager.active_panel, scheme=scheme))
        return True

    async def navy_link(self, panel: Any, request: Any = None, *, scheme: str = "sftp") -> bool:
        """Utilities > *Navigator Link*: ``cmNavyLink`` -- where to connect,
        asked; *panel* sent there once connected, and the place kept by name
        if *Keep* was ticked.  True once the panel is there."""
        from navigator.lib.drives import profiles, recent, sessions
        from navigator.widgets.drives.connect_dialog import ConnectDialog

        app = self.application
        if request is not None:
            scheme = request.scheme
        if scheme == "gvfs":
            return await self.gvfs_link(panel)
        if request is None:
            # Every protocol's menu item, and the Link box's *New ... link*:
            # its connection manager.  A *request* (filled in from elsewhere)
            # still goes to the one-shot box below.
            from navigator.widgets.drives.link_manager import family_of

            return await self.link_manager(panel, family_of(scheme))
        family = (("ftp", "ftps") if scheme in ("ftp", "ftps") else ("s3", "s3+http") if scheme in ("s3", "s3+http")
                  else (scheme,))
        missing = sessions.available(scheme)
        request = await ConnectDialog(request, missing=missing, recent=recent.recent(family),
                                      scheme=scheme).execute(app)
        if request is None:
            return False
        site = Site(request.scheme, request.user, request.host, request.port)
        path = PurePosixPath(request.path) if request.path else profiles.HOME
        if request.keep and request.name:
            await asyncio.to_thread(profiles.save, request.name, request.scheme, request.host,
                                    request.user, request.port, request.path)
        if not await self.go_remote(panel, Location(site, path)):
            return False
        # Remembered once it worked, every line of it together: a mistyped
        # host that never answered does not come back to be picked.
        await asyncio.to_thread(recent.remember, recent.Recent(
            request.scheme, request.host, request.user, request.port, request.path))
        return True

    async def link_manager(self, panel: Any, family: str) -> bool:
        """Utilities > *SSH link*, *FTP link*, *SMB link*, *S3 link* and
        *GVfs/KIO link*: *family*'s connection manager (``LinkManagerDialog``),
        and *panel* sent where *Connect* says.  True once the panel is there."""
        from navigator.lib.drives import recent, sessions
        from navigator.widgets.drives.link_manager import FAMILIES, LinkManagerDialog, entries_for, location_of

        entries = await asyncio.to_thread(entries_for, family)
        schemes = FAMILIES[family].schemes
        missing = sessions.available(schemes[0]) if schemes else None
        request = await LinkManagerDialog(entries, family=family, mode="panel",
                                          missing=missing).execute(self.application)
        if request is None:
            return False
        if request.copy_key:
            self.copy_ssh_key(request)
            return False
        if request.configure:
            self.configure_rclone()
            return False
        target = location_of(request)
        if family == "gvfs" and target.path == PurePosixPath("."):
            # A desktop place opens at its root: GVfs and KIO have no home there.
            target = Location(target.site, PurePosixPath("/"))
        from navigator.lib.drives import forwards

        wanted = forwards.parse(request.forwards, strict=False) if family == "sftp" else None
        if not await self.go_remote(panel, target, wanted):
            return False
        if family != "gvfs":
            # Remembered once it worked, as ``navy_link`` does.
            await asyncio.to_thread(recent.remember, recent.Recent(
                request.scheme, request.host, request.user, request.port, request.path))
        return True

    async def gvfs_link(self, panel: Any) -> bool:
        """Utilities > *GVfs/KIO link*: its connection manager, the places
        kept by URI -- ``mtp://``, ``dav://``, ``google-drive://``... -- and
        *panel* sent there, mounted through GVfs (:mod:`navigator.lib.drives.gvfs`)
        or, where the desktop's plumbing is KDE's, kio-fuse
        (:mod:`navigator.lib.drives.kio`).  True once the panel is there."""
        return await self.link_manager(panel, "gvfs")

    async def go_remote(self, panel: Any, target: Location, forwards: list[Any] | None = None) -> bool:
        """*panel* to *target* on another drive, connected first -- asking
        what the connection needs, *forwards* opened with it (:meth:`reach`).
        A *target* whose path is ``.`` opens on the home directory there.
        True once the panel is there."""
        from navigator.lib.drives import profiles

        if not await self.reach(target, forwards):
            return False
        if target.path == profiles.HOME:
            try:
                home = getattr(drive_of(target), "home", PurePosixPath("/"))
            except DriveGone:
                return False
            target = Location(target.site, home)
        if panel.parent is None:
            return False  # closed while it connected
        panel.leave_found()
        panel.location = target
        return True

    async def reach(self, target: Location, forwards: list[Any] | None = None) -> bool:
        """*target*'s drive connected, if it is not already: the host key, a
        password or a passphrase asked as the connection needs them, and
        tried again with each answer.  False if it could not be, which is
        said, or was cancelled.  *forwards* are SSH's port forwards to open
        with a new connection; None, the ones a profile for the place keeps."""
        from navigator.lib.drives import credentials, sessions
        from navigator.lib.drives.sessions import (
            SESSIONS, Answers, NeedPassphrase, NeedPassword, UnknownHostKey,
        )
        from navigator.lib.system.job import Job
        from navigator.lib.system.progress import run_with_progress
        from navigator.widgets.drives.host_key_query import HostKeyQuery
        from navigator.widgets.drives.password_dialog import PasswordDialog
        from navigator.widgets.editor.loading import progress_box
        from navml.widgets.dialog.control import escape_caption

        site = target.site
        from navigator.lib.drives import root

        if site == root.ROOT_SITE and target.outer is None:
            # Not a connection: root access, asked for (a departure;
            # :mod:`navigator.lib.system.elevate`).
            from navigator.widgets.file_ops.as_root import reach_root

            return await reach_root(self.application, target)
        if target.is_local or SESSIONS.is_open(site) or site.scheme == "trash":
            # The Trash is no connection either (:mod:`navigator.lib.drives.trash`).
            return True
        app = self.application
        if target.outer is not None:
            # A place in an archive: the archive opened -- made, if named and
            # not there -- on the drive it is on, reached first.
            from navigator.lib.drives import archive

            if not target.outer.is_local and not await self.reach(target.outer):
                return False
            try:
                await asyncio.to_thread(archive.open_archive, target.outer, None, create=True)
            except (OSError, archive.NotAnArchive) as error:
                await Dialog(title=tr("Error"), prompt=tr("Cannot read {path}: {error}").format(
                    path=str(target.outer), error=getattr(error, "strerror", None) or error),
                    buttons="ok").execute(app)
                return False
            return True
        protocol = sessions.protocol_name(site.scheme)
        title = tr("{protocol} link").format(protocol=protocol)
        reason = sessions.available(site.scheme)
        if reason is not None:
            await Dialog(title=title, prompt=escape_caption(reason), buttons="ok").execute(app)
            return False
        lock = self._reaching.setdefault(site, asyncio.Lock())
        async with lock:
            if SESSIONS.is_open(site):
                return True
            answers = Answers(start=str(target.path), interactive=self._interactive_asker(protocol))
            if site.scheme == "sftp":
                # The port forwards to open with it: the link manager's, or
                # those kept with the place (the Link box, a saved desktop,
                # the command line) -- read on a thread, from the database.
                from navigator.lib.drives import profiles

                answers.forwards = (forwards if forwards is not None
                                    else await asyncio.to_thread(profiles.forwards_for, site))
            while True:
                job = Job()
                job.position = job.total = 0
                job.cancellable = True
                try:
                    await run_with_progress(
                        app, lambda: SESSIONS.connect(site, answers), job,
                        lambda: progress_box(job, tr("Connecting to {host} over {protocol}").format(
                            host=site.host, protocol=protocol)),
                    )
                    return True
                except UnknownHostKey as unknown:
                    choice = await HostKeyQuery(unknown.hostname, unknown.key_type,
                                                unknown.fingerprint).execute(app)
                    if choice is None:
                        return False
                    answers.for_hop(unknown.hop).host_key = choice
                except NeedPassword as needed:
                    # GVfs keeps its own passwords (the desktop's keyring), not ours.
                    can_keep = (sessions.module_name(site.scheme) != sessions.GVFS
                                 and await asyncio.to_thread(credentials.keyring_available))
                    who = f"{needed.user}@{needed.host}" if needed.user else needed.host
                    if site.scheme in ("s3", "s3+http"):
                        # S3's password is the access key's secret.
                        prompt = (tr("Wrong secret key for {who}. Try again:") if needed.wrong
                                  else tr("Secret key for {who}:")).format(
                            who=escape_caption(who))
                    elif site.scheme == "rclone":
                        # rclone's password is its encrypted configuration's, not the remote's.
                        prompt = (tr("Wrong password for rclone's configuration. Try again:") if needed.wrong
                                  else tr("Password for rclone's configuration:"))
                    else:
                        prompt = (tr("Wrong {protocol} password for {who}. Try again:") if needed.wrong
                                  else tr("{protocol} password for {who}:")).format(
                            protocol=protocol, who=escape_caption(who))
                    answer = await PasswordDialog(prompt, can_keep=can_keep).execute(app)
                    if answer is None:
                        return False
                    asked = answers.for_hop(needed.hop)
                    asked.password, asked.save_password = answer
                except NeedPassphrase as needed:
                    prompt = (tr("Wrong passphrase for {key}. Try again:") if needed.wrong
                              else tr("Passphrase for {key}:")).format(key=escape_caption(needed.key_file))
                    answer = await PasswordDialog(prompt).execute(app)
                    if answer is None:
                        return False
                    answers.for_hop(needed.hop).passphrase = answer[0]
                except OSError as error:
                    if job.stopped:
                        return False
                    await Dialog(title=title,
                                 prompt=escape_caption(error.strerror or str(error)),
                                 buttons="ok").execute(app)
                    return False

    def _interactive_asker(self, protocol: str) -> Any:
        """What a connecting thread calls with a server's own questions
        (SSH's keyboard-interactive: a one-time code, a PIN): each put in a
        box on the loop, the thread waiting for the replies -- None if one was
        cancelled -- as a copy's worker waits for its questions."""
        import concurrent.futures

        loop = asyncio.get_running_loop()

        def ask(title: str, instructions: str, prompts: list[tuple[str, bool]]) -> list[str] | None:
            future: concurrent.futures.Future[Any] = concurrent.futures.Future()
            loop.call_soon_threadsafe(
                lambda: self.spawn(self._answer_prompts(protocol, title, instructions, prompts, future)))
            return future.result()

        return ask

    async def _answer_prompts(self, protocol: str, title: str, instructions: str,
                              prompts: list[tuple[str, bool]], future: Any) -> None:
        from navml.widgets.dialog.control import escape_caption

        from navigator.widgets.drives.password_dialog import PasswordDialog

        replies: list[str] = []
        try:
            for prompt, echo in prompts:
                text = f"{instructions.strip()}\n{prompt}" if instructions and instructions.strip() else prompt
                box = PasswordDialog(escape_caption(text.strip()))
                box.title = f"{protocol}: {title}" if title else protocol
                box.entry.entry.password = not echo
                answer = await box.execute(self.application)
                if answer is None:
                    future.set_result(None)
                    return
                replies.append(answer[0])
            future.set_result(replies)
        except BaseException as error:
            if not future.done():
                future.set_result(None)
            if not isinstance(error, Exception):
                raise

    async def on_edit_links(self, event: EditLinks) -> bool:
        manager = self.active_manager
        self.spawn(self.edit_links(manager.active_panel if manager is not None else None))
        return True

    async def edit_links(self, panel: Any) -> None:
        """Utilities > *Saved links*: the profiles read on a thread, edited in
        one box, written back on OK in one transaction -- and, for *Connect*,
        *panel* sent to the one chosen."""
        from navigator.lib.drives import profiles
        from navigator.widgets.drives.links_dialog import LinksDialog

        entries = await asyncio.to_thread(profiles.entries)
        answer = await LinksDialog(entries).execute(self.application)
        if answer is None:
            return
        entries = answer[1]
        await asyncio.to_thread(profiles.store, entries)
        if answer[0] == "connect" and panel is not None:
            chosen = entries[answer[2]]
            row = await asyncio.to_thread(profiles.find, chosen.name)
            if row is not None:
                await self.go_remote(panel, profiles.location_of(row))

    async def on_terminal(self, event: Terminal) -> bool:
        self.spawn(self.open_remote_shell("sftp"))
        return True

    async def on_docker_shell(self, event: DockerShell) -> bool:
        self.spawn(self.open_remote_shell("docker"))
        return True

    async def on_podman_shell(self, event: PodmanShell) -> bool:
        self.spawn(self.open_remote_shell("podman"))
        return True

    async def on_adb_shell(self, event: AdbShell) -> bool:
        self.spawn(self.open_remote_shell("adb"))
        return True

    def _running_remote_shell(self, site: Site) -> Any:
        """The command window still logged in to *site* by Remote shell, brought
        forward -- DN's ``OpenTerminal`` selecting its one terminal -- or None."""
        from navigator.widgets.shell.terminal_window import TerminalWindow

        for window in reversed(self.desktop.windows()):
            if isinstance(window, TerminalWindow) and window.remote_site == site and window.view.busy:
                if self.console_visible:
                    self.toggle_console()
                self.desktop.activate(window)
                return window
        return None

    async def open_remote_shell(self, family: str = "sftp") -> Any:
        """Utilities > *Remote shell* > *SSH*, *Docker container*, *Podman
        container*, *Android device*: ``cmTerminal``'s ``OpenTerminal``.
        *family*'s link manager (``LinkManagerDialog``) in its shell mode, and
        *Connect* runs ``ssh -t``, ``docker exec -it`` or ``adb shell`` there
        in a command window (:mod:`navigator.lib.drives.remote_shell`) -- or
        brings forward the one still running for that place.  Nothing is
        taken from the panel: where is chosen in the box.  Returns the
        window, or None when cancelled."""
        from navigator.lib.drives import recent, remote_shell
        from navigator.widgets.drives.link_manager import LinkManagerDialog, entries_for, location_of

        entries = await asyncio.to_thread(entries_for, family)
        request = await LinkManagerDialog(entries, family=family, mode="shell").execute(self.application)
        if request is None:
            return None
        if request.copy_key:
            return self.copy_ssh_key(request)
        location = location_of(request)
        window = self._running_remote_shell(location.site)
        if window is None:
            # Gone when the shell ends -- Ctrl+D, ``exit`` -- however its last
            # command did; kept to show the program's own failure (refused,
            # unreachable, not let in, no such container).
            from navigator.lib.drives import forwards

            window = self.run_in_window(remote_shell.command(location, request.options,
                                                             forwards.parse(request.forwards, strict=False)),
                                        closes=remote_shell.closes(location.site.scheme),
                                        title=remote_shell.title(location.site))
            if window is None:
                return None
            window.remote_site = location.site
        await asyncio.to_thread(recent.remember, recent.Recent(
            request.scheme, request.host, request.user, request.port, request.path))
        return window

    def copy_ssh_key(self, request: Any) -> Any:
        """The SSH link manager's *Copy key...*: ``ssh-copy-id`` putting
        *request*'s public key on its server, in a command window that stays
        to show how it went (``ssh`` asks the password there, ``ssh-keygen``
        a passphrase first when the key is being made).  Returns the window."""
        from navigator.lib.drives import remote_shell

        site = Site(request.scheme, request.user, request.host, request.port)
        return self.run_in_window(
            remote_shell.copy_id_command(site, request.copy_key, request.options, generate=request.generate_key),
            closes=False, title=f"ssh-copy-id {remote_shell.login(site)}")

    def configure_rclone(self) -> Any:
        """The rclone link manager's *Configure...*: ``rclone config``, rclone's
        own interactive setup, in a command window that stays to show how it
        went.  Returns the window."""
        import shlex

        from navigator.lib.drives import rclone

        return self.run_in_window(shlex.join(rclone.configure_command()), closes=False, title="rclone config")

    async def on_hang_up(self, event: HangUp) -> bool:
        self.spawn(self.hang_up())
        return True

    async def hang_up(self) -> None:
        """Utilities > *Disconnect*: ``cmHangUp`` -- the one connection closed
        once agreed to, or one chosen of several (or all); its panels go back
        to the disk (:meth:`close_linked`)."""
        from navml.widgets.dialog.control import escape_caption
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.drives import mounted, sessions
        from navigator.lib.drives.sessions import SESSIONS

        app = self.application
        drives = [drive for drive in mounted() if sessions.is_connection(drive.site.scheme)]
        if not drives:
            return
        if len(drives) == 1:
            site = drives[0].site
            prompt = tr("Close the {protocol} connection to {host}?").format(
                protocol=sessions.protocol_name(site.scheme), host=escape_caption(site.host))
            if await Dialog(title=tr("Disconnect"), prompt=prompt, buttons="yes-no").execute(app) is True:
                await asyncio.to_thread(SESSIONS.close, site)
            return
        menu = SubMenu()
        items = {id(menu.add_item(escape_caption(str(drive.site)))): [drive.site] for drive in drives}
        menu.add_line()
        items[id(menu.add_item(tr("~A~ll")))] = [drive.site for drive in drives]
        title = tr("Disconnect")
        box = PopupMenu(menu, behind=self, title=title)
        width, height = PopupMenu.measure(menu, app, self, title)
        box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
        chosen = await box.execute(app)
        for site in items.get(id(chosen), []):
            await asyncio.to_thread(SESSIONS.close, site)

    def _heard_closed(self, site: Any, why: str) -> None:
        """A connection closed, on whatever thread closed it: the loop told."""
        app = self.application
        if app is not None and app.is_running:
            app.call_from_thread(lambda: self.close_linked(site, why))

    def close_linked(self, site: Any, why: str = "closed") -> None:
        """DN's ``cmCloseLinked``: every panel on *site* back on the disk, where
        it last was there; *why* ``"lost"`` says so once."""
        moved = False
        for window in self.desktop.windows():
            if isinstance(window, Manager):
                for panel in window.all_panels:
                    if panel.location.site == site:
                        panel.leave_found()
                        panel.location = panel.local_anchor
                        moved = True
        if why == "lost" and moved:
            from navigator.lib.drives.sessions import protocol_name, protocol_sign

            self.spawn(Dialog(
                title=tr("{protocol} link").format(protocol=protocol_name(site.scheme)),
                prompt=tr("Remote drive {name} is not accessible").format(
                    name=f"{protocol_sign(site.scheme)}:{site.host}"),
                buttons="ok").execute(self.application))

    def connections_in_use(self) -> set[Any]:
        """The sites some panel is on now: those no idle timer closes."""
        used = set()
        for window in self.desktop.windows():
            if isinstance(window, Manager):
                for panel in window.all_panels:
                    if not panel.location.is_local:
                        used.add(panel.location.site)
        return used

    async def follow_root(self) -> None:
        """Whether root access is open, looked at once a second: the helper
        starts and ends on threads, the reaper's among them."""
        from navigator.lib.system.elevate import ELEVATION

        self.root_mark.open = ELEVATION.running
        if not ELEVATION.running and self.console.is_root:
            # Closed from elsewhere -- its helper ended: the user's shell back.
            self._back_to_user_shell()

    def _back_to_user_shell(self) -> None:
        """The console's own shell back from root's, where the panel is now."""
        self.console.go_user()
        where = self._front_directory()
        if where is not None:
            self.console.subshell.sync(where)

    async def on_show_background(self, event: ShowBackground) -> bool:
        """Window > *Background operation*: a box sent away put back up --
        the one there is, or the one chosen from a list of them all."""
        from navigator.lib.system.background import BACKGROUND

        if len(BACKGROUND.jobs) > 1:
            self.spawn(self.choose_background())
        else:
            BACKGROUND.recall()
        return True

    async def choose_background(self) -> None:
        """Every operation in the background in a box, oldest first, as the
        menu bar's mark lists them: what each was started on and how far it
        is, or that it waits.  The cursor starts on one with a question,
        else on the newest; the one chosen has its box back."""
        from navml.widgets.dialog.control import escape_caption
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.system.background import BACKGROUND

        app = self.application
        jobs = BACKGROUND.jobs
        box_menu = SubMenu()
        chosen_of = {}
        for number, entry in enumerate(jobs, 1):
            if entry.asking:
                line = tr("{operation}: waiting for an answer").format(operation=entry.subject)
            else:
                line = tr("{operation}: {percent}% done").format(operation=entry.subject, percent=entry.percent)
            # Numbered for a key each, as DN's lists of windows were.
            hotkey = f"~{number}~ " if number < 10 else "  "
            chosen_of[id(box_menu.add_item(hotkey + escape_caption(line)))] = entry
        waiting = [index for index, entry in enumerate(jobs) if entry.asking]
        title = tr("Background operations")
        box = PopupMenu(box_menu, behind=self, title=title, current=waiting[0] if waiting else len(jobs) - 1)
        width, height = PopupMenu.measure(box_menu, app, self, title)
        box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
        chosen = await box.execute(app)
        entry = chosen_of.get(id(chosen)) if chosen is not None else None
        # It may have ended while the box was up.
        if entry is not None and entry in BACKGROUND.jobs:
            BACKGROUND.recall(entry)

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

    async def on_close_root_access(self, event: CloseRootAccess) -> bool:
        self.spawn(self.close_root_access())
        return True

    def _name_root_access(self) -> None:
        """Utilities' one root entry says what it would do: *Elevate root
        access* while root access is closed, *Close root access* while open."""
        item = self.menu.root_access
        if self.root_mark.open:
            item.text = tr("Close ~r~oot access")
            item.tooltip = tr("End root access now; the console goes back to your own shell")
        else:
            item.text = tr("Elevate ~r~oot access")
            item.tooltip = tr("Open root access now: the console's shell and a step refused permission run as root")

    #: ``ELEVATION.available()`` by System Setup's *Elevate*: its ``which``
    #: of sudo or pkexec asked once, not each time a menu is painted.
    _reachable: dict[str, bool] = {}

    def _root_reachable(self) -> bool:
        from navigator.lib.system.elevate import ELEVATION

        if ELEVATION.command is not None:  # the tests' helper
            return True
        chosen = SETTINGS.system.elevate
        if chosen not in Shell._reachable:
            Shell._reachable[chosen] = ELEVATION.available()
        return Shell._reachable[chosen]

    async def on_toggle_root_access(self, event: ToggleRootAccess) -> bool:
        self.spawn(self.close_root_access() if self.root_mark.open else self.open_root_access())
        return True

    async def open_root_access(self) -> None:
        """Utilities > *Elevate root access*: the root helper started, asking
        for the password as *As root* does; the ROOT mark up at once, and the
        console's shell root's too (:meth:`Console.go_root`), the user's own
        parked until root access closes."""
        from navml.widgets.dialog.control import escape_caption

        from navigator.widgets.file_ops.as_root import open_root

        app = self.application
        if app is None or not await open_root(app):
            return
        self.root_mark.open = True
        self.console.on_root_ended = self._root_shell_ended
        try:
            await self.console.go_root(self._command_directory())
        except OSError as error:
            await Dialog(title=tr("Error"), buttons="ok", prompt=tr(
                "The console could not be made root's: {reason}").format(
                    reason=escape_caption(error.strerror or str(error)))).execute(app)

    def _root_shell_ended(self) -> None:
        """``exit`` typed at the root shell: the user's back, root access left open."""
        where = self._front_directory()
        if where is not None:
            self.console.subshell.sync(where)

    async def close_root_access(self) -> None:
        """Utilities > *Close root access*: the panels at ``root:`` back on
        the disk (:meth:`close_linked`), then the helper closed -- a window
        still reading a file as root reads no more of it."""
        from navigator.lib.drives import root
        from navigator.lib.system.elevate import ELEVATION

        if self.console.is_root:
            self._back_to_user_shell()
        self.close_linked(root.ROOT_SITE)
        await asyncio.to_thread(ELEVATION.close)
        self.root_mark.open = False

    async def reap_connections(self) -> None:
        """*Communications*' *Close an idle connection after*, looked at once a minute."""
        from navigator.lib.drives.sessions import SESSIONS

        idle = SETTINGS.remote.idle_disconnect * 60
        if idle > 0:
            await asyncio.to_thread(SESSIONS.reap, self.connections_in_use(), idle)

    async def on_key_bindings_setup(self, event: KeyBindingsSetup) -> bool:
        self.spawn(self.key_bindings())
        return True

    async def key_bindings(self) -> None:
        """Options > Configuration > Key bindings: the dialog over every key
        table as bound now; OK binds what it answers and writes
        ``keybindings.ini`` (on a thread).  A file that cannot be written is
        said so, and the keys stay bound for this session."""
        import asyncio

        from navigator.lib.config import keybindings
        from navigator.widgets.setup.key_bindings_dialog import KeyBindingsDialog

        app = self.application
        found = keybindings.sections(type(app))
        answer = await KeyBindingsDialog(found).execute(app)
        if answer is None:
            return
        keybindings.apply(found, answer)
        try:
            await asyncio.to_thread(keybindings.write, found, answer)
        except OSError as error:
            from navml.widgets.dialog.dialog import Dialog

            await Dialog(
                title=tr("Error"),
                prompt=tr("Cannot save the key bindings: {error}").format(error=error.strerror or error),
                buttons="ok",
            ).execute(app)

    async def on_setup_confirmation(self, event: SetupConfirmation) -> bool:
        self.spawn(self.settings("confirmations"))
        return True

    async def on_editor_defaults(self, event: EditorDefaults) -> bool:
        self.spawn(self.settings("editor_viewer"))
        return True

    async def on_file_manager_setup(self, event: FileManagerSetup) -> bool:
        self.spawn(self.settings("file_manager"))
        return True

    async def on_drive_info_setup(self, event: DriveInfoSetup) -> bool:
        self.spawn(self.settings("drive_info"))
        return True

    async def on_column_defaults(self, event: ColumnDefaults) -> bool:
        self.spawn(self.settings("column_defaults"))
        return True

    def checks(self, command: Command) -> bool | None:
        """≡ > Trashcan on/off is ticked while the trash can shows."""
        if isinstance(command, ToggleTrashCan):
            return self.trash.shown
        return super().checks(command)

    async def on_game(self, event: Game) -> bool:
        """≡ > Game: ``TGameWindow`` -- the one game window, brought forward if
        it is open, else opened in the middle of the desktop (``ofCentered``)."""
        from navigator.widgets.game.game_window import GameWindow
        from navigator.widgets.game.game_window.game_window import HEIGHT, WIDTH

        if self.console_visible:
            self.toggle_console()
        desktop = self.desktop
        for window in desktop.windows():
            if isinstance(window, GameWindow):
                desktop.activate(window)
                return True
        window = desktop.open(GameWindow())
        width, height = min(WIDTH, desktop.width), min(HEIGHT, desktop.height)
        window.locate(max(0, (desktop.width - width) // 2), max(0, (desktop.height - height) // 2), width, height)
        window.glass.focus()
        return True

    async def on_toggle_trash_can(self, event: ToggleTrashCan) -> bool:
        """≡ > Trashcan on/off: ``cmHideShowTools``."""
        self.trash.shown = not self.trash.shown
        return True

    async def on_open_trash(self, event: OpenTrash) -> bool:
        """Disk > Trash, and the trash can's double click: the file manager's
        active panel on the Trash (not DN's -- ``OpenTrash``'s docstring)."""
        manager = self.active_manager
        if manager is None:
            return False
        if self.console_visible:
            self.toggle_console()
        self.desktop.activate(manager)
        self.spawn(manager.open_trash())
        return True

    async def on_empty_trash(self, event: EmptyTrash) -> bool:
        manager = self.active_manager
        if manager is None:
            return False
        self.spawn(manager.empty_trash())
        return True

    async def on_savers_setup(self, event: SaversSetup) -> bool:
        self.spawn(self.settings("savers"))
        return True

    async def on_country_setup(self, event: CountrySetup) -> bool:
        self.spawn(self.settings("country"))
        return True

    async def on_screen_rest(self, event: ScreenRest) -> bool:
        self.spawn(self.rest(asked=True))
        return True

    async def rest(self, *, asked: bool = False) -> None:
        """``InsertIdler``: one of the selected savers, at random, until a key.

        A built-in one is :class:`ScreenSaver` over everything; an external
        one runs on the console as a command does, until it exits.  With
        none selected DN did nothing; ≡ > Screen rest, *asked*, brings
        *Star flight* then, a departure -- a menu item that did nothing
        looked broken.
        """
        import shlex

        from navigator.lib.appearance import savers
        from navigator.widgets.shell.screen_saver import KINDS, ScreenSaver

        app = self.application
        if app is None or self.resting:
            return
        names = SETTINGS.savers.names() or (["star_flight"] if asked else [])
        if not names:
            return
        name = random.choice(names)
        self.resting = True
        try:
            if name in KINDS:
                await ScreenSaver(name).execute(app)
            else:
                path = savers.savers_dir() / name
                if path.is_file() and not self.console.busy:
                    self.run_command(shlex.quote(str(path)), typed=False)
        finally:
            self.resting = False

    async def on_highlight_groups(self, event: HighlightGroups) -> bool:
        self.spawn(self.settings("highlight_groups"))
        return True

    async def on_file_manager_defaults(self, event: FileManagerDefaults) -> bool:
        self.spawn(self.settings("panel_defaults"))
        return True

    async def setup(self, dialog: Any, *sections: str) -> None:
        """Run a setup *dialog*, then apply what it accepted and save it.

        DN's ``ExecResource`` and ``cmUpdateConfig`` in one: the values are
        assigned to :data:`SETTINGS`, whose bindings repaint whatever shows
        them, and each section is written back to ``navigator.ini`` -- that
        section alone, over whatever the file holds now.  A dialog over one
        section answers that section's values; over several, a dict of them
        by section name, and of those only the sections whose values OK
        changed are assigned and written.  A file that cannot be written is
        said so, and the values stay applied for this session.
        """
        answer = await dialog.execute(self.application)
        if answer is None:
            return
        changes = answer if len(sections) > 1 else {sections[0]: answer}
        if len(sections) > 1:
            sections = tuple(
                name for name in sections
                if changes[name].items() - SETTINGS.section(name).values().items()
            )
        for name in sections:
            SETTINGS.section(name).update(changes[name])
        try:
            for name in sections:
                SETTINGS.save(section=name)
        except OSError as error:
            from navml.widgets.dialog.dialog import Dialog

            await Dialog(
                title=tr("Error"),
                prompt=tr("Cannot save the settings: {error}").format(error=error.strerror or error),
                buttons="ok",
            ).execute(self.application)

    # -- the directory tree window --------------------------------------------

    # -- File View History, File Edit History ---------------------------------

    async def on_view_history(self, event: ViewHistory) -> bool:
        self.spawn(self.file_history("view"))
        return True

    async def on_edit_history(self, event: EditHistory) -> bool:
        self.spawn(self.file_history("edit"))
        return True

    async def file_history(self, kind: str) -> None:
        """``ViewHistoryMenu``/``EditHistoryMenu``: pick a file, open it as it was left.

        With the Interface option off the list is not shown, and DN's
        ``dlSetViewHistory``/``dlSetEditHistory`` says why; an empty history
        shows nothing at all, as ``Count = 0`` did.
        """
        from navml.widgets.dialog.dialog import Dialog

        from navigator.lib.config.file_history import open_editor, open_viewer
        from navigator.models.edit_record import EditRecord
        from navigator.models.view_record import ViewRecord
        from navigator.widgets.shell.file_history_dialog import FileHistoryDialog

        viewing = kind == "view"
        tracking = SETTINGS.interface.track_viewing if viewing else SETTINGS.interface.track_editing
        if not tracking:
            option = tr("Track viewing history") if viewing else tr("Track editing history")
            await Dialog(
                title=tr("Error"),
                prompt=tr('Set the interface option\n"{option}" ON first').format(option=option),
                buttons="ok",
            ).execute(self.application)
            return
        model = ViewRecord if viewing else EditRecord
        if not model.count():
            return
        title = tr("File View History") if viewing else tr("File Edit History")
        path = await FileHistoryDialog(model, title=title).execute(self.application)
        if path is None:
            return
        try:
            if viewing:
                await open_viewer(self.desktop, path)
            else:
                await open_editor(self.desktop, path)
        except OSError as error:
            await Dialog(
                title=tr("Cannot view file") if viewing else tr("Cannot edit file"),
                prompt=f"{path}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)

    # -- File > View > Open..., File > Edit > Open... ---------------------------

    async def on_open_view(self, event: OpenView) -> bool:
        self.spawn(self.open_chosen("view"))
        return True

    async def on_open_edit(self, event: OpenEdit) -> bool:
        self.spawn(self.open_chosen("edit"))
        return True

    async def open_chosen(self, kind: str) -> None:
        """A file chosen in a file box, viewed or edited -- not DN's.

        The box opens on the active panel's directory when that is on the
        disk, else where Navigator was started, and lists dot-files as that
        panel does.  A name typed that is not there yet is a new file to the
        editor, as Shift+F4's is, and said so by the viewer.  With *Internal
        viewer* (*editor*) off the file goes to ``$PAGER`` (``$EDITOR``), as
        Shift+F4's does -- not through ``viewers.ini``/``editors.ini``, whose
        macros name the file at the panel's cursor rather than this one.
        """
        import errno
        import shlex

        from navml.widgets.dialog.dialog import Dialog
        from navml.widgets.dialog.file_dialog import FileDialog

        from navigator.lib.config.file_history import open_editor, open_viewer

        viewing = kind == "view"
        manager = self.active_manager
        panel = manager.active_panel if manager is not None else None
        directory = panel.path if panel is not None and panel.location.is_local else None
        hidden = panel.show_hidden if panel is not None else SETTINGS.system.show_hidden
        name = await FileDialog(
            title=tr("View file") if viewing else tr("Edit file"),
            label=tr("~F~ile name"),
            history_id="view_open" if viewing else "edit_open",
            directory=directory,
            hidden=hidden,
            ok_text=tr("~O~pen"),
        ).execute(self.application)
        if not name:
            return
        path = Path(name)
        internal = SETTINGS.system.internal_viewer if viewing else SETTINGS.system.internal_editor
        if not internal:
            if viewing and not await asyncio.to_thread(path.exists):
                await Dialog(title=tr("Cannot view file"), prompt=f"{path.name}: {os.strerror(errno.ENOENT)}",
                             buttons="ok").execute(self.application)
                return
            variable, fallback = ("PAGER", "less") if viewing else ("EDITOR", "vi")
            program = os.environ.get(variable, "").strip() or fallback
            self.run_command(f"{program} {shlex.quote(str(path))}")
            return
        try:
            if viewing:
                await open_viewer(self.desktop, path)
            else:
                await open_editor(self.desktop, path, new=not await asyncio.to_thread(path.exists))
        except OSError as error:
            await Dialog(
                title=tr("Cannot view file") if viewing else tr("Cannot edit file"),
                prompt=f"{path.name}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)

    async def on_open_tree_window(self, event: OpenTreeWindow) -> bool:
        """Disk > Directory tree: a tree window, opened on the active panel's directory."""
        from navigator.widgets.tree.tree_window import TreeWindow

        manager = self.active_manager
        panel = manager.active_panel if manager is not None else None
        if panel is None:
            self.desktop.open(TreeWindow())
        else:
            start = panel.path if panel.location.is_local else None
            self.desktop.open(TreeWindow(start=start, hidden=panel.show_hidden))
        return True

    async def on_open_process_window(self, event: OpenProcessWindow) -> bool:
        from navigator.widgets.shell.process_window import ProcessWindow

        self.desktop.open(ProcessWindow())
        return True

    async def on_open_service_window(self, event: OpenServiceWindow) -> bool:
        """Utilities > Services: the system's services in a window."""
        from navigator.widgets.shell.service_window import ServiceWindow

        self.desktop.open(ServiceWindow())
        return True

    async def on_open_monitor_window(self, event: OpenMonitorWindow) -> bool:
        """Utilities > System monitor: the processors, the memory and the sensors in a window."""
        from navigator.widgets.shell.monitor_window import MonitorWindow

        self.desktop.open(MonitorWindow())
        return True

    async def on_open_volumes_window(self, event: OpenVolumesWindow) -> bool:
        """Disk > Volumes: the mounted volumes in a window."""
        from navigator.widgets.shell.volumes_window import VolumesWindow

        self.desktop.open(VolumesWindow())
        return True

    async def on_open_usage_window(self, event: OpenUsageWindow) -> bool:
        """Disk > Directory sizes: what takes the room under the active panel's
        directory -- on whatever drive it is -- in a window."""
        from navigator.widgets.shell.usage_window import UsageWindow

        manager = self.active_manager
        panel = manager.active_panel if manager is not None else None
        self.desktop.open(UsageWindow(start=panel.location if panel is not None else None, manager=manager))
        return True

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

    async def on_desktop_emptied(self, event: Event) -> bool:
        """The last window on ``desktop`` closed: the console is all there is.

        Named by the generator's ``on_<id>_<event>`` convention, so the stub it
        writes is what this overrides.
        """
        self.show_console()
        return True

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)


def _escape(text: str) -> str:
    """*text* with every character a shell would split or expand backslashed."""
    return "".join("\\" + char if char in _SHELL_SPECIAL else char for char in text)


class UserScreenPeek(Widget):
    """A layer over the whole screen that paints nothing and takes the next
    key or click: what DN's ``ShowUserScreen`` waited for.  Modal, so the
    console under it is shown and not typed into."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.modal = True
        self.can_focus = True
        self.dims_behind = False
        self.x = bind(lambda o: 0)
        self.y = bind(lambda o: 0)
        self.width = bind(lambda o: o.parent.width if o.parent is not None else 0)
        self.height = bind(lambda o: o.parent.height if o.parent is not None else 0)
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
        """Nothing: the console under it is the point."""

