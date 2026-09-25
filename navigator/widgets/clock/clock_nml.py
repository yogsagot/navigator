# navml: generated
"""Generated from ``clock.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.timer import Timer    # clock.nml:1

__navml_component__ = "Clock"

__all__ = ["Clock"]


class Clock(_Component):
    """DOS Navigator's clock, in the top-right corner of the menu bar.

    ``HH:MM`` in 24-hour time, its colon blinking once a second.
    The document holds the blink and ``clock.py`` paints.  The time itself is
    not state: it is read from the wall clock at every paint, and the tick that
    flips ``blink`` is what guarantees there is a paint every second.
    """

    #: The document this class was generated from.
    __navml_source__ = "clock.nml"

    #: Whether the colon is showing this second.
    blink: bool = _reactive(True)    # clock.nml:11

    #: Ids, annotated so the hand-written half completes them.
    tick: Timer    # clock.nml:17

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.tick = Timer(parent=self)    # clock.nml:16

        self.width = 5    # clock.nml:13
        self.height = 1    # clock.nml:14

        self.tick.interval = 1000    # clock.nml:18

        async def _on_timer(event):    # clock.nml:19
            self.blink = not self.blink
            return True
        self.tick.on_timer = _on_timer
