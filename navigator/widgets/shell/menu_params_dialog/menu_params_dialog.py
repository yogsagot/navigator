"""What OK means in *Menu Parameters*: the line typed, empty or not."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog


class MenuParamsDialog(Dialog):
    """The words a user menu item's ``%3`` .. ``%9`` take."""

    def __init__(self, caption: str = "", default: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if caption:
            self.caption = caption
        self.entry.value = default

    def accept(self) -> Any:
        """The line as typed: an empty one is still an OK, and runs the item."""
        return self.entry.value
