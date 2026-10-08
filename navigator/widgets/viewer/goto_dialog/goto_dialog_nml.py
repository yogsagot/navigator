# navml: generated
"""Generated from ``goto_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # goto_dialog.nml:1
from navml.widgets.dialog.field import Field    # goto_dialog.nml:2

__navml_component__ = "GotoDialog"

__all__ = ["GotoDialog"]


class GotoDialog(Dialog, _Component):
    """F5 in a hex viewer: DOS Navigator's ``dlgGotoAddress``, *Goto Address*.

    One line, read as hex, as ``Val('$' + S)`` read it.  A row taller than DN's
    34 by 7, for the blank row ``MkdirDialog`` keeps between line and buttons.
    """

    #: The document this class was generated from.
    __navml_source__ = "goto_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    address: Field    # goto_dialog.nml:14

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.address = Field(parent=self)    # goto_dialog.nml:13

        self.modal_width = 34    # goto_dialog.nml:9
        self.modal_height = 8    # goto_dialog.nml:10
        self.title = _bind(lambda _o: _tr('Goto Address'), yielding=True)    # goto_dialog.nml:11

        self.address.x = 3    # goto_dialog.nml:15
        self.address.y = 2    # goto_dialog.nml:16
        self.address.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # goto_dialog.nml:17
        self.address.height = 1    # goto_dialog.nml:18
        self.address.label_text = _bind(    # goto_dialog.nml:19
            lambda _o: _tr('~A~ddress'),
            yielding=True,
        )
        self.address.label_width = 9    # goto_dialog.nml:20
        self.address.history_id = 'goto_address'    # goto_dialog.nml:21
