"""What OK answers: the label, empty for none."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class BookmarkLabelDialog(Dialog):
    """F2 in the bookmarks box: name a bookmark."""

    def accept(self) -> Any:
        """The label, stripped -- ``""`` takes it away, where Cancel answers None."""
        return self.entry.value.strip()
