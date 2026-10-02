# navml: generated
"""Generated from ``confirmations_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # confirmations_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # confirmations_dialog.nml:2

__navml_component__ = "ConfirmationsDialog"

__all__ = ["ConfirmationsDialog"]


class ConfirmationsDialog(Dialog, _Component):
    """Options > Configuration > Confirmations: DOS Navigator's ``dlgConfirmations``.

    The resource's one column of boxes, less *Close CD player*, which has no
    drive to close here.  Four columns wider than DN's 36, for this library's
    eleven-column buttons; Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "confirmations_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    options: CheckBoxes    # confirmations_dialog.nml:15

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options = CheckBoxes(parent=self)    # confirmations_dialog.nml:14

        self.modal_width = 40    # confirmations_dialog.nml:10
        self.modal_height = 13    # confirmations_dialog.nml:11
        self.title = 'Confirmations'    # confirmations_dialog.nml:12

        self.options.x = 3    # confirmations_dialog.nml:16
        self.options.y = 1    # confirmations_dialog.nml:17
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # confirmations_dialog.nml:18
        self.options.height = 7    # confirmations_dialog.nml:19
        self.options.items = ['Erase ~s~ingle file', 'Erase ~m~ultiple files', 'Erase ~n~on-empty sub-dir', 'Erase ~r~ead-only files', '~C~reate non-existing dir', 'Drag~-~and~-~drop operations', 'E~x~it confirmation']    # confirmations_dialog.nml:20
