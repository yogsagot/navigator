"""What the delete's progress box writes, and what its one button means."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr
from navkit.reactive import unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.file_ops.copy_progress.copy_progress import fit_path


class DeleteProgress(Dialog):
    """*Erase*: what is going, a gauge, and *Cancel*."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # *Cancel* where DN's ``dlStop`` said *Stop*: a departure in word only.
        unbind(self.ok, Button.text)
        self.ok.text = tr("~C~ancel")

    def fit(self, path: str) -> str:
        """*path*, cut from the left to fit the row."""
        return fit_path("", path, self.width - 4)

    def count(self, done: int, total: int, percent: int) -> str:
        """``N of M (P%)``, the line under the gauge; *percent* is the bar's own.

        Nothing while the entries are still being counted.
        """
        if not total:
            return ""
        return tr("{done:,} of {total:,} ({percent}%)").format(done=done, total=total, percent=percent)

    def accept(self) -> Any:
        """*Cancel* answers what Esc does."""
        return None
