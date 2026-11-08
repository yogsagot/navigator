"""What OK means in *Find*: a :class:`~navigator.lib.viewer.ViewSearch`, or nothing."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.viewer import ViewSearch


class ViewerFindDialog(Dialog):
    """F7 in a viewer: what to look for, and how."""

    def __init__(self, last: ViewSearch | None = None, *, encoding: str = "utf-8", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The *Hex* line shows the text in the viewer's encoding.
        self.hex.encoding = encoding
        if last is not None:
            # DN opened the dialog on the last search, text and switches --
            # and here its bytes, when hex made some the text cannot say.
            self.what.value = last.what
            self.options.value = int(last.case) | int(last.words) << 1
            self.direction.value = int(last.backward)
        self.hex.data = self._bytes_of(self.what.value)
        if last is not None and last.data is not None:
            self.hex.set_data(last.data)

    def _bytes_of(self, text: str) -> bytes:
        return text.encode(self.hex.encoding, errors="ignore")

    def accept(self) -> Any:
        """The search, or ``None`` for an empty line -- which is what Cancel says."""
        what, data = self.what.value, self.hex.data
        if not what and not data:
            return None
        return ViewSearch(
            what,
            case=bool(self.options.value & 1),
            words=bool(self.options.value & 2),
            backward=self.direction.value == 1,
            # Only bytes the text is not, in this encoding: hex made them.
            data=None if data == self._bytes_of(what) else data,
        )
