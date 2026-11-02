"""What OK means in *Query*: the statement typed, or None for nothing."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class QueryDialog(Dialog):
    """F6: one statement to run, reading only."""

    def accept(self) -> Any:
        text = self.sql.value.strip()
        return text or None
