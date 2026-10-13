# navml: generated
"""Generated from ``rename_dialog.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # rename_dialog.nml:1
from navml.widgets.dialog.field import Field    # rename_dialog.nml:2
from navml.widgets.dialog.label import Label    # rename_dialog.nml:3

__navml_component__ = "RenameDialog"

__all__ = ["RenameDialog"]


class RenameDialog(Dialog, _Component):
    """File > Quick rename: one name in a box, OK and Cancel.  A departure --

    DN renamed a single file in place (Alt+F6, ``CM_RenameSingle``) or through
    F6's *Rename/Move* dialog; this is the in-place line's job put in a box,
    for the menu, where there is no panel cell to lay a line over.
    """

    #: The document this class was generated from.
    __navml_source__ = "rename_dialog.nml"

    #: The caption over the line, naming the file.
    caption: str = _reactive('')    # rename_dialog.nml:11

    #: Ids, annotated so the hand-written half completes them.
    caption_label: Label    # rename_dialog.nml:19
    line: Field    # rename_dialog.nml:28

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption_label = Label(parent=self)    # rename_dialog.nml:18
        self.line = Field(parent=self)    # rename_dialog.nml:27

        self.modal_width = 60    # rename_dialog.nml:13
        self.modal_height = 9    # rename_dialog.nml:14
        self.title = _bind(lambda _o: _tr('Quick rename'), yielding=True)    # rename_dialog.nml:15
        self.close_on_outside_click = True    # rename_dialog.nml:16

        self.caption_label.x = 2    # rename_dialog.nml:20
        self.caption_label.y = 1    # rename_dialog.nml:21
        self.caption_label.width = _bind(    # rename_dialog.nml:22
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.caption_label.height = 1    # rename_dialog.nml:23
        self.caption_label.text = _bind(lambda _o: self.caption)    # rename_dialog.nml:24
        self.caption_label.link = _bind(lambda _o: self.line.entry)    # rename_dialog.nml:25

        self.line.x = 2    # rename_dialog.nml:29
        self.line.y = 2    # rename_dialog.nml:30
        self.line.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # rename_dialog.nml:31
        self.line.height = 1    # rename_dialog.nml:32
        self.line.label_text = ''    # rename_dialog.nml:33
        self.line.label_width = 0    # rename_dialog.nml:34
