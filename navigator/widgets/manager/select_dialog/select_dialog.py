"""What OK means in *Select* and *Unselect*: a mask, and whether to invert it."""

from __future__ import annotations

from typing import Any

from navml.history import HISTORY
from navml.widgets.dialog.dialog import Dialog


class SelectDialog(Dialog):
    """Gray ``+`` / ``-``: which files to tag, or to untag."""

    #: What the line holds with no history yet.  DN's ``x_x`` was ``*.*``, which
    #: on DOS meant every file; on POSIX that is ``*``.
    DEFAULT_MASK = "*"

    def __init__(self, invert: bool = False, **kwargs: Any) -> None:
        """*invert* ticks *Except mask* before the dialog opens -- Shift held."""
        super().__init__(**kwargs)
        # DN opened on the newest mask in ``hsSelectBox``, or its default --
        # selected, as ``TInputLine.SetData`` left it, so typing replaces it.
        entries = HISTORY.entries("select")
        self.mask.value = entries[0] if entries else self.DEFAULT_MASK
        self.mask.entry.select_all()
        self.options.value = int(invert)

    def accept(self) -> Any:
        """``(mask, invert)``, or ``None`` for an empty line -- what Cancel says."""
        mask = self.mask.value.strip()
        if not mask:
            return None
        return mask, bool(self.options.value & 1)
