# navml: generated
"""Generated from ``delete_bookmark_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # delete_bookmark_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # delete_bookmark_dialog.nml:2
from navml.widgets.dialog.label import Label    # delete_bookmark_dialog.nml:3

__navml_component__ = "DeleteBookmarkDialog"

__all__ = ["DeleteBookmarkDialog"]


class DeleteBookmarkDialog(Dialog, _Component):
    """Del in the bookmarks box, with Confirmations' *Delete bookmark* ticked.

    A departure, asked for: SelectDrive's box had no Del.  Shaped as Alt+X's
    ``ExitDialog``, with the same *Don't ask again*, which unticks the
    confirmation when the answer is *Yes*.
    """

    #: The document this class was generated from.
    __navml_source__ = "delete_bookmark_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    prompt_head: Label    # delete_bookmark_dialog.nml:19
    prompt_tail: Label    # delete_bookmark_dialog.nml:29
    options: CheckBoxes    # delete_bookmark_dialog.nml:38

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.prompt_head = Label(parent=self)    # delete_bookmark_dialog.nml:18
        self.prompt_tail = Label(parent=self)    # delete_bookmark_dialog.nml:28
        self.options = CheckBoxes(parent=self)    # delete_bookmark_dialog.nml:37

        self.modal_width = 50    # delete_bookmark_dialog.nml:11
        self.modal_height = 10    # delete_bookmark_dialog.nml:12
        self.title = _bind(lambda _o: _tr('Delete bookmark'), yielding=True)    # delete_bookmark_dialog.nml:13
        self.buttons = 'yes-no'    # delete_bookmark_dialog.nml:14
        self.close_on_outside_click = True    # delete_bookmark_dialog.nml:16

        self.prompt_head.x = 2    # delete_bookmark_dialog.nml:20
        self.prompt_head.y = 1    # delete_bookmark_dialog.nml:21
        self.prompt_head.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # delete_bookmark_dialog.nml:22
        self.prompt_head.height = 1    # delete_bookmark_dialog.nml:23
        self.prompt_head.align = 'center'    # delete_bookmark_dialog.nml:24
        self.prompt_head.text = _bind(    # delete_bookmark_dialog.nml:25
            lambda _o: _tr('Do you wish to delete the bookmark'),
            yielding=True,
        )

        self.prompt_tail.x = 2    # delete_bookmark_dialog.nml:30
        self.prompt_tail.y = 2    # delete_bookmark_dialog.nml:31
        self.prompt_tail.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # delete_bookmark_dialog.nml:32
        self.prompt_tail.height = 1    # delete_bookmark_dialog.nml:33
        self.prompt_tail.align = 'center'    # delete_bookmark_dialog.nml:34

        self.options.x = _bind(lambda _o: max(0, (_o.parent.width - 22) // 2))    # delete_bookmark_dialog.nml:39
        self.options.y = 4    # delete_bookmark_dialog.nml:40
        self.options.width = 22    # delete_bookmark_dialog.nml:41
        self.options.height = 1    # delete_bookmark_dialog.nml:42
        self.options.items = _bind(    # delete_bookmark_dialog.nml:43
            lambda _o: [_tr("~D~on't ask again")],
            yielding=True,
        )
        self.options.tooltips = _bind(    # delete_bookmark_dialog.nml:44
            lambda _o: [_tr('Delete bookmarks without asking from now on (Options > Confirmations)')],
            yielding=True,
        )
