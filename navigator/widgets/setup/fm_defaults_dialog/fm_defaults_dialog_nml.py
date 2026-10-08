# navml: generated
"""Generated from ``fm_defaults_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # fm_defaults_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # fm_defaults_dialog.nml:2
from navml.widgets.dialog.label import Label    # fm_defaults_dialog.nml:3
from navml.widgets.dialog.radio_buttons import RadioButtons    # fm_defaults_dialog.nml:4

__navml_component__ = "FMDefaultsDialog"

__all__ = ["FMDefaultsDialog"]


class FMDefaultsDialog(Dialog, _Component):
    """Options > File Manager > New Manager defaults: DOS Navigator's ``dlgFMDefaults``.

    The resource whole: *Sort by* in three columns of two, *Display* in two
    of four, and what the left panel of a new file manager is.  Four columns
    wider than DN's 48; Help is left out, having nothing to show yet.
    Two captions depart from DN's: *Group* is *Type*, since on POSIX a group
    is the file's owner group, and the left panel's *Drive* is *Files*.
    """

    #: The document this class was generated from.
    __navml_source__ = "fm_defaults_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    sort_caption: Label    # fm_defaults_dialog.nml:19
    sort_by: RadioButtons    # fm_defaults_dialog.nml:28
    display_caption: Label    # fm_defaults_dialog.nml:36
    display: CheckBoxes    # fm_defaults_dialog.nml:45
    left_caption: Label    # fm_defaults_dialog.nml:53
    left_panel: RadioButtons    # fm_defaults_dialog.nml:62

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.sort_caption = Label(parent=self)    # fm_defaults_dialog.nml:18
        self.sort_by = RadioButtons(parent=self)    # fm_defaults_dialog.nml:27
        self.display_caption = Label(parent=self)    # fm_defaults_dialog.nml:35
        self.display = CheckBoxes(parent=self)    # fm_defaults_dialog.nml:44
        self.left_caption = Label(parent=self)    # fm_defaults_dialog.nml:52
        self.left_panel = RadioButtons(parent=self)    # fm_defaults_dialog.nml:61

        self.modal_width = 52    # fm_defaults_dialog.nml:14
        self.modal_height = 18    # fm_defaults_dialog.nml:15
        self.title = _bind(lambda _o: _tr('Panel Defaults'), yielding=True)    # fm_defaults_dialog.nml:16

        self.sort_caption.x = 2    # fm_defaults_dialog.nml:20
        self.sort_caption.y = 1    # fm_defaults_dialog.nml:21
        self.sort_caption.width = 12    # fm_defaults_dialog.nml:22
        self.sort_caption.height = 1    # fm_defaults_dialog.nml:23
        self.sort_caption.text = _bind(    # fm_defaults_dialog.nml:24
            lambda _o: _tr('Sort by'),
            yielding=True,
        )
        self.sort_caption.link = _bind(lambda _o: self.sort_by)    # fm_defaults_dialog.nml:25

        self.sort_by.x = 2    # fm_defaults_dialog.nml:29
        self.sort_by.y = 2    # fm_defaults_dialog.nml:30
        self.sort_by.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_dialog.nml:31
        self.sort_by.height = 2    # fm_defaults_dialog.nml:32
        self.sort_by.items = _bind(    # fm_defaults_dialog.nml:33
            lambda _o: [_tr('~N~ame'), _tr('~E~xtension'), _tr('~S~ize'), _tr('~T~ime'), _tr('T~y~pe'), _tr('~U~nsorted')],
            yielding=True,
        )

        self.display_caption.x = 2    # fm_defaults_dialog.nml:37
        self.display_caption.y = 5    # fm_defaults_dialog.nml:38
        self.display_caption.width = 12    # fm_defaults_dialog.nml:39
        self.display_caption.height = 1    # fm_defaults_dialog.nml:40
        self.display_caption.text = _bind(    # fm_defaults_dialog.nml:41
            lambda _o: _tr('Display'),
            yielding=True,
        )
        self.display_caption.link = _bind(lambda _o: self.display)    # fm_defaults_dialog.nml:42

        self.display.x = 2    # fm_defaults_dialog.nml:46
        self.display.y = 6    # fm_defaults_dialog.nml:47
        self.display.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_dialog.nml:48
        self.display.height = 4    # fm_defaults_dialog.nml:49
        self.display.items = _bind(    # fm_defaults_dialog.nml:50
            lambda _o: [_tr('Director~y~ length'), _tr('~C~urrent file'), _tr('Se~l~ected files'), _tr('T~o~tals'), _tr('~F~ree space'), _tr('Files ~h~ighlight'), _tr('E~x~ecutable first'), _tr('~A~rchives first')],
            yielding=True,
        )

        self.left_caption.x = 2    # fm_defaults_dialog.nml:54
        self.left_caption.y = 11    # fm_defaults_dialog.nml:55
        self.left_caption.width = 40    # fm_defaults_dialog.nml:56
        self.left_caption.height = 1    # fm_defaults_dialog.nml:57
        self.left_caption.text = _bind(    # fm_defaults_dialog.nml:58
            lambda _o: _tr('Left panel in new Manager will be...'),
            yielding=True,
        )
        self.left_caption.link = _bind(lambda _o: self.left_panel)    # fm_defaults_dialog.nml:59

        self.left_panel.x = 2    # fm_defaults_dialog.nml:63
        self.left_panel.y = 12    # fm_defaults_dialog.nml:64
        self.left_panel.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_dialog.nml:65
        self.left_panel.height = 1    # fm_defaults_dialog.nml:66
        self.left_panel.items = _bind(    # fm_defaults_dialog.nml:67
            lambda _o: [_tr('Files'), _tr('~I~nfo'), _tr('T~r~ee'), _tr('A~b~sent')],
            yielding=True,
        )
