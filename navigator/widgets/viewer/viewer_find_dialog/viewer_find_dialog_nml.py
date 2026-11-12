# navml: generated
"""Generated from ``viewer_find_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # viewer_find_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # viewer_find_dialog.nml:2
from navml.widgets.dialog.field import Field    # viewer_find_dialog.nml:3
from navml.widgets.dialog.hex_line import HexLine    # viewer_find_dialog.nml:4
from navml.widgets.dialog.label import Label    # viewer_find_dialog.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # viewer_find_dialog.nml:6

__navml_component__ = "ViewerFindDialog"

__all__ = ["ViewerFindDialog"]


class ViewerFindDialog(Dialog, _Component):
    """F7 in a viewer: DOS Navigator's ``dlgViewerFind``.

    Laid out where ``DN.DNR`` puts it -- the line under its caption, *Options*
    and *Direction* side by side under that -- in the same 50 by 14, with the
    *Hex* line ``StartSearch`` put two rows under the first (``THexLine``).  DN's
    Help button goes, as every dialog's does until there is help to show.
    """

    #: The document this class was generated from.
    __navml_source__ = "viewer_find_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    what_caption: Label    # viewer_find_dialog.nml:20
    what: Field    # viewer_find_dialog.nml:30
    hex_caption: Label    # viewer_find_dialog.nml:41
    hex: HexLine    # viewer_find_dialog.nml:50
    options_caption: Label    # viewer_find_dialog.nml:58
    options: CheckBoxes    # viewer_find_dialog.nml:66
    direction_caption: Label    # viewer_find_dialog.nml:74
    direction: RadioButtons    # viewer_find_dialog.nml:82

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.what_caption = Label(parent=self)    # viewer_find_dialog.nml:19
        self.what = Field(parent=self)    # viewer_find_dialog.nml:29
        self.hex_caption = Label(parent=self)    # viewer_find_dialog.nml:40
        self.hex = HexLine(parent=self)    # viewer_find_dialog.nml:49
        self.options_caption = Label(parent=self)    # viewer_find_dialog.nml:57
        self.options = CheckBoxes(parent=self)    # viewer_find_dialog.nml:65
        self.direction_caption = Label(parent=self)    # viewer_find_dialog.nml:73
        self.direction = RadioButtons(parent=self)    # viewer_find_dialog.nml:81

        self.modal_width = 50    # viewer_find_dialog.nml:15
        self.modal_height = 14    # viewer_find_dialog.nml:16
        self.title = _bind(lambda _o: _tr('Find'), yielding=True)    # viewer_find_dialog.nml:17

        self.what_caption.x = 2    # viewer_find_dialog.nml:21
        self.what_caption.y = 2    # viewer_find_dialog.nml:22
        self.what_caption.width = 14    # viewer_find_dialog.nml:23
        self.what_caption.text = _bind(    # viewer_find_dialog.nml:24
            lambda _o: _tr('~S~earch for'),
            yielding=True,
        )
        self.what_caption.link = _bind(lambda _o: self.what.entry)    # viewer_find_dialog.nml:25

        self.what.y = 3    # viewer_find_dialog.nml:31
        self.what.label_text = ''    # viewer_find_dialog.nml:35
        self.what.label_width = 0    # viewer_find_dialog.nml:36
        self.what.history_id = 'view_find'    # viewer_find_dialog.nml:37
        self.what.x = 2    # viewer_find_dialog.nml:33
        self.what.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # viewer_find_dialog.nml:34

        self.hex_caption.x = 2    # viewer_find_dialog.nml:42
        self.hex_caption.y = 4    # viewer_find_dialog.nml:43
        self.hex_caption.width = 14    # viewer_find_dialog.nml:44
        self.hex_caption.text = _bind(lambda _o: _tr('He~x~'), yielding=True)    # viewer_find_dialog.nml:45
        self.hex_caption.link = _bind(lambda _o: self.hex)    # viewer_find_dialog.nml:46

        self.hex.x = _bind(lambda _o: self.what.x + self.what.entry.x)    # viewer_find_dialog.nml:51
        self.hex.y = 5    # viewer_find_dialog.nml:52
        self.hex.width = _bind(lambda _o: self.what.entry.width)    # viewer_find_dialog.nml:53
        self.hex.height = 1    # viewer_find_dialog.nml:54
        self.hex.link = _bind(lambda _o: self.what.entry)    # viewer_find_dialog.nml:55

        self.options_caption.x = 2    # viewer_find_dialog.nml:59
        self.options_caption.y = 7    # viewer_find_dialog.nml:60
        self.options_caption.width = 12    # viewer_find_dialog.nml:61
        self.options_caption.text = _bind(    # viewer_find_dialog.nml:62
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # viewer_find_dialog.nml:63

        self.options.x = 2    # viewer_find_dialog.nml:67
        self.options.y = 8    # viewer_find_dialog.nml:68
        self.options.width = 22    # viewer_find_dialog.nml:69
        self.options.height = 2    # viewer_find_dialog.nml:70
        self.options.items = _bind(    # viewer_find_dialog.nml:71
            lambda _o: [_tr('~C~ase sensitive'), _tr('~W~hole words')],
            yielding=True,
        )

        self.direction_caption.x = 26    # viewer_find_dialog.nml:75
        self.direction_caption.y = 7    # viewer_find_dialog.nml:76
        self.direction_caption.width = 12    # viewer_find_dialog.nml:77
        self.direction_caption.text = _bind(    # viewer_find_dialog.nml:78
            lambda _o: _tr('Direction'),
            yielding=True,
        )
        self.direction_caption.link = _bind(lambda _o: self.direction)    # viewer_find_dialog.nml:79

        self.direction.x = 26    # viewer_find_dialog.nml:83
        self.direction.y = 8    # viewer_find_dialog.nml:84
        self.direction.width = 18    # viewer_find_dialog.nml:85
        self.direction.height = 2    # viewer_find_dialog.nml:86
        self.direction.items = _bind(    # viewer_find_dialog.nml:87
            lambda _o: [_tr('~F~orward'), _tr('~B~ackward')],
            yielding=True,
        )
