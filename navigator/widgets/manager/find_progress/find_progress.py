"""The search box's one piece of Python: a path fitted to its line."""

from __future__ import annotations

from typing import Any

from navkit import glyphs

from navml.widgets.dialog.dialog import Dialog


class FindProgress(Dialog):
    """Where Alt+F7 is looking, and what it has found so far."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.ok.text = "Cancel"

    def fit(self, path: str) -> str:
        """*path*, its start cut to ``…`` (``...`` in ASCII) if the line is too
        short (DN's ``Cut``)."""
        room = max(4, self.modal_width - 4)
        if len(path) <= room:
            return path
        marker = glyphs.ellipsis(self.glyphs)
        return marker + path[-(room - len(marker)):]
