"""The menu bar's ``>MACRO<``, before *ROOT* and the clock, while keys are recorded.

DOS Navigator's clock drew ``>MACRO<`` in its place while a key macro was
being recorded (``GAUGES.PAS``, ``MacroRecord``); here it stands beside the
clock rather than over it, as *ROOT* does, so the time still shows.  Its
tooltip says which slot and how recording ends
(``navigator/lib/config/macros.py``).
"""

from __future__ import annotations

from typing import Any

from navkit import commands, tooltip
from navkit.bidi import display_width
from navkit.i18n import tr
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.tooltip import with_keys
from navkit.widget import Widget


def caption() -> str:
    """DN's own word, not translated: it named a mode, as ``ROOT`` names one."""
    return ">MACRO<"


class MacroMark(Widget):
    """``>MACRO<`` while :attr:`slot` is a slot being recorded (0: none)."""

    #: The slot being recorded, 1 to 9; 0 while nothing is.
    slot: int = reactive(0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.height = 1

    @computed
    def natural_width(self) -> int:
        return display_width(caption())

    def tooltip_at(self, x: int, y: int) -> str:
        """Which slot, and the chord that ends the recording."""
        from navigator.commands import RecordMacro

        app = self.application
        key = commands.key_for(app, RecordMacro(self.slot)) if app is not None and self.slot else None
        return tooltip.lines(
            tr("Recording keys into macro {slot}").format(slot=self.slot),
            with_keys(tr("The same keys again stop it"), commands.key_label(key) if key else ""),
        )

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        surface.draw_text(0, 0, caption(), self.style)
