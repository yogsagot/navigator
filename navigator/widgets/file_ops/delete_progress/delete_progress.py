"""What the delete's progress box writes, and what its one button means."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.system.progress import duration_text
from navigator.widgets.file_ops import background_button
from navigator.widgets.file_ops.copy_progress.copy_progress import fit_path, whole_path


class DeleteProgress(Dialog):
    """*Erase*: what is going, a gauge, and *Cancel*."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # *Cancel* where DN's ``dlStop`` said *Stop*: a departure in word only.
        # *Background* beside it, when the watcher can let the box go.
        background_button.wire(self, tr("~C~ancel"))

    def fit(self, path: str) -> str:
        """*path*, cut from the left to fit the row."""
        return fit_path("", path, self.width - 4)

    def whole(self, path: str) -> str:
        """*path* whole where its row cut it."""
        return whole_path("", path, self.width - 4)

    def count(self, done: int, total: int, percent: int) -> str:
        """``N of M (P%)``, the line under the gauge; *percent* is the bar's own.

        Nothing while the entries are still being counted.
        """
        if not total:
            return ""
        return tr("{done:,} of {total:,} ({percent}%)").format(done=done, total=total, percent=percent)

    def pace(self, speed: float, left: float) -> str:
        """``Speed 1,200 files/s, 0:42 left``; the speed alone while still counting, nothing before either."""
        if speed < 0:
            return ""
        n = round(speed)
        if left < 0:
            return tr_n("Speed {n:,} file/s", "Speed {n:,} files/s", n)
        return tr_n("Speed {n:,} file/s, {time} left", "Speed {n:,} files/s, {time} left", n,
                    time=duration_text(left))

    def accept(self) -> Any:
        """*Cancel* answers what Esc does; *Background* sends the box away."""
        return background_button.answer(self)
