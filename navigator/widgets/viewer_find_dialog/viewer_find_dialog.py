"""What OK means in *Find*: a :class:`~navigator.viewer.ViewSearch`, or nothing."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.viewer import ViewSearch


class ViewerFindDialog(Dialog):
    """F7 in a viewer: what to look for, and how."""

    def __init__(self, last: ViewSearch | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if last is not None:
            # DN opened the dialog on the last search, text and switches.
            self.what.value = last.what
            self.options.value = int(last.case) | int(last.words) << 1
            self.direction.value = int(last.backward)

    def accept(self) -> Any:
        """The search, or ``None`` for an empty line -- which is what Cancel says."""
        what = self.what.value
        if not what:
            return None
        return ViewSearch(
            what,
            case=bool(self.options.value & 1),
            words=bool(self.options.value & 2),
            backward=self.direction.value == 1,
        )
