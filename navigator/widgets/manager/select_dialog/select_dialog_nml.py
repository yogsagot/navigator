# navml: generated
"""Generated from ``select_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # select_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # select_dialog.nml:2
from navml.widgets.dialog.field import Field    # select_dialog.nml:3
from navml.widgets.dialog.label import Label    # select_dialog.nml:4

__navml_component__ = "SelectDialog"

__all__ = ["SelectDialog"]


class SelectDialog(Dialog, _Component):
    """Gray ``+`` and ``-``: DOS Navigator's ``dlgSelect`` and ``dlgUnselect``.

    One document for the two, which ``DN.DNR`` spelled out twice and which
    differ only in their title.  Laid out where the resource puts them -- the
    caption on the first row, the mask under it, *Except mask* two rows down
    -- three columns wider and a row taller, because this library's buttons
    are eleven wide and sit ``height - 4`` from the top.
    """

    #: The document this class was generated from.
    __navml_source__ = "select_dialog.nml"

    #: Which of the two: *Select* (Gray ``+``) or *Unselect* (Gray ``-``).
    select: bool = _reactive(True)    # select_dialog.nml:15

    #: Ids, annotated so the hand-written half completes them.
    mask_caption: Label    # select_dialog.nml:22
    mask: Field    # select_dialog.nml:32
    options: CheckBoxes    # select_dialog.nml:42

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.mask_caption = Label(parent=self)    # select_dialog.nml:21
        self.mask = Field(parent=self)    # select_dialog.nml:31
        self.options = CheckBoxes(parent=self)    # select_dialog.nml:41

        self.modal_width = 30    # select_dialog.nml:17
        self.modal_height = 10    # select_dialog.nml:18
        self.title = _bind(    # select_dialog.nml:19
            lambda _o: _tr('Select') if self.select else _tr('Unselect')
        )

        self.mask_caption.x = 2    # select_dialog.nml:23
        self.mask_caption.y = 1    # select_dialog.nml:24
        self.mask_caption.width = 12    # select_dialog.nml:25
        self.mask_caption.height = 1    # select_dialog.nml:26
        self.mask_caption.text = _bind(    # select_dialog.nml:27
            lambda _o: _tr('~F~ile mask'),
            yielding=True,
        )
        self.mask_caption.link = _bind(lambda _o: self.mask.entry)    # select_dialog.nml:28

        self.mask.x = 2    # select_dialog.nml:33
        self.mask.y = 2    # select_dialog.nml:34
        self.mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # select_dialog.nml:35
        self.mask.height = 1    # select_dialog.nml:36
        self.mask.label_text = ''    # select_dialog.nml:37
        self.mask.label_width = 0    # select_dialog.nml:38
        self.mask.history_id = 'select'    # select_dialog.nml:39

        self.options.x = 2    # select_dialog.nml:43
        self.options.y = 4    # select_dialog.nml:44
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # select_dialog.nml:45
        self.options.height = 1    # select_dialog.nml:46
        self.options.items = _bind(    # select_dialog.nml:47
            lambda _o: [_tr('~E~xcept mask')],
            yielding=True,
        )
