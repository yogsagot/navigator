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
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.commands import ChooseTarget    # link_dialog.nml:1
from navml.widgets.dialog.button import Button    # link_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # link_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # link_dialog.nml:4
from navml.widgets.dialog.field import Field    # link_dialog.nml:5
from navml.widgets.dialog.label import Label    # link_dialog.nml:6

__navml_component__ = "LinkDialog"

__all__ = ["LinkDialog"]


class LinkDialog(Dialog, _Component):
    """Shift+F5: where symbolic links to the selected entries are made.

    A departure with no resource behind it, so it is the Copy dialog cut down:
    the prompt and the line in the same rows, one check box where the copy
    modes stood, and the same OK / Cancel / Tree / Help along the bottom.
    """

    #: The document this class was generated from.
    __navml_source__ = "link_dialog.nml"

    #: F10 opens the tree, as it does in the Copy dialog.
    keys = {    # link_dialog.nml:19
        'f10': ChooseTarget,    # link_dialog.nml:20
    }

    #: Ids, annotated so the hand-written half completes them.
    prompt_caption: Label    # link_dialog.nml:24
    target: Field    # link_dialog.nml:32
    options: CheckBoxes    # link_dialog.nml:43
    pick: Button    # link_dialog.nml:51
    abandon: Button    # link_dialog.nml:60
    tree: Button    # link_dialog.nml:68
    help: Button    # link_dialog.nml:76

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # link_dialog.nml:51
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # link_dialog.nml:60
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_tree_click(self, event: _Event) -> bool:    # link_dialog.nml:68
        """``tree`` raised an event whose handler is ``on_click``."""
        return False

    async def on_help_click(self, event: _Event) -> bool:    # link_dialog.nml:76
        """``help`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.prompt_caption = Label(parent=self)    # link_dialog.nml:23
        self.target = Field(parent=self)    # link_dialog.nml:31
        self.options = CheckBoxes(parent=self)    # link_dialog.nml:42
        self.pick = Button(parent=self)    # link_dialog.nml:50
        self.abandon = Button(parent=self)    # link_dialog.nml:59
        self.tree = Button(parent=self)    # link_dialog.nml:67
        self.help = Button(parent=self)    # link_dialog.nml:75

        self.modal_width = 61    # link_dialog.nml:14
        self.modal_height = 10    # link_dialog.nml:15
        self.title = 'Create symlink'    # link_dialog.nml:16

        self.prompt_caption.x = 2    # link_dialog.nml:25
        self.prompt_caption.y = 1    # link_dialog.nml:26
        self.prompt_caption.width = _bind(    # link_dialog.nml:27
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.prompt_caption.height = 1    # link_dialog.nml:28
        self.prompt_caption.link = _bind(lambda _o: self.target.entry)    # link_dialog.nml:29

        self.target.x = 2    # link_dialog.nml:33
        self.target.y = 2    # link_dialog.nml:34
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # link_dialog.nml:35
        self.target.height = 1    # link_dialog.nml:36
        self.target.label_text = ''    # link_dialog.nml:37
        self.target.label_width = 0    # link_dialog.nml:38
        self.target.history_id = 'link'    # link_dialog.nml:39

        self.options.x = 3    # link_dialog.nml:44
        self.options.y = 4    # link_dialog.nml:45
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # link_dialog.nml:46
        self.options.height = 1    # link_dialog.nml:47
        self.options.items = ['~R~elative link']    # link_dialog.nml:48

        self.pick.text = 'O~K~'    # link_dialog.nml:52
        self.pick.default = True    # link_dialog.nml:53
        self.pick.x = 5    # link_dialog.nml:54
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # link_dialog.nml:55
        self.pick.width = 11    # link_dialog.nml:56
        self.pick.height = 2    # link_dialog.nml:57
        self.pick.on_click = self.on_pick_click    # link_dialog.nml:51

        self.abandon.text = 'Cancel'    # link_dialog.nml:61
        self.abandon.x = 18    # link_dialog.nml:62
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # link_dialog.nml:63
        self.abandon.width = 11    # link_dialog.nml:64
        self.abandon.height = 2    # link_dialog.nml:65
        self.abandon.on_click = self.on_abandon_click    # link_dialog.nml:60

        self.tree.text = '~T~ree'    # link_dialog.nml:69
        self.tree.x = 31    # link_dialog.nml:70
        self.tree.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # link_dialog.nml:71
        self.tree.width = 11    # link_dialog.nml:72
        self.tree.height = 2    # link_dialog.nml:73
        self.tree.on_click = self.on_tree_click    # link_dialog.nml:68

        self.help.text = 'Help'    # link_dialog.nml:77
        self.help.disabled = True    # link_dialog.nml:78
        self.help.x = 44    # link_dialog.nml:79
        self.help.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # link_dialog.nml:80
        self.help.width = 11    # link_dialog.nml:81
        self.help.height = 2    # link_dialog.nml:82
        self.help.on_click = self.on_help_click    # link_dialog.nml:76
