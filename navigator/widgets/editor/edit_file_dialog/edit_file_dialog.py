"""What OK means in *Edit new file*: the name typed."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class EditFileDialog(Dialog):
    """Shift+F4: the name of a file to edit."""

    def accept(self) -> Any:
        """The name, or ``None`` for an empty field -- what Cancel answers too."""
        return self.entry.value.strip() or None
