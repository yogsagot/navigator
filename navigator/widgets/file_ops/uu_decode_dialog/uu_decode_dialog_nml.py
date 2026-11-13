# navml: generated
"""Generated from ``uu_decode_dialog.nml``.

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
from navigator.widgets.file_ops.commands import ChooseTarget    # uu_decode_dialog.nml:1
from navml.widgets.dialog.button import Button    # uu_decode_dialog.nml:2
from navml.widgets.dialog.button_row import ButtonRow    # uu_decode_dialog.nml:3
from navml.widgets.dialog.commands import Help    # uu_decode_dialog.nml:4
from navml.widgets.dialog.check_boxes import CheckBoxes    # uu_decode_dialog.nml:5
from navml.widgets.dialog.dialog import Dialog    # uu_decode_dialog.nml:6
from navml.widgets.dialog.field import Field    # uu_decode_dialog.nml:7
from navml.widgets.dialog.label import Label    # uu_decode_dialog.nml:8

__navml_component__ = "UUDecodeDialog"

__all__ = ["UUDecodeDialog"]


class UUDecodeDialog(Dialog, _Component):
    """File > Encoding > UU Decode, Ctrl+F8: DOS Navigator's ``dlgUUDecode``.

    The target directory under its caption, the three options, and OK /
    Cancel / Tree / Help.  A row taller than DN's 49 by 11, for this library's
    buttons.
    """

    #: The document this class was generated from.
    __navml_source__ = "uu_decode_dialog.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # uu_decode_dialog.nml:22
        'f10': ChooseTarget,    # uu_decode_dialog.nml:23
    }

    #: Ids, annotated so the hand-written half completes them.
    target_caption: Label    # uu_decode_dialog.nml:32
    target: Field    # uu_decode_dialog.nml:41
    options: CheckBoxes    # uu_decode_dialog.nml:51
    pick: Button    # uu_decode_dialog.nml:72
    abandon: Button    # uu_decode_dialog.nml:77
    tree: Button    # uu_decode_dialog.nml:81
    help: Button    # uu_decode_dialog.nml:87

    #: The commands this component handles itself.
    async def on_choose_target(self, event: _Any) -> bool:    # uu_decode_dialog.nml:27
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

    async def on_pick_click(self, event: _Event) -> bool:    # uu_decode_dialog.nml:72
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # uu_decode_dialog.nml:77
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_help_click(self, event: _Event) -> bool:    # uu_decode_dialog.nml:87
        """``help`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.target_caption = Label(parent=self)    # uu_decode_dialog.nml:31
        self.target = Field(parent=self)    # uu_decode_dialog.nml:40
        self.options = CheckBoxes(parent=self)    # uu_decode_dialog.nml:50
        _w1 = ButtonRow(parent=self)    # uu_decode_dialog.nml:62
        self.pick = Button(parent=_w1)    # uu_decode_dialog.nml:71
        self.abandon = Button(parent=_w1)    # uu_decode_dialog.nml:76
        self.tree = Button(parent=_w1)    # uu_decode_dialog.nml:80
        self.help = Button(parent=_w1)    # uu_decode_dialog.nml:86

        self.modal_width = 49    # uu_decode_dialog.nml:16
        self.modal_height = 12    # uu_decode_dialog.nml:17
        self.title = _bind(lambda _o: _tr('UU Decode'), yielding=True)    # uu_decode_dialog.nml:18
        self.help_topic = 'file-operations.md#decoding'    # uu_decode_dialog.nml:19
        self.buttons = 'none'    # uu_decode_dialog.nml:20
        self.buttons_row = _bind(    # uu_decode_dialog.nml:29
            lambda _o: (self.pick, self.abandon, self.tree, self.help)
        )

        self.target_caption.x = 2    # uu_decode_dialog.nml:33
        self.target_caption.y = 1    # uu_decode_dialog.nml:34
        self.target_caption.width = 20    # uu_decode_dialog.nml:35
        self.target_caption.text = _bind(    # uu_decode_dialog.nml:36
            lambda _o: _tr('Target ~d~irectory'),
            yielding=True,
        )
        self.target_caption.link = _bind(lambda _o: self.target.entry)    # uu_decode_dialog.nml:37

        self.target.y = 2    # uu_decode_dialog.nml:42
        self.target.label_text = ''    # uu_decode_dialog.nml:46
        self.target.label_width = 0    # uu_decode_dialog.nml:47
        self.target.history_id = 'uudecode'    # uu_decode_dialog.nml:48
        self.target.x = 2    # uu_decode_dialog.nml:44
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # uu_decode_dialog.nml:45

        self.options.y = 4    # uu_decode_dialog.nml:52
        self.options.height = 3    # uu_decode_dialog.nml:53
        self.options.items = _bind(    # uu_decode_dialog.nml:57
            lambda _o: [_tr('~C~heck existing files'), _tr('Display ~e~rror messages'), _tr('~S~ave broken files')],
            yielding=True,
        )
        self.options.x = 2    # uu_decode_dialog.nml:55
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # uu_decode_dialog.nml:56

        _w1.justify = 'start'    # uu_decode_dialog.nml:63
        _w1.button_width = 10    # uu_decode_dialog.nml:64
        _w1.spacing = 0    # uu_decode_dialog.nml:65
        _w1.x = 7# uu_decode_dialog.nml:67
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 7))    # uu_decode_dialog.nml:68
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # uu_decode_dialog.nml:69

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # uu_decode_dialog.nml:73
        self.pick.default = True    # uu_decode_dialog.nml:74
        self.pick.on_click = self.on_pick_click    # uu_decode_dialog.nml:72

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # uu_decode_dialog.nml:78
        self.abandon.on_click = self.on_abandon_click    # uu_decode_dialog.nml:77

        self.tree.text = _bind(lambda _o: _tr('~T~ree'), yielding=True)    # uu_decode_dialog.nml:82

        async def _on_click(event):    # uu_decode_dialog.nml:83
            self.spawn(self.choose_target())
            return True
        self.tree.on_click = _on_click

        self.help.text = _bind(lambda _o: _tr('Help'), yielding=True)    # uu_decode_dialog.nml:88
        self.help.command = Help    # uu_decode_dialog.nml:89
        self.help.on_click = self.on_help_click    # uu_decode_dialog.nml:87

        self._navml_built(__class__)
