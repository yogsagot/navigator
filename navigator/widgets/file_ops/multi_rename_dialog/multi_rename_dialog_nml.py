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
from navml.widgets.dialog.choice_field import ChoiceField    # multi_rename_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # multi_rename_dialog.nml:4
from navml.widgets.dialog.field import Field    # multi_rename_dialog.nml:5
from navml.widgets.dialog.label import Label    # multi_rename_dialog.nml:6
from navml.widgets.dialog.radio_buttons import RadioButtons    # multi_rename_dialog.nml:7
from navml.widgets.dialog.static_text import StaticText    # multi_rename_dialog.nml:8

__navml_component__ = "MultiRenameDialog"

__all__ = ["MultiRenameDialog"]


class MultiRenameDialog(Dialog, _Component):
    """File > Multi-rename (Alt+A): the tagged files renamed by one pattern, every

    new name shown before anything is done.  A departure -- Total Commander's
    *Multi-Rename Tool*; DOS Navigator's group rename was F6's ``*``/``?`` mask,
    which stays.  The placeholders are :mod:`navigator.lib.file_ops.multirename`'s.
    """

    #: The document this class was generated from.
    __navml_source__ = "multi_rename_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    name_mask: Field    # multi_rename_dialog.nml:20
    ext_mask: Field    # multi_rename_dialog.nml:30
    search: Field    # multi_rename_dialog.nml:40
    replace: Field    # multi_rename_dialog.nml:50
    options: CheckBoxes    # multi_rename_dialog.nml:60
    codepage: ChoiceField    # multi_rename_dialog.nml:71
    case_caption: Label    # multi_rename_dialog.nml:80
    case: RadioButtons    # multi_rename_dialog.nml:88
    start: Field    # multi_rename_dialog.nml:96
    step: Field    # multi_rename_dialog.nml:104
    digits: Field    # multi_rename_dialog.nml:112
    preview: RenamePreview    # multi_rename_dialog.nml:120
    status: StaticText    # multi_rename_dialog.nml:128

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.name_mask = Field(parent=self)    # multi_rename_dialog.nml:19
        self.ext_mask = Field(parent=self)    # multi_rename_dialog.nml:29
        self.search = Field(parent=self)    # multi_rename_dialog.nml:39
        self.replace = Field(parent=self)    # multi_rename_dialog.nml:49
        self.options = CheckBoxes(parent=self)    # multi_rename_dialog.nml:59
        self.codepage = ChoiceField(parent=self)    # multi_rename_dialog.nml:70
        self.case_caption = Label(parent=self)    # multi_rename_dialog.nml:79
        self.case = RadioButtons(parent=self)    # multi_rename_dialog.nml:87
        self.start = Field(parent=self)    # multi_rename_dialog.nml:95
        self.step = Field(parent=self)    # multi_rename_dialog.nml:103
        self.digits = Field(parent=self)    # multi_rename_dialog.nml:111
        self.preview = RenamePreview(parent=self)    # multi_rename_dialog.nml:119
        self.status = StaticText(parent=self)    # multi_rename_dialog.nml:127

        self.modal_width = 76    # multi_rename_dialog.nml:15
        self.modal_height = 25    # multi_rename_dialog.nml:16
        self.title = _bind(lambda _o: _tr('Multi-rename'), yielding=True)    # multi_rename_dialog.nml:17

        self.name_mask.y = 1    # multi_rename_dialog.nml:21
        self.name_mask.label_text = _bind(    # multi_rename_dialog.nml:25
            lambda _o: _tr('~N~ame mask'),
            yielding=True,
        )
        self.name_mask.label_width = 16    # multi_rename_dialog.nml:26
        self.name_mask.history_id = 'rename_name_mask'    # multi_rename_dialog.nml:27
        self.name_mask.x = 2    # multi_rename_dialog.nml:23
        self.name_mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:24

        self.ext_mask.y = 2    # multi_rename_dialog.nml:31
        self.ext_mask.label_text = _bind(    # multi_rename_dialog.nml:35
            lambda _o: _tr('E~x~tension mask'),
            yielding=True,
        )
        self.ext_mask.label_width = 16    # multi_rename_dialog.nml:36
        self.ext_mask.history_id = 'rename_ext_mask'    # multi_rename_dialog.nml:37
        self.ext_mask.x = 2    # multi_rename_dialog.nml:33
        self.ext_mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:34

        self.search.y = 3    # multi_rename_dialog.nml:41
        self.search.label_text = _bind(    # multi_rename_dialog.nml:45
            lambda _o: _tr('~S~earch for'),
            yielding=True,
        )
        self.search.label_width = 16    # multi_rename_dialog.nml:46
        self.search.history_id = 'rename_search'    # multi_rename_dialog.nml:47
        self.search.x = 2    # multi_rename_dialog.nml:43
        self.search.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:44

        self.replace.y = 4    # multi_rename_dialog.nml:51
        self.replace.label_text = _bind(    # multi_rename_dialog.nml:55
            lambda _o: _tr('Re~p~lace with'),
            yielding=True,
        )
        self.replace.label_width = 16    # multi_rename_dialog.nml:56
        self.replace.history_id = 'rename_replace'    # multi_rename_dialog.nml:57
        self.replace.x = 2    # multi_rename_dialog.nml:53
        self.replace.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:54

        self.options.x = 3    # multi_rename_dialog.nml:61
        self.options.y = 6    # multi_rename_dialog.nml:62
        self.options.width = 26    # multi_rename_dialog.nml:63
        self.options.height = 4    # multi_rename_dialog.nml:64
        self.options.items = _bind(    # multi_rename_dialog.nml:65
            lambda _o: [_tr('Regular ~e~xpression'), _tr('Case sens~i~tive'), _tr('~F~irst match only'), _tr('Clean up na~m~es')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # multi_rename_dialog.nml:66
            lambda _o: [_tr('The search is a regular expression, not plain text'), '', _tr('Replace only the first match in each name'), _tr('Bytes that are not UTF-8 read in the code page below, NFC, control characters to _, names differing only by case numbered')],
            yielding=True,
        )

        self.codepage.x = 2    # multi_rename_dialog.nml:72
        self.codepage.y = 11    # multi_rename_dialog.nml:73
        self.codepage.width = 47    # multi_rename_dialog.nml:74
        self.codepage.label_text = _bind(    # multi_rename_dialog.nml:75
            lambda _o: _tr('C~o~de page'),
            yielding=True,
        )
        self.codepage.label_width = 11    # multi_rename_dialog.nml:76
        self.codepage.disabled = _bind(lambda _o: not self.options.value & 8)    # multi_rename_dialog.nml:77

        self.case_caption.x = 31    # multi_rename_dialog.nml:81
        self.case_caption.y = 5    # multi_rename_dialog.nml:82
        self.case_caption.width = 10    # multi_rename_dialog.nml:83
        self.case_caption.text = _bind(lambda _o: _tr('Case'), yielding=True)    # multi_rename_dialog.nml:84
        self.case_caption.link = _bind(lambda _o: self.case)    # multi_rename_dialog.nml:85

        self.case.x = 31    # multi_rename_dialog.nml:89
        self.case.y = 6    # multi_rename_dialog.nml:90
        self.case.width = 18    # multi_rename_dialog.nml:91
        self.case.height = 5    # multi_rename_dialog.nml:92
        self.case.items = _bind(    # multi_rename_dialog.nml:93
            lambda _o: [_tr('Unchan~g~ed'), _tr('~l~ower'), _tr('~U~PPER'), _tr('~W~ord Caps'), _tr('Fi~r~st only')],
            yielding=True,
        )

        self.start.x = 51    # multi_rename_dialog.nml:97
        self.start.y = 6    # multi_rename_dialog.nml:98
        self.start.width = 22    # multi_rename_dialog.nml:99
        self.start.label_text = _bind(    # multi_rename_dialog.nml:100
            lambda _o: _tr('Coun~t~er'),
            yielding=True,
        )
        self.start.label_width = 9    # multi_rename_dialog.nml:101

        self.step.x = 51    # multi_rename_dialog.nml:105
        self.step.y = 7    # multi_rename_dialog.nml:106
        self.step.width = 22    # multi_rename_dialog.nml:107
        self.step.label_text = _bind(lambda _o: _tr('Step'), yielding=True)    # multi_rename_dialog.nml:108
        self.step.label_width = 9    # multi_rename_dialog.nml:109

        self.digits.x = 51    # multi_rename_dialog.nml:113
        self.digits.y = 8    # multi_rename_dialog.nml:114
        self.digits.width = 22    # multi_rename_dialog.nml:115
        self.digits.label_text = _bind(    # multi_rename_dialog.nml:116
            lambda _o: _tr('~D~igits'),
            yielding=True,
        )
        self.digits.label_width = 9    # multi_rename_dialog.nml:117

        self.preview.x = 2    # multi_rename_dialog.nml:122
        self.preview.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:123
        self.preview.y = 13    # multi_rename_dialog.nml:124
        self.preview.height = _bind(lambda _o: max(0, _o.parent.height - 18))    # multi_rename_dialog.nml:125

        self.status.align = 'center'    # multi_rename_dialog.nml:133
        self.status.x = 2    # multi_rename_dialog.nml:130
        self.status.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # multi_rename_dialog.nml:131
        self.status.y = _bind(    # multi_rename_dialog.nml:132
            lambda _o: max(0, _o.parent.height - 4 - _o.height)
        )
