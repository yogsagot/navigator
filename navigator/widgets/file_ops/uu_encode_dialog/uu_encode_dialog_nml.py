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
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.file_ops.commands import ChooseTarget    # uu_encode_dialog.nml:1
from navml.widgets.dialog.button import Button    # uu_encode_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # uu_encode_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # uu_encode_dialog.nml:4
from navml.widgets.dialog.field import Field    # uu_encode_dialog.nml:5
from navml.widgets.dialog.label import Label    # uu_encode_dialog.nml:6
from navml.widgets.dialog.masked_field import MaskedField    # uu_encode_dialog.nml:7
from navml.widgets.dialog.radio_buttons import RadioButtons    # uu_encode_dialog.nml:8

__navml_component__ = "UUEncodeDialog"

__all__ = ["UUEncodeDialog"]


class UUEncodeDialog(Dialog, _Component):
    """File > UU Encode, Ctrl+F7: DOS Navigator's ``dlgUUEncode``.

    Laid out where the resource puts things: where to on the second row, the
    *Prefixes* and the *Checksum level* side by side under it, *Lines per
    section* and the *Target file format* below, and OK / Cancel / Tree along
    the bottom.  A row taller than DN's 60 by 17, for this library's buttons;
    Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "uu_encode_dialog.nml"

    #: ``StatusDef``'s ``F10 Tree``, as the Copy dialog's.
    keys = {    # uu_encode_dialog.nml:23
        'f10': ChooseTarget,    # uu_encode_dialog.nml:24
    }

    #: Ids, annotated so the hand-written half completes them.
    target: Field    # uu_encode_dialog.nml:28
    prefixes_caption: Label    # uu_encode_dialog.nml:38
    prefixes: CheckBoxes    # uu_encode_dialog.nml:48
    checksum_caption: Label    # uu_encode_dialog.nml:56
    checksum: RadioButtons    # uu_encode_dialog.nml:66
    lines: MaskedField    # uu_encode_dialog.nml:74
    format_caption: Label    # uu_encode_dialog.nml:84
    format: RadioButtons    # uu_encode_dialog.nml:93
    pick: Button    # uu_encode_dialog.nml:101
    abandon: Button    # uu_encode_dialog.nml:110
    tree: Button    # uu_encode_dialog.nml:118

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # uu_encode_dialog.nml:101
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # uu_encode_dialog.nml:110
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_tree_click(self, event: _Event) -> bool:    # uu_encode_dialog.nml:118
        """``tree`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.target = Field(parent=self)    # uu_encode_dialog.nml:27
        self.prefixes_caption = Label(parent=self)    # uu_encode_dialog.nml:37
        self.prefixes = CheckBoxes(parent=self)    # uu_encode_dialog.nml:47
        self.checksum_caption = Label(parent=self)    # uu_encode_dialog.nml:55
        self.checksum = RadioButtons(parent=self)    # uu_encode_dialog.nml:65
        self.lines = MaskedField(parent=self)    # uu_encode_dialog.nml:73
        self.format_caption = Label(parent=self)    # uu_encode_dialog.nml:83
        self.format = RadioButtons(parent=self)    # uu_encode_dialog.nml:92
        self.pick = Button(parent=self)    # uu_encode_dialog.nml:100
        self.abandon = Button(parent=self)    # uu_encode_dialog.nml:109
        self.tree = Button(parent=self)    # uu_encode_dialog.nml:117

        self.modal_width = 60    # uu_encode_dialog.nml:18
        self.modal_height = 18    # uu_encode_dialog.nml:19
        self.title = 'UU Encode'    # uu_encode_dialog.nml:20

        self.target.x = 2    # uu_encode_dialog.nml:29
        self.target.y = 2    # uu_encode_dialog.nml:30
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # uu_encode_dialog.nml:31
        self.target.height = 1    # uu_encode_dialog.nml:32
        self.target.label_text = '~E~ncode to'    # uu_encode_dialog.nml:33
        self.target.label_width = 12    # uu_encode_dialog.nml:34
        self.target.history_id = 'uuencode'    # uu_encode_dialog.nml:35

        self.prefixes_caption.x = 2    # uu_encode_dialog.nml:39
        self.prefixes_caption.y = 4    # uu_encode_dialog.nml:40
        self.prefixes_caption.width = 12    # uu_encode_dialog.nml:41
        self.prefixes_caption.height = 1    # uu_encode_dialog.nml:42
        self.prefixes_caption.text = '~P~refixes'    # uu_encode_dialog.nml:43
        self.prefixes_caption.link = _bind(lambda _o: self.prefixes)    # uu_encode_dialog.nml:44

        self.prefixes.x = 2    # uu_encode_dialog.nml:49
        self.prefixes.y = 5    # uu_encode_dialog.nml:50
        self.prefixes.width = 29    # uu_encode_dialog.nml:51
        self.prefixes.height = 3    # uu_encode_dialog.nml:52
        self.prefixes.items = ['~F~ile creation date&time', 'Char ~m~apping table', 'St~a~tistics']    # uu_encode_dialog.nml:53

        self.checksum_caption.x = 32    # uu_encode_dialog.nml:57
        self.checksum_caption.y = 4    # uu_encode_dialog.nml:58
        self.checksum_caption.width = 18    # uu_encode_dialog.nml:59
        self.checksum_caption.height = 1    # uu_encode_dialog.nml:60
        self.checksum_caption.text = '~C~hecksum level'    # uu_encode_dialog.nml:61
        self.checksum_caption.link = _bind(lambda _o: self.checksum)    # uu_encode_dialog.nml:62

        self.checksum.x = 32    # uu_encode_dialog.nml:67
        self.checksum.y = 5    # uu_encode_dialog.nml:68
        self.checksum.width = _bind(lambda _o: max(0, _o.parent.width - 34))    # uu_encode_dialog.nml:69
        self.checksum.height = 5    # uu_encode_dialog.nml:70
        self.checksum.items = ['~N~one', 'of Entire ~i~nput file', 'of Each ~s~ection', 'of Eac~h~ line', 'Advanced ~6~4-bit']    # uu_encode_dialog.nml:71

        self.lines.x = 2    # uu_encode_dialog.nml:75
        self.lines.y = 9    # uu_encode_dialog.nml:76
        self.lines.width = 26    # uu_encode_dialog.nml:77
        self.lines.height = 1    # uu_encode_dialog.nml:78
        self.lines.label_text = '~L~ines per section'    # uu_encode_dialog.nml:79
        self.lines.label_width = 20    # uu_encode_dialog.nml:80
        self.lines.mask = '9999'    # uu_encode_dialog.nml:81

        self.format_caption.x = 2    # uu_encode_dialog.nml:85
        self.format_caption.y = 11    # uu_encode_dialog.nml:86
        self.format_caption.width = 20    # uu_encode_dialog.nml:87
        self.format_caption.height = 1    # uu_encode_dialog.nml:88
        self.format_caption.text = '~T~arget file format'    # uu_encode_dialog.nml:89
        self.format_caption.link = _bind(lambda _o: self.format)    # uu_encode_dialog.nml:90

        self.format.x = 2    # uu_encode_dialog.nml:94
        self.format.y = 12    # uu_encode_dialog.nml:95
        self.format.width = 29    # uu_encode_dialog.nml:96
        self.format.height = 1    # uu_encode_dialog.nml:97
        self.format.items = ['~D~OS <CR>+<LF>', '~U~NIX']    # uu_encode_dialog.nml:98

        self.pick.text = 'O~K~'    # uu_encode_dialog.nml:102
        self.pick.default = True    # uu_encode_dialog.nml:103
        self.pick.x = 12    # uu_encode_dialog.nml:104
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # uu_encode_dialog.nml:105
        self.pick.width = 11    # uu_encode_dialog.nml:106
        self.pick.height = 2    # uu_encode_dialog.nml:107
        self.pick.on_click = self.on_pick_click    # uu_encode_dialog.nml:101

        self.abandon.text = 'Cancel'    # uu_encode_dialog.nml:111
        self.abandon.x = 25    # uu_encode_dialog.nml:112
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # uu_encode_dialog.nml:113
        self.abandon.width = 11    # uu_encode_dialog.nml:114
        self.abandon.height = 2    # uu_encode_dialog.nml:115
        self.abandon.on_click = self.on_abandon_click    # uu_encode_dialog.nml:110

        self.tree.text = 'T~r~ee'    # uu_encode_dialog.nml:119
        self.tree.x = 38    # uu_encode_dialog.nml:120
        self.tree.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # uu_encode_dialog.nml:121
        self.tree.width = 11    # uu_encode_dialog.nml:122
        self.tree.height = 2    # uu_encode_dialog.nml:123
        self.tree.on_click = self.on_tree_click    # uu_encode_dialog.nml:118
