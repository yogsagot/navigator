"""What OK means in *Compare directories*: a :class:`~navigator.dircompare.CompareRequest`."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.dircompare import CompareRequest


class CompareDialog(Dialog):
    """Panel > Compare directories: what to compare, and what to do with what differs."""

    def accept(self) -> Any:
        options = self.options.value
        return CompareRequest(
            size=bool(options & 1),
            time=bool(options & 2),
            attributes=bool(options & 4),
            contents=bool(options & 8),
            select=self.mode.value == 0,
        )
