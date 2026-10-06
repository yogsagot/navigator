# navml: generated
"""Generated from ``edit_line_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # edit_line_dialog.nml:1
from navml.widgets.dialog.field import Field    # edit_line_dialog.nml:2
from navml.widgets.dialog.label import Label    # edit_line_dialog.nml:3

__navml_component__ = "EditLineDialog"

__all__ = ["EditLineDialog"]


class EditLineDialog(Dialog, _Component):
    """DOS Navigator's ``InputBox``: a caption over one line, OK and Cancel --

    *Edit History*'s, here, as Commands history's *Edit* opened it.
    """

    #: The document this class was generated from.
    __navml_source__ = "edit_line_dialog.nml"

    #: The caption over the line.
    caption: str = _reactive('~S~tring')    # edit_line_dialog.nml:9

    #: Ids, annotated so the hand-written half completes them.
    caption_label: Label    # edit_line_dialog.nml:16
    line: Field    # edit_line_dialog.nml:26

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption_label = Label(parent=self)    # edit_line_dialog.nml:15
        self.line = Field(parent=self)    # edit_line_dialog.nml:25

        self.modal_width = 60    # edit_line_dialog.nml:11
        self.modal_height = 9    # edit_line_dialog.nml:12
        self.title = 'Edit History'    # edit_line_dialog.nml:13

        self.caption_label.x = 2    # edit_line_dialog.nml:17
        self.caption_label.y = 1    # edit_line_dialog.nml:18
        self.caption_label.width = _bind(    # edit_line_dialog.nml:19
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.caption_label.height = 1    # edit_line_dialog.nml:20
        self.caption_label.text = _bind(lambda _o: self.caption)    # edit_line_dialog.nml:21
        self.caption_label.link = _bind(lambda _o: self.line.entry)    # edit_line_dialog.nml:22

        self.line.x = 2    # edit_line_dialog.nml:27
        self.line.y = 2    # edit_line_dialog.nml:28
        self.line.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # edit_line_dialog.nml:29
        self.line.height = 1    # edit_line_dialog.nml:30
        self.line.label_text = ''    # edit_line_dialog.nml:31
        self.line.label_width = 0    # edit_line_dialog.nml:32
        self.line.history_id = 'edit_history'    # edit_line_dialog.nml:33
