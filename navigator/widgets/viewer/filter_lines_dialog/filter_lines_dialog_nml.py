# navml: generated
"""Generated from ``filter_lines_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # filter_lines_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # filter_lines_dialog.nml:2
from navml.widgets.dialog.field import Field    # filter_lines_dialog.nml:3
from navml.widgets.dialog.label import Label    # filter_lines_dialog.nml:4

__navml_component__ = "FilterLinesDialog"

__all__ = ["FilterLinesDialog"]


class FilterLinesDialog(Dialog, _Component):
    """Ctrl+G in a viewer, View > *Filter lines*: the lines to show, and how they

    are matched.  A departure, asked for -- DN's viewer had no such box; it is
    laid out as F7's *Find* is, the pattern on the line under its caption and
    the switches under that.
    """

    #: The document this class was generated from.
    __navml_source__ = "filter_lines_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    what_caption: Label    # filter_lines_dialog.nml:16
    what: Field    # filter_lines_dialog.nml:25
    options_caption: Label    # filter_lines_dialog.nml:36
    options: CheckBoxes    # filter_lines_dialog.nml:45

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.what_caption = Label(parent=self)    # filter_lines_dialog.nml:15
        self.what = Field(parent=self)    # filter_lines_dialog.nml:24
        self.options_caption = Label(parent=self)    # filter_lines_dialog.nml:35
        self.options = CheckBoxes(parent=self)    # filter_lines_dialog.nml:44

        self.modal_width = 50    # filter_lines_dialog.nml:11
        self.modal_height = 13    # filter_lines_dialog.nml:12
        self.title = _bind(lambda _o: _tr('Filter lines'), yielding=True)    # filter_lines_dialog.nml:13

        self.what_caption.x = 2    # filter_lines_dialog.nml:17
        self.what_caption.y = 2    # filter_lines_dialog.nml:18
        self.what_caption.width = 24    # filter_lines_dialog.nml:19
        self.what_caption.height = 1    # filter_lines_dialog.nml:20
        self.what_caption.text = _bind(    # filter_lines_dialog.nml:21
            lambda _o: _tr('~S~how lines containing'),
            yielding=True,
        )
        self.what_caption.link = _bind(lambda _o: self.what.entry)    # filter_lines_dialog.nml:22

        self.what.y = 3    # filter_lines_dialog.nml:26
        self.what.height = 1    # filter_lines_dialog.nml:27
        self.what.label_text = ''    # filter_lines_dialog.nml:31
        self.what.label_width = 0    # filter_lines_dialog.nml:32
        self.what.history_id = 'view_lines'    # filter_lines_dialog.nml:33
        self.what.x = 2    # filter_lines_dialog.nml:29
        self.what.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # filter_lines_dialog.nml:30

        self.options_caption.x = 2    # filter_lines_dialog.nml:37
        self.options_caption.y = 5    # filter_lines_dialog.nml:38
        self.options_caption.width = 12    # filter_lines_dialog.nml:39
        self.options_caption.height = 1    # filter_lines_dialog.nml:40
        self.options_caption.text = _bind(    # filter_lines_dialog.nml:41
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # filter_lines_dialog.nml:42

        self.options.y = 6    # filter_lines_dialog.nml:46
        self.options.height = 3    # filter_lines_dialog.nml:47
        self.options.items = _bind(    # filter_lines_dialog.nml:51
            lambda _o: [_tr('~R~egular expression'), _tr('~C~ase sensitive'), _tr('~I~nvert (lines not matching)')],
            yielding=True,
        )
        self.options.x = 2    # filter_lines_dialog.nml:49
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # filter_lines_dialog.nml:50
