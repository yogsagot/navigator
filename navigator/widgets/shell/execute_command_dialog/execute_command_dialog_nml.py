# navml: generated
"""Generated from ``execute_command_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # execute_command_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # execute_command_dialog.nml:2
from navml.widgets.dialog.field import Field    # execute_command_dialog.nml:3
from navml.widgets.dialog.label import Label    # execute_command_dialog.nml:4

__navml_component__ = "ExecuteCommandDialog"

__all__ = ["ExecuteCommandDialog"]


class ExecuteCommandDialog(Dialog, _Component):
    """File > Execute OS command: DOS Navigator's ``InputBox`` as ``ExecDOSCmd``

    opened it -- a caption over one line, in the command line's history --
    with a row of check boxes that are not DN's: *In a window* runs the command
    in a window of its own (``TerminalWindow``) rather than on the console,
    *Zoomed* and *Modal* say how that window opens, seeded from System Setup.
    """

    #: The document this class was generated from.
    __navml_source__ = "execute_command_dialog.nml"

    #: The caption over the line.
    caption: str = _reactive('~C~ommand')    # execute_command_dialog.nml:13

    #: Ids, annotated so the hand-written half completes them.
    caption_label: Label    # execute_command_dialog.nml:20
    line: Field    # execute_command_dialog.nml:29
    options: CheckBoxes    # execute_command_dialog.nml:39

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption_label = Label(parent=self)    # execute_command_dialog.nml:19
        self.line = Field(parent=self)    # execute_command_dialog.nml:28
        self.options = CheckBoxes(parent=self)    # execute_command_dialog.nml:38

        self.modal_width = 60    # execute_command_dialog.nml:15
        self.modal_height = 10    # execute_command_dialog.nml:16
        self.title = _bind(lambda _o: _tr('Execute OS Command'), yielding=True)    # execute_command_dialog.nml:17

        self.caption_label.x = 2    # execute_command_dialog.nml:21
        self.caption_label.y = 1    # execute_command_dialog.nml:22
        self.caption_label.width = _bind(    # execute_command_dialog.nml:23
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.caption_label.height = 1    # execute_command_dialog.nml:24
        self.caption_label.text = _bind(lambda _o: self.caption)    # execute_command_dialog.nml:25
        self.caption_label.link = _bind(lambda _o: self.line.entry)    # execute_command_dialog.nml:26

        self.line.x = 2    # execute_command_dialog.nml:30
        self.line.y = 2    # execute_command_dialog.nml:31
        self.line.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # execute_command_dialog.nml:32
        self.line.height = 1    # execute_command_dialog.nml:33
        self.line.label_text = ''    # execute_command_dialog.nml:34
        self.line.label_width = 0    # execute_command_dialog.nml:35
        self.line.history_id = 'command'    # execute_command_dialog.nml:36

        self.options.x = 2    # execute_command_dialog.nml:40
        self.options.y = 4    # execute_command_dialog.nml:41
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # execute_command_dialog.nml:42
        self.options.height = 1    # execute_command_dialog.nml:43
        self.options.items = _bind(    # execute_command_dialog.nml:44
            lambda _o: [_tr('In a ~w~indow'), _tr('~Z~oomed'), _tr('~M~odal')],
            yielding=True,
        )
