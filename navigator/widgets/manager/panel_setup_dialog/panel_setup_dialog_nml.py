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
    the left panel's kind: laid out as ``FMDefaultsDialog`` is, so the two
    read alike, with its captions -- *Group* is *Type* here too.  Help is left
    out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "panel_setup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    sort_caption: Label    # panel_setup_dialog.nml:19
    sort_by: RadioButtons    # panel_setup_dialog.nml:28
    display_caption: Label    # panel_setup_dialog.nml:36
    display: CheckBoxes    # panel_setup_dialog.nml:45
    mask_caption: Label    # panel_setup_dialog.nml:53
    mask: Field    # panel_setup_dialog.nml:63

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.sort_caption = Label(parent=self)    # panel_setup_dialog.nml:18
        self.sort_by = RadioButtons(parent=self)    # panel_setup_dialog.nml:27
        self.display_caption = Label(parent=self)    # panel_setup_dialog.nml:35
        self.display = CheckBoxes(parent=self)    # panel_setup_dialog.nml:44
        self.mask_caption = Label(parent=self)    # panel_setup_dialog.nml:52
        self.mask = Field(parent=self)    # panel_setup_dialog.nml:62

        self.modal_width = 52    # panel_setup_dialog.nml:14
        self.modal_height = 17    # panel_setup_dialog.nml:15
        self.title = 'Panel Options'    # panel_setup_dialog.nml:16

        self.sort_caption.x = 2    # panel_setup_dialog.nml:20
        self.sort_caption.y = 1    # panel_setup_dialog.nml:21
        self.sort_caption.width = 12    # panel_setup_dialog.nml:22
        self.sort_caption.height = 1    # panel_setup_dialog.nml:23
        self.sort_caption.text = 'Sort by'    # panel_setup_dialog.nml:24
        self.sort_caption.link = _bind(lambda _o: self.sort_by)    # panel_setup_dialog.nml:25

        self.sort_by.x = 2    # panel_setup_dialog.nml:29
        self.sort_by.y = 2    # panel_setup_dialog.nml:30
        self.sort_by.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # panel_setup_dialog.nml:31
        self.sort_by.height = 2    # panel_setup_dialog.nml:32
        self.sort_by.items = ['~N~ame', '~E~xtension', '~S~ize', '~T~ime', 'T~y~pe', '~U~nsorted']    # panel_setup_dialog.nml:33

        self.display_caption.x = 2    # panel_setup_dialog.nml:37
        self.display_caption.y = 5    # panel_setup_dialog.nml:38
        self.display_caption.width = 12    # panel_setup_dialog.nml:39
        self.display_caption.height = 1    # panel_setup_dialog.nml:40
        self.display_caption.text = 'Display'    # panel_setup_dialog.nml:41
        self.display_caption.link = _bind(lambda _o: self.display)    # panel_setup_dialog.nml:42

        self.display.x = 2    # panel_setup_dialog.nml:46
        self.display.y = 6    # panel_setup_dialog.nml:47
        self.display.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # panel_setup_dialog.nml:48
        self.display.height = 4    # panel_setup_dialog.nml:49
        self.display.items = ['Director~y~ length', '~C~urrent file', 'Se~l~ected files', 'T~o~tals', '~F~ree space', 'Files ~h~ighlight', 'E~x~ecutable first', '~A~rchives first']    # panel_setup_dialog.nml:50

        self.mask_caption.x = 2    # panel_setup_dialog.nml:54
        self.mask_caption.y = 11    # panel_setup_dialog.nml:55
        self.mask_caption.width = 12    # panel_setup_dialog.nml:56
        self.mask_caption.height = 1    # panel_setup_dialog.nml:57
        self.mask_caption.text = 'File ~m~ask'    # panel_setup_dialog.nml:58
        self.mask_caption.link = _bind(lambda _o: self.mask.entry)    # panel_setup_dialog.nml:59

        self.mask.x = 2    # panel_setup_dialog.nml:64
        self.mask.y = 12    # panel_setup_dialog.nml:65
        self.mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # panel_setup_dialog.nml:66
        self.mask.height = 1    # panel_setup_dialog.nml:67
        self.mask.label_text = ''    # panel_setup_dialog.nml:68
        self.mask.label_width = 0    # panel_setup_dialog.nml:69
        self.mask.history_id = 'file_mask'    # panel_setup_dialog.nml:70
