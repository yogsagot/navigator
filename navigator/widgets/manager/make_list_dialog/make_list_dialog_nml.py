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

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # make_list_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # make_list_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # make_list_dialog.nml:3
from navml.widgets.dialog.commands import Help    # make_list_dialog.nml:4
from navml.widgets.dialog.dialog import Dialog    # make_list_dialog.nml:5
from navml.widgets.dialog.field import Field    # make_list_dialog.nml:6

__navml_component__ = "MakeListDialog"

__all__ = ["MakeListDialog"]


class MakeListDialog(Dialog, _Component):
    """Alt+L, Panel > Make list file: DOS Navigator's ``dlgMakeList``.

    Its rows as ``DN.DNR`` has them, three columns wider, and its OK, Cancel
    and Help.  *Action*'s history is the command line's,
    ``hsExecDOSCmd``, as DN's was.
    """

    #: The document this class was generated from.
    __navml_source__ = "make_list_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    file_name: Field    # make_list_dialog.nml:24
    action: Field    # make_list_dialog.nml:34
    options: CheckBoxes    # make_list_dialog.nml:45
    pick: Button    # make_list_dialog.nml:61
    abandon: Button    # make_list_dialog.nml:66
    helper: Button    # make_list_dialog.nml:71

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # make_list_dialog.nml:61
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # make_list_dialog.nml:66
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # make_list_dialog.nml:71
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.file_name = Field(parent=self)    # make_list_dialog.nml:23
        self.action = Field(parent=self)    # make_list_dialog.nml:33
        self.options = CheckBoxes(parent=self)    # make_list_dialog.nml:44
        _w1 = ButtonRow(parent=self)    # make_list_dialog.nml:54
        self.pick = Button(parent=_w1)    # make_list_dialog.nml:60
        self.abandon = Button(parent=_w1)    # make_list_dialog.nml:65
        self.helper = Button(parent=_w1)    # make_list_dialog.nml:70

        self.modal_width = 52    # make_list_dialog.nml:14
        self.modal_height = 12    # make_list_dialog.nml:15
        self.title = _bind(lambda _o: _tr('Make List File'), yielding=True)    # make_list_dialog.nml:16
        self.help_topic = 'panels.md#make-a-list-file'    # make_list_dialog.nml:17
        self.buttons = 'none'    # make_list_dialog.nml:18
        self.buttons_row = _bind(    # make_list_dialog.nml:20
            lambda _o: (self.pick, self.abandon, self.helper)
        )

        self.file_name.y = 2    # make_list_dialog.nml:25
        self.file_name.label_text = _bind(    # make_list_dialog.nml:29
            lambda _o: _tr('~F~ile name'),
            yielding=True,
        )
        self.file_name.label_width = 11    # make_list_dialog.nml:30
        self.file_name.history_id = 'make_list'    # make_list_dialog.nml:31
        self.file_name.x = 2    # make_list_dialog.nml:27
        self.file_name.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # make_list_dialog.nml:28

        self.action.y = 4    # make_list_dialog.nml:35
        self.action.label_text = _bind(    # make_list_dialog.nml:39
            lambda _o: _tr('~A~ction'),
            yielding=True,
        )
        self.action.label_width = 11    # make_list_dialog.nml:40
        self.action.history_id = 'command'    # make_list_dialog.nml:42
        self.action.x = 2    # make_list_dialog.nml:37
        self.action.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # make_list_dialog.nml:38

        self.options.y = 6    # make_list_dialog.nml:46
        self.options.height = 2    # make_list_dialog.nml:47
        self.options.items = _bind(    # make_list_dialog.nml:51
            lambda _o: [_tr('~S~tore path names to list file'), _tr('A~u~todetermine necessity of path names')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # make_list_dialog.nml:52
            lambda _o: [_tr("Write each file's whole path, not its name alone"), _tr("Write a file's path only where it is not in the list file's own directory")],
            yielding=True,
        )
        self.options.x = 4    # make_list_dialog.nml:49
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # make_list_dialog.nml:50

        _w1.x = 0# make_list_dialog.nml:56
        _w1.width = _bind(lambda _o: max(0, _o.parent.width))    # make_list_dialog.nml:57
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # make_list_dialog.nml:58

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # make_list_dialog.nml:62
        self.pick.default = True    # make_list_dialog.nml:63
        self.pick.on_click = self.on_pick_click    # make_list_dialog.nml:61

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # make_list_dialog.nml:67
        self.abandon.on_click = self.on_abandon_click    # make_list_dialog.nml:66

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # make_list_dialog.nml:72
        self.helper.command = Help    # make_list_dialog.nml:73
        self.helper.on_click = self.on_helper_click    # make_list_dialog.nml:71

        self._navml_built(__class__)
