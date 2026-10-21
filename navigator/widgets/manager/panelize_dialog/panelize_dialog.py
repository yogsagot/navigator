"""What OK means in the box: the command typed, if there is one."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class PanelizeDialog(Dialog):
    """The line seeded with *command*, the last one run unless given."""

    def __init__(self, command: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.line.value = command
        self.line.entry.anchor, self.line.entry.cursor = 0, len(command)

    def accept(self) -> Any:
        """The command, or ``None`` for an empty line, as Cancel answers."""
        return self.line.value.strip() or None
