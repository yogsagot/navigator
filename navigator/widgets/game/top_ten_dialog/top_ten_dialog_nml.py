# navml: generated
"""Generated from ``top_ten_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # top_ten_dialog.nml:1
from navml.widgets.dialog.label import Label    # top_ten_dialog.nml:2

__navml_component__ = "TopTenDialog"

__all__ = ["TopTenDialog"]


class TopTenDialog(Dialog, _Component):
    """DOS Navigator's ``dlgTetrisTop10`` and ``dlgPentixTop10``: the heading,

    and ten lines under it in a frame (``ShowScores``), the one just entered
    bright.  OK alone, as DN's.
    """

    #: The document this class was generated from.
    __navml_source__ = "top_ten_dialog.nml"

    game_style: str = _reactive('tetris')    # top_ten_dialog.nml:13

    #: Ids, annotated so the hand-written half completes them.
    heading: Label    # top_ten_dialog.nml:16

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.heading = Label(parent=self)    # top_ten_dialog.nml:15

        self.modal_width = 59    # top_ten_dialog.nml:8
        self.modal_height = 19    # top_ten_dialog.nml:9
        self.title = _bind(    # top_ten_dialog.nml:10
            lambda _o: 'Pentix Top Ten' if self.game_style == 'pentix' else 'Tetris Top Ten'
        )
        self.buttons = 'ok'    # top_ten_dialog.nml:11

        self.heading.x = 2    # top_ten_dialog.nml:17
        self.heading.y = 2    # top_ten_dialog.nml:18
        self.heading.width = 55    # top_ten_dialog.nml:19
        self.heading.height = 1    # top_ten_dialog.nml:20
        self.heading.text = '~Name                           Start  End       Score~'    # top_ten_dialog.nml:21
