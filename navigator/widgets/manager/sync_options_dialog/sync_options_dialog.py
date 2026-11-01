"""What the *Synchronize options* dialog opens on, and what OK means: a
:class:`~navigator.lib.file_ops.dirsync.SyncOptions`.

It opens on what was last accepted, kept in ``navigator.ini``'s
``[synchronize]`` (:func:`~navigator.widgets.manager.sync_window.sync_window.sync_options`).
"""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops.dirsync import TOLERANCES, SyncOptions
from navigator.settings import SynchronizeData


class SyncOptionsDialog(Dialog):
    """*Synchronize options*: which files, how near two times are the same, and *Asymmetric*."""

    def __init__(self, options: SyncOptions | None = None, **kwargs: Any) -> None:
        """*options* are what the dialog opens on."""
        super().__init__(**kwargs)
        options = options or SyncOptions()
        self.mask.value = options.mask
        self.mask.entry.select_all()
        times = next((name for name, seconds in TOLERANCES.items() if seconds == options.tolerance), "fat")
        self.times.value = self.times.sel = SynchronizeData.TIMES.index(times)
        self.options.value = (1 if options.hour_shift else 0) | (2 if options.asymmetric else 0)

    def accept(self) -> SyncOptions:
        return SyncOptions(
            mask=self.mask.value.strip(),
            tolerance=TOLERANCES[SynchronizeData.TIMES[self.times.value]],
            hour_shift=bool(self.options.value & 1),
            asymmetric=bool(self.options.value & 2),
        )
