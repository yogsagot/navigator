# navml: generated
"""Generated from ``ascii_chart.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # ascii_chart.nml:1
from navml.widgets.dialog.static_text import StaticText    # ascii_chart.nml:2
from navigator.widgets.shell.char_table import CharTable    # ascii_chart.nml:3

__navml_component__ = "AsciiChart"

__all__ = ["AsciiChart"]


class AsciiChart(Dialog, _Component):
    """DOS Navigator's ``TASCIIChart`` (``ASCIITAB.PAS``): *ASCII Chart*, 34 by 12.

    The table fills the inside of the frame but its last two rows -- 32 by 8,
    one character a cell -- and the report (``TReport``) is the last row:
    ``Char: c Decimal: nnn Hex: hh``.  ``Dialog``'s buttons and message are
    not this layout, and the hand-written half hides them.
    """

    #: The document this class was generated from.
    __navml_source__ = "ascii_chart.nml"

    #: Ids, annotated so the hand-written half completes them.
    table: CharTable    # ascii_chart.nml:18
    report: StaticText    # ascii_chart.nml:27

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.table = CharTable(parent=self)    # ascii_chart.nml:17
        self.report = StaticText(parent=self)    # ascii_chart.nml:26

        self.modal_width = 34    # ascii_chart.nml:12
        self.modal_height = 12    # ascii_chart.nml:13
        self.title = _bind(lambda _o: _tr('ASCII Chart'), yielding=True)    # ascii_chart.nml:14
        self.buttons = 'none'    # ascii_chart.nml:15

        self.table.x = 1    # ascii_chart.nml:19
        self.table.y = 1    # ascii_chart.nml:20
        self.table.width = 32    # ascii_chart.nml:21
        self.table.height = 8    # ascii_chart.nml:22

        async def _on_chosen(event):    # ascii_chart.nml:24
            self.close(self.accept())
            return True
        self.table.on_chosen = _on_chosen

        self.report.x = 1    # ascii_chart.nml:28
        self.report.y = 10    # ascii_chart.nml:29
        self.report.width = 32    # ascii_chart.nml:30

        self._navml_built(__class__)
