# navml: generated
"""Generated from ``uu_encode_dialog.nml``.

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
from navigator.widgets.file_ops.commands import ChooseTarget    # uu_encode_dialog.nml:1
from navml.widgets.dialog.button import Button    # uu_encode_dialog.nml:2
from navml.widgets.dialog.button_row import ButtonRow    # uu_encode_dialog.nml:3
from navml.widgets.dialog.check_boxes import CheckBoxes    # uu_encode_dialog.nml:4
from navml.widgets.dialog.dialog import Dialog    # uu_encode_dialog.nml:5
from navml.widgets.dialog.field import Field    # uu_encode_dialog.nml:6
from navml.widgets.dialog.label import Label    # uu_encode_dialog.nml:7
from navml.widgets.dialog.masked_field import MaskedField    # uu_encode_dialog.nml:8
from navml.widgets.dialog.radio_buttons import RadioButtons    # uu_encode_dialog.nml:9

__navml_component__ = "UUEncodeDialog"

__all__ = ["UUEncodeDialog"]


class UUEncodeDialog(Dialog, _Component):
    """File > Encoding > UU Encode, Ctrl+F7: DOS Navigator's ``dlgUUEncode``.

    Laid out where the resource puts things: where to on the second row, the
    *Prefixes* and the *Checksum level* side by side under it, *Lines per
    section* and the *Target file format* below, and OK / Cancel / Tree along
    the bottom.  A row taller than DN's 60 by 17, for this library's buttons;
    Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "uu_encode_dialog.nml"

    #: ``StatusDef``'s ``F10 Tree``, as the Copy dialog's.
    keys = {    # uu_encode_dialog.nml:25
        'f10': ChooseTarget,    # uu_encode_dialog.nml:26
    }

    #: Ids, annotated so the hand-written half completes them.
    target: Field    # uu_encode_dialog.nml:36
    prefixes_caption: Label    # uu_encode_dialog.nml:46
    prefixes: CheckBoxes    # uu_encode_dialog.nml:55
    checksum_caption: Label    # uu_encode_dialog.nml:63
    checksum: RadioButtons    # uu_encode_dialog.nml:72
    lines: MaskedField    # uu_encode_dialog.nml:81
    format_caption: Label    # uu_encode_dialog.nml:90
    format: RadioButtons    # uu_encode_dialog.nml:98
    pick: Button    # uu_encode_dialog.nml:113
    abandon: Button    # uu_encode_dialog.nml:118
    tree: Button    # uu_encode_dialog.nml:125

    #: The commands this component handles itself.
    async def on_choose_target(self, event: _Any) -> bool:    # uu_encode_dialog.nml:30
        """``ChooseTarget``."""
        self.spawn(self.choose_target())
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # uu_encode_dialog.nml:113
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # uu_encode_dialog.nml:118
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.target = Field(parent=self)    # uu_encode_dialog.nml:35
        self.prefixes_caption = Label(parent=self)    # uu_encode_dialog.nml:45
        self.prefixes = CheckBoxes(parent=self)    # uu_encode_dialog.nml:54
        self.checksum_caption = Label(parent=self)    # uu_encode_dialog.nml:62
        self.checksum = RadioButtons(parent=self)    # uu_encode_dialog.nml:71
        self.lines = MaskedField(parent=self)    # uu_encode_dialog.nml:80
        self.format_caption = Label(parent=self)    # uu_encode_dialog.nml:89
        self.format = RadioButtons(parent=self)    # uu_encode_dialog.nml:97
        _w1 = ButtonRow(parent=self)    # uu_encode_dialog.nml:105
        self.pick = Button(parent=_w1)    # uu_encode_dialog.nml:112
        self.abandon = Button(parent=_w1)    # uu_encode_dialog.nml:117
        self.tree = Button(parent=_w1)    # uu_encode_dialog.nml:124

        self.modal_width = 60    # uu_encode_dialog.nml:19
        self.modal_height = 18    # uu_encode_dialog.nml:20
        self.title = _bind(lambda _o: _tr('UU Encode'), yielding=True)    # uu_encode_dialog.nml:21
        self.buttons = 'none'    # uu_encode_dialog.nml:22
        self.buttons_row = _bind(    # uu_encode_dialog.nml:32
            lambda _o: (self.pick, self.abandon, self.tree)
        )

        self.target.y = 2    # uu_encode_dialog.nml:37
        self.target.label_text = _bind(    # uu_encode_dialog.nml:41
            lambda _o: _tr('~E~ncode to'),
            yielding=True,
        )
        self.target.label_width = 12    # uu_encode_dialog.nml:42
        self.target.history_id = 'uuencode'    # uu_encode_dialog.nml:43
        self.target.x = 2    # uu_encode_dialog.nml:39
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # uu_encode_dialog.nml:40

        self.prefixes_caption.x = 2    # uu_encode_dialog.nml:47
        self.prefixes_caption.y = 4    # uu_encode_dialog.nml:48
        self.prefixes_caption.width = 12    # uu_encode_dialog.nml:49
        self.prefixes_caption.text = _bind(    # uu_encode_dialog.nml:50
            lambda _o: _tr('~P~refixes'),
            yielding=True,
        )
        self.prefixes_caption.link = _bind(lambda _o: self.prefixes)    # uu_encode_dialog.nml:51

        self.prefixes.x = 2    # uu_encode_dialog.nml:56
        self.prefixes.y = 5    # uu_encode_dialog.nml:57
        self.prefixes.width = 29    # uu_encode_dialog.nml:58
        self.prefixes.height = 3    # uu_encode_dialog.nml:59
        self.prefixes.items = _bind(    # uu_encode_dialog.nml:60
            lambda _o: [_tr('~F~ile creation date&time'), _tr('Char ~m~apping table'), _tr('St~a~tistics')],
            yielding=True,
        )

        self.checksum_caption.x = 32    # uu_encode_dialog.nml:64
        self.checksum_caption.y = 4    # uu_encode_dialog.nml:65
        self.checksum_caption.width = 18    # uu_encode_dialog.nml:66
        self.checksum_caption.text = _bind(    # uu_encode_dialog.nml:67
            lambda _o: _tr('~C~hecksum level'),
            yielding=True,
        )
        self.checksum_caption.link = _bind(lambda _o: self.checksum)    # uu_encode_dialog.nml:68

        self.checksum.y = 5    # uu_encode_dialog.nml:73
        self.checksum.height = 5    # uu_encode_dialog.nml:74
        self.checksum.items = _bind(    # uu_encode_dialog.nml:78
            lambda _o: [_tr('~N~one'), _tr('of Entire ~i~nput file'), _tr('of Each ~s~ection'), _tr('of Eac~h~ line'), _tr('Advanced ~6~4-bit')],
            yielding=True,
        )
        self.checksum.x = 32    # uu_encode_dialog.nml:76
        self.checksum.width = _bind(lambda _o: max(0, _o.parent.width - 34))    # uu_encode_dialog.nml:77

        self.lines.x = 2    # uu_encode_dialog.nml:82
        self.lines.y = 9    # uu_encode_dialog.nml:83
        self.lines.width = 26    # uu_encode_dialog.nml:84
        self.lines.label_text = _bind(    # uu_encode_dialog.nml:85
            lambda _o: _tr('~L~ines per section'),
            yielding=True,
        )
        self.lines.label_width = 20    # uu_encode_dialog.nml:86
        self.lines.mask = '9999'    # uu_encode_dialog.nml:87

        self.format_caption.x = 2    # uu_encode_dialog.nml:91
        self.format_caption.y = 11    # uu_encode_dialog.nml:92
        self.format_caption.width = 20    # uu_encode_dialog.nml:93
        self.format_caption.text = _bind(    # uu_encode_dialog.nml:94
            lambda _o: _tr('~T~arget file format'),
            yielding=True,
        )
        self.format_caption.link = _bind(lambda _o: self.format)    # uu_encode_dialog.nml:95

        self.format.x = 2    # uu_encode_dialog.nml:99
        self.format.y = 12    # uu_encode_dialog.nml:100
        self.format.width = 29    # uu_encode_dialog.nml:101
        self.format.height = 1    # uu_encode_dialog.nml:102
        self.format.items = _bind(    # uu_encode_dialog.nml:103
            lambda _o: [_tr('~D~OS <CR>+<LF>'), _tr('~U~NIX')],
            yielding=True,
        )

        _w1.justify = 'start'    # uu_encode_dialog.nml:106
        _w1.x = 12# uu_encode_dialog.nml:108
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 12))    # uu_encode_dialog.nml:109
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # uu_encode_dialog.nml:110

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # uu_encode_dialog.nml:114
        self.pick.default = True    # uu_encode_dialog.nml:115
        self.pick.on_click = self.on_pick_click    # uu_encode_dialog.nml:113

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # uu_encode_dialog.nml:119
        self.abandon.on_click = self.on_abandon_click    # uu_encode_dialog.nml:118

        self.tree.text = _bind(lambda _o: _tr('T~r~ee'), yielding=True)    # uu_encode_dialog.nml:126

        async def _on_click(event):    # uu_encode_dialog.nml:127
            self.spawn(self.choose_target())
            return True
        self.tree.on_click = _on_click

        self._navml_built(__class__)
