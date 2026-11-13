"""Running what is typed: in the console or a window of its own, Execute OS command, and following
the shell's directory back into the panel.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

import asyncio
from time import monotonic
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog
from navml.history import HISTORY

from navigator.lib.system.subshell import CommandFinished
from navigator.widgets.shell.commands import ExecuteCommandLineInWindow
from navigator.widgets.shell.command_line.command_line import HISTORY_ID
from navigator.settings import SETTINGS
from navigator.widgets.shell.shell.helpers import _escape, elapsed_text

if TYPE_CHECKING:
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class Running(_Base):
    """Running what is typed: in the console or a window of its own, Execute OS command, and following"""

    async def execute_os_command(self) -> None:
        """File > Execute OS command: ``ExecDOSCmd`` -- DN's ``InputBox``, opened
        on the file at the active panel's cursor if it is one to run (followed
        by a blank, for its arguments), in the command line's history (DN's
        ``hsExecDOSCmd`` was apart from it: a departure); OK runs
        it as though it had been typed there.  *OS* where DN's title said *DOS*.
        *In a window* (not DN's) runs it in a window of its own instead, opened
        *Zoomed* and *Modal* as ticked."""
        from navigator.widgets.shell.execute_command_dialog import ExecuteCommandDialog

        text = ""
        manager = self.active_manager
        entry = manager.active_panel.selected if manager is not None else None
        if entry is not None and entry.is_executable:
            name = entry.name
            if entry.directory is not None:
                # A *Find:* entry by its whole path -- on the disk only: one
                # elsewhere cannot be run by a path from here, so its name.
                from navigator.lib.drives.root import on_disk

                place = on_disk(manager.active_panel.entry_location(entry))
                if place.is_local:
                    name = str(place.local)
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

        The line goes to the shell as typed -- a departure: DN's ``ExecString``
        split it at ``||`` into a batch file and expanded ``MakeCMDParams``'
        ``%1``..``%6`` / ``%11``..``%16`` (the two cursors' files' parts) and
        ``%%`` (``RUNCMD.INC:58-77``, ``ADVANCE.PAS:1936-1960``).  Here ``%``
        and ``||`` are the shell's (``date +%Y``, ``a || b``); Ctrl+Enter,
        Ctrl+[ and Ctrl+] put the cursor files' names on the line instead, and
        the user menu keeps macros of its own.
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
        # DN's ``TimerMark``: ``ExecString`` stamped whatever it ran.
        self._timer_started = monotonic() if self.command_line.timer else None
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
        started, self._timer_started = self._timer_started, None
        if started is not None and self.application is not None:
            # DN's ``ShowTimeInfo``, the Timer line's: how long it took.
            box = Dialog(title=tr("Information"), buttons="ok",
                         prompt=tr("Elapsed time: {time}").format(time=elapsed_text(monotonic() - started)))
            self.spawn(box.execute(self.application))

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
        otherwise let it take the directory DOS came back with.  A *Find:*
        listing keeps its place, as DN's find drive did (``Store`` kept every
        non-disk drive).  A remote panel goes back to the disk when the
        command ``cd``'d -- a departure: DN's non-disk drives always stayed;
        a ``cd`` typed on a server's panel here means the disk is wanted.
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
        elif (cwd is not None and cwd != panel.path and panel.found is None
              and not SETTINGS.startup.preserve_directory and not self._is_use_directory(cwd)):
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
