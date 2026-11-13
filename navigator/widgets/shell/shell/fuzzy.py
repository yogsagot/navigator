"""fzf and zoxide (a departure: DOS Navigator had neither): history, directories and files picked
fuzzily.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from navkit.i18n import tr

from navml.history import HISTORY

from navigator.lib.system import fuzzy
from navigator.lib.system.subshell import HistoryReady, PickChosen
from navigator.widgets.shell.command_line.command_line import HISTORY_ID
from navigator.widgets.shell.shell.helpers import _escape

if TYPE_CHECKING:
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class Fuzzy(_Base):
    """fzf and zoxide (a departure: DOS Navigator had neither): history, directories and files picked"""

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
