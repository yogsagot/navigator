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
    title: str = _reactive('')    # fm_defaults_page.nml:17

    #: Ids, annotated so the hand-written half completes them.
    sort_caption: Label    # fm_defaults_page.nml:20
    reverse: CheckBoxes    # fm_defaults_page.nml:31
    sort_by: RadioButtons    # fm_defaults_page.nml:39
    display_caption: Label    # fm_defaults_page.nml:47
    display: CheckBoxes    # fm_defaults_page.nml:56
    left_caption: Label    # fm_defaults_page.nml:64
    left_panel: RadioButtons    # fm_defaults_page.nml:73
    mode_caption: Label    # fm_defaults_page.nml:81
    view_mode: RadioButtons    # fm_defaults_page.nml:90

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.sort_caption = Label(parent=self)    # fm_defaults_page.nml:19
        self.reverse = CheckBoxes(parent=self)    # fm_defaults_page.nml:30
        self.sort_by = RadioButtons(parent=self)    # fm_defaults_page.nml:38
        self.display_caption = Label(parent=self)    # fm_defaults_page.nml:46
        self.display = CheckBoxes(parent=self)    # fm_defaults_page.nml:55
        self.left_caption = Label(parent=self)    # fm_defaults_page.nml:63
        self.left_panel = RadioButtons(parent=self)    # fm_defaults_page.nml:72
        self.mode_caption = Label(parent=self)    # fm_defaults_page.nml:80
        self.view_mode = RadioButtons(parent=self)    # fm_defaults_page.nml:89

        self.sort_caption.x = 2    # fm_defaults_page.nml:21
        self.sort_caption.y = 1    # fm_defaults_page.nml:22
        self.sort_caption.width = 12    # fm_defaults_page.nml:23
        self.sort_caption.height = 1    # fm_defaults_page.nml:24
        self.sort_caption.text = _bind(    # fm_defaults_page.nml:25
            lambda _o: _tr('Sort by'),
            yielding=True,
        )
        self.sort_caption.link = _bind(lambda _o: self.sort_by)    # fm_defaults_page.nml:26

        self.reverse.x = _bind(lambda _o: max(0, _o.parent.width - 24))    # fm_defaults_page.nml:32
        self.reverse.y = 1    # fm_defaults_page.nml:33
        self.reverse.width = 22    # fm_defaults_page.nml:34
        self.reverse.height = 1    # fm_defaults_page.nml:35
        self.reverse.items = _bind(    # fm_defaults_page.nml:36
            lambda _o: [_tr('Re~v~erse order')],
            yielding=True,
        )

        self.sort_by.x = 2    # fm_defaults_page.nml:40
        self.sort_by.y = 2    # fm_defaults_page.nml:41
        self.sort_by.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_page.nml:42
        self.sort_by.height = 3    # fm_defaults_page.nml:43
        self.sort_by.items = _bind(    # fm_defaults_page.nml:44
            lambda _o: [_tr('~N~ame'), _tr('~E~xtension'), _tr('~S~ize'), _tr('~T~ime'), _tr('Attributes'), _tr('O~w~ner'), _tr('Ty~p~e'), _tr('~U~nsorted')],
            yielding=True,
        )

        self.display_caption.x = 2    # fm_defaults_page.nml:48
        self.display_caption.y = 6    # fm_defaults_page.nml:49
        self.display_caption.width = 12    # fm_defaults_page.nml:50
        self.display_caption.height = 1    # fm_defaults_page.nml:51
        self.display_caption.text = _bind(    # fm_defaults_page.nml:52
            lambda _o: _tr('Display'),
            yielding=True,
        )
        self.display_caption.link = _bind(lambda _o: self.display)    # fm_defaults_page.nml:53

        self.display.x = 2    # fm_defaults_page.nml:57
        self.display.y = 7    # fm_defaults_page.nml:58
        self.display.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_page.nml:59
        self.display.height = 4    # fm_defaults_page.nml:60
        self.display.items = _bind(    # fm_defaults_page.nml:61
            lambda _o: [_tr('Director~y~ length'), _tr('~C~urrent file'), _tr('Se~l~ected files'), _tr('T~o~tals'), _tr('~F~ree space'), _tr('Files ~h~ighlight'), _tr('E~x~ecutable first'), _tr('~A~rchives first')],
            yielding=True,
        )

        self.left_caption.x = 2    # fm_defaults_page.nml:65
        self.left_caption.y = 12    # fm_defaults_page.nml:66
        self.left_caption.width = 40    # fm_defaults_page.nml:67
        self.left_caption.height = 1    # fm_defaults_page.nml:68
        self.left_caption.text = _bind(    # fm_defaults_page.nml:69
            lambda _o: _tr('Left panel in new Manager will be...'),
            yielding=True,
        )
        self.left_caption.link = _bind(lambda _o: self.left_panel)    # fm_defaults_page.nml:70

        self.left_panel.x = 2    # fm_defaults_page.nml:74
        self.left_panel.y = 13    # fm_defaults_page.nml:75
        self.left_panel.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_page.nml:76
        self.left_panel.height = 1    # fm_defaults_page.nml:77
        self.left_panel.items = _bind(    # fm_defaults_page.nml:78
            lambda _o: [_tr('Files'), _tr('~I~nfo'), _tr('T~r~ee'), _tr('A~b~sent')],
            yielding=True,
        )

        self.mode_caption.x = 2    # fm_defaults_page.nml:82
        self.mode_caption.y = 15    # fm_defaults_page.nml:83
        self.mode_caption.width = 12    # fm_defaults_page.nml:84
        self.mode_caption.height = 1    # fm_defaults_page.nml:85
        self.mode_caption.text = _bind(    # fm_defaults_page.nml:86
            lambda _o: _tr('Panel mode'),
            yielding=True,
        )
        self.mode_caption.link = _bind(lambda _o: self.view_mode)    # fm_defaults_page.nml:87

        self.view_mode.x = 2    # fm_defaults_page.nml:91
        self.view_mode.y = 16    # fm_defaults_page.nml:92
        self.view_mode.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # fm_defaults_page.nml:93
        self.view_mode.height = 1    # fm_defaults_page.nml:94
        self.view_mode.items = _bind(    # fm_defaults_page.nml:95
            lambda _o: [_tr('Si~m~ple'), _tr('~D~etailed'), _tr('List')],
            yielding=True,
        )
