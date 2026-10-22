# navml: generated
"""Generated from ``fm_setup_page.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # fm_setup_page.nml:1
from navml.widgets.dialog.field import Field    # fm_setup_page.nml:2
from navml.widgets.dialog.label import Label    # fm_setup_page.nml:3
from navml.widgets.dialog.radio_buttons import RadioButtons    # fm_setup_page.nml:4

__navml_component__ = "FMSetupPage"

__all__ = ["FMSetupPage"]


class FMSetupPage(_Component):
    """Options > File Manager > Setup: DOS Navigator's ``dlgFMSetup``.

    The resource's *Behavior* down the left and *Display* and the tag sign down
    the right, less what only meant something on DOS: *Alt difference* and
    *Ctrl difference*, the *Quick search* key (Single Alt, Single Ctrl,
    Caps+Char -- a terminal reports none of them alone, and Ctrl+S is the key),
    the *Drive line*, and ``descript.ion`` descriptions (*Do not kill
    descriptions*, *Files with descriptions*).  DN's caption *Use ~/~→ keys*
    had lost its left arrow; it is *Use ←/→ keys* here.  Three columns wider
    than DN's 57; Help is left out, having nothing to show yet.  *Auto refresh
    panels* is not DN's (``[file_manager] auto_refresh``), nor is *Right
    button* (``[file_manager] right_button``): DN's always selected, nor *Link
    target line* (``[file_manager] link_line``): DN had no symlinks, nor *Option
    flags* (``[file_manager] show_options``): the panels' strips on their bottom
    frames.
    """

    #: The document this class was generated from.
    __navml_source__ = "fm_setup_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # fm_setup_page.nml:23

    #: Ids, annotated so the hand-written half completes them.
    behavior_caption: Label    # fm_setup_page.nml:26
    behavior: CheckBoxes    # fm_setup_page.nml:35
    display_caption: Label    # fm_setup_page.nml:43
    display: CheckBoxes    # fm_setup_page.nml:52
    tag_sign: Field    # fm_setup_page.nml:60
    right_button_caption: Label    # fm_setup_page.nml:69
    right_button: RadioButtons    # fm_setup_page.nml:78

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.behavior_caption = Label(parent=self)    # fm_setup_page.nml:25
        self.behavior = CheckBoxes(parent=self)    # fm_setup_page.nml:34
        self.display_caption = Label(parent=self)    # fm_setup_page.nml:42
        self.display = CheckBoxes(parent=self)    # fm_setup_page.nml:51
        self.tag_sign = Field(parent=self)    # fm_setup_page.nml:59
        self.right_button_caption = Label(parent=self)    # fm_setup_page.nml:68
        self.right_button = RadioButtons(parent=self)    # fm_setup_page.nml:77

        self.behavior_caption.x = 2    # fm_setup_page.nml:27
        self.behavior_caption.y = 1    # fm_setup_page.nml:28
        self.behavior_caption.width = 12    # fm_setup_page.nml:29
        self.behavior_caption.height = 1    # fm_setup_page.nml:30
        self.behavior_caption.text = _bind(    # fm_setup_page.nml:31
            lambda _o: _tr('Behavior'),
            yielding=True,
        )
        self.behavior_caption.link = _bind(lambda _o: self.behavior)    # fm_setup_page.nml:32

        self.behavior.x = 2    # fm_setup_page.nml:36
        self.behavior.y = 2    # fm_setup_page.nml:37
        self.behavior.width = 33    # fm_setup_page.nml:38
        self.behavior.height = 9    # fm_setup_page.nml:39
        self.behavior.items = _bind(    # fm_setup_page.nml:40
            lambda _o: [_tr('Auto c~h~ange directory'), _tr('Drag~-~and~-~drop from columns'), _tr('~B~eep after copy'), _tr('~E~NTER opens archive'), _tr('~S~PACE toggles selection'), _tr('~D~EL erases file(s)'), _tr('Use ←/→ ~k~eys'), _tr('BS - go to ~u~pper directory'), _tr('Auto ~r~efresh panels')],
            yielding=True,
        )

        self.display_caption.x = 37    # fm_setup_page.nml:44
        self.display_caption.y = 1    # fm_setup_page.nml:45
        self.display_caption.width = 12    # fm_setup_page.nml:46
        self.display_caption.height = 1    # fm_setup_page.nml:47
        self.display_caption.text = _bind(    # fm_setup_page.nml:48
            lambda _o: _tr('Display'),
            yielding=True,
        )
        self.display_caption.link = _bind(lambda _o: self.display)    # fm_setup_page.nml:49

        self.display.x = 37    # fm_setup_page.nml:53
        self.display.y = 2    # fm_setup_page.nml:54
        self.display.width = _bind(lambda _o: max(0, _o.parent.width - 39))    # fm_setup_page.nml:55
        self.display.height = 5    # fm_setup_page.nml:56
        self.display.items = _bind(    # fm_setup_page.nml:57
            lambda _o: [_tr('Colu~m~n titles'), _tr('~I~nfo divider'), _tr('~T~ag character'), _tr('Li~n~k target line'), _tr('Option ~f~lags')],
            yielding=True,
        )

        self.tag_sign.x = 37    # fm_setup_page.nml:61
        self.tag_sign.y = 8    # fm_setup_page.nml:62
        self.tag_sign.width = 16    # fm_setup_page.nml:63
        self.tag_sign.height = 1    # fm_setup_page.nml:64
        self.tag_sign.label_text = _bind(    # fm_setup_page.nml:65
            lambda _o: _tr('Ta~g~ sign:'),
            yielding=True,
        )
        self.tag_sign.label_width = 12    # fm_setup_page.nml:66

        self.right_button_caption.x = 37    # fm_setup_page.nml:70
        self.right_button_caption.y = 10    # fm_setup_page.nml:71
        self.right_button_caption.width = 14    # fm_setup_page.nml:72
        self.right_button_caption.height = 1    # fm_setup_page.nml:73
        self.right_button_caption.text = _bind(    # fm_setup_page.nml:74
            lambda _o: _tr('Right button'),
            yielding=True,
        )
        self.right_button_caption.link = _bind(lambda _o: self.right_button)    # fm_setup_page.nml:75

        self.right_button.x = 37    # fm_setup_page.nml:79
        self.right_button.y = 11    # fm_setup_page.nml:80
        self.right_button.width = _bind(    # fm_setup_page.nml:81
            lambda _o: max(0, _o.parent.width - 39)
        )
        self.right_button.height = 2    # fm_setup_page.nml:82
        self.right_button.items = _bind(    # fm_setup_page.nml:83
            lambda _o: [_tr('Conte~x~t menu'), _tr('Se~l~ect files')],
            yielding=True,
        )
