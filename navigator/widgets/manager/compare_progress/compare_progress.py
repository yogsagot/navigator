"""The recursive compare's box: a path fitted to its line, and the count said."""

from __future__ import annotations

from typing import Any

from navkit import glyphs
from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog


class CompareProgress(Dialog):
    """Where *Window, recursive* is comparing, and how many differences it has found."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.ok.text = tr("Cancel")

    def fit(self, path: str) -> str:
        """*path*, its start cut to ``…`` if the line is too short, as the search's box does."""
        room = max(4, self.modal_width - 4)
        if len(path) <= room:
            return path
        marker = glyphs.ellipsis(self.glyphs)
        return marker + path[-(room - len(marker)):]

    def count_text(self, count: int) -> str:
        if not count:
            return tr("No differences found")
        return tr_n("{n} difference found", "{n} differences found", count)
