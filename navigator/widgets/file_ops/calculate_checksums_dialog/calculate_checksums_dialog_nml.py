# navml: generated
"""Generated from ``calculate_checksums_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # calculate_checksums_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # calculate_checksums_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # calculate_checksums_dialog.nml:3
from navml.widgets.dialog.field import Field    # calculate_checksums_dialog.nml:4
from navml.widgets.dialog.label import Label    # calculate_checksums_dialog.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # calculate_checksums_dialog.nml:6

__navml_component__ = "CalculateChecksumsDialog"

__all__ = ["CalculateChecksumsDialog"]


class CalculateChecksumsDialog(Dialog, _Component):
    """File > Encoding > Checksums > Calculate.  Not DN's: a departure, asked for -- DOS

    Navigator had no checksums (``navigator.lib.file_ops.checksum``).

    The digest on the left, where it goes on the right, and the combined
    list's name under them, greyed while each file gets its own list.
    """

    #: The document this class was generated from.
    __navml_source__ = "calculate_checksums_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    algorithm_caption: Label    # calculate_checksums_dialog.nml:22
    algorithm: RadioButtons    # calculate_checksums_dialog.nml:30
    mode_caption: Label    # calculate_checksums_dialog.nml:38
    mode: RadioButtons    # calculate_checksums_dialog.nml:46
    list_name: Field    # calculate_checksums_dialog.nml:56
    pick: Button    # calculate_checksums_dialog.nml:74
    abandon: Button    # calculate_checksums_dialog.nml:79

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # calculate_checksums_dialog.nml:74
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # calculate_checksums_dialog.nml:79
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.algorithm_caption = Label(parent=self)    # calculate_checksums_dialog.nml:21
        self.algorithm = RadioButtons(parent=self)    # calculate_checksums_dialog.nml:29
        self.mode_caption = Label(parent=self)    # calculate_checksums_dialog.nml:37
        self.mode = RadioButtons(parent=self)    # calculate_checksums_dialog.nml:45
        self.list_name = Field(parent=self)    # calculate_checksums_dialog.nml:55
        _w1 = ButtonRow(parent=self)    # calculate_checksums_dialog.nml:66
        self.pick = Button(parent=_w1)    # calculate_checksums_dialog.nml:73
        self.abandon = Button(parent=_w1)    # calculate_checksums_dialog.nml:78

        self.modal_width = 60    # calculate_checksums_dialog.nml:14
        self.modal_height = 14    # calculate_checksums_dialog.nml:15
        self.title = _bind(    # calculate_checksums_dialog.nml:16
            lambda _o: _tr('Calculate Checksums'),
            yielding=True,
        )
        self.buttons = 'none'    # calculate_checksums_dialog.nml:17
        self.buttons_row = _bind(lambda _o: (self.pick, self.abandon))    # calculate_checksums_dialog.nml:19

        self.algorithm_caption.x = 2    # calculate_checksums_dialog.nml:23
        self.algorithm_caption.y = 1    # calculate_checksums_dialog.nml:24
        self.algorithm_caption.width = 12    # calculate_checksums_dialog.nml:25
        self.algorithm_caption.text = _bind(    # calculate_checksums_dialog.nml:26
            lambda _o: _tr('~A~lgorithm'),
            yielding=True,
        )
        self.algorithm_caption.link = _bind(lambda _o: self.algorithm)    # calculate_checksums_dialog.nml:27

        self.algorithm.x = 2    # calculate_checksums_dialog.nml:31
        self.algorithm.y = 2    # calculate_checksums_dialog.nml:32
        self.algorithm.width = 20    # calculate_checksums_dialog.nml:33
        self.algorithm.height = 5    # calculate_checksums_dialog.nml:34
        self.algorithm.items = _bind(    # calculate_checksums_dialog.nml:35
            lambda _o: [_tr('~M~D5'), _tr('SHA-~1~'), _tr('~S~HA-256'), _tr('SHA-~5~12'), _tr('~B~LAKE2b')],
            yielding=True,
        )

        self.mode_caption.x = 24    # calculate_checksums_dialog.nml:39
        self.mode_caption.y = 1    # calculate_checksums_dialog.nml:40
        self.mode_caption.width = 12    # calculate_checksums_dialog.nml:41
        self.mode_caption.text = _bind(    # calculate_checksums_dialog.nml:42
            lambda _o: _tr('~W~rite'),
            yielding=True,
        )
        self.mode_caption.link = _bind(lambda _o: self.mode)    # calculate_checksums_dialog.nml:43

        self.mode.y = 2    # calculate_checksums_dialog.nml:47
        self.mode.height = 2    # calculate_checksums_dialog.nml:48
        self.mode.items = _bind(    # calculate_checksums_dialog.nml:52
            lambda _o: [_tr('~O~ne list for all files'), _tr('~E~ach file its own list')],
            yielding=True,
        )
        self.mode.x = 24    # calculate_checksums_dialog.nml:50
        self.mode.width = _bind(lambda _o: max(0, _o.parent.width - 26))    # calculate_checksums_dialog.nml:51

        self.list_name.y = 8    # calculate_checksums_dialog.nml:57
        self.list_name.label_text = _bind(    # calculate_checksums_dialog.nml:61
            lambda _o: _tr('~L~ist file'),
            yielding=True,
        )
        self.list_name.label_width = 11    # calculate_checksums_dialog.nml:62
        self.list_name.history_id = 'checksum'    # calculate_checksums_dialog.nml:63
        self.list_name.disabled = _bind(lambda _o: self.mode.value != 0)    # calculate_checksums_dialog.nml:64
        self.list_name.x = 2    # calculate_checksums_dialog.nml:59
        self.list_name.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # calculate_checksums_dialog.nml:60

        _w1.justify = 'start'    # calculate_checksums_dialog.nml:67
        _w1.x = 17# calculate_checksums_dialog.nml:69
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 17))    # calculate_checksums_dialog.nml:70
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # calculate_checksums_dialog.nml:71

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # calculate_checksums_dialog.nml:75
        self.pick.default = True    # calculate_checksums_dialog.nml:76
        self.pick.on_click = self.on_pick_click    # calculate_checksums_dialog.nml:74

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # calculate_checksums_dialog.nml:80
        self.abandon.on_click = self.on_abandon_click    # calculate_checksums_dialog.nml:79

        self._navml_built(__class__)
