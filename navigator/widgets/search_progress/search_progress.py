"""What the progress box computes, and what its one button means."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

#: ``StrGrd``'s width: thirty columns of gauge.
GAUGE = 30


class SearchProgress(Dialog):
    """*Search Progress*: a gauge, a percentage, and *Stop*."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # DN's ``dlStop``: the dialog's own button, renamed.
        self.ok.text = "~S~top"

    def percent(self) -> int:
        """DN's ``Percent(L, I)``."""
        if self.total <= 0:
            return 100
        return min(100, max(0, self.position * 100 // self.total))

    def gauge_text(self) -> str:
        """``StrGrd(L, I, 30)``: ``█`` for the part done, ``▒`` for the rest."""
        done = GAUGE if self.total <= 0 else min(GAUGE, max(0, self.position * GAUGE // self.total))
        return "█" * done + "▒" * (GAUGE - done)

    def accept(self) -> Any:
        """*Stop* answers what Esc does: nothing, which is a stopped search."""
        return None
