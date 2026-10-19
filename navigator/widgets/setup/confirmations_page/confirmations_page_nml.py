# navml: generated
"""Generated from ``confirmations_page.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # confirmations_page.nml:1

__navml_component__ = "ConfirmationsPage"

__all__ = ["ConfirmationsPage"]


class ConfirmationsPage(_Component):
    """Options > Configuration > Confirmations: DOS Navigator's ``dlgConfirmations``.

    The resource's one column of boxes, less *Close CD player*, which has no
    drive to close here.  Four columns wider than DN's 36, for this library's
    eleven-column buttons; Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "confirmations_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # confirmations_page.nml:10

    #: Ids, annotated so the hand-written half completes them.
    options: CheckBoxes    # confirmations_page.nml:13

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options = CheckBoxes(parent=self)    # confirmations_page.nml:12

        self.options.x = 3    # confirmations_page.nml:14
        self.options.y = 1    # confirmations_page.nml:15
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # confirmations_page.nml:16
        self.options.height = 7    # confirmations_page.nml:17
        self.options.items = _bind(    # confirmations_page.nml:18
            lambda _o: [_tr('Erase ~s~ingle file'), _tr('Erase ~m~ultiple files'), _tr('Erase ~n~on-empty sub-dir'), _tr('Erase ~r~ead-only files'), _tr('~C~reate non-existing dir'), _tr('Drag~-~and~-~drop operations'), _tr('E~x~it confirmation')],
            yielding=True,
        )
