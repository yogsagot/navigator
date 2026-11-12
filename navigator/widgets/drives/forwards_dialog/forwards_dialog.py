"""The handlers behind ``forwards_dialog.nml``: a connection's port forwards.

The forwards are copied in and edited here; OK answers the list (a
:class:`~navigator.lib.drives.forwards.Forward` each), Cancel None and
nothing changes.  The link manager keeps them with the connection when it
is saved (``RemoteProfile.forwards``)."""

from __future__ import annotations

from typing import Any

from navkit.events import KeyEvent
from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives.forwards import Forward, describe


class ForwardsDialog(Dialog):
    """The forwards, one a row, with *Add*, *Edit* and *Delete*."""

    def __init__(self, forwards: list[Forward] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.items: list[Forward] = list(forwards or ())
        self._refresh(0)

    def mounted(self) -> None:
        super().mounted()
        (self.forwards if self.items else self.append).focus()

    def key_hints(self) -> list[tuple[str, str]]:
        return [("Ins", tr("Add")), ("F4", tr("Edit")), ("Del", tr("Delete"))]

    def _refresh(self, cursor: int) -> None:
        self.forwards.items = [escape_caption(describe(forward)) for forward in self.items] or [
            escape_caption(tr("(none — Add makes one)"))]
        self.forwards.cursor = max(0, min(cursor, len(self.items) - 1))
        self.edit.disabled = self.delete.disabled = not self.items

    @property
    def current(self) -> int | None:
        cursor = self.forwards.cursor
        return cursor if 0 <= cursor < len(self.items) else None

    def accept(self) -> list[Forward]:
        return list(self.items)

    async def on_key(self, event: KeyEvent) -> bool:
        """Ins, F4 and Del, wherever the keyboard is in the box."""
        if not (event.ctrl or event.alt or event.shift):
            work = {"insert": self.add_forward, "f4": self.edit_forward, "delete": self.delete_forward}.get(event.key)
            if work is not None:
                self.spawn(work())
                return True
        return await super().on_key(event)

    async def add_forward(self) -> None:
        """A new forward, after the one under the cursor."""
        from navigator.widgets.drives.forwards_dialog.forward_dialog import ForwardDialog

        forward = await ForwardDialog().execute(self.application)
        if forward is None:
            return
        at = (self.current + 1) if self.current is not None else len(self.items)
        self.items.insert(at, forward)
        self._refresh(at)
        self.forwards.focus()

    async def edit_forward(self) -> None:
        from navigator.widgets.drives.forwards_dialog.forward_dialog import ForwardDialog

        index = self.current
        if index is None:
            return
        forward = await ForwardDialog(self.items[index]).execute(self.application)
        if forward is not None:
            self.items[index] = forward
            self._refresh(index)
        self.forwards.focus()

    async def delete_forward(self) -> None:
        index = self.current
        if index is None:
            return
        del self.items[index]
        self._refresh(index)
        (self.forwards if self.items else self.append).focus()


__all__ = ["ForwardsDialog"]
