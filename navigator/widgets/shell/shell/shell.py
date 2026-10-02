"""The handlers behind ``shell.nml``.

What the document says is the two bars, the command line and the two layers
between them; what is left here is opening the file manager on the desktop,
Ctrl+O, and running what is typed on the command line.

This file never names the generated class.  ``class Shell(DockLayout)`` is
what a Python-only widget would say too, and it is the base the markup's
``Shell(DockLayout):`` head names.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.commands import Command
from navkit.events import Event, KeyEvent
from navkit.reactive import bind, computed, effect
from navkit.screen import Surface
from navkit.stylesheet import Stylesheet
from navml.widgets.menu.commands import OpenMenu
from navml.history import HISTORY

from navigator.subshell import CommandFinished, CompletionsReady, HistoryChosen, HistoryReady
from navigator.widgets.manager.commands import HideLeft, HideRight, ToggleMark
from navigator.widgets.shell.commands import (
    About,
    CommandLineEnd,
    CommandLineHome,
    CompleteCommandLine,
    EditorDefaults,
    ExecuteCommandLine,
    FileManagerDefaults,
    FileManagerSetup,
    InsertName,
    InsertPath,
    InterfaceSetup,
    NewManager,
    OpenTreeWindow,
    SetupConfirmation,
    StartupSetup,
    SystemSetup,
    ToggleMarkBySpace,
)
from navigator.widgets.shell.command_line.command_line import HISTORY_ID
from navml.widgets.layout.dock_layout import DockLayout

from navigator.scheme import default_scheme
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager

if TYPE_CHECKING:
    from navigator.widgets.editor.edit_window import FileSaved

#: The most candidates a Tab puts in its list; ``compgen -c`` on one letter
#: can be thousands.
MAX_COMPLETIONS = 500

#: What a file name has to have escaped to reach a command as one word.
_SHELL_SPECIAL = set(" \t'\"\\$&;|<>()*?[]!#{}`")


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
        #: ``.root`` on the whole screen while Navigator runs as root, so a
        #: sheet can mark every window and dialog under it.
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.add_class("root")
        self.console.cwd = left
        self.console.subshell.on_finished = self._command_finished
        # A shell that exits while it has the real terminal -- ``exit`` typed
        # at it -- can no longer hand it back, so Navigator takes it.
        self.console.subshell.on_exit = lambda status: self.end_relay()
        # Options > Configuration > Interface: ``ouiClock``, ``ouiHideStatus``,
        # ``ouiHideMenu`` and ``ouiHideCmdline``.  Bound here rather than in
        # the markup, which evaluates a line that reads nothing of its widget
        # once -- and these read only SETTINGS.
        interface = SETTINGS.interface
        self.clock.visible = bind(lambda w: interface.clock)
        self.keybar.visible = bind(lambda w: not interface.hide_status_line)
        # *Auto hide Command Line*: DN 1.51 declared the box and never read
        # it, so this is the behaviour its ``CheckSize`` and ``ToggleCmdLine``
        # gave a hidden line -- shown once it holds text, its row back to the
        # desktop once it is empty again.
        self.command_line.visible = bind(
            lambda w: not interface.hide_command_line
            and (not interface.auto_hide_command_line or w.value != "")
        )
        # A hidden bar gives the desktop its row and floats over it while a
        # menu is open -- ``current`` is -1 only while none is.
        self.menu.inline_style = bind(
            lambda w: "dock: none" if interface.hide_menu_bar else "dock: top; basis: 1"
        )
        self.menu.visible = bind(lambda w: not interface.hide_menu_bar or w.current >= 0)
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
        #: Whether the real terminal was handed to the shell for a command
        #: rather than by Ctrl+O, and so is to be taken back when it is done.
        self._relayed_for_command = False
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
        if showing and not SETTINGS.system.internal_terminal and self.relay_terminal():
            return
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

    def _front_directory(self) -> Path | None:
        """The active panel's directory in the file manager in front, if one is open."""
        window = self.desktop.active_window
        manager = window if isinstance(window, Manager) else self.active_manager
        return manager.active_panel.path if manager is not None else None

    def _follow_panel(self) -> None:
        """Keep the idle shell where the panel is, so its prompt names that directory."""
        where = self._front_directory()
        if where is not None:
            self.console.subshell.sync(where)

    @computed
    def command_prompt(self) -> str:
        """``<directory>$``: where the file manager in front is, as ``GetDir`` said.

        DOS Navigator's prompt was the process's current directory, which a
        focused panel kept equal to its own.  A command runs in the active
        panel's directory here, so the prompt says that one.  With no file
        manager open it is where the shell last was.  Shown only until the
        shell's own prompt arrives (:attr:`command_prompt_cells`).  It ends in
        a POSIX shell's ``$``, not DOS's ``PROMPT $P$G`` ``>``.
        """
        where = self._front_directory()
        if where is None:
            where = self.console.subshell.cwd or self.console.cwd
        return f"{where}$" if where is not None else "$"

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
        """
        console = self.console
        where = self._front_directory()
        if where is not None and console.prompt_cwd != where:
            # Read so the next prompt re-decides, whatever it says.
            console.prompts
            if console.subshell.catching_up:
                return console.prompt
            return ()
        return console.prompt

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
        if isinstance(
            command,
            (ExecuteCommandLine, CommandLineHome, CommandLineEnd, CompleteCommandLine,
             InsertName, InsertPath),
        ) and (self._editor_has_keys() or SETTINGS.interface.hide_command_line):
            # A hidden command line runs and takes nothing: DN's
            # ``cmExecCommandLine`` and ``cmInsertName`` did nothing under
            # ``ouiHideCmdline``, and the keys fall through to the panel.
            return False
        if isinstance(command, (InsertName, InsertPath)):
            return self._panel_entry() is not None
        if isinstance(command, (HideLeft, HideRight)):
            # Reached here only from outside a file manager: from the
            # console, DN's user screen, and not from a viewer or an editor.
            return self.console_visible and self.active_manager is not None
        if isinstance(command, ToggleMarkBySpace):
            # ``CmdLine.Str <> ''``: once anything is on the line -- a blank
            # included -- Space types.  Otherwise it is Insert, wherever the
            # file manager would take Insert.
            manager = self.active_manager
            return (
                not self.command_line.value
                and manager is not None
                and manager.enables(ToggleMark())
            )
        if isinstance(
            command, (ExecuteCommandLine, CommandLineHome, CommandLineEnd, CompleteCommandLine)
        ):
            if not self.command_line.value.strip():
                return False
            if isinstance(command, ExecuteCommandLine):
                return not self.console.busy
            if isinstance(command, CompleteCommandLine):
                subshell = self.console.subshell
                return subshell.is_running and subshell.can_complete and not self.console.busy
        return super().enables(command)

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
        """``FileChanged``: every panel showing the saved file's directory re-reads."""
        directory = event.path.parent
        for window in self.desktop.windows():
            if isinstance(window, Manager):
                for panel in (window.left, window.right):
                    if panel.path == directory:
                        panel.reload()
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

    def _panel_entry(self) -> tuple[Path, Any] | None:
        """The active panel's directory and the entry under its cursor, if any."""
        manager = self.active_manager
        if manager is None:
            return None
        panel = manager.active_panel
        entry = panel.selected
        return (panel.path, entry) if entry is not None else None

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
            text = _escape(str(directory / entry.name))
        else:
            text = _escape(entry.name)
        self.command_line.insert_name(text)

    async def on_toggle_mark_by_space(self, event: ToggleMarkBySpace) -> bool:
        self.active_manager.active_panel.toggle_mark()
        return True

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

    def run_command(self, command: str) -> None:
        """Run *command* as though it had been typed on the command line."""
        if not command.strip():
            return
        HISTORY.add(HISTORY_ID, command)
        self.command_line.clear()
        self._walk = None
        cwd = self._command_directory()
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

    def _follow_shell(self, cwd: Path | None) -> None:
        """Send the active panel wherever the shell went, and re-read both."""
        manager = self.active_manager
        if manager is None:
            return
        panel = manager.active_panel
        if cwd is not None and cwd != panel.path and cwd.is_dir():
            panel.path = cwd
        for each in (manager.left, manager.right):
            each.reload()

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
        start = current.active_panel.path if current is not None else Path.cwd()
        self.desktop.open(Manager(start, start))
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

    async def on_system_setup(self, event: SystemSetup) -> bool:
        from navigator.widgets.setup.system_setup_dialog import SystemSetupDialog

        self.spawn(self.setup(SystemSetupDialog(), "system"))
        return True

    async def on_startup_setup(self, event: StartupSetup) -> bool:
        from navigator.widgets.setup.startup_dialog import StartupDialog

        self.spawn(self.setup(StartupDialog(), "startup"))
        return True

    async def on_interface_setup(self, event: InterfaceSetup) -> bool:
        from navigator.widgets.setup.interface_dialog import InterfaceDialog

        self.spawn(self.setup(InterfaceDialog(), "interface"))
        return True

    async def on_setup_confirmation(self, event: SetupConfirmation) -> bool:
        from navigator.widgets.setup.confirmations_dialog import ConfirmationsDialog

        self.spawn(self.setup(ConfirmationsDialog(), "confirmations"))
        return True

    async def on_editor_defaults(self, event: EditorDefaults) -> bool:
        from navigator.widgets.setup.editor_defaults_dialog import EditorDefaultsDialog

        self.spawn(self.setup(EditorDefaultsDialog(), "editor", "viewer"))
        return True

    async def on_file_manager_setup(self, event: FileManagerSetup) -> bool:
        from navigator.widgets.setup.fm_setup_dialog import FMSetupDialog

        self.spawn(self.setup(FMSetupDialog(), "file_manager"))
        return True

    async def on_file_manager_defaults(self, event: FileManagerDefaults) -> bool:
        from navigator.widgets.setup.fm_defaults_dialog import FMDefaultsDialog

        self.spawn(self.setup(FMDefaultsDialog(), "panel_defaults"))
        return True

    async def setup(self, dialog: Any, *sections: str) -> None:
        """Run a setup *dialog*, then apply what it accepted and save it.

        DN's ``ExecResource`` and ``cmUpdateConfig`` in one: the values are
        assigned to :data:`SETTINGS`, whose bindings repaint whatever shows
        them, and each section is written back to ``navigator.ini`` -- that
        section alone, over whatever the file holds now.  A dialog over one
        section answers that section's values; over several, a dict of them
        by section name.  A file that cannot be written is said so, and the
        values stay applied for this session.
        """
        answer = await dialog.execute(self.application)
        if answer is None:
            return
        changes = answer if len(sections) > 1 else {sections[0]: answer}
        for name in sections:
            SETTINGS.section(name).update(changes[name])
        try:
            for name in sections:
                SETTINGS.save(section=name)
        except OSError as error:
            from navml.widgets.dialog.dialog import Dialog

            await Dialog(
                title="Error",
                prompt=f"Cannot save the settings: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)

    # -- the directory tree window --------------------------------------------

    async def on_open_tree_window(self, event: OpenTreeWindow) -> bool:
        """Disk > Directory tree: a tree window, opened on the active panel's directory."""
        from navigator.widgets.tree.tree_window import TreeWindow

        manager = self.active_manager
        panel = manager.active_panel if manager is not None else None
        if panel is None:
            self.desktop.open(TreeWindow())
        else:
            self.desktop.open(TreeWindow(start=panel.path, hidden=panel.show_hidden))
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


def _escape(text: str) -> str:
    """*text* with every character a shell would split or expand backslashed."""
    return "".join("\\" + char if char in _SHELL_SPECIAL else char for char in text)
