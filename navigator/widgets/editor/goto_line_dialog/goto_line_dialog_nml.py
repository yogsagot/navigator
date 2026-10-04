# navml: generated
"""Generated from ``goto_line_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # goto_line_dialog.nml:1
from navml.widgets.dialog.field import Field    # goto_line_dialog.nml:2

__navml_component__ = "GotoLineDialog"

__all__ = ["GotoLineDialog"]


class GotoLineDialog(Dialog, _Component):
    """Alt+G in the editor: DOS Navigator's ``dlgGotoLine``, *Goto Line*.

    The label at column 3, the line from 16 to 28 and its history after it, as
    the resource has them.  A row taller than DN's 34 by 7, for the blank row
    the viewer's *Goto Address* keeps between line and buttons.
    """

    #: The document this class was generated from.
    __navml_source__ = "goto_line_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    number: Field    # goto_line_dialog.nml:15

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.number = Field(parent=self)    # goto_line_dialog.nml:14

        self.modal_width = 34    # goto_line_dialog.nml:10
        self.modal_height = 8    # goto_line_dialog.nml:11
        self.title = 'Goto Line'    # goto_line_dialog.nml:12

        self.number.x = 3    # goto_line_dialog.nml:16
        self.number.y = 2    # goto_line_dialog.nml:17
        self.number.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # goto_line_dialog.nml:18
        self.number.height = 1    # goto_line_dialog.nml:19
        self.number.label_text = '~L~ine number'    # goto_line_dialog.nml:20
        self.number.label_width = 13    # goto_line_dialog.nml:21
        self.number.history_id = 'goto_line'    # goto_line_dialog.nml:22
