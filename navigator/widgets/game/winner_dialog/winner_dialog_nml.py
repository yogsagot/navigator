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

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # winner_dialog.nml:1
from navml.widgets.dialog.field import Field    # winner_dialog.nml:2

__navml_component__ = "WinnerDialog"

__all__ = ["WinnerDialog"]


class WinnerDialog(Dialog, _Component):
    """DOS Navigator's ``dlgTetrisWinner``: a name for the Top Ten, its history

    ``hsTetris``.  A row taller than DN's 50 by 7, for this library's
    buttons; Help is left out.
    """

    #: The document this class was generated from.
    __navml_source__ = "winner_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    player: Field    # winner_dialog.nml:14

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.player = Field(parent=self)    # winner_dialog.nml:13

        self.modal_width = 50    # winner_dialog.nml:8
        self.modal_height = 8    # winner_dialog.nml:9
        self.title = _bind(    # winner_dialog.nml:10
            lambda _o: _tr('You have entered Top Ten!'),
            yielding=True,
        )
        self.buttons = 'ok-cancel'    # winner_dialog.nml:11

        self.player.x = 2    # winner_dialog.nml:15
        self.player.y = 2    # winner_dialog.nml:16
        self.player.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # winner_dialog.nml:17
        self.player.height = 1    # winner_dialog.nml:18
        self.player.label_text = _bind(    # winner_dialog.nml:19
            lambda _o: _tr('Enter your name:'),
            yielding=True,
        )
        self.player.label_width = 18    # winner_dialog.nml:20
        self.player.history_id = 'tetris'    # winner_dialog.nml:21
