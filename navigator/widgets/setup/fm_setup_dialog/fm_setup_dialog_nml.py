# navml: generated
"""Generated from ``fm_setup_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # fm_setup_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # fm_setup_dialog.nml:2
from navml.widgets.dialog.field import Field    # fm_setup_dialog.nml:3
from navml.widgets.dialog.label import Label    # fm_setup_dialog.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # fm_setup_dialog.nml:5

__navml_component__ = "FMSetupDialog"

__all__ = ["FMSetupDialog"]


class FMSetupDialog(Dialog, _Component):
    """Options > File Manager > Setup: DOS Navigator's ``dlgFMSetup``.

    The resource whole and where it put it: *Behavior* down the left,
    *Display*, *Quick search* and the tag sign down the right, and the
    description files across the bottom.  Three columns wider than DN's 57;
    Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "fm_setup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    behavior_caption: Label    # fm_setup_dialog.nml:19
    behavior: CheckBoxes    # fm_setup_dialog.nml:28
    display_caption: Label    # fm_setup_dialog.nml:36
    display: CheckBoxes    # fm_setup_dialog.nml:45
    quick_caption: Label    # fm_setup_dialog.nml:53
    quick_search: RadioButtons    # fm_setup_dialog.nml:62
    tag_sign: Field    # fm_setup_dialog.nml:70
    description_caption: Label    # fm_setup_dialog.nml:79
    description_files: Field    # fm_setup_dialog.nml:88

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.behavior_caption = Label(parent=self)    # fm_setup_dialog.nml:18
        self.behavior = CheckBoxes(parent=self)    # fm_setup_dialog.nml:27
        self.display_caption = Label(parent=self)    # fm_setup_dialog.nml:35
        self.display = CheckBoxes(parent=self)    # fm_setup_dialog.nml:44
        self.quick_caption = Label(parent=self)    # fm_setup_dialog.nml:52
        self.quick_search = RadioButtons(parent=self)    # fm_setup_dialog.nml:61
        self.tag_sign = Field(parent=self)    # fm_setup_dialog.nml:69
        self.description_caption = Label(parent=self)    # fm_setup_dialog.nml:78
        self.description_files = Field(parent=self)    # fm_setup_dialog.nml:87

        self.modal_width = 60    # fm_setup_dialog.nml:14
        self.modal_height = 21    # fm_setup_dialog.nml:15
        self.title = 'File Manager Setup'    # fm_setup_dialog.nml:16

        self.behavior_caption.x = 2    # fm_setup_dialog.nml:20
        self.behavior_caption.y = 1    # fm_setup_dialog.nml:21
        self.behavior_caption.width = 12    # fm_setup_dialog.nml:22
        self.behavior_caption.height = 1    # fm_setup_dialog.nml:23
        self.behavior_caption.text = 'Behavior'    # fm_setup_dialog.nml:24
        self.behavior_caption.link = _bind(lambda _o: self.behavior)    # fm_setup_dialog.nml:25

        self.behavior.x = 2    # fm_setup_dialog.nml:29
        self.behavior.y = 2    # fm_setup_dialog.nml:30
        self.behavior.width = 33    # fm_setup_dialog.nml:31
        self.behavior.height = 11    # fm_setup_dialog.nml:32
        self.behavior.items = ['Auto c~h~ange directory', 'Drag~-~and~-~drop from columns', '~B~eep after copy', '~E~NTER opens archive', '~S~PACE toggles selection', '~D~EL erases file(s)', 'Use ~/~→ keys', '~A~lt difference', '~C~trl difference', 'BS - go to ~u~pper directory', 'Do not kill descriptions']    # fm_setup_dialog.nml:33

        self.display_caption.x = 37    # fm_setup_dialog.nml:37
        self.display_caption.y = 1    # fm_setup_dialog.nml:38
        self.display_caption.width = 12    # fm_setup_dialog.nml:39
        self.display_caption.height = 1    # fm_setup_dialog.nml:40
        self.display_caption.text = 'Display'    # fm_setup_dialog.nml:41
        self.display_caption.link = _bind(lambda _o: self.display)    # fm_setup_dialog.nml:42

        self.display.x = 37    # fm_setup_dialog.nml:46
        self.display.y = 2    # fm_setup_dialog.nml:47
        self.display.width = _bind(lambda _o: max(0, _o.parent.width - 39))    # fm_setup_dialog.nml:48
        self.display.height = 4    # fm_setup_dialog.nml:49
        self.display.items = ['Colu~m~n titles', 'Drive ~l~ine', '~I~nfo divider', '~T~ag character']    # fm_setup_dialog.nml:50

        self.quick_caption.x = 37    # fm_setup_dialog.nml:54
        self.quick_caption.y = 7    # fm_setup_dialog.nml:55
        self.quick_caption.width = 14    # fm_setup_dialog.nml:56
        self.quick_caption.height = 1    # fm_setup_dialog.nml:57
        self.quick_caption.text = 'Quick search'    # fm_setup_dialog.nml:58
        self.quick_caption.link = _bind(lambda _o: self.quick_search)    # fm_setup_dialog.nml:59

        self.quick_search.x = 37    # fm_setup_dialog.nml:63
        self.quick_search.y = 8    # fm_setup_dialog.nml:64
        self.quick_search.width = _bind(    # fm_setup_dialog.nml:65
            lambda _o: max(0, _o.parent.width - 39)
        )
        self.quick_search.height = 3    # fm_setup_dialog.nml:66
        self.quick_search.items = ['Si~n~gle Alt', 'Single Ct~r~l', 'Caps~+~Char']    # fm_setup_dialog.nml:67

        self.tag_sign.x = 37    # fm_setup_dialog.nml:71
        self.tag_sign.y = 12    # fm_setup_dialog.nml:72
        self.tag_sign.width = 16    # fm_setup_dialog.nml:73
        self.tag_sign.height = 1    # fm_setup_dialog.nml:74
        self.tag_sign.label_text = 'Ta~g~ sign:'    # fm_setup_dialog.nml:75
        self.tag_sign.label_width = 12    # fm_setup_dialog.nml:76

        self.description_caption.x = 2    # fm_setup_dialog.nml:80
        self.description_caption.y = 14    # fm_setup_dialog.nml:81
        self.description_caption.width = 28    # fm_setup_dialog.nml:82
        self.description_caption.height = 1    # fm_setup_dialog.nml:83
        self.description_caption.text = 'Files ~w~ith descriptions'    # fm_setup_dialog.nml:84
        self.description_caption.link = _bind(    # fm_setup_dialog.nml:85
            lambda _o: self.description_files.entry
        )

        self.description_files.x = 2    # fm_setup_dialog.nml:89
        self.description_files.y = 15    # fm_setup_dialog.nml:90
        self.description_files.width = _bind(    # fm_setup_dialog.nml:91
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.description_files.height = 1    # fm_setup_dialog.nml:92
        self.description_files.label_text = ''    # fm_setup_dialog.nml:93
        self.description_files.label_width = 0    # fm_setup_dialog.nml:94
