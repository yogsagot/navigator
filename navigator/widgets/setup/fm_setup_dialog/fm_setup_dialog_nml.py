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

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # fm_setup_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # fm_setup_dialog.nml:2
from navml.widgets.dialog.field import Field    # fm_setup_dialog.nml:3
from navml.widgets.dialog.label import Label    # fm_setup_dialog.nml:4

__navml_component__ = "FMSetupDialog"

__all__ = ["FMSetupDialog"]


class FMSetupDialog(Dialog, _Component):
    """Options > File Manager > Setup: DOS Navigator's ``dlgFMSetup``.

    The resource's *Behavior* down the left and *Display* and the tag sign down
    the right, less what only meant something on DOS: *Alt difference* and
    *Ctrl difference*, the *Quick search* key (Single Alt, Single Ctrl,
    Caps+Char -- a terminal reports none of them alone, and Ctrl+S is the key),
    the *Drive line*, and ``descript.ion`` descriptions (*Do not kill
    descriptions*, *Files with descriptions*).  DN's caption *Use ~/~→ keys*
    had lost its left arrow; it is *Use ←/→ keys* here.  Three columns wider
    than DN's 57; Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "fm_setup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    behavior_caption: Label    # fm_setup_dialog.nml:22
    behavior: CheckBoxes    # fm_setup_dialog.nml:31
    display_caption: Label    # fm_setup_dialog.nml:39
    display: CheckBoxes    # fm_setup_dialog.nml:48
    tag_sign: Field    # fm_setup_dialog.nml:56

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.behavior_caption = Label(parent=self)    # fm_setup_dialog.nml:21
        self.behavior = CheckBoxes(parent=self)    # fm_setup_dialog.nml:30
        self.display_caption = Label(parent=self)    # fm_setup_dialog.nml:38
        self.display = CheckBoxes(parent=self)    # fm_setup_dialog.nml:47
        self.tag_sign = Field(parent=self)    # fm_setup_dialog.nml:55

        self.modal_width = 60    # fm_setup_dialog.nml:17
        self.modal_height = 15    # fm_setup_dialog.nml:18
        self.title = _bind(lambda _o: _tr('File Manager Setup'), yielding=True)    # fm_setup_dialog.nml:19

        self.behavior_caption.x = 2    # fm_setup_dialog.nml:23
        self.behavior_caption.y = 1    # fm_setup_dialog.nml:24
        self.behavior_caption.width = 12    # fm_setup_dialog.nml:25
        self.behavior_caption.height = 1    # fm_setup_dialog.nml:26
        self.behavior_caption.text = _bind(    # fm_setup_dialog.nml:27
            lambda _o: _tr('Behavior'),
            yielding=True,
        )
        self.behavior_caption.link = _bind(lambda _o: self.behavior)    # fm_setup_dialog.nml:28

        self.behavior.x = 2    # fm_setup_dialog.nml:32
        self.behavior.y = 2    # fm_setup_dialog.nml:33
        self.behavior.width = 33    # fm_setup_dialog.nml:34
        self.behavior.height = 8    # fm_setup_dialog.nml:35
        self.behavior.items = _bind(    # fm_setup_dialog.nml:36
            lambda _o: [_tr('Auto c~h~ange directory'), _tr('Drag~-~and~-~drop from columns'), _tr('~B~eep after copy'), _tr('~E~NTER opens archive'), _tr('~S~PACE toggles selection'), _tr('~D~EL erases file(s)'), _tr('Use ←/→ ~k~eys'), _tr('BS - go to ~u~pper directory')],
            yielding=True,
        )

        self.display_caption.x = 37    # fm_setup_dialog.nml:40
        self.display_caption.y = 1    # fm_setup_dialog.nml:41
        self.display_caption.width = 12    # fm_setup_dialog.nml:42
        self.display_caption.height = 1    # fm_setup_dialog.nml:43
        self.display_caption.text = _bind(    # fm_setup_dialog.nml:44
            lambda _o: _tr('Display'),
            yielding=True,
        )
        self.display_caption.link = _bind(lambda _o: self.display)    # fm_setup_dialog.nml:45

        self.display.x = 37    # fm_setup_dialog.nml:49
        self.display.y = 2    # fm_setup_dialog.nml:50
        self.display.width = _bind(lambda _o: max(0, _o.parent.width - 39))    # fm_setup_dialog.nml:51
        self.display.height = 3    # fm_setup_dialog.nml:52
        self.display.items = _bind(    # fm_setup_dialog.nml:53
            lambda _o: [_tr('Colu~m~n titles'), _tr('~I~nfo divider'), _tr('~T~ag character')],
            yielding=True,
        )

        self.tag_sign.x = 37    # fm_setup_dialog.nml:57
        self.tag_sign.y = 6    # fm_setup_dialog.nml:58
        self.tag_sign.width = 16    # fm_setup_dialog.nml:59
        self.tag_sign.height = 1    # fm_setup_dialog.nml:60
        self.tag_sign.label_text = _bind(    # fm_setup_dialog.nml:61
            lambda _o: _tr('Ta~g~ sign:'),
            yielding=True,
        )
        self.tag_sign.label_width = 12    # fm_setup_dialog.nml:62
