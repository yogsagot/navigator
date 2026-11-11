# navml: generated
"""Generated from ``link_target_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # link_target_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # link_target_dialog.nml:2
from navml.widgets.dialog.field import Field    # link_target_dialog.nml:3
from navml.widgets.dialog.label import Label    # link_target_dialog.nml:4

__navml_component__ = "LinkTargetDialog"

__all__ = ["LinkTargetDialog"]


class LinkTargetDialog(Dialog, _Component):
    """File > Symlink > Edit link target: one link's target in a line.  A

    departure with no resource behind it, as Shift+F5's box is: Quick
    rename's box with Create symlink's *Relative link* under the line.
    """

    #: The document this class was generated from.
    __navml_source__ = "link_target_dialog.nml"

    #: ``Link NAME points to``, naming the link.
    caption: str = _reactive('')    # link_target_dialog.nml:11

    #: Ids, annotated so the hand-written half completes them.
    caption_label: Label    # link_target_dialog.nml:19
    line: Field    # link_target_dialog.nml:29
    options: CheckBoxes    # link_target_dialog.nml:41

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption_label = Label(parent=self)    # link_target_dialog.nml:18
        self.line = Field(parent=self)    # link_target_dialog.nml:28
        self.options = CheckBoxes(parent=self)    # link_target_dialog.nml:40

        self.modal_width = 61    # link_target_dialog.nml:13
        self.modal_height = 10    # link_target_dialog.nml:14
        self.title = _bind(lambda _o: _tr('Edit link target'), yielding=True)    # link_target_dialog.nml:15
        self.close_on_outside_click = True    # link_target_dialog.nml:16

        self.caption_label.y = 1    # link_target_dialog.nml:20
        self.caption_label.height = 1    # link_target_dialog.nml:21
        self.caption_label.text = _bind(lambda _o: self.caption)    # link_target_dialog.nml:25
        self.caption_label.link = _bind(lambda _o: self.line.entry)    # link_target_dialog.nml:26
        self.caption_label.x = 2    # link_target_dialog.nml:23
        self.caption_label.width = _bind(    # link_target_dialog.nml:24
            lambda _o: max(0, _o.parent.width - 4)
        )

        self.line.y = 2    # link_target_dialog.nml:30
        self.line.height = 1    # link_target_dialog.nml:31
        self.line.label_text = ''    # link_target_dialog.nml:35
        self.line.label_width = 0    # link_target_dialog.nml:36
        self.line.history_id = 'link'    # link_target_dialog.nml:37
        self.line.x = 2    # link_target_dialog.nml:33
        self.line.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # link_target_dialog.nml:34

        self.options.y = 4    # link_target_dialog.nml:42
        self.options.height = 1    # link_target_dialog.nml:43
        self.options.items = _bind(    # link_target_dialog.nml:47
            lambda _o: [_tr('~R~elative link')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # link_target_dialog.nml:48
            lambda _o: [_tr('Point the link at a path relative to it, so the two can be moved together')],
            yielding=True,
        )
        self.options.x = 3    # link_target_dialog.nml:45
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # link_target_dialog.nml:46
