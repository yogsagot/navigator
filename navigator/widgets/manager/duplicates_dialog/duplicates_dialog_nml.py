# navml: generated
"""Generated from ``duplicates_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # duplicates_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # duplicates_dialog.nml:2
from navml.widgets.dialog.field import Field    # duplicates_dialog.nml:3

__navml_component__ = "DuplicatesDialog"

__all__ = ["DuplicatesDialog"]


class DuplicatesDialog(Dialog, _Component):
    """Panel > Find duplicates: which files below the panel's directory to

    compare.  A departure, asked for -- DOS Navigator had no such command
    (:mod:`navigator.lib.file_ops.duplicates`).
    """

    #: The document this class was generated from.
    __navml_source__ = "duplicates_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    mask: Field    # duplicates_dialog.nml:15
    min_size: Field    # duplicates_dialog.nml:25
    options: CheckBoxes    # duplicates_dialog.nml:35

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.mask = Field(parent=self)    # duplicates_dialog.nml:14
        self.min_size = Field(parent=self)    # duplicates_dialog.nml:24
        self.options = CheckBoxes(parent=self)    # duplicates_dialog.nml:34

        self.modal_width = 52    # duplicates_dialog.nml:9
        self.modal_height = 10    # duplicates_dialog.nml:10
        self.title = _bind(lambda _o: _tr('Find duplicates'), yielding=True)    # duplicates_dialog.nml:11
        self.buttons = 'ok-cancel'    # duplicates_dialog.nml:12

        self.mask.x = 2    # duplicates_dialog.nml:16
        self.mask.y = 1    # duplicates_dialog.nml:17
        self.mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # duplicates_dialog.nml:18
        self.mask.height = 1    # duplicates_dialog.nml:19
        self.mask.label_text = _bind(    # duplicates_dialog.nml:20
            lambda _o: _tr('~F~ile mask'),
            yielding=True,
        )
        self.mask.label_width = 16    # duplicates_dialog.nml:21
        self.mask.history_id = 'find_mask'    # duplicates_dialog.nml:22

        self.min_size.x = 2    # duplicates_dialog.nml:26
        self.min_size.y = 3    # duplicates_dialog.nml:27
        self.min_size.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # duplicates_dialog.nml:28
        self.min_size.height = 1    # duplicates_dialog.nml:29
        self.min_size.label_text = _bind(    # duplicates_dialog.nml:30
            lambda _o: _tr('~M~inimum size'),
            yielding=True,
        )
        self.min_size.label_width = 16    # duplicates_dialog.nml:31
        self.min_size.history_id = 'duplicates_size'    # duplicates_dialog.nml:32

        self.options.x = 3    # duplicates_dialog.nml:36
        self.options.y = 5    # duplicates_dialog.nml:37
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # duplicates_dialog.nml:38
        self.options.height = 1    # duplicates_dialog.nml:39
        self.options.items = _bind(    # duplicates_dialog.nml:40
            lambda _o: [_tr('Search ~s~ubdirectories')],
            yielding=True,
        )
