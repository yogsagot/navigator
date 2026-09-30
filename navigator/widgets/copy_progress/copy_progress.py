"""What the copy's progress box writes beside its gauges, and what its one button means."""

from __future__ import annotations

from typing import Any

from navkit.reactive import unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog


class CopyProgress(Dialog):
    """*Copy* or *Rename/move*: two gauges and *Stop*.

    The gauges are ``file_bar`` and ``total_bar``, two
    ``ProgressBar`` widgets, so they follow the box's width.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # DN's ``dlStop``, as `SearchProgress' relabels it.
        unbind(self.ok, Button.text)
        self.ok.text = "~S~top"

    def fit(self, label: str, path: str) -> str:
        """*label* and then *path*, the path cut from the left to fit the row.

        From the left because the end of a path is what tells one file from
        the next; the box widening to fit, as ``TWhileView`` did, would make
        it jump about with every name.
        """
        room = max(4, self.width - 4 - len(label))
        if len(path) > room:
            path = "..." + path[len(path) - room + 3 :]
        return escape_caption(label + path)

    def count(self, done: int, percent: int) -> str:
        """``N bytes (P%)``, the line under each gauge; *percent* is the bar's own."""
        return f"{done:,} bytes ({percent}%)"

    def accept(self) -> Any:
        """*Stop* answers what Esc does."""
        return None
