"""What the checksums box writes, and what its one button means."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr, tr_n
from navkit.reactive import unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.file_ops.copy_progress.copy_progress import fit_path, whole_path


class ChecksumProgress(Dialog):
    """Files being hashed: which one, how far through them all, and *Cancel*."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        unbind(self.ok, Button.text)
        self.ok.text = tr("~C~ancel")

    def fit(self, path: str) -> str:
        """*path*, cut from the left to fit the row."""
        return fit_path("", path, self.width - 6)

    def whole(self, path: str) -> str:
        """*path* whole where its row cut it."""
        return whole_path("", path, self.width - 6)

    @staticmethod
    def counted(done: int, total: int, percent: int) -> str:
        """``3 of 12 files, 40%``; the percentage alone before the files are known."""
        if total <= 0:
            return f"{percent}%"
        return tr_n("{done} of {n} file, {percent}%", "{done} of {n} files, {percent}%", total,
                    done=done, percent=percent)

    def accept(self) -> Any:
        """*Cancel* answers what Esc does: nothing, which stops the work."""
        return None
