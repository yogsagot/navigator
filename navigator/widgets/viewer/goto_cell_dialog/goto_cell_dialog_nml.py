# navml: generated
"""Generated from ``goto_cell_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # goto_cell_dialog.nml:1
from navml.widgets.dialog.field import Field    # goto_cell_dialog.nml:2

__navml_component__ = "GotoCellDialog"

__all__ = ["GotoCellDialog"]


class GotoCellDialog(Dialog, _Component):
    """F6 in the spreadsheet: DOS Navigator's ``dlgGotoCellNumber``, *Go to Cell

    Number* -- one line, a cell (``B12``), a row (``12``) or a column (``B``).
    A row taller than DN's 41 by 7, for the blank row this library keeps
    between line and buttons; Help is left out.
    """

    #: The document this class was generated from.
    __navml_source__ = "goto_cell_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    cell: Field    # goto_cell_dialog.nml:15

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.cell = Field(parent=self)    # goto_cell_dialog.nml:14

        self.modal_width = 41    # goto_cell_dialog.nml:9
        self.modal_height = 8    # goto_cell_dialog.nml:10
        self.title = _bind(lambda _o: _tr('Go to Cell Number'), yielding=True)    # goto_cell_dialog.nml:11

        self.cell.x = 3    # goto_cell_dialog.nml:16
        self.cell.y = 2    # goto_cell_dialog.nml:17
        self.cell.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # goto_cell_dialog.nml:18
        self.cell.height = 1    # goto_cell_dialog.nml:19
        self.cell.label_text = _bind(    # goto_cell_dialog.nml:20
            lambda _o: _tr('~E~nter new cell number'),
            yielding=True,
        )
        self.cell.label_width = 23    # goto_cell_dialog.nml:21
        self.cell.history_id = 'goto_cell'    # goto_cell_dialog.nml:22
