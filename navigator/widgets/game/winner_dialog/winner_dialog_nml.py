# navml: generated
"""Generated from ``winner_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # winner_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # winner_dialog.nml:2
from navml.widgets.dialog.commands import Help    # winner_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # winner_dialog.nml:4
from navml.widgets.dialog.field import Field    # winner_dialog.nml:5

__navml_component__ = "WinnerDialog"

__all__ = ["WinnerDialog"]


class WinnerDialog(Dialog, _Component):
    """DOS Navigator's ``dlgTetrisWinner``: a name for the Top Ten, its history

    ``hsTetris``.  A row taller than DN's 50 by 7, for this library's
    buttons.
    """

    #: The document this class was generated from.
    __navml_source__ = "winner_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    player: Field    # winner_dialog.nml:20
    pick: Button    # winner_dialog.nml:40
    abandon: Button    # winner_dialog.nml:45
    helper: Button    # winner_dialog.nml:50

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # winner_dialog.nml:40
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # winner_dialog.nml:45
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # winner_dialog.nml:50
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.player = Field(parent=self)    # winner_dialog.nml:19
        _w1 = ButtonRow(parent=self)    # winner_dialog.nml:30
        self.pick = Button(parent=_w1)    # winner_dialog.nml:39
        self.abandon = Button(parent=_w1)    # winner_dialog.nml:44
        self.helper = Button(parent=_w1)    # winner_dialog.nml:49

        self.modal_width = 50    # winner_dialog.nml:11
        self.modal_height = 8    # winner_dialog.nml:12
        self.title = _bind(    # winner_dialog.nml:13
            lambda _o: _tr('You have entered Top Ten!'),
            yielding=True,
        )
        self.help_topic = 'game.md#the-top-ten'    # winner_dialog.nml:14
        self.buttons = 'none'    # winner_dialog.nml:15
        self.buttons_row = _bind(    # winner_dialog.nml:17
            lambda _o: (self.pick, self.abandon, self.helper)
        )

        self.player.y = 2    # winner_dialog.nml:21
        self.player.label_text = _bind(    # winner_dialog.nml:25
            lambda _o: _tr('Enter your name:'),
            yielding=True,
        )
        self.player.label_width = 18    # winner_dialog.nml:26
        self.player.history_id = 'tetris'    # winner_dialog.nml:27
        self.player.x = 2    # winner_dialog.nml:23
        self.player.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # winner_dialog.nml:24

        _w1.justify = 'start'    # winner_dialog.nml:31
        _w1.button_width = 10    # winner_dialog.nml:32
        _w1.spacing = 0    # winner_dialog.nml:33
        _w1.x = 17# winner_dialog.nml:35
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 17))    # winner_dialog.nml:36
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # winner_dialog.nml:37

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # winner_dialog.nml:41
        self.pick.default = True    # winner_dialog.nml:42
        self.pick.on_click = self.on_pick_click    # winner_dialog.nml:40

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # winner_dialog.nml:46
        self.abandon.on_click = self.on_abandon_click    # winner_dialog.nml:45

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # winner_dialog.nml:51
        self.helper.command = Help    # winner_dialog.nml:52
        self.helper.on_click = self.on_helper_click    # winner_dialog.nml:50

        self._navml_built(__class__)
