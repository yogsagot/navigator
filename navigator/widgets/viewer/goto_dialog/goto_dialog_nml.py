# navml: generated
"""Generated from ``goto_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # goto_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # goto_dialog.nml:2
from navml.widgets.dialog.commands import Help    # goto_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # goto_dialog.nml:4
from navml.widgets.dialog.field import Field    # goto_dialog.nml:5

__navml_component__ = "GotoDialog"

__all__ = ["GotoDialog"]


class GotoDialog(Dialog, _Component):
    """F5 in a hex viewer: DOS Navigator's ``dlgGotoAddress``, *Goto Address*.

    One line, read as hex, as ``Val('$' + S)`` read it.  A row taller than DN's
    34 by 7, for the blank row ``MkdirDialog`` keeps between line and buttons.
    """

    #: The document this class was generated from.
    __navml_source__ = "goto_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    address: Field    # goto_dialog.nml:21
    pick: Button    # goto_dialog.nml:41
    abandon: Button    # goto_dialog.nml:46
    helper: Button    # goto_dialog.nml:51

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # goto_dialog.nml:41
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # goto_dialog.nml:46
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # goto_dialog.nml:51
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.address = Field(parent=self)    # goto_dialog.nml:20
        _w1 = ButtonRow(parent=self)    # goto_dialog.nml:31
        self.pick = Button(parent=_w1)    # goto_dialog.nml:40
        self.abandon = Button(parent=_w1)    # goto_dialog.nml:45
        self.helper = Button(parent=_w1)    # goto_dialog.nml:50

        self.modal_width = 34    # goto_dialog.nml:12
        self.modal_height = 8    # goto_dialog.nml:13
        self.title = _bind(lambda _o: _tr('Goto Address'), yielding=True)    # goto_dialog.nml:14
        self.buttons = 'none'    # goto_dialog.nml:15
        self.buttons_row = _bind(    # goto_dialog.nml:17
            lambda _o: (self.pick, self.abandon, self.helper)
        )
        self.help_topic = 'viewer.md#go-to-an-address'    # goto_dialog.nml:18

        self.address.y = 2    # goto_dialog.nml:22
        self.address.label_text = _bind(    # goto_dialog.nml:26
            lambda _o: _tr('~A~ddress'),
            yielding=True,
        )
        self.address.label_width = 9    # goto_dialog.nml:27
        self.address.history_id = 'goto_address'    # goto_dialog.nml:28
        self.address.x = 3    # goto_dialog.nml:24
        self.address.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # goto_dialog.nml:25

        _w1.justify = 'start'    # goto_dialog.nml:32
        _w1.button_width = 10    # goto_dialog.nml:33
        _w1.spacing = 0    # goto_dialog.nml:34
        _w1.x = 2# goto_dialog.nml:36
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # goto_dialog.nml:37
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # goto_dialog.nml:38

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # goto_dialog.nml:42
        self.pick.default = True    # goto_dialog.nml:43
        self.pick.on_click = self.on_pick_click    # goto_dialog.nml:41

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # goto_dialog.nml:47
        self.abandon.on_click = self.on_abandon_click    # goto_dialog.nml:46

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # goto_dialog.nml:52
        self.helper.command = Help    # goto_dialog.nml:53
        self.helper.on_click = self.on_helper_click    # goto_dialog.nml:51

        self._navml_built(__class__)
