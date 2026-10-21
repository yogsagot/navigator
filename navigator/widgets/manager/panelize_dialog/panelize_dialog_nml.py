# navml: generated
"""Generated from ``panelize_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # panelize_dialog.nml:1
from navml.widgets.dialog.field import Field    # panelize_dialog.nml:2
from navml.widgets.dialog.label import Label    # panelize_dialog.nml:3

__navml_component__ = "PanelizeDialog"

__all__ = ["PanelizeDialog"]


class PanelizeDialog(Dialog, _Component):
    """Panel > Panelize command (Alt+O): the command whose output becomes the

    panel's listing.  A departure -- Midnight Commander's *External panelize*,
    which DOS Navigator never had (:mod:`navigator.lib.file_ops.panelize`).
    """

    #: The document this class was generated from.
    __navml_source__ = "panelize_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    caption_label: Label    # panelize_dialog.nml:15
    line: Field    # panelize_dialog.nml:24

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption_label = Label(parent=self)    # panelize_dialog.nml:14
        self.line = Field(parent=self)    # panelize_dialog.nml:23

        self.modal_width = 64    # panelize_dialog.nml:9
        self.modal_height = 9    # panelize_dialog.nml:10
        self.title = _bind(lambda _o: _tr('Panelize command'), yielding=True)    # panelize_dialog.nml:11
        self.close_on_outside_click = True    # panelize_dialog.nml:12

        self.caption_label.x = 2    # panelize_dialog.nml:16
        self.caption_label.y = 1    # panelize_dialog.nml:17
        self.caption_label.width = _bind(    # panelize_dialog.nml:18
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.caption_label.height = 1    # panelize_dialog.nml:19
        self.caption_label.text = _bind(    # panelize_dialog.nml:20
            lambda _o: _tr('~C~ommand (one file name a line)'),
            yielding=True,
        )
        self.caption_label.link = _bind(lambda _o: self.line.entry)    # panelize_dialog.nml:21

        self.line.x = 2    # panelize_dialog.nml:25
        self.line.y = 2    # panelize_dialog.nml:26
        self.line.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # panelize_dialog.nml:27
        self.line.height = 1    # panelize_dialog.nml:28
        self.line.label_text = ''    # panelize_dialog.nml:29
        self.line.label_width = 0    # panelize_dialog.nml:30
        self.line.history_id = 'panelize'    # panelize_dialog.nml:31
