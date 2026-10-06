"""What OK means in *Make List File*: where, what each line says, and the boxes."""

from __future__ import annotations

from typing import Any

from navml.history import HISTORY
from navml.widgets.dialog.dialog import Dialog

from navigator.makelist import DEFAULT_NAME


class MakeListDialog(Dialog):
    """DN's ``TMakeListRec``: ``FileName``, ``Action`` and ``Options``.

    Opened on the last list file made and the last command run, as DN's
    ``HistoryStr(hsMakeList, 0)`` and ``HistoryStr(hsExecDOSCmd, 0)`` filled
    it, and on the boxes as they were last left.
    """

    def __init__(self, options: int = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        names = HISTORY.entries("make_list")
        commands = HISTORY.entries("command")
        self.file_name.value = names[0] if names else DEFAULT_NAME
        self.action.value = commands[0] if commands else ""
        self.options.value = options

    def accept(self) -> tuple[str, str, int] | None:
        """``(file name, action, options)``, or None with no file name."""
        name = self.file_name.value.strip()
        if not name:
            return None
        return name, self.action.value, self.options.value
