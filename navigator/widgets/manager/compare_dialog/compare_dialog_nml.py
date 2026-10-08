# navml: generated
"""Generated from ``compare_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # compare_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # compare_dialog.nml:2
from navml.widgets.dialog.label import Label    # compare_dialog.nml:3
from navml.widgets.dialog.radio_buttons import RadioButtons    # compare_dialog.nml:4

__navml_component__ = "CompareDialog"

__all__ = ["CompareDialog"]


class CompareDialog(Dialog, _Component):
    """Panel > Compare directories: DOS Navigator's ``dlgCompareDirs``.

    *Options* over *Selection mode*, as ``DN.DNR`` stacks them; the buttons go
    under them rather than down the right, where this library puts every
    dialog's, and DN's Help goes until there is help to show.
    """

    #: The document this class was generated from.
    __navml_source__ = "compare_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    options_caption: Label    # compare_dialog.nml:17
    options: CheckBoxes    # compare_dialog.nml:27
    mode_caption: Label    # compare_dialog.nml:36
    mode: RadioButtons    # compare_dialog.nml:45

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options_caption = Label(parent=self)    # compare_dialog.nml:16
        self.options = CheckBoxes(parent=self)    # compare_dialog.nml:26
        self.mode_caption = Label(parent=self)    # compare_dialog.nml:35
        self.mode = RadioButtons(parent=self)    # compare_dialog.nml:44

        self.modal_width = 34    # compare_dialog.nml:12
        self.modal_height = 15    # compare_dialog.nml:13
        self.title = _bind(    # compare_dialog.nml:14
            lambda _o: _tr('Compare directories'),
            yielding=True,
        )

        self.options_caption.x = 2    # compare_dialog.nml:18
        self.options_caption.y = 1    # compare_dialog.nml:19
        self.options_caption.width = 12    # compare_dialog.nml:20
        self.options_caption.height = 1    # compare_dialog.nml:21
        self.options_caption.text = _bind(    # compare_dialog.nml:22
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # compare_dialog.nml:23

        self.options.x = 2    # compare_dialog.nml:28
        self.options.y = 2    # compare_dialog.nml:29
        self.options.width = 26    # compare_dialog.nml:30
        self.options.height = 4    # compare_dialog.nml:31
        self.options.items = _bind(    # compare_dialog.nml:32
            lambda _o: [_tr('Compare ~s~ize'), _tr('Compare ~t~ime'), _tr('Compare ~a~ttributes'), _tr('Compare ~c~ontents')],
            yielding=True,
        )
        self.options.value = 3    # compare_dialog.nml:33

        self.mode_caption.x = 2    # compare_dialog.nml:37
        self.mode_caption.y = 7    # compare_dialog.nml:38
        self.mode_caption.width = 16    # compare_dialog.nml:39
        self.mode_caption.height = 1    # compare_dialog.nml:40
        self.mode_caption.text = _bind(    # compare_dialog.nml:41
            lambda _o: _tr('Selection mode'),
            yielding=True,
        )
        self.mode_caption.link = _bind(lambda _o: self.mode)    # compare_dialog.nml:42

        self.mode.x = 2    # compare_dialog.nml:46
        self.mode.y = 8    # compare_dialog.nml:47
        self.mode.width = 26    # compare_dialog.nml:48
        self.mode.height = 2    # compare_dialog.nml:49
        self.mode.items = _bind(    # compare_dialog.nml:50
            lambda _o: [_tr('S~e~lect'), _tr('~U~nselect')],
            yielding=True,
        )
