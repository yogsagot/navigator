"""What OK means in *Remember directory settings*: remember, and whether for the directories below too."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

#: The *Also for its subdirectories* box's bit.
SUBDIRS = 0x01


class RememberDirectoryDialog(Dialog):
    """OK answers ``{"subdirs": bool}``, Esc None."""

    def __init__(self, name: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The tail of a path too long for the line, as Del's bookmark question cuts it.
        room = max(4, self.prompt_tail.width or 52)
        shown = name if len(name) <= room else "..." + name[-(room - 3):]
        self.prompt_tail.text = escape_caption(shown)

    def accept(self) -> dict[str, bool]:
        return {"subdirs": bool(self.options.value & SUBDIRS)}
