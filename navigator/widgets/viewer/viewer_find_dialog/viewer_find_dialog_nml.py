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

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # viewer_find_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # viewer_find_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # viewer_find_dialog.nml:3
from navml.widgets.dialog.commands import Help    # viewer_find_dialog.nml:4
from navml.widgets.dialog.dialog import Dialog    # viewer_find_dialog.nml:5
from navml.widgets.dialog.field import Field    # viewer_find_dialog.nml:6
from navml.widgets.dialog.hex_line import HexLine    # viewer_find_dialog.nml:7
from navml.widgets.dialog.label import Label    # viewer_find_dialog.nml:8
from navml.widgets.dialog.radio_buttons import RadioButtons    # viewer_find_dialog.nml:9

__navml_component__ = "ViewerFindDialog"

__all__ = ["ViewerFindDialog"]


class ViewerFindDialog(Dialog, _Component):
    """F7 in a viewer: DOS Navigator's ``dlgViewerFind``.

    Laid out where ``DN.DNR`` puts it -- the line under its caption, *Options*
    and *Direction* side by side under that -- in the same 50 by 14, with the
    *Hex* line ``StartSearch`` put two rows under the first (``THexLine``), and
    its OK, Cancel and Help.
    """

    #: The document this class was generated from.
    __navml_source__ = "viewer_find_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    what_caption: Label    # viewer_find_dialog.nml:27
    what: Field    # viewer_find_dialog.nml:37
    hex_caption: Label    # viewer_find_dialog.nml:48
    hex: HexLine    # viewer_find_dialog.nml:57
    options_caption: Label    # viewer_find_dialog.nml:65
    options: CheckBoxes    # viewer_find_dialog.nml:73
    direction_caption: Label    # viewer_find_dialog.nml:81
    direction: RadioButtons    # viewer_find_dialog.nml:89
    pick: Button    # viewer_find_dialog.nml:105
    abandon: Button    # viewer_find_dialog.nml:110
    helper: Button    # viewer_find_dialog.nml:115

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # viewer_find_dialog.nml:105
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # viewer_find_dialog.nml:110
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # viewer_find_dialog.nml:115
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.what_caption = Label(parent=self)    # viewer_find_dialog.nml:26
        self.what = Field(parent=self)    # viewer_find_dialog.nml:36
        self.hex_caption = Label(parent=self)    # viewer_find_dialog.nml:47
        self.hex = HexLine(parent=self)    # viewer_find_dialog.nml:56
        self.options_caption = Label(parent=self)    # viewer_find_dialog.nml:64
        self.options = CheckBoxes(parent=self)    # viewer_find_dialog.nml:72
        self.direction_caption = Label(parent=self)    # viewer_find_dialog.nml:80
        self.direction = RadioButtons(parent=self)    # viewer_find_dialog.nml:88
        _w1 = ButtonRow(parent=self)    # viewer_find_dialog.nml:98
        self.pick = Button(parent=_w1)    # viewer_find_dialog.nml:104
        self.abandon = Button(parent=_w1)    # viewer_find_dialog.nml:109
        self.helper = Button(parent=_w1)    # viewer_find_dialog.nml:114

        self.modal_width = 50    # viewer_find_dialog.nml:18
        self.modal_height = 14    # viewer_find_dialog.nml:19
        self.title = _bind(lambda _o: _tr('Find'), yielding=True)    # viewer_find_dialog.nml:20
        self.buttons = 'none'    # viewer_find_dialog.nml:21
        self.buttons_row = _bind(    # viewer_find_dialog.nml:23
            lambda _o: (self.pick, self.abandon, self.helper)
        )
        self.help_topic = 'viewer.md#searching'    # viewer_find_dialog.nml:24

        self.what_caption.x = 2    # viewer_find_dialog.nml:28
        self.what_caption.y = 2    # viewer_find_dialog.nml:29
        self.what_caption.width = 14    # viewer_find_dialog.nml:30
        self.what_caption.text = _bind(    # viewer_find_dialog.nml:31
            lambda _o: _tr('~S~earch for'),
            yielding=True,
        )
        self.what_caption.link = _bind(lambda _o: self.what.entry)    # viewer_find_dialog.nml:32

        self.what.y = 3    # viewer_find_dialog.nml:38
        self.what.label_text = ''    # viewer_find_dialog.nml:42
        self.what.label_width = 0    # viewer_find_dialog.nml:43
        self.what.history_id = 'view_find'    # viewer_find_dialog.nml:44
        self.what.x = 2    # viewer_find_dialog.nml:40
        self.what.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # viewer_find_dialog.nml:41

        self.hex_caption.x = 2    # viewer_find_dialog.nml:49
        self.hex_caption.y = 4    # viewer_find_dialog.nml:50
        self.hex_caption.width = 14    # viewer_find_dialog.nml:51
        self.hex_caption.text = _bind(lambda _o: _tr('He~x~'), yielding=True)    # viewer_find_dialog.nml:52
        self.hex_caption.link = _bind(lambda _o: self.hex)    # viewer_find_dialog.nml:53

        self.hex.x = _bind(lambda _o: self.what.x + self.what.entry.x)    # viewer_find_dialog.nml:58
        self.hex.y = 5    # viewer_find_dialog.nml:59
        self.hex.width = _bind(lambda _o: self.what.entry.width)    # viewer_find_dialog.nml:60
        self.hex.height = 1    # viewer_find_dialog.nml:61
        self.hex.link = _bind(lambda _o: self.what.entry)    # viewer_find_dialog.nml:62

        self.options_caption.x = 2    # viewer_find_dialog.nml:66
        self.options_caption.y = 7    # viewer_find_dialog.nml:67
        self.options_caption.width = 12    # viewer_find_dialog.nml:68
        self.options_caption.text = _bind(    # viewer_find_dialog.nml:69
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # viewer_find_dialog.nml:70

        self.options.x = 2    # viewer_find_dialog.nml:74
        self.options.y = 8    # viewer_find_dialog.nml:75
        self.options.width = 27    # viewer_find_dialog.nml:76
        self.options.height = 2    # viewer_find_dialog.nml:77
        self.options.items = _bind(    # viewer_find_dialog.nml:78
            lambda _o: [_tr('~C~ase sensitive'), _tr('~W~hole words')],
            yielding=True,
        )

        self.direction_caption.x = 30    # viewer_find_dialog.nml:82
        self.direction_caption.y = 7    # viewer_find_dialog.nml:83
        self.direction_caption.width = 12    # viewer_find_dialog.nml:84
        self.direction_caption.text = _bind(    # viewer_find_dialog.nml:85
            lambda _o: _tr('Direction'),
            yielding=True,
        )
        self.direction_caption.link = _bind(lambda _o: self.direction)    # viewer_find_dialog.nml:86

        self.direction.x = 30    # viewer_find_dialog.nml:90
        self.direction.y = 8    # viewer_find_dialog.nml:91
        self.direction.width = 18    # viewer_find_dialog.nml:93
        self.direction.height = 2    # viewer_find_dialog.nml:94
        self.direction.items = _bind(    # viewer_find_dialog.nml:95
            lambda _o: [_tr('~F~orward'), _tr('~B~ackward')],
            yielding=True,
        )

        _w1.x = 0# viewer_find_dialog.nml:100
        _w1.width = _bind(lambda _o: max(0, _o.parent.width))    # viewer_find_dialog.nml:101
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # viewer_find_dialog.nml:102

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # viewer_find_dialog.nml:106
        self.pick.default = True    # viewer_find_dialog.nml:107
        self.pick.on_click = self.on_pick_click    # viewer_find_dialog.nml:105

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # viewer_find_dialog.nml:111
        self.abandon.on_click = self.on_abandon_click    # viewer_find_dialog.nml:110

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # viewer_find_dialog.nml:116
        self.helper.command = Help    # viewer_find_dialog.nml:117
        self.helper.on_click = self.on_helper_click    # viewer_find_dialog.nml:115

        self._navml_built(__class__)
