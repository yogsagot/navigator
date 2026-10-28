"""What the copy's progress box writes beside its gauges, and what its one button means."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr, tr_n
from navkit.reactive import unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.system.progress import duration_text
from navigator.widgets.manager.panel.panel import human_size


def fit_path(label: str, path: str, width: int) -> str:
    """*label* and then *path*, the path cut from the left to fit *width* cells.

    From the left because the end of a path is what tells one file from
    the next; the box widening to fit, as ``TWhileView`` did, would make
    it jump about with every name.
    """
    room = max(4, width - len(label))
    if len(path) > room:
        path = "..." + path[len(path) - room + 3 :]
    return escape_caption(label + path)


def whole_path(label: str, path: str, width: int) -> str:
    """*path* whole where :func:`fit_path` cuts it, else ``""``: its row's tooltip."""
    return path if len(path) > max(4, width - len(label)) else ""


class CopyProgress(Dialog):
    """*Copy* or *Rename/move*: two gauges and *Stop*.

    The gauges are ``file_bar`` and ``total_bar``, two
    ``ProgressBar`` widgets, so they follow the box's width.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # DN's ``dlStop``, as `SearchProgress' relabels it.
        unbind(self.ok, Button.text)
        self.ok.text = tr("~S~top")

    def fit(self, label: str, path: str) -> str:
        """*label* and then *path*, cut to the row: :func:`fit_path`."""
        return fit_path(label, path, self.width - 4)

    def whole(self, label: str, path: str) -> str:
        """*path* whole where its row cut it: :func:`whole_path`."""
        return whole_path(label, path, self.width - 4)

    def count(self, done: int, percent: int) -> str:
        """``N bytes (355MB, P%)``, the line under each gauge; *percent* is the bar's own.

        The short size as the speed row writes it, left out under a kilobyte,
        where it would only say the count again.
        """
        if done < 1024:
            return tr_n("{n:,} byte ({percent}%)", "{n:,} bytes ({percent}%)", done, percent=percent)
        return tr_n("{n:,} byte ({size}, {percent}%)", "{n:,} bytes ({size}, {percent}%)", done,
                    size=human_size(done) + "B", percent=percent)

    def pace(self, speed: float, left: float) -> str:
        """``Speed 9.5MB/s, 0:42 left``; the speed alone with no total, nothing before either is known."""
        if speed < 0:
            return ""
        rate = human_size(int(speed)) + "B"
        if left < 0:
            return tr("Speed {speed}/s").format(speed=rate)
        return tr("Speed {speed}/s, {time} left").format(speed=rate, time=duration_text(left))

    def accept(self) -> Any:
        """*Stop* answers what Esc does."""
        return None
