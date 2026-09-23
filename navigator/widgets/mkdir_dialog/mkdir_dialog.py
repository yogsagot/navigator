"""What OK means here, which is the whole of this file.

``accept()`` is the one thing a derived dialog usually has to say: everything
else -- the frame, the modality, Tab, Enter, Escape, the ``Alt+letter`` walk,
the answer coming back out of :meth:`~navml.widgets.dialog.Dialog.execute` --
is ``Dialog``'s already.
"""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog import Dialog


class MkdirDialog(Dialog):
    """F7: make a directory in the active panel."""

    def accept(self) -> Any:
        """The name to create, or ``None`` if the field is empty.

        ``None`` rather than ``""`` because that is what Cancel answers, and
        a caller should not have to tell an empty OK from a cancel in order to
        do nothing about either.
        """
        return self.entry.value.strip() or None
