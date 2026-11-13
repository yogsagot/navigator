"""The console and the real terminal: Ctrl+O, the user screen, relaying keys Midnight Commander's
way, the menu and the keys nothing nearer took, and the console's history keys.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from navkit.events import KeyEvent
from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog
from navml.widgets.menu.commands import OpenMenu

from navigator.lib.system.subshell import HistoryChosen
from navigator.settings import SETTINGS

if TYPE_CHECKING:
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class ConsoleMixin(_Base):
    """The console and the real terminal: Ctrl+O, the user screen, relaying keys Midnight Commander's"""

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

    async def command_history(self) -> None:
        """Alt+F8: ``CmdHistory`` -- *Run* puts the command on the line and runs
        it, *Drop* puts it there alone, the cursor at its end -- but not on a
        hidden line (``ouiHideCmdline``), which takes nothing."""
        from navigator.widgets.shell.command_history_dialog import CommandHistoryDialog

        answer = await CommandHistoryDialog().execute(self.application)
        if answer is None:
            return
        how, command = answer
        if how == "run":
            self.run_command(command)
        elif not SETTINGS.interface.hide_command_line:
            # DN's ``CurString := DT.I``: Ctrl+E/Ctrl+X go on from the one chosen.
            self.command_line.walk_to(command)

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

    def show_user_screen(self) -> None:
        """DN's ``cmShowUserScreen`` (Alt+F5, and Esc on an empty line under
        *ESC for user screen*): the console, until any key or click, which
        then goes nowhere else and the windows come back.  Already showing
        (Ctrl+O's), it stays -- DN's never closed the Output window either;
        with *Use internal terminal* off it is Ctrl+O's handing over of the
        real terminal."""
        if self.console_visible:
            return
        if not SETTINGS.system.internal_terminal:
            self.toggle_console()
            return
        app = self.application
        if app is None:
            return
        self.toggle_console()
        if not self.console_visible:
            return
        self.spawn(self._peek(app))

    async def _peek(self, app: Any) -> None:
        # The user screen, not a page of history the view was scrolled back to.
        self.console.screen.scroll_to_bottom()
        await UserScreenPeek(console=self.console).execute(app)
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

        The active window's own menu, if it names one (``f10_menu``), is
        dropped instead: the editor's, as DN's editor window had a bar of its
        own that ``cmMenu`` reached first.  Every other window's F10 is the
        bar's first entry, as theirs had none.
        """
        own = getattr(self.desktop.active_window, "f10_menu", None)
        entries = self.menu.entries()
        if own is not None and own in entries:
            self.menu.open(entries.index(own), drop=True)
        else:
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
        # ``TCommandLine.HandleEvent`` took none -- but a character typed with
        # Shift starts the panel's quick search, as ``TFilePanel`` did then.
        if SETTINGS.interface.hide_command_line:
            return self._search_with_the_line_hidden(event)
        if self._console_is_the_terminal() and await self._terminal_key(event):
            return True
        if self._panel_keeps(event):
            return False
        if await self.command_line.on_key(event):
            return True
        # *ESC for user screen* (``ouiEsc``): Esc with nothing on the line
        # sends ``cmShowUserScreen`` -- Alt+F5's peek, until any key.  A line
        # with text was cleared by the Esc above instead.
        if event.matches("escape") and SETTINGS.interface.esc_user_screen:
            self.show_user_screen()
            return True
        return False

    def _panel_keeps(self, event: KeyEvent) -> bool:
        """A plain arrow, Home or End a panel declined, with *Use arrows* off:
        not the line's either -- DN's ``TSpecScroll`` let it go nowhere.  DN's
        test is read for its intent (:meth:`Panel.arrows_to_line`)."""
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
