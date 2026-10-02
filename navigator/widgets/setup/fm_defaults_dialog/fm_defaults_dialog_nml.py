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
    """

    #: The document this class was generated from.
    __navml_source__ = "fm_defaults_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    sort_caption: Label    # fm_defaults_dialog.nml:17
    sort_by: RadioButtons    # fm_defaults_dialog.nml:26
    display_caption: Label    # fm_defaults_dialog.nml:34
    display: CheckBoxes    # fm_defaults_dialog.nml:43
    left_caption: Label    # fm_defaults_dialog.nml:51
    left_panel: RadioButtons    # fm_defaults_dialog.nml:60

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.sort_caption = Label(parent=self)    # fm_defaults_dialog.nml:16
        self.sort_by = RadioButtons(parent=self)    # fm_defaults_dialog.nml:25
        self.display_caption = Label(parent=self)    # fm_defaults_dialog.nml:33
        self.display = CheckBoxes(parent=self)    # fm_defaults_dialog.nml:42
        self.left_caption = Label(parent=self)    # fm_defaults_dialog.nml:50
        self.left_panel = RadioButtons(parent=self)    # fm_defaults_dialog.nml:59

        self.modal_width = 52    # fm_defaults_dialog.nml:12
        self.modal_height = 18    # fm_defaults_dialog.nml:13
        self.title = 'Panel Defaults'    # fm_defaults_dialog.nml:14

        self.sort_caption.x = 2    # fm_defaults_dialog.nml:18
        self.sort_caption.y = 1    # fm_defaults_dialog.nml:19
        self.sort_caption.width = 12    # fm_defaults_dialog.nml:20
        self.sort_caption.height = 1    # fm_defaults_dialog.nml:21
        self.sort_caption.text = 'Sort by'    # fm_defaults_dialog.nml:22
        self.sort_caption.link = _bind(lambda _o: self.sort_by)    # fm_defaults_dialog.nml:23

        self.sort_by.x = 2    # fm_defaults_dialog.nml:27
        self.sort_by.y = 2    # fm_defaults_dialog.nml:28
        self.sort_by.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_dialog.nml:29
        self.sort_by.height = 2    # fm_defaults_dialog.nml:30
        self.sort_by.items = ['~N~ame', '~E~xtension', '~S~ize', '~T~ime', '~G~roup', '~U~nsorted']    # fm_defaults_dialog.nml:31

        self.display_caption.x = 2    # fm_defaults_dialog.nml:35
        self.display_caption.y = 5    # fm_defaults_dialog.nml:36
        self.display_caption.width = 12    # fm_defaults_dialog.nml:37
        self.display_caption.height = 1    # fm_defaults_dialog.nml:38
        self.display_caption.text = 'Display'    # fm_defaults_dialog.nml:39
        self.display_caption.link = _bind(lambda _o: self.display)    # fm_defaults_dialog.nml:40

        self.display.x = 2    # fm_defaults_dialog.nml:44
        self.display.y = 6    # fm_defaults_dialog.nml:45
        self.display.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_dialog.nml:46
        self.display.height = 4    # fm_defaults_dialog.nml:47
        self.display.items = ['Director~y~ length', '~C~urrent file', 'Se~l~ected files', 'T~o~tals', '~F~ree space', 'Files ~h~ighlight', 'E~x~ecutable first', '~A~rchives first']    # fm_defaults_dialog.nml:48

        self.left_caption.x = 2    # fm_defaults_dialog.nml:52
        self.left_caption.y = 11    # fm_defaults_dialog.nml:53
        self.left_caption.width = 40    # fm_defaults_dialog.nml:54
        self.left_caption.height = 1    # fm_defaults_dialog.nml:55
        self.left_caption.text = 'Left panel in new Manager will be...'    # fm_defaults_dialog.nml:56
        self.left_caption.link = _bind(lambda _o: self.left_panel)    # fm_defaults_dialog.nml:57

        self.left_panel.x = 2    # fm_defaults_dialog.nml:61
        self.left_panel.y = 12    # fm_defaults_dialog.nml:62
        self.left_panel.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_dialog.nml:63
        self.left_panel.height = 1    # fm_defaults_dialog.nml:64
        self.left_panel.items = ['~D~rive', '~I~nfo', 'T~r~ee', 'A~b~sent']    # fm_defaults_dialog.nml:65
