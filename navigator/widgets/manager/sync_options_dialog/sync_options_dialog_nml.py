# navml: generated
"""Generated from ``sync_options_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # sync_options_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # sync_options_dialog.nml:2
from navml.widgets.dialog.field import Field    # sync_options_dialog.nml:3
from navml.widgets.dialog.label import Label    # sync_options_dialog.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # sync_options_dialog.nml:5

__navml_component__ = "SyncOptionsDialog"

__all__ = ["SyncOptionsDialog"]


class SyncOptionsDialog(Dialog, _Component):
    """The *Synchronize* window's *Options*: Total Commander's *Synchronize

    directories* options.  Not DN's: a departure, asked for -- DOS Navigator
    had no window to synchronize from (``navigator.lib.file_ops.dirsync``).

    The file mask on top, as *Select*'s, how near two times are the same
    under it, and the two switches; OK compares both trees again.
    """

    #: The document this class was generated from.
    __navml_source__ = "sync_options_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    mask_caption: Label    # sync_options_dialog.nml:19
    mask: Field    # sync_options_dialog.nml:28
    times_caption: Label    # sync_options_dialog.nml:39
    times: RadioButtons    # sync_options_dialog.nml:48
    options: CheckBoxes    # sync_options_dialog.nml:57

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.mask_caption = Label(parent=self)    # sync_options_dialog.nml:18
        self.mask = Field(parent=self)    # sync_options_dialog.nml:27
        self.times_caption = Label(parent=self)    # sync_options_dialog.nml:38
        self.times = RadioButtons(parent=self)    # sync_options_dialog.nml:47
        self.options = CheckBoxes(parent=self)    # sync_options_dialog.nml:56

        self.modal_width = 52    # sync_options_dialog.nml:14
        self.modal_height = 16    # sync_options_dialog.nml:15
        self.title = _bind(    # sync_options_dialog.nml:16
            lambda _o: _tr('Synchronize options'),
            yielding=True,
        )

        self.mask_caption.x = 2    # sync_options_dialog.nml:20
        self.mask_caption.y = 1    # sync_options_dialog.nml:21
        self.mask_caption.width = 12    # sync_options_dialog.nml:22
        self.mask_caption.height = 1    # sync_options_dialog.nml:23
        self.mask_caption.text = _bind(    # sync_options_dialog.nml:24
            lambda _o: _tr('~F~ile mask'),
            yielding=True,
        )
        self.mask_caption.link = _bind(lambda _o: self.mask.entry)    # sync_options_dialog.nml:25

        self.mask.x = 2    # sync_options_dialog.nml:29
        self.mask.y = 2    # sync_options_dialog.nml:30
        self.mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # sync_options_dialog.nml:31
        self.mask.height = 1    # sync_options_dialog.nml:32
        self.mask.label_text = ''    # sync_options_dialog.nml:33
        self.mask.label_width = 0    # sync_options_dialog.nml:34
        self.mask.history_id = 'sync_mask'    # sync_options_dialog.nml:35
        self.mask.tooltip = _bind(    # sync_options_dialog.nml:36
            lambda _o: _tr('Empty compares everything; ; between patterns, - before one leaves it out, / after one names directories: *.py;-.git/'),
            yielding=True,
        )

        self.times_caption.x = 2    # sync_options_dialog.nml:40
        self.times_caption.y = 4    # sync_options_dialog.nml:41
        self.times_caption.width = 30    # sync_options_dialog.nml:42
        self.times_caption.height = 1    # sync_options_dialog.nml:43
        self.times_caption.text = _bind(    # sync_options_dialog.nml:44
            lambda _o: _tr('Times are the same'),
            yielding=True,
        )
        self.times_caption.link = _bind(lambda _o: self.times)    # sync_options_dialog.nml:45

        self.times.x = 2    # sync_options_dialog.nml:49
        self.times.y = 5    # sync_options_dialog.nml:50
        self.times.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # sync_options_dialog.nml:51
        self.times.height = 3    # sync_options_dialog.nml:52
        self.times.items = _bind(    # sync_options_dialog.nml:53
            lambda _o: [_tr('~E~xactly, to the second'), _tr('Within ~2~ seconds (FAT)'), _tr('Within a ~m~inute (FTP)')],
            yielding=True,
        )
        self.times.tooltips = _bind(    # sync_options_dialog.nml:54
            lambda _o: [_tr('Any difference of a second or more makes two files different'), _tr('FAT and exFAT keep times in steps of two seconds'), _tr("An FTP server's listing may give times to the minute")],
            yielding=True,
        )

        self.options.x = 2    # sync_options_dialog.nml:58
        self.options.y = 9    # sync_options_dialog.nml:59
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # sync_options_dialog.nml:60
        self.options.height = 2    # sync_options_dialog.nml:61
        self.options.items = _bind(    # sync_options_dialog.nml:62
            lambda _o: [_tr('Or an exact ~h~our apart'), _tr('~A~symmetric: right becomes a copy of left')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # sync_options_dialog.nml:63
            lambda _o: [_tr("A daylight-saving change moves a FAT stick's times by an hour"), _tr('What only the right side has is deleted, and a file that differs is copied right, whichever is newer')],
            yielding=True,
        )
