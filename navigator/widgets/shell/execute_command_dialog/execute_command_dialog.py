"""What OK means in *Execute OS Command*: the line, and where it runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit.i18n import tr
from navml.widgets.dialog.dialog import Dialog

#: The check boxes' bits, in the order they are listed.
IN_WINDOW, ZOOMED, MODAL = 1, 2, 4


@dataclass(frozen=True)
class CommandChoice:
    """The line as typed, and whether -- and how -- it runs in a window."""

    command: str
    in_window: bool = False
    zoomed: bool = True
    modal: bool = False


class ExecuteCommandDialog(Dialog):
    """One line, seeded with *text*, the caret after it."""

    def __init__(self, text: str = "", *, in_window: bool = False, zoomed: bool = True,
                 modal: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.caption = tr("~C~ommand")
        self.line.value = text
        self.line.entry.anchor = None
        self.line.entry.cursor = len(text)
        self.options.value = (IN_WINDOW if in_window else 0) | (ZOOMED if zoomed else 0) | (MODAL if modal else 0)

    def accept(self) -> Any:
        bits = self.options.value
        return CommandChoice(self.line.value, bool(bits & IN_WINDOW), bool(bits & ZOOMED), bool(bits & MODAL))
