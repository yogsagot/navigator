"""The search box's one piece of Python: a path fitted to its line."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class FindProgress(Dialog):
    """Where Alt+F7 is looking, and what it has found so far."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.ok.text = "Cancel"

    def fit(self, path: str) -> str:
        """*path*, its start cut to ``...`` if the line is too short (DN's ``Cut``)."""
        room = max(4, self.modal_width - 4)
        return path if len(path) <= room else "..." + path[-(room - 3):]
