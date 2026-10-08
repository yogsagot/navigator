# navml: generated
"""Generated from ``make_list_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # make_list_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # make_list_dialog.nml:2
from navml.widgets.dialog.field import Field    # make_list_dialog.nml:3

__navml_component__ = "MakeListDialog"

__all__ = ["MakeListDialog"]


class MakeListDialog(Dialog, _Component):
    """Alt+L, Panel > Make list file: DOS Navigator's ``dlgMakeList``.

    Its rows as ``DN.DNR`` has them, three columns wider; Help is left out,
    having nothing to show yet.  *Action*'s history is the command line's,
    ``hsExecDOSCmd``, as DN's was.
    """

    #: The document this class was generated from.
    __navml_source__ = "make_list_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    file_name: Field    # make_list_dialog.nml:17
    action: Field    # make_list_dialog.nml:27
    options: CheckBoxes    # make_list_dialog.nml:37

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.file_name = Field(parent=self)    # make_list_dialog.nml:16
        self.action = Field(parent=self)    # make_list_dialog.nml:26
        self.options = CheckBoxes(parent=self)    # make_list_dialog.nml:36

        self.modal_width = 52    # make_list_dialog.nml:11
        self.modal_height = 12    # make_list_dialog.nml:12
        self.title = _bind(lambda _o: _tr('Make List File'), yielding=True)    # make_list_dialog.nml:13

        self.file_name.x = 2    # make_list_dialog.nml:18
        self.file_name.y = 2    # make_list_dialog.nml:19
        self.file_name.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # make_list_dialog.nml:20
        self.file_name.height = 1    # make_list_dialog.nml:21
        self.file_name.label_text = _bind(    # make_list_dialog.nml:22
            lambda _o: _tr('~F~ile name'),
            yielding=True,
        )
        self.file_name.label_width = 11    # make_list_dialog.nml:23
        self.file_name.history_id = 'make_list'    # make_list_dialog.nml:24

        self.action.x = 2    # make_list_dialog.nml:28
        self.action.y = 4    # make_list_dialog.nml:29
        self.action.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # make_list_dialog.nml:30
        self.action.height = 1    # make_list_dialog.nml:31
        self.action.label_text = _bind(    # make_list_dialog.nml:32
            lambda _o: _tr('~A~ction'),
            yielding=True,
        )
        self.action.label_width = 11    # make_list_dialog.nml:33
        self.action.history_id = 'command'    # make_list_dialog.nml:34

        self.options.x = 4    # make_list_dialog.nml:38
        self.options.y = 6    # make_list_dialog.nml:39
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # make_list_dialog.nml:40
        self.options.height = 2    # make_list_dialog.nml:41
        self.options.items = _bind(    # make_list_dialog.nml:42
            lambda _o: [_tr('~S~tore path names to list file'), _tr('A~u~todetermine necessity of path names')],
            yielding=True,
        )
