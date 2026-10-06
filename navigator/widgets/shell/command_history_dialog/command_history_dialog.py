"""What *Commands history* answers, and the changes it makes to the list.

``("run", command)``, ``("drop", command)`` or None.  *Kill* and *Edit* act
on the history (navml's ``HISTORY``, the command line's ``command`` list)
there and then, as ``TTHistList`` did on ``CmdStrings``, and the box stays;
a marked command is kept -- it is pinned -- and *Kill* refuses it, where DN
beeped.  An edited command goes in as the newest, where DN replaced it where
it stood: the store keeps its lists by when.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navml.history import HISTORY
from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.shell.command_line.command_line import HISTORY_ID


class CommandHistoryDialog(Dialog):
    """DN's ``CmdHistory``."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self._load(None)

    def _load(self, focus: str | None) -> None:
        commands = list(reversed(HISTORY.entries(HISTORY_ID)))
        self.commands.items = commands
        self.commands.kept = frozenset(c for c in commands if HISTORY.is_pinned(HISTORY_ID, c))
        if focus in commands:
            self.commands.cursor = commands.index(focus)
        else:
            self.commands.cursor = max(0, len(commands) - 1)
        self._pinned = self.commands.kept

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.run, self.drop, self.edit, self.kill, self.abandon)

    def _sync_pins(self) -> None:
        """What Space marked and unmarked, pinned and released in the store."""
        kept = self.commands.kept
        for command in kept ^ self._pinned:
            HISTORY.pin(HISTORY_ID, command, command in kept)
        self._pinned = kept

    def close(self, result: Any = None) -> None:
        self._sync_pins()
        super().close(result)

    def _answer(self, how: str) -> None:
        command = self.commands.selected
        self.close((how, command) if command is not None else None)

    async def on_run_click(self, event: Event) -> bool:
        self._answer("run")
        return True

    async def on_commands_chosen(self, event: Event) -> bool:
        self._answer("run")
        return True

    async def on_drop_click(self, event: Event) -> bool:
        self._answer("drop")
        return True

    async def on_kill_click(self, event: Event) -> bool:
        self.kill_selected()
        return True

    async def on_commands_killed(self, event: Event) -> bool:
        self.kill_selected()
        return True

    def kill_selected(self) -> None:
        """*Kill*, Del: the command forgotten -- unless it is marked."""
        self._sync_pins()
        command = self.commands.selected
        if command is None or command in self.commands.kept:
            return
        index = self.commands.cursor
        HISTORY.remove(HISTORY_ID, command)
        items = self.commands.items
        self._load(items[index + 1] if index + 1 < len(items) else (items[index - 1] if index else None))
        self.commands.focus()

    async def on_edit_click(self, event: Event) -> bool:
        self.spawn(self.edit_selected())
        return True

    async def edit_selected(self) -> None:
        """*Edit*: ``InputBox(dlEditHistory, ...)`` over the command."""
        from navigator.widgets.shell.edit_line_dialog import EditLineDialog

        self._sync_pins()
        command = self.commands.selected
        if command is None:
            return
        edited = await EditLineDialog(command).execute(self.application)
        if edited is None or not edited.strip() or edited == command:
            self.commands.focus()
            return
        pinned = command in self.commands.kept
        HISTORY.remove(HISTORY_ID, command)
        HISTORY.add(HISTORY_ID, edited)
        if pinned:
            HISTORY.pin(HISTORY_ID, edited)
        self._load(edited)
        self.commands.focus()
