# navml: generated
"""Generated from ``remember_directory_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # remember_directory_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # remember_directory_dialog.nml:2
from navml.widgets.dialog.label import Label    # remember_directory_dialog.nml:3

__navml_component__ = "RememberDirectoryDialog"

__all__ = ["RememberDirectoryDialog"]


class RememberDirectoryDialog(Dialog, _Component):
    """Panel > *Remember for this directory*, on a directory not remembered yet:

    whether the directories below take its settings too.

    Not DN's, which remembered nothing per directory
    (``navigator/lib/config/directory_settings.py``).
    """

    #: The document this class was generated from.
    __navml_source__ = "remember_directory_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    prompt_head: Label    # remember_directory_dialog.nml:17
    prompt_tail: Label    # remember_directory_dialog.nml:27
    options: CheckBoxes    # remember_directory_dialog.nml:36

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.prompt_head = Label(parent=self)    # remember_directory_dialog.nml:16
        self.prompt_tail = Label(parent=self)    # remember_directory_dialog.nml:26
        self.options = CheckBoxes(parent=self)    # remember_directory_dialog.nml:35

        self.modal_width = 56    # remember_directory_dialog.nml:11
        self.modal_height = 10    # remember_directory_dialog.nml:12
        self.title = _bind(    # remember_directory_dialog.nml:13
            lambda _o: _tr('Remember directory settings'),
            yielding=True,
        )
        self.buttons = 'ok-cancel'    # remember_directory_dialog.nml:14

        self.prompt_head.y = 1    # remember_directory_dialog.nml:18
        self.prompt_head.align = 'center'    # remember_directory_dialog.nml:22
        self.prompt_head.text = _bind(    # remember_directory_dialog.nml:23
            lambda _o: _tr('Keep the sort order, view and file mask shown for'),
            yielding=True,
        )
        self.prompt_head.x = 2    # remember_directory_dialog.nml:20
        self.prompt_head.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # remember_directory_dialog.nml:21

        self.prompt_tail.y = 2    # remember_directory_dialog.nml:28
        self.prompt_tail.align = 'center'    # remember_directory_dialog.nml:32
        self.prompt_tail.x = 2    # remember_directory_dialog.nml:30
        self.prompt_tail.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # remember_directory_dialog.nml:31

        self.options.y = 4    # remember_directory_dialog.nml:37
        self.options.width = 32    # remember_directory_dialog.nml:38
        self.options.height = 1    # remember_directory_dialog.nml:39
        self.options.items = _bind(    # remember_directory_dialog.nml:42
            lambda _o: [_tr('Also for its ~s~ubdirectories')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # remember_directory_dialog.nml:43
            lambda _o: [_tr('Every directory below shown the same way, unless it is remembered for itself')],
            yielding=True,
        )
        self.options.x = _bind(    # remember_directory_dialog.nml:41
            lambda _o: max(0, (_o.parent.width - _o.width) // 2)
        )
