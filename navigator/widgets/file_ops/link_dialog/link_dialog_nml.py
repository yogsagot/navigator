# navml: generated
"""Generated from ``link_dialog.nml``.

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
from navigator.widgets.file_ops.commands import ChooseTarget    # link_dialog.nml:1
from navml.widgets.dialog.button import Button    # link_dialog.nml:2
from navml.widgets.dialog.button_row import ButtonRow    # link_dialog.nml:3
from navml.widgets.dialog.check_boxes import CheckBoxes    # link_dialog.nml:4
from navml.widgets.dialog.dialog import Dialog    # link_dialog.nml:5
from navml.widgets.dialog.field import Field    # link_dialog.nml:6
from navml.widgets.dialog.label import Label    # link_dialog.nml:7
from navml.widgets.dialog.radio_buttons import RadioButtons    # link_dialog.nml:8
from navigator.widgets.file_ops.copy_dialog.copy_dialog import choose_target_line    # link_dialog.nml:9

__navml_component__ = "LinkDialog"

__all__ = ["LinkDialog"]


class LinkDialog(Dialog, _Component):
    """Shift+F5: where links to the selected entries are made.

    A departure with no resource behind it, so it is the Copy dialog cut down:
    the prompt and the line in the same rows, the kind of link and one check
    box where the copy modes stood, and the same OK / Cancel / Tree / Help
    along the bottom.
    """

    #: The document this class was generated from.
    __navml_source__ = "link_dialog.nml"

    #: F10 opens the tree, as it does in the Copy dialog.
    keys = {    # link_dialog.nml:24
        'f10': ChooseTarget,    # link_dialog.nml:25
    }

    #: Ids, annotated so the hand-written half completes them.
    prompt_caption: Label    # link_dialog.nml:36
    target: Field    # link_dialog.nml:44
    kind: RadioButtons    # link_dialog.nml:55
    options: CheckBoxes    # link_dialog.nml:66
    pick: Button    # link_dialog.nml:82
    abandon: Button    # link_dialog.nml:87
    tree: Button    # link_dialog.nml:91
    help: Button    # link_dialog.nml:96

    #: The commands this component handles itself.
    async def on_choose_target(self, event: _Any) -> bool:    # link_dialog.nml:29
        """``ChooseTarget``."""
        self.spawn(choose_target_line(self, self._here, self._hidden))
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # link_dialog.nml:82
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # link_dialog.nml:87
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_help_click(self, event: _Event) -> bool:    # link_dialog.nml:96
        """``help`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.prompt_caption = Label(parent=self)    # link_dialog.nml:35
        self.target = Field(parent=self)    # link_dialog.nml:43
        self.kind = RadioButtons(parent=self)    # link_dialog.nml:54
        self.options = CheckBoxes(parent=self)    # link_dialog.nml:65
        _w1 = ButtonRow(parent=self)    # link_dialog.nml:75
        self.pick = Button(parent=_w1)    # link_dialog.nml:81
        self.abandon = Button(parent=_w1)    # link_dialog.nml:86
        self.tree = Button(parent=_w1)    # link_dialog.nml:90
        self.help = Button(parent=_w1)    # link_dialog.nml:95

        self.modal_width = 61    # link_dialog.nml:18
        self.modal_height = 11    # link_dialog.nml:19
        self.title = _bind(lambda _o: _tr('Create link'), yielding=True)    # link_dialog.nml:20
        self.buttons = 'none'    # link_dialog.nml:21
        self.buttons_row = _bind(    # link_dialog.nml:31
            lambda _o: (self.pick, self.abandon, self.tree, self.help)
        )

        self.prompt_caption.y = 1    # link_dialog.nml:37
        self.prompt_caption.link = _bind(lambda _o: self.target.entry)    # link_dialog.nml:41
        self.prompt_caption.x = 2    # link_dialog.nml:39
        self.prompt_caption.width = _bind(    # link_dialog.nml:40
            lambda _o: max(0, _o.parent.width - 4)
        )

        self.target.y = 2    # link_dialog.nml:45
        self.target.label_text = ''    # link_dialog.nml:49
        self.target.label_width = 0    # link_dialog.nml:50
        self.target.history_id = 'link'    # link_dialog.nml:51
        self.target.x = 2    # link_dialog.nml:47
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # link_dialog.nml:48

        self.kind.x = 3    # link_dialog.nml:56
        self.kind.y = 4    # link_dialog.nml:57
        self.kind.width = 24    # link_dialog.nml:58
        self.kind.height = 2    # link_dialog.nml:59
        self.kind.items = _bind(    # link_dialog.nml:60
            lambda _o: [_tr('S~y~mbolic link'), _tr('~H~ard link')],
            yielding=True,
        )
        self.kind.tooltips = _bind(    # link_dialog.nml:61
            lambda _o: [_tr('A small file holding the path of the original'), _tr('A second name for the same file, on the same file system; never for a directory')],
            yielding=True,
        )

        self.options.y = 4    # link_dialog.nml:67
        self.options.height = 1    # link_dialog.nml:68
        self.options.items = _bind(    # link_dialog.nml:72
            lambda _o: [_tr('~R~elative link')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # link_dialog.nml:73
            lambda _o: [_tr('Point the link at a path relative to it, so the two can be moved together')],
            yielding=True,
        )
        self.options.x = 29    # link_dialog.nml:70
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 32))    # link_dialog.nml:71

        _w1.x = 0# link_dialog.nml:77
        _w1.width = _bind(lambda _o: max(0, _o.parent.width))    # link_dialog.nml:78
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # link_dialog.nml:79

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # link_dialog.nml:83
        self.pick.default = True    # link_dialog.nml:84
        self.pick.on_click = self.on_pick_click    # link_dialog.nml:82

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # link_dialog.nml:88
        self.abandon.on_click = self.on_abandon_click    # link_dialog.nml:87

        self.tree.text = _bind(lambda _o: _tr('~T~ree'), yielding=True)    # link_dialog.nml:92

        async def _on_click(event):    # link_dialog.nml:93
            self.spawn(choose_target_line(self, self._here, self._hidden))
            return True
        self.tree.on_click = _on_click

        self.help.text = _bind(lambda _o: _tr('Help'), yielding=True)    # link_dialog.nml:97
        self.help.disabled = True    # link_dialog.nml:98
        self.help.on_click = self.on_help_click    # link_dialog.nml:96
