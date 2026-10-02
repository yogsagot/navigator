# navml: generated
"""Generated from ``exit_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # exit_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # exit_dialog.nml:2
from navml.widgets.dialog.label import Label    # exit_dialog.nml:3

__navml_component__ = "ExitDialog"

__all__ = ["ExitDialog"]


class ExitDialog(Dialog, _Component):
    """Alt+X: DOS Navigator's ``dlQueryExit``, ``Do you wish to quit`` /

    ``DOS Navigator?`` with *Yes* and *No* (``mfYesNoConfirm``).

    A message box in DN; a dialog here -- a departure -- because it carries
    *Don't ask again*, which unticks Confirmations' *Exit confirmation* when
    the answer is *Yes*, the way a modern program offers it.
    """

    #: The document this class was generated from.
    __navml_source__ = "exit_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    prompt_head: Label    # exit_dialog.nml:18
    prompt_tail: Label    # exit_dialog.nml:27
    options: CheckBoxes    # exit_dialog.nml:37

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.prompt_head = Label(parent=self)    # exit_dialog.nml:17
        self.prompt_tail = Label(parent=self)    # exit_dialog.nml:26
        self.options = CheckBoxes(parent=self)    # exit_dialog.nml:36

        self.modal_width = 40    # exit_dialog.nml:12
        self.modal_height = 10    # exit_dialog.nml:13
        self.title = 'Exit'    # exit_dialog.nml:14
        self.buttons = 'yes-no'    # exit_dialog.nml:15

        self.prompt_head.x = 2    # exit_dialog.nml:19
        self.prompt_head.y = 1    # exit_dialog.nml:20
        self.prompt_head.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # exit_dialog.nml:21
        self.prompt_head.height = 1    # exit_dialog.nml:22
        self.prompt_head.align = 'center'    # exit_dialog.nml:23
        self.prompt_head.text = 'Do you wish to quit'    # exit_dialog.nml:24

        self.prompt_tail.x = 2    # exit_dialog.nml:28
        self.prompt_tail.y = 2    # exit_dialog.nml:29
        self.prompt_tail.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # exit_dialog.nml:30
        self.prompt_tail.height = 1    # exit_dialog.nml:31
        self.prompt_tail.align = 'center'    # exit_dialog.nml:32
        self.prompt_tail.text = 'Navigator?'    # exit_dialog.nml:33

        self.options.x = _bind(lambda _o: max(0, (_o.parent.width - 22) // 2))    # exit_dialog.nml:38
        self.options.y = 4    # exit_dialog.nml:39
        self.options.width = 22    # exit_dialog.nml:40
        self.options.height = 1    # exit_dialog.nml:41
        self.options.items = ["~D~on't ask again"]    # exit_dialog.nml:42
