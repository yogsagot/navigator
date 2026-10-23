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

    ``HH:MM`` in 24-hour time, or ``hh:MMam`` in 12 as *Country support*
    says (DN's ``CountryInfo.TimeFmt``), its colon blinking once a second.
    Five columns wide, seven in 12 hours: ``Shell`` binds the width.
    The document holds the blink and ``clock.py`` paints.  The time itself is
    not state: it is read from the wall clock at every paint, and the tick that
    flips ``blink`` is what guarantees there is a paint every second.
    """

    #: The document this class was generated from.
    __navml_source__ = "clock.nml"

    #: Whether the colon is showing this second.
    blink: bool = _reactive(True)    # clock.nml:13

    #: Ids, annotated so the hand-written half completes them.
    tick: Timer    # clock.nml:19

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.tick = Timer(parent=self)    # clock.nml:18

        self.width = 5    # clock.nml:15
        self.height = 1    # clock.nml:16

        self.tick.interval = 500    # clock.nml:20

        async def _on_timer(event):    # clock.nml:21
            self.blink = not self.blink
            return True
        self.tick.on_timer = _on_timer
