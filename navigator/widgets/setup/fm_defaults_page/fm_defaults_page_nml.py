# navml: generated
"""Generated from ``fm_defaults_page.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # fm_defaults_page.nml:1
from navml.widgets.dialog.label import Label    # fm_defaults_page.nml:2
from navml.widgets.dialog.radio_buttons import RadioButtons    # fm_defaults_page.nml:3
from navigator.widgets.manager.manager.manager import sort_radio_captions    # fm_defaults_page.nml:4

__navml_component__ = "FMDefaultsPage"

__all__ = ["FMDefaultsPage"]


class FMDefaultsPage(_Component):
    """Options > File Manager > New Manager defaults: DOS Navigator's ``dlgFMDefaults``.

    The resource whole: *Sort by* in three columns of three (DN's six in
    two rows, with *Attributes* and *Owner* added), *Display* in two
    of four, and what the left panel of a new file manager is.  Four columns
    wider than DN's 48, and four more for the arrows each order's caption ends
    in; Help is left out, having nothing to show yet.
    Two captions depart from DN's: *Group* is *Type*, since on POSIX a group
    is the file's owner group, and the left panel's *Drive* is *Files*.
    *Panel mode* is not DN's: Ctrl+Y's three modes, for a new panel.
    """

    #: The document this class was generated from.
    __navml_source__ = "fm_defaults_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # fm_defaults_page.nml:18

    #: Ids, annotated so the hand-written half completes them.
    sort_caption: Label    # fm_defaults_page.nml:21
    reverse: CheckBoxes    # fm_defaults_page.nml:31
    sort_by: RadioButtons    # fm_defaults_page.nml:40
    display_caption: Label    # fm_defaults_page.nml:50
    display: CheckBoxes    # fm_defaults_page.nml:58
    left_caption: Label    # fm_defaults_page.nml:67
    left_panel: RadioButtons    # fm_defaults_page.nml:75
    mode_caption: Label    # fm_defaults_page.nml:84
    view_mode: RadioButtons    # fm_defaults_page.nml:92

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.sort_caption = Label(parent=self)    # fm_defaults_page.nml:20
        self.reverse = CheckBoxes(parent=self)    # fm_defaults_page.nml:30
        self.sort_by = RadioButtons(parent=self)    # fm_defaults_page.nml:39
        self.display_caption = Label(parent=self)    # fm_defaults_page.nml:49
        self.display = CheckBoxes(parent=self)    # fm_defaults_page.nml:57
        self.left_caption = Label(parent=self)    # fm_defaults_page.nml:66
        self.left_panel = RadioButtons(parent=self)    # fm_defaults_page.nml:74
        self.mode_caption = Label(parent=self)    # fm_defaults_page.nml:83
        self.view_mode = RadioButtons(parent=self)    # fm_defaults_page.nml:91

        self.sort_caption.x = 2    # fm_defaults_page.nml:22
        self.sort_caption.y = 1    # fm_defaults_page.nml:23
        self.sort_caption.width = 12    # fm_defaults_page.nml:24
        self.sort_caption.text = _bind(    # fm_defaults_page.nml:25
            lambda _o: _tr('Sort by'),
            yielding=True,
        )
        self.sort_caption.link = _bind(lambda _o: self.sort_by)    # fm_defaults_page.nml:26

        self.reverse.y = 1    # fm_defaults_page.nml:32
        self.reverse.width = 22    # fm_defaults_page.nml:33
        self.reverse.height = 1    # fm_defaults_page.nml:34
        self.reverse.items = _bind(    # fm_defaults_page.nml:37
            lambda _o: [_tr('Re~v~erse order')],
            yielding=True,
        )
        self.reverse.x = _bind(    # fm_defaults_page.nml:36
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )

        self.sort_by.y = 2    # fm_defaults_page.nml:41
        self.sort_by.height = 3    # fm_defaults_page.nml:42
        self.sort_by.items = _bind(    # fm_defaults_page.nml:47
            lambda _o: sort_radio_captions(bool(self.reverse.value), self.glyphs)
        )
        self.sort_by.x = 2    # fm_defaults_page.nml:44
        self.sort_by.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_page.nml:45

        self.display_caption.x = 2    # fm_defaults_page.nml:51
        self.display_caption.y = 6    # fm_defaults_page.nml:52
        self.display_caption.width = 12    # fm_defaults_page.nml:53
        self.display_caption.text = _bind(    # fm_defaults_page.nml:54
            lambda _o: _tr('Display'),
            yielding=True,
        )
        self.display_caption.link = _bind(lambda _o: self.display)    # fm_defaults_page.nml:55

        self.display.y = 7    # fm_defaults_page.nml:59
        self.display.height = 4    # fm_defaults_page.nml:60
        self.display.items = _bind(    # fm_defaults_page.nml:64
            lambda _o: [_tr('Director~y~ length'), _tr('~C~urrent file'), _tr('Se~l~ected files'), _tr('T~o~tals'), _tr('~F~ree space'), _tr('Files ~h~ighlight'), _tr('E~x~ecutable first'), _tr('~A~rchives first')],
            yielding=True,
        )
        self.display.x = 2    # fm_defaults_page.nml:62
        self.display.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_page.nml:63

        self.left_caption.x = 2    # fm_defaults_page.nml:68
        self.left_caption.y = 12    # fm_defaults_page.nml:69
        self.left_caption.width = 40    # fm_defaults_page.nml:70
        self.left_caption.text = _bind(    # fm_defaults_page.nml:71
            lambda _o: _tr('Left panel in new Manager will be...'),
            yielding=True,
        )
        self.left_caption.link = _bind(lambda _o: self.left_panel)    # fm_defaults_page.nml:72

        self.left_panel.y = 13    # fm_defaults_page.nml:76
        self.left_panel.height = 1    # fm_defaults_page.nml:77
        self.left_panel.items = _bind(    # fm_defaults_page.nml:81
            lambda _o: [_tr('File ~p~anel'), _tr('~I~nfo'), _tr('T~r~ee'), _tr('A~b~sent')],
            yielding=True,
        )
        self.left_panel.x = 2    # fm_defaults_page.nml:79
        self.left_panel.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_page.nml:80

        self.mode_caption.x = 2    # fm_defaults_page.nml:85
        self.mode_caption.y = 15    # fm_defaults_page.nml:86
        self.mode_caption.width = 12    # fm_defaults_page.nml:87
        self.mode_caption.text = _bind(    # fm_defaults_page.nml:88
            lambda _o: _tr('Panel mode'),
            yielding=True,
        )
        self.mode_caption.link = _bind(lambda _o: self.view_mode)    # fm_defaults_page.nml:89

        self.view_mode.y = 16    # fm_defaults_page.nml:93
        self.view_mode.height = 1    # fm_defaults_page.nml:94
        self.view_mode.items = _bind(    # fm_defaults_page.nml:98
            lambda _o: [_tr('Si~m~ple'), _tr('~D~etailed'), _tr('List')],
            yielding=True,
        )
        self.view_mode.x = 2    # fm_defaults_page.nml:96
        self.view_mode.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_page.nml:97
