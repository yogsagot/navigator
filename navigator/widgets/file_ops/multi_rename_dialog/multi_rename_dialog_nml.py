# navml: generated
"""Generated from ``multi_rename_dialog.nml``.

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
from navigator.widgets.file_ops.multi_rename_dialog.rename_preview import RenamePreview    # multi_rename_dialog.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # multi_rename_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # multi_rename_dialog.nml:3
from navml.widgets.dialog.field import Field    # multi_rename_dialog.nml:4
from navml.widgets.dialog.label import Label    # multi_rename_dialog.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # multi_rename_dialog.nml:6
from navml.widgets.dialog.static_text import StaticText    # multi_rename_dialog.nml:7

__navml_component__ = "MultiRenameDialog"

__all__ = ["MultiRenameDialog"]


class MultiRenameDialog(Dialog, _Component):
    """Panel > Multi-rename (Alt+A): the tagged files renamed by one pattern, every

    new name shown before anything is done.  A departure -- Total Commander's
    *Multi-Rename Tool*; DOS Navigator's group rename was F6's ``*``/``?`` mask,
    which stays.  The placeholders are :mod:`navigator.lib.file_ops.multirename`'s.
    """

    #: The document this class was generated from.
    __navml_source__ = "multi_rename_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    name_mask: Field    # multi_rename_dialog.nml:19
    ext_mask: Field    # multi_rename_dialog.nml:29
    search: Field    # multi_rename_dialog.nml:39
    replace: Field    # multi_rename_dialog.nml:49
    options: CheckBoxes    # multi_rename_dialog.nml:59
    case_caption: Label    # multi_rename_dialog.nml:67
    case: RadioButtons    # multi_rename_dialog.nml:76
    start: Field    # multi_rename_dialog.nml:84
    step: Field    # multi_rename_dialog.nml:93
    digits: Field    # multi_rename_dialog.nml:102
    preview: RenamePreview    # multi_rename_dialog.nml:111
    status: StaticText    # multi_rename_dialog.nml:118

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.name_mask = Field(parent=self)    # multi_rename_dialog.nml:18
        self.ext_mask = Field(parent=self)    # multi_rename_dialog.nml:28
        self.search = Field(parent=self)    # multi_rename_dialog.nml:38
        self.replace = Field(parent=self)    # multi_rename_dialog.nml:48
        self.options = CheckBoxes(parent=self)    # multi_rename_dialog.nml:58
        self.case_caption = Label(parent=self)    # multi_rename_dialog.nml:66
        self.case = RadioButtons(parent=self)    # multi_rename_dialog.nml:75
        self.start = Field(parent=self)    # multi_rename_dialog.nml:83
        self.step = Field(parent=self)    # multi_rename_dialog.nml:92
        self.digits = Field(parent=self)    # multi_rename_dialog.nml:101
        self.preview = RenamePreview(parent=self)    # multi_rename_dialog.nml:110
        self.status = StaticText(parent=self)    # multi_rename_dialog.nml:117

        self.modal_width = 76    # multi_rename_dialog.nml:14
        self.modal_height = 23    # multi_rename_dialog.nml:15
        self.title = _bind(lambda _o: _tr('Multi-rename'), yielding=True)    # multi_rename_dialog.nml:16

        self.name_mask.x = 2    # multi_rename_dialog.nml:20
        self.name_mask.y = 1    # multi_rename_dialog.nml:21
        self.name_mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:22
        self.name_mask.height = 1    # multi_rename_dialog.nml:23
        self.name_mask.label_text = _bind(    # multi_rename_dialog.nml:24
            lambda _o: _tr('~N~ame mask'),
            yielding=True,
        )
        self.name_mask.label_width = 16    # multi_rename_dialog.nml:25
        self.name_mask.history_id = 'rename_name_mask'    # multi_rename_dialog.nml:26

        self.ext_mask.x = 2    # multi_rename_dialog.nml:30
        self.ext_mask.y = 2    # multi_rename_dialog.nml:31
        self.ext_mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:32
        self.ext_mask.height = 1    # multi_rename_dialog.nml:33
        self.ext_mask.label_text = _bind(    # multi_rename_dialog.nml:34
            lambda _o: _tr('E~x~tension mask'),
            yielding=True,
        )
        self.ext_mask.label_width = 16    # multi_rename_dialog.nml:35
        self.ext_mask.history_id = 'rename_ext_mask'    # multi_rename_dialog.nml:36

        self.search.x = 2    # multi_rename_dialog.nml:40
        self.search.y = 3    # multi_rename_dialog.nml:41
        self.search.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:42
        self.search.height = 1    # multi_rename_dialog.nml:43
        self.search.label_text = _bind(    # multi_rename_dialog.nml:44
            lambda _o: _tr('~S~earch for'),
            yielding=True,
        )
        self.search.label_width = 16    # multi_rename_dialog.nml:45
        self.search.history_id = 'rename_search'    # multi_rename_dialog.nml:46

        self.replace.x = 2    # multi_rename_dialog.nml:50
        self.replace.y = 4    # multi_rename_dialog.nml:51
        self.replace.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:52
        self.replace.height = 1    # multi_rename_dialog.nml:53
        self.replace.label_text = _bind(    # multi_rename_dialog.nml:54
            lambda _o: _tr('Re~p~lace with'),
            yielding=True,
        )
        self.replace.label_width = 16    # multi_rename_dialog.nml:55
        self.replace.history_id = 'rename_replace'    # multi_rename_dialog.nml:56

        self.options.x = 3    # multi_rename_dialog.nml:60
        self.options.y = 6    # multi_rename_dialog.nml:61
        self.options.width = 26    # multi_rename_dialog.nml:62
        self.options.height = 3    # multi_rename_dialog.nml:63
        self.options.items = _bind(    # multi_rename_dialog.nml:64
            lambda _o: [_tr('Regular ~e~xpression'), _tr('Case sens~i~tive'), _tr('~F~irst match only')],
            yielding=True,
        )

        self.case_caption.x = 31    # multi_rename_dialog.nml:68
        self.case_caption.y = 5    # multi_rename_dialog.nml:69
        self.case_caption.width = 10    # multi_rename_dialog.nml:70
        self.case_caption.height = 1    # multi_rename_dialog.nml:71
        self.case_caption.text = _bind(lambda _o: _tr('Case'), yielding=True)    # multi_rename_dialog.nml:72
        self.case_caption.link = _bind(lambda _o: self.case)    # multi_rename_dialog.nml:73

        self.case.x = 31    # multi_rename_dialog.nml:77
        self.case.y = 6    # multi_rename_dialog.nml:78
        self.case.width = 18    # multi_rename_dialog.nml:79
        self.case.height = 5    # multi_rename_dialog.nml:80
        self.case.items = _bind(    # multi_rename_dialog.nml:81
            lambda _o: [_tr('Unchan~g~ed'), _tr('~l~ower'), _tr('~U~PPER'), _tr('~W~ord Caps'), _tr('Fi~r~st only')],
            yielding=True,
        )

        self.start.x = 51    # multi_rename_dialog.nml:85
        self.start.y = 6    # multi_rename_dialog.nml:86
        self.start.width = 22    # multi_rename_dialog.nml:87
        self.start.height = 1    # multi_rename_dialog.nml:88
        self.start.label_text = _bind(    # multi_rename_dialog.nml:89
            lambda _o: _tr('Coun~t~er'),
            yielding=True,
        )
        self.start.label_width = 9    # multi_rename_dialog.nml:90

        self.step.x = 51    # multi_rename_dialog.nml:94
        self.step.y = 7    # multi_rename_dialog.nml:95
        self.step.width = 22    # multi_rename_dialog.nml:96
        self.step.height = 1    # multi_rename_dialog.nml:97
        self.step.label_text = _bind(lambda _o: _tr('Step'), yielding=True)    # multi_rename_dialog.nml:98
        self.step.label_width = 9    # multi_rename_dialog.nml:99

        self.digits.x = 51    # multi_rename_dialog.nml:103
        self.digits.y = 8    # multi_rename_dialog.nml:104
        self.digits.width = 22    # multi_rename_dialog.nml:105
        self.digits.height = 1    # multi_rename_dialog.nml:106
        self.digits.label_text = _bind(    # multi_rename_dialog.nml:107
            lambda _o: _tr('~D~igits'),
            yielding=True,
        )
        self.digits.label_width = 9    # multi_rename_dialog.nml:108

        self.preview.x = 2    # multi_rename_dialog.nml:112
        self.preview.y = 11    # multi_rename_dialog.nml:113
        self.preview.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:114
        self.preview.height = _bind(lambda _o: max(0, _o.parent.height - 16))    # multi_rename_dialog.nml:115

        self.status.x = 2    # multi_rename_dialog.nml:119
        self.status.y = _bind(lambda _o: max(0, _o.parent.height - 5))    # multi_rename_dialog.nml:120
        self.status.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:121
        self.status.height = 1    # multi_rename_dialog.nml:122
        self.status.align = 'center'    # multi_rename_dialog.nml:123
