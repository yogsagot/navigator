# navml: generated
"""Generated from ``delete_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # delete_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # delete_dialog.nml:2
from navml.widgets.dialog.label import Label    # delete_dialog.nml:3

__navml_component__ = "DeleteDialog"

__all__ = ["DeleteDialog"]


class DeleteDialog(Dialog, _Component):
    """F8: DOS Navigator's ``ValidErase``, as one dialog.

    DN asked through message boxes: ``Do you wish to delete file NAME ?`` for
    one, ``these files?`` and then ``OK to delete N files ?`` for several.
    This is those words in one box -- a departure -- because it carries what
    a message box could not: *Recursive delete*, which answers *All* to every
    ``Directory ... is not empty`` before it is asked.  *Yes* and *No* are the
    base's OK and Cancel, relabelled.
    """

    #: The document this class was generated from.
    __navml_source__ = "delete_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    prompt_head: Label    # delete_dialog.nml:21
    prompt_caption: Label    # delete_dialog.nml:31
    options: CheckBoxes    # delete_dialog.nml:40

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.prompt_head = Label(parent=self)    # delete_dialog.nml:20
        self.prompt_caption = Label(parent=self)    # delete_dialog.nml:30
        self.options = CheckBoxes(parent=self)    # delete_dialog.nml:39

        self.modal_width = 50    # delete_dialog.nml:14
        self.modal_height = 10    # delete_dialog.nml:15
        self.title = 'Delete'    # delete_dialog.nml:16
        self.buttons = 'ok-cancel'    # delete_dialog.nml:17

        self.prompt_head.x = 2    # delete_dialog.nml:22
        self.prompt_head.y = 1    # delete_dialog.nml:23
        self.prompt_head.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # delete_dialog.nml:24
        self.prompt_head.height = 1    # delete_dialog.nml:25
        self.prompt_head.align = 'center'    # delete_dialog.nml:26
        self.prompt_head.text = 'Do you wish to delete'    # delete_dialog.nml:27

        self.prompt_caption.x = 2    # delete_dialog.nml:32
        self.prompt_caption.y = 2    # delete_dialog.nml:33
        self.prompt_caption.width = _bind(    # delete_dialog.nml:34
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.prompt_caption.height = 1    # delete_dialog.nml:35
        self.prompt_caption.align = 'center'    # delete_dialog.nml:36

        self.options.x = _bind(lambda _o: max(0, (_o.parent.width - 24) // 2))    # delete_dialog.nml:41
        self.options.y = 4    # delete_dialog.nml:42
        self.options.width = 24    # delete_dialog.nml:43
        self.options.height = 1    # delete_dialog.nml:44
        self.options.items = ['~R~ecursive delete']    # delete_dialog.nml:45
