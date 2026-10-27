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
from navml.widgets.dialog.dialog import Dialog    # calculate_checksums_dialog.nml:2
from navml.widgets.dialog.field import Field    # calculate_checksums_dialog.nml:3
from navml.widgets.dialog.label import Label    # calculate_checksums_dialog.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # calculate_checksums_dialog.nml:5

__navml_component__ = "CalculateChecksumsDialog"

__all__ = ["CalculateChecksumsDialog"]


class CalculateChecksumsDialog(Dialog, _Component):
    """File > Checksums > Calculate.  Not DN's: a departure, asked for -- DOS

    Navigator had no checksums (``navigator.lib.file_ops.checksum``).

    The digest on the left, where it goes on the right, and the combined
    list's name under them, greyed while each file gets its own list.
    """

    #: The document this class was generated from.
    __navml_source__ = "calculate_checksums_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    algorithm_caption: Label    # calculate_checksums_dialog.nml:18
    algorithm: RadioButtons    # calculate_checksums_dialog.nml:27
    mode_caption: Label    # calculate_checksums_dialog.nml:35
    mode: RadioButtons    # calculate_checksums_dialog.nml:44
    list_name: Field    # calculate_checksums_dialog.nml:53
    pick: Button    # calculate_checksums_dialog.nml:64
    abandon: Button    # calculate_checksums_dialog.nml:73

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # calculate_checksums_dialog.nml:64
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # calculate_checksums_dialog.nml:73
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.algorithm_caption = Label(parent=self)    # calculate_checksums_dialog.nml:17
        self.algorithm = RadioButtons(parent=self)    # calculate_checksums_dialog.nml:26
        self.mode_caption = Label(parent=self)    # calculate_checksums_dialog.nml:34
        self.mode = RadioButtons(parent=self)    # calculate_checksums_dialog.nml:43
        self.list_name = Field(parent=self)    # calculate_checksums_dialog.nml:52
        self.pick = Button(parent=self)    # calculate_checksums_dialog.nml:63
        self.abandon = Button(parent=self)    # calculate_checksums_dialog.nml:72

        self.modal_width = 60    # calculate_checksums_dialog.nml:13
        self.modal_height = 14    # calculate_checksums_dialog.nml:14
        self.title = _bind(    # calculate_checksums_dialog.nml:15
            lambda _o: _tr('Calculate Checksums'),
            yielding=True,
        )

        self.algorithm_caption.x = 2    # calculate_checksums_dialog.nml:19
        self.algorithm_caption.y = 1    # calculate_checksums_dialog.nml:20
        self.algorithm_caption.width = 12    # calculate_checksums_dialog.nml:21
        self.algorithm_caption.height = 1    # calculate_checksums_dialog.nml:22
        self.algorithm_caption.text = _bind(    # calculate_checksums_dialog.nml:23
            lambda _o: _tr('~A~lgorithm'),
            yielding=True,
        )
        self.algorithm_caption.link = _bind(lambda _o: self.algorithm)    # calculate_checksums_dialog.nml:24

        self.algorithm.x = 2    # calculate_checksums_dialog.nml:28
        self.algorithm.y = 2    # calculate_checksums_dialog.nml:29
        self.algorithm.width = 20    # calculate_checksums_dialog.nml:30
        self.algorithm.height = 5    # calculate_checksums_dialog.nml:31
        self.algorithm.items = _bind(    # calculate_checksums_dialog.nml:32
            lambda _o: [_tr('~M~D5'), _tr('SHA-~1~'), _tr('~S~HA-256'), _tr('SHA-~5~12'), _tr('~B~LAKE2b')],
            yielding=True,
        )

        self.mode_caption.x = 24    # calculate_checksums_dialog.nml:36
        self.mode_caption.y = 1    # calculate_checksums_dialog.nml:37
        self.mode_caption.width = 12    # calculate_checksums_dialog.nml:38
        self.mode_caption.height = 1    # calculate_checksums_dialog.nml:39
        self.mode_caption.text = _bind(    # calculate_checksums_dialog.nml:40
            lambda _o: _tr('~W~rite'),
            yielding=True,
        )
        self.mode_caption.link = _bind(lambda _o: self.mode)    # calculate_checksums_dialog.nml:41

        self.mode.x = 24    # calculate_checksums_dialog.nml:45
        self.mode.y = 2    # calculate_checksums_dialog.nml:46
        self.mode.width = _bind(lambda _o: max(0, _o.parent.width - 26))    # calculate_checksums_dialog.nml:47
        self.mode.height = 2    # calculate_checksums_dialog.nml:48
        self.mode.items = _bind(    # calculate_checksums_dialog.nml:49
            lambda _o: [_tr('~O~ne list for all files'), _tr('~E~ach file its own list')],
            yielding=True,
        )

        self.list_name.x = 2    # calculate_checksums_dialog.nml:54
        self.list_name.y = 8    # calculate_checksums_dialog.nml:55
        self.list_name.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # calculate_checksums_dialog.nml:56
        self.list_name.height = 1    # calculate_checksums_dialog.nml:57
        self.list_name.label_text = _bind(    # calculate_checksums_dialog.nml:58
            lambda _o: _tr('~L~ist file'),
            yielding=True,
        )
        self.list_name.label_width = 11    # calculate_checksums_dialog.nml:59
        self.list_name.history_id = 'checksum'    # calculate_checksums_dialog.nml:60
        self.list_name.disabled = _bind(lambda _o: self.mode.value != 0)    # calculate_checksums_dialog.nml:61

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # calculate_checksums_dialog.nml:65
        self.pick.default = True    # calculate_checksums_dialog.nml:66
        self.pick.x = 17    # calculate_checksums_dialog.nml:67
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # calculate_checksums_dialog.nml:68
        self.pick.width = 11    # calculate_checksums_dialog.nml:69
        self.pick.height = 2    # calculate_checksums_dialog.nml:70
        self.pick.on_click = self.on_pick_click    # calculate_checksums_dialog.nml:64

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # calculate_checksums_dialog.nml:74
        self.abandon.x = 30    # calculate_checksums_dialog.nml:75
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # calculate_checksums_dialog.nml:76
        self.abandon.width = 11    # calculate_checksums_dialog.nml:77
        self.abandon.height = 2    # calculate_checksums_dialog.nml:78
        self.abandon.on_click = self.on_abandon_click    # calculate_checksums_dialog.nml:73
