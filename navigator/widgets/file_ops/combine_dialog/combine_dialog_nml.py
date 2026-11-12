# navml: generated
"""Generated from ``combine_dialog.nml``.

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
from navigator.widgets.file_ops.commands import ChooseTarget    # combine_dialog.nml:1
from navml.widgets.dialog.button import Button    # combine_dialog.nml:2
from navml.widgets.dialog.button_row import ButtonRow    # combine_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # combine_dialog.nml:4
from navml.widgets.dialog.field import Field    # combine_dialog.nml:5
from navml.widgets.dialog.label import Label    # combine_dialog.nml:6

__navml_component__ = "CombineDialog"

__all__ = ["CombineDialog"]


class CombineDialog(Dialog, _Component):
    """File > Split/combine on a part (``NAME.001`` ...) or the set's ``NAME.crc``:

    DOS Navigator's ``dlgCombineFile``.

    *Combine NAME to* over the target line, and OK / Cancel / Tree; Help is
    left out, having nothing to show yet.  A row taller than DN's 50 by 8, for
    this library's buttons.
    """

    #: The document this class was generated from.
    __navml_source__ = "combine_dialog.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # combine_dialog.nml:20
        'f10': ChooseTarget,    # combine_dialog.nml:21
    }

    #: Ids, annotated so the hand-written half completes them.
    target_caption: Label    # combine_dialog.nml:28
    target: Field    # combine_dialog.nml:38
    pick: Button    # combine_dialog.nml:55
    abandon: Button    # combine_dialog.nml:60
    tree: Button    # combine_dialog.nml:64

    #: The commands this component handles itself.
    async def on_choose_target(self, event: _Any) -> bool:    # combine_dialog.nml:25
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

    async def on_pick_click(self, event: _Event) -> bool:    # combine_dialog.nml:55
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # combine_dialog.nml:60
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.target_caption = Label(parent=self)    # combine_dialog.nml:27
        self.target = Field(parent=self)    # combine_dialog.nml:37
        _w1 = ButtonRow(parent=self)    # combine_dialog.nml:47
        self.pick = Button(parent=_w1)    # combine_dialog.nml:54
        self.abandon = Button(parent=_w1)    # combine_dialog.nml:59
        self.tree = Button(parent=_w1)    # combine_dialog.nml:63

        self.modal_width = 50    # combine_dialog.nml:15
        self.modal_height = 9    # combine_dialog.nml:16
        self.title = _bind(lambda _o: _tr('Combine file'), yielding=True)    # combine_dialog.nml:17
        self.buttons = 'none'    # combine_dialog.nml:18

        self.target_caption.y = 1    # combine_dialog.nml:29
        self.target_caption.text = _bind(    # combine_dialog.nml:33
            lambda _o: _tr('~C~ombine to'),
            yielding=True,
        )
        self.target_caption.link = _bind(lambda _o: self.target.entry)    # combine_dialog.nml:34
        self.target_caption.x = 2    # combine_dialog.nml:31
        self.target_caption.width = _bind(    # combine_dialog.nml:32
            lambda _o: max(0, _o.parent.width - 4)
        )

        self.target.y = 2    # combine_dialog.nml:39
        self.target.label_text = ''    # combine_dialog.nml:43
        self.target.label_width = 0    # combine_dialog.nml:44
        self.target.history_id = 'splitfile'    # combine_dialog.nml:45
        self.target.x = 2    # combine_dialog.nml:41
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # combine_dialog.nml:42

        _w1.justify = 'start'    # combine_dialog.nml:48
        _w1.x = 5# combine_dialog.nml:50
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 5))    # combine_dialog.nml:51
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # combine_dialog.nml:52

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # combine_dialog.nml:56
        self.pick.default = True    # combine_dialog.nml:57
        self.pick.on_click = self.on_pick_click    # combine_dialog.nml:55

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # combine_dialog.nml:61
        self.abandon.on_click = self.on_abandon_click    # combine_dialog.nml:60

        self.tree.text = _bind(lambda _o: _tr('~T~ree'), yielding=True)    # combine_dialog.nml:65

        async def _on_click(event):    # combine_dialog.nml:66
            self.spawn(self.choose_target())
            return True
        self.tree.on_click = _on_click
