# navml: generated
"""Generated from ``copy_dialog.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navigator.widgets.file_ops.commands import ChooseTarget    # copy_dialog.nml:1
from navml.widgets.dialog.button import Button    # copy_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # copy_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # copy_dialog.nml:4
from navml.widgets.dialog.field import Field    # copy_dialog.nml:5
from navml.widgets.dialog.label import Label    # copy_dialog.nml:6
from navml.widgets.dialog.radio_buttons import RadioButtons    # copy_dialog.nml:7

__navml_component__ = "CopyDialog"

__all__ = ["CopyDialog"]


class CopyDialog(Dialog, _Component):
    """F5 and F6: DOS Navigator's ``dlgCopyDialog`` and ``dlgRenameDialog``.

    One document for the two, which ``DN.DNR`` spelled out twice and which
    differ only in their title -- the prompt above the line is built when the
    dialog opens, as ``CopyDialog`` built it.  Laid out where the resource puts
    things: the line on the second row, the five copy modes under it, the four
    options in two columns under those, and OK / Cancel / Tree / Help along
    the bottom.  Two columns wider and a row taller than DN's 59 by 16, because
    this library's buttons are eleven wide and sit ``height - 4`` from the top.
    """

    #: The document this class was generated from.
    __navml_source__ = "copy_dialog.nml"

    #: ``StatusDef hcCopyDialog``'s ``F10 Tree``.
    keys = {    # copy_dialog.nml:27
        'f10': ChooseTarget,    # copy_dialog.nml:28
    }

    #: Which of the two: *Copy* (F5) or *Rename/move* (F6).
    move: bool = _reactive(False)    # copy_dialog.nml:20

    #: Ids, annotated so the hand-written half completes them.
    prompt_caption: Label    # copy_dialog.nml:33
    target: Field    # copy_dialog.nml:42
    mode: RadioButtons    # copy_dialog.nml:53
    options: CheckBoxes    # copy_dialog.nml:64
    pick: Button    # copy_dialog.nml:74
    abandon: Button    # copy_dialog.nml:83
    tree: Button    # copy_dialog.nml:91
    help: Button    # copy_dialog.nml:101

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # copy_dialog.nml:74
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # copy_dialog.nml:83
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_tree_click(self, event: _Event) -> bool:    # copy_dialog.nml:91
        """``tree`` raised an event whose handler is ``on_click``."""
        return False

    async def on_help_click(self, event: _Event) -> bool:    # copy_dialog.nml:101
        """``help`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.prompt_caption = Label(parent=self)    # copy_dialog.nml:32
        self.target = Field(parent=self)    # copy_dialog.nml:41
        self.mode = RadioButtons(parent=self)    # copy_dialog.nml:52
        self.options = CheckBoxes(parent=self)    # copy_dialog.nml:63
        self.pick = Button(parent=self)    # copy_dialog.nml:73
        self.abandon = Button(parent=self)    # copy_dialog.nml:82
        self.tree = Button(parent=self)    # copy_dialog.nml:90
        self.help = Button(parent=self)    # copy_dialog.nml:100

        self.modal_width = 61    # copy_dialog.nml:22
        self.modal_height = 17    # copy_dialog.nml:23
        self.title = _bind(lambda _o: 'Rename/move' if self.move else 'Copy')    # copy_dialog.nml:24

        self.prompt_caption.x = 2    # copy_dialog.nml:34
        self.prompt_caption.y = 1    # copy_dialog.nml:35
        self.prompt_caption.width = _bind(    # copy_dialog.nml:36
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.prompt_caption.height = 1    # copy_dialog.nml:37
        self.prompt_caption.link = _bind(lambda _o: self.target.entry)    # copy_dialog.nml:38

        self.target.x = 2    # copy_dialog.nml:43
        self.target.y = 2    # copy_dialog.nml:44
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # copy_dialog.nml:45
        self.target.height = 1    # copy_dialog.nml:46
        self.target.label_text = ''    # copy_dialog.nml:47
        self.target.label_width = 0    # copy_dialog.nml:48
        self.target.history_id = 'copy'    # copy_dialog.nml:49

        self.mode.x = 3    # copy_dialog.nml:54
        self.mode.y = 4    # copy_dialog.nml:55
        self.mode.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # copy_dialog.nml:56
        self.mode.height = 5    # copy_dialog.nml:57
        self.mode.items = ['~O~verwrite all existing files', 'A~p~pend to all existing files', '~A~sk for overwrite', '~S~kip all existing files', 'Refresh o~l~d files']    # copy_dialog.nml:58

        self.options.x = 3    # copy_dialog.nml:65
        self.options.y = 10    # copy_dialog.nml:66
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # copy_dialog.nml:67
        self.options.height = 2    # copy_dialog.nml:68
        self.options.items = ['Check ~f~ree disk space', 'Pr~e~serve attributes', 'Follow symli~n~ks', 'Remove so~u~rce files']    # copy_dialog.nml:69

        self.pick.text = 'O~K~'    # copy_dialog.nml:75
        self.pick.default = True    # copy_dialog.nml:76
        self.pick.x = 5    # copy_dialog.nml:77
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # copy_dialog.nml:78
        self.pick.width = 11    # copy_dialog.nml:79
        self.pick.height = 2    # copy_dialog.nml:80
        self.pick.on_click = self.on_pick_click    # copy_dialog.nml:74

        self.abandon.text = 'Cancel'    # copy_dialog.nml:84
        self.abandon.x = 18    # copy_dialog.nml:85
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # copy_dialog.nml:86
        self.abandon.width = 11    # copy_dialog.nml:87
        self.abandon.height = 2    # copy_dialog.nml:88
        self.abandon.on_click = self.on_abandon_click    # copy_dialog.nml:83

        self.tree.text = '~T~ree'    # copy_dialog.nml:92
        self.tree.x = 31    # copy_dialog.nml:93
        self.tree.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # copy_dialog.nml:94
        self.tree.width = 11    # copy_dialog.nml:95
        self.tree.height = 2    # copy_dialog.nml:96
        self.tree.on_click = self.on_tree_click    # copy_dialog.nml:91

        self.help.text = 'Help'    # copy_dialog.nml:102
        self.help.disabled = True    # copy_dialog.nml:103
        self.help.x = 44    # copy_dialog.nml:104
        self.help.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # copy_dialog.nml:105
        self.help.width = 11    # copy_dialog.nml:106
        self.help.height = 2    # copy_dialog.nml:107
        self.help.on_click = self.on_help_click    # copy_dialog.nml:101
