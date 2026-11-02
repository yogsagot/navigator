# navml: generated
"""Generated from ``sheet_find_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # sheet_find_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # sheet_find_dialog.nml:2
from navml.widgets.dialog.field import Field    # sheet_find_dialog.nml:3
from navml.widgets.dialog.label import Label    # sheet_find_dialog.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # sheet_find_dialog.nml:5

__navml_component__ = "SheetFindDialog"

__all__ = ["SheetFindDialog"]


class SheetFindDialog(Dialog, _Component):
    """F7 in the spreadsheet: DOS Navigator's ``dlgFindCell``, *Find* -- the

    pattern, *Search as* a string or a value, *Case sensitive* (DN's
    ``sesitive`` mended) and *Whole words only*, in the resource's places.
    DN's 49 by 13; Help is left out.
    """

    #: The document this class was generated from.
    __navml_source__ = "sheet_find_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    pattern: Field    # sheet_find_dialog.nml:19
    search_as_caption: Label    # sheet_find_dialog.nml:29
    search_as: RadioButtons    # sheet_find_dialog.nml:38
    options: CheckBoxes    # sheet_find_dialog.nml:46

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.pattern = Field(parent=self)    # sheet_find_dialog.nml:18
        self.search_as_caption = Label(parent=self)    # sheet_find_dialog.nml:28
        self.search_as = RadioButtons(parent=self)    # sheet_find_dialog.nml:37
        self.options = CheckBoxes(parent=self)    # sheet_find_dialog.nml:45

        self.modal_width = 49    # sheet_find_dialog.nml:12
        self.modal_height = 13    # sheet_find_dialog.nml:13
        self.title = _bind(lambda _o: _tr('Find'), yielding=True)    # sheet_find_dialog.nml:14
        self.buttons = 'ok-cancel'    # sheet_find_dialog.nml:15

        self.pattern.x = 2    # sheet_find_dialog.nml:20
        self.pattern.y = 2    # sheet_find_dialog.nml:21
        self.pattern.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # sheet_find_dialog.nml:22
        self.pattern.height = 1    # sheet_find_dialog.nml:23
        self.pattern.label_text = _bind(    # sheet_find_dialog.nml:24
            lambda _o: _tr('~P~attern'),
            yielding=True,
        )
        self.pattern.label_width = 9    # sheet_find_dialog.nml:25
        self.pattern.history_id = 'find_cell'    # sheet_find_dialog.nml:26

        self.search_as_caption.x = 3    # sheet_find_dialog.nml:30
        self.search_as_caption.y = 4    # sheet_find_dialog.nml:31
        self.search_as_caption.width = 15    # sheet_find_dialog.nml:32
        self.search_as_caption.height = 1    # sheet_find_dialog.nml:33
        self.search_as_caption.text = _bind(    # sheet_find_dialog.nml:34
            lambda _o: _tr('Search as'),
            yielding=True,
        )
        self.search_as_caption.link = _bind(lambda _o: self.search_as)    # sheet_find_dialog.nml:35

        self.search_as.x = 3    # sheet_find_dialog.nml:39
        self.search_as.y = 5    # sheet_find_dialog.nml:40
        self.search_as.width = 15    # sheet_find_dialog.nml:41
        self.search_as.height = 2    # sheet_find_dialog.nml:42
        self.search_as.items = _bind(    # sheet_find_dialog.nml:43
            lambda _o: [_tr('~S~tring'), _tr('~V~alue')],
            yielding=True,
        )

        self.options.x = 20    # sheet_find_dialog.nml:47
        self.options.y = 5    # sheet_find_dialog.nml:48
        self.options.width = 26    # sheet_find_dialog.nml:49
        self.options.height = 2    # sheet_find_dialog.nml:50
        self.options.items = _bind(    # sheet_find_dialog.nml:51
            lambda _o: [_tr('~C~ase sensitive'), _tr('~W~hole words only')],
            yielding=True,
        )
