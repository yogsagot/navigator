"""What OK means in *Find duplicates*: a :class:`~navigator.lib.file_ops.duplicates.DuplicatesRequest`.

The box opens as it was last left, for the session.
"""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops import filefind
from navigator.lib.file_ops.duplicates import DuplicatesRequest

#: The last answers: the mask and the size as typed, the box as a bit.
_session: dict[str, Any] = {"mask": filefind.filetypes.ALL_FILES, "min_size": "1", "options": 1}


class DuplicatesDialog(Dialog):
    """The mask, the smallest size compared, and whether to go below the directory."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.mask.value = _session["mask"]
        self.min_size.value = _session["min_size"]
        self.options.value = _session["options"]

    def valid(self) -> bool:
        """Refused, with a box saying why, while the size is not a number of bytes."""
        if (self.min_size.value.strip() or "1").isdigit():
            return True
        if self.application is not None:
            box = Dialog(title=tr("Error"), prompt=tr("The minimum size is a number of bytes"), buttons="ok")
            self.spawn(box.execute(self.application))
        return False

    def accept(self) -> DuplicatesRequest:
        size = self.min_size.value.strip() or "1"
        _session.update(mask=self.mask.value, min_size=size, options=self.options.value)
        return DuplicatesRequest(mask=self.mask.value.replace(" ", "") or filefind.filetypes.ALL_FILES,
                                 min_size=max(1, int(size)), recursive=bool(self.options.value & 1))
