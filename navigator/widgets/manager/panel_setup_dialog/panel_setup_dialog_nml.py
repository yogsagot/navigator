# navml: generated
"""Generated from ``panel_setup_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # panel_setup_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # panel_setup_dialog.nml:2
from navml.widgets.dialog.field import Field    # panel_setup_dialog.nml:3
from navml.widgets.dialog.label import Label    # panel_setup_dialog.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # panel_setup_dialog.nml:5

__navml_component__ = "PanelSetupDialog"

__all__ = ["PanelSetupDialog"]


class PanelSetupDialog(Dialog, _Component):
    """Alt+S, Panel > Setup Panel: DOS Navigator's ``dlgPanelSetup``, *Panel Options*.

    *Panel Defaults* for one panel, with the file mask where that dialog has
    the left panel's kind: laid out as ``FMDefaultsPage`` is, so the two
    read alike, with its captions -- *Group* is *Type* here too.  Help is left
    out, having nothing to show yet.  *Reverse order* is not DN's.
    """

    #: The document this class was generated from.
    __navml_source__ = "panel_setup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    sort_caption: Label    # panel_setup_dialog.nml:19
    reverse: CheckBoxes    # panel_setup_dialog.nml:30
    sort_by: RadioButtons    # panel_setup_dialog.nml:39
    display_caption: Label    # panel_setup_dialog.nml:47
    display: CheckBoxes    # panel_setup_dialog.nml:56
    mask_caption: Label    # panel_setup_dialog.nml:64
    mask: Field    # panel_setup_dialog.nml:74

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.sort_caption = Label(parent=self)    # panel_setup_dialog.nml:18
        self.reverse = CheckBoxes(parent=self)    # panel_setup_dialog.nml:29
        self.sort_by = RadioButtons(parent=self)    # panel_setup_dialog.nml:38
        self.display_caption = Label(parent=self)    # panel_setup_dialog.nml:46
        self.display = CheckBoxes(parent=self)    # panel_setup_dialog.nml:55
        self.mask_caption = Label(parent=self)    # panel_setup_dialog.nml:63
        self.mask = Field(parent=self)    # panel_setup_dialog.nml:73

        self.modal_width = 56    # panel_setup_dialog.nml:14
        self.modal_height = 18    # panel_setup_dialog.nml:15
        self.title = _bind(lambda _o: _tr('Panel Options'), yielding=True)    # panel_setup_dialog.nml:16

        self.sort_caption.x = 2    # panel_setup_dialog.nml:20
        self.sort_caption.y = 1    # panel_setup_dialog.nml:21
        self.sort_caption.width = 12    # panel_setup_dialog.nml:22
        self.sort_caption.height = 1    # panel_setup_dialog.nml:23
        self.sort_caption.text = _bind(    # panel_setup_dialog.nml:24
            lambda _o: _tr('Sort by'),
            yielding=True,
        )
        self.sort_caption.link = _bind(lambda _o: self.sort_by)    # panel_setup_dialog.nml:25

        self.reverse.x = _bind(lambda _o: max(0, _o.parent.width - 24))    # panel_setup_dialog.nml:31
        self.reverse.y = 1    # panel_setup_dialog.nml:32
        self.reverse.width = 22    # panel_setup_dialog.nml:33
        self.reverse.height = 1    # panel_setup_dialog.nml:34
        self.reverse.items = _bind(    # panel_setup_dialog.nml:35
            lambda _o: [_tr('Re~v~erse order')],
            yielding=True,
        )
        self.reverse.tooltips = _bind(    # panel_setup_dialog.nml:36
            lambda _o: [_tr('The order runs the other way: largest, newest, Z first...')],
            yielding=True,
        )

        self.sort_by.x = 2    # panel_setup_dialog.nml:40
        self.sort_by.y = 2    # panel_setup_dialog.nml:41
        self.sort_by.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # panel_setup_dialog.nml:42
        self.sort_by.height = 3    # panel_setup_dialog.nml:43
        self.sort_by.items = _bind(    # panel_setup_dialog.nml:44
            lambda _o: [_tr('~N~ame'), _tr('~E~xtension'), _tr('~S~ize'), _tr('~T~ime'), _tr('Attributes'), _tr('O~w~ner'), _tr('Ty~p~e'), _tr('~U~nsorted')],
            yielding=True,
        )

        self.display_caption.x = 2    # panel_setup_dialog.nml:48
        self.display_caption.y = 6    # panel_setup_dialog.nml:49
        self.display_caption.width = 12    # panel_setup_dialog.nml:50
        self.display_caption.height = 1    # panel_setup_dialog.nml:51
        self.display_caption.text = _bind(    # panel_setup_dialog.nml:52
            lambda _o: _tr('Display'),
            yielding=True,
        )
        self.display_caption.link = _bind(lambda _o: self.display)    # panel_setup_dialog.nml:53

        self.display.x = 2    # panel_setup_dialog.nml:57
        self.display.y = 7    # panel_setup_dialog.nml:58
        self.display.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # panel_setup_dialog.nml:59
        self.display.height = 4    # panel_setup_dialog.nml:60
        self.display.items = _bind(    # panel_setup_dialog.nml:61
            lambda _o: [_tr('Director~y~ length'), _tr('~C~urrent file'), _tr('Se~l~ected files'), _tr('T~o~tals'), _tr('~F~ree space'), _tr('Files ~h~ighlight'), _tr('E~x~ecutable first'), _tr('~A~rchives first')],
            yielding=True,
        )

        self.mask_caption.x = 2    # panel_setup_dialog.nml:65
        self.mask_caption.y = 12    # panel_setup_dialog.nml:66
        self.mask_caption.width = 12    # panel_setup_dialog.nml:67
        self.mask_caption.height = 1    # panel_setup_dialog.nml:68
        self.mask_caption.text = _bind(    # panel_setup_dialog.nml:69
            lambda _o: _tr('File ~m~ask'),
            yielding=True,
        )
        self.mask_caption.link = _bind(lambda _o: self.mask.entry)    # panel_setup_dialog.nml:70

        self.mask.x = 2    # panel_setup_dialog.nml:75
        self.mask.y = 13    # panel_setup_dialog.nml:76
        self.mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # panel_setup_dialog.nml:77
        self.mask.height = 1    # panel_setup_dialog.nml:78
        self.mask.label_text = ''    # panel_setup_dialog.nml:79
        self.mask.label_width = 0    # panel_setup_dialog.nml:80
        self.mask.history_id = 'file_mask'    # panel_setup_dialog.nml:81
