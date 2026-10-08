# navml: generated
"""Generated from ``edit_file_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # edit_file_dialog.nml:1
from navml.widgets.dialog.field import Field    # edit_file_dialog.nml:2

__navml_component__ = "EditFileDialog"

__all__ = ["EditFileDialog"]


class EditFileDialog(Dialog, _Component):
    """Shift+F4, DN's ``cmXEditFile``: the name of a file to edit, which need not

    exist yet.  Shaped as F7's Make directory is: one field with its history.
    """

    #: The document this class was generated from.
    __navml_source__ = "edit_file_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    entry: Field    # edit_file_dialog.nml:13

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.entry = Field(parent=self)    # edit_file_dialog.nml:12

        self.modal_width = 60    # edit_file_dialog.nml:7
        self.modal_height = 8    # edit_file_dialog.nml:8
        self.title = _bind(lambda _o: _tr('Edit new file'), yielding=True)    # edit_file_dialog.nml:9
        self.close_on_outside_click = True    # edit_file_dialog.nml:10

        self.entry.x = 2    # edit_file_dialog.nml:14
        self.entry.y = 2    # edit_file_dialog.nml:15
        self.entry.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # edit_file_dialog.nml:16
        self.entry.height = 1    # edit_file_dialog.nml:17
        self.entry.label_text = _bind(    # edit_file_dialog.nml:18
            lambda _o: _tr('~F~ile name'),
            yielding=True,
        )
        self.entry.label_width = 12    # edit_file_dialog.nml:19
        self.entry.history_id = 'editfile'    # edit_file_dialog.nml:21
