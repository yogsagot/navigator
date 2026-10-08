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

from navkit.events import Event as _Event
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
    table: CharTable    # ascii_chart.nml:17
    report: StaticText    # ascii_chart.nml:24

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_table_chosen(self, event: _Event) -> bool:    # ascii_chart.nml:17
        """``table`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.table = CharTable(parent=self)    # ascii_chart.nml:16
        self.report = StaticText(parent=self)    # ascii_chart.nml:23

        self.modal_width = 34    # ascii_chart.nml:12
        self.modal_height = 12    # ascii_chart.nml:13
        self.title = _bind(lambda _o: _tr('ASCII Chart'), yielding=True)    # ascii_chart.nml:14

        self.table.x = 1    # ascii_chart.nml:18
        self.table.y = 1    # ascii_chart.nml:19
        self.table.width = 32    # ascii_chart.nml:20
        self.table.height = 8    # ascii_chart.nml:21
        self.table.on_chosen = self.on_table_chosen    # ascii_chart.nml:17

        self.report.x = 1    # ascii_chart.nml:25
        self.report.y = 10    # ascii_chart.nml:26
        self.report.width = 32    # ascii_chart.nml:27
        self.report.height = 1    # ascii_chart.nml:28
