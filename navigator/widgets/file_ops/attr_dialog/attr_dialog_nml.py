# navml: generated
"""Generated from ``attr_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # attr_dialog.nml:1
from navml.widgets.dialog.choice_field import ChoiceField    # attr_dialog.nml:2
from navml.widgets.dialog.date_field import DateField    # attr_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # attr_dialog.nml:4
from navml.widgets.dialog.label import Label    # attr_dialog.nml:5
from navml.widgets.dialog.masked_field import MaskedField    # attr_dialog.nml:6
from navml.widgets.dialog.radio_buttons import RadioButtons    # attr_dialog.nml:7
from navml.widgets.dialog.static_text import StaticText    # attr_dialog.nml:8
from navml.widgets.dialog.time_field import TimeField    # attr_dialog.nml:9

__navml_component__ = "AttrDialog"

__all__ = ["AttrDialog"]


class AttrDialog(Dialog, _Component):
    """Alt+E: *File Attributes*, DOS Navigator's ``dlgFilesAttr`` read for Linux.

    A departure in what it edits -- DN's four DOS bits are the twelve mode bits,
    and the owner and group stand beside DN's date and time -- and DN's in its
    shape: one dialog over every tagged file, where a bit the files disagree on
    is ``[?]`` and left alone unless moved.  The grid is one ``CheckBoxes`` of
    twelve, three tall, which ``Cluster`` lays out in four columns of three:
    owner, group, others and the special bits, each read/write/execute down.
    """

    #: The document this class was generated from.
    __navml_source__ = "attr_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    name_row: StaticText    # attr_dialog.nml:27
    info_row: StaticText    # attr_dialog.nml:35
    heading: Label    # attr_dialog.nml:44
    bits: CheckBoxes    # attr_dialog.nml:53
    octal: MaskedField    # attr_dialog.nml:63
    symbolic: StaticText    # attr_dialog.nml:75
    user: ChoiceField    # attr_dialog.nml:84
    group: ChoiceField    # attr_dialog.nml:93
    date: DateField    # attr_dialog.nml:105
    clock: TimeField    # attr_dialog.nml:114
    recurse_caption: Label    # attr_dialog.nml:124
    recurse: RadioButtons    # attr_dialog.nml:133

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.name_row = StaticText(parent=self)    # attr_dialog.nml:26
        self.info_row = StaticText(parent=self)    # attr_dialog.nml:34
        self.heading = Label(parent=self)    # attr_dialog.nml:43
        self.bits = CheckBoxes(parent=self)    # attr_dialog.nml:52
        self.octal = MaskedField(parent=self)    # attr_dialog.nml:62
        self.symbolic = StaticText(parent=self)    # attr_dialog.nml:74
        self.user = ChoiceField(parent=self)    # attr_dialog.nml:83
        self.group = ChoiceField(parent=self)    # attr_dialog.nml:92
        self.date = DateField(parent=self)    # attr_dialog.nml:104
        self.clock = TimeField(parent=self)    # attr_dialog.nml:113
        self.recurse_caption = Label(parent=self)    # attr_dialog.nml:123
        self.recurse = RadioButtons(parent=self)    # attr_dialog.nml:132

        self.modal_width = 60    # attr_dialog.nml:20
        self.modal_height = 20    # attr_dialog.nml:21
        self.title = _bind(lambda _o: _tr('File Attributes'), yielding=True)    # attr_dialog.nml:22
        self.buttons = 'ok-cancel'    # attr_dialog.nml:23

        self.name_row.x = 2    # attr_dialog.nml:28
        self.name_row.y = 1    # attr_dialog.nml:29
        self.name_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:30
        self.name_row.height = 1    # attr_dialog.nml:31

        self.info_row.x = 2    # attr_dialog.nml:36
        self.info_row.y = 2    # attr_dialog.nml:37
        self.info_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:38
        self.info_row.height = 1    # attr_dialog.nml:39

        self.heading.x = 3    # attr_dialog.nml:45
        self.heading.y = 4    # attr_dialog.nml:46
        self.heading.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:47
        self.heading.height = 1    # attr_dialog.nml:48
        self.heading.text = _bind(    # attr_dialog.nml:49
            lambda _o: _tr('O~w~ner      Group      Others     Special'),
            yielding=True,
        )
        self.heading.link = _bind(lambda _o: self.bits)    # attr_dialog.nml:50

        self.bits.x = 3    # attr_dialog.nml:54
        self.bits.y = 5    # attr_dialog.nml:55
        self.bits.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:56
        self.bits.height = 3    # attr_dialog.nml:57
        self.bits.items = _bind(    # attr_dialog.nml:58
            lambda _o: [_tr('Read'), _tr('Write'), _tr('Exec'), _tr('Read'), _tr('Write'), _tr('Exec'), _tr('Read'), _tr('Write'), _tr('Exec'), _tr('Set UID'), _tr('Set GID'), _tr('Sticky')],
            yielding=True,
        )

        self.octal.x = 2    # attr_dialog.nml:64
        self.octal.y = 9    # attr_dialog.nml:65
        self.octal.width = 16    # attr_dialog.nml:66
        self.octal.height = 1    # attr_dialog.nml:67
        self.octal.label_text = _bind(lambda _o: _tr('~O~ctal'), yielding=True)    # attr_dialog.nml:68
        self.octal.label_width = 10    # attr_dialog.nml:69
        self.octal.mask = '9999'    # attr_dialog.nml:70
        self.octal.base = 8    # attr_dialog.nml:71

        self.symbolic.x = 20    # attr_dialog.nml:76
        self.symbolic.y = 9    # attr_dialog.nml:77
        self.symbolic.width = 12    # attr_dialog.nml:78
        self.symbolic.height = 1    # attr_dialog.nml:79

        self.user.x = 2    # attr_dialog.nml:85
        self.user.y = 10    # attr_dialog.nml:86
        self.user.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:87
        self.user.height = 1    # attr_dialog.nml:88
        self.user.label_text = _bind(lambda _o: _tr('~U~ser'), yielding=True)    # attr_dialog.nml:89
        self.user.label_width = 10    # attr_dialog.nml:90

        self.group.x = 2    # attr_dialog.nml:94
        self.group.y = 11    # attr_dialog.nml:95
        self.group.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:96
        self.group.height = 1    # attr_dialog.nml:97
        self.group.label_text = _bind(lambda _o: _tr('~G~roup'), yielding=True)    # attr_dialog.nml:98
        self.group.label_width = 10    # attr_dialog.nml:99

        self.date.x = 2    # attr_dialog.nml:106
        self.date.y = 12    # attr_dialog.nml:107
        self.date.width = 26    # attr_dialog.nml:108
        self.date.height = 1    # attr_dialog.nml:109
        self.date.label_text = _bind(lambda _o: _tr('~D~ate'), yielding=True)    # attr_dialog.nml:110
        self.date.label_width = 10    # attr_dialog.nml:111

        self.clock.x = 30    # attr_dialog.nml:115
        self.clock.y = 12    # attr_dialog.nml:116
        self.clock.width = 20    # attr_dialog.nml:117
        self.clock.height = 1    # attr_dialog.nml:118
        self.clock.label_text = _bind(lambda _o: _tr('~T~ime'), yielding=True)    # attr_dialog.nml:119
        self.clock.label_width = 6    # attr_dialog.nml:120

        self.recurse_caption.x = 2    # attr_dialog.nml:125
        self.recurse_caption.y = 14    # attr_dialog.nml:126
        self.recurse_caption.width = 10    # attr_dialog.nml:127
        self.recurse_caption.height = 1    # attr_dialog.nml:128
        self.recurse_caption.text = _bind(    # attr_dialog.nml:129
            lambda _o: _tr('~R~ecurse'),
            yielding=True,
        )
        self.recurse_caption.link = _bind(lambda _o: self.recurse)    # attr_dialog.nml:130

        self.recurse.x = 12    # attr_dialog.nml:134
        self.recurse.y = 14    # attr_dialog.nml:135
        self.recurse.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:136
        self.recurse.height = 1    # attr_dialog.nml:137
        self.recurse.items = _bind(    # attr_dialog.nml:138
            lambda _o: [_tr('No'), _tr('Files'), _tr('Dirs'), _tr('All')],
            yielding=True,
        )
