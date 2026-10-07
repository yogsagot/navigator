# navml: generated
"""Generated from ``uu_decode_dialog.nml``.

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
from navigator.widgets.file_ops.commands import ChooseTarget    # uu_decode_dialog.nml:1
from navml.widgets.dialog.button import Button    # uu_decode_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # uu_decode_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # uu_decode_dialog.nml:4
from navml.widgets.dialog.field import Field    # uu_decode_dialog.nml:5
from navml.widgets.dialog.label import Label    # uu_decode_dialog.nml:6

__navml_component__ = "UUDecodeDialog"

__all__ = ["UUDecodeDialog"]


class UUDecodeDialog(Dialog, _Component):
    """File > UU Decode, Ctrl+F8: DOS Navigator's ``dlgUUDecode``.

    The target directory under its caption, the three options, and OK /
    Cancel / Tree; Help is left out, having nothing to show yet.  A row taller
    than DN's 49 by 11, for this library's buttons.
    """

    #: The document this class was generated from.
    __navml_source__ = "uu_decode_dialog.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # uu_decode_dialog.nml:18
        'f10': ChooseTarget,    # uu_decode_dialog.nml:19
    }

    #: Ids, annotated so the hand-written half completes them.
    target_caption: Label    # uu_decode_dialog.nml:22
    target: Field    # uu_decode_dialog.nml:32
    options: CheckBoxes    # uu_decode_dialog.nml:42
    pick: Button    # uu_decode_dialog.nml:50
    abandon: Button    # uu_decode_dialog.nml:59
    tree: Button    # uu_decode_dialog.nml:67

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # uu_decode_dialog.nml:50
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # uu_decode_dialog.nml:59
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_tree_click(self, event: _Event) -> bool:    # uu_decode_dialog.nml:67
        """``tree`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.target_caption = Label(parent=self)    # uu_decode_dialog.nml:21
        self.target = Field(parent=self)    # uu_decode_dialog.nml:31
        self.options = CheckBoxes(parent=self)    # uu_decode_dialog.nml:41
        self.pick = Button(parent=self)    # uu_decode_dialog.nml:49
        self.abandon = Button(parent=self)    # uu_decode_dialog.nml:58
        self.tree = Button(parent=self)    # uu_decode_dialog.nml:66

        self.modal_width = 49    # uu_decode_dialog.nml:14
        self.modal_height = 12    # uu_decode_dialog.nml:15
        self.title = 'UU Decode'    # uu_decode_dialog.nml:16

        self.target_caption.x = 2    # uu_decode_dialog.nml:23
        self.target_caption.y = 1    # uu_decode_dialog.nml:24
        self.target_caption.width = 20    # uu_decode_dialog.nml:25
        self.target_caption.height = 1    # uu_decode_dialog.nml:26
        self.target_caption.text = 'Target ~d~irectory'    # uu_decode_dialog.nml:27
        self.target_caption.link = _bind(lambda _o: self.target.entry)    # uu_decode_dialog.nml:28

        self.target.x = 2    # uu_decode_dialog.nml:33
        self.target.y = 2    # uu_decode_dialog.nml:34
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # uu_decode_dialog.nml:35
        self.target.height = 1    # uu_decode_dialog.nml:36
        self.target.label_text = ''    # uu_decode_dialog.nml:37
        self.target.label_width = 0    # uu_decode_dialog.nml:38
        self.target.history_id = 'uudecode'    # uu_decode_dialog.nml:39

        self.options.x = 2    # uu_decode_dialog.nml:43
        self.options.y = 4    # uu_decode_dialog.nml:44
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # uu_decode_dialog.nml:45
        self.options.height = 3    # uu_decode_dialog.nml:46
        self.options.items = ['~C~heck existing files', 'Display ~e~rror messages', '~S~ave broken files']    # uu_decode_dialog.nml:47

        self.pick.text = 'O~K~'    # uu_decode_dialog.nml:51
        self.pick.default = True    # uu_decode_dialog.nml:52
        self.pick.x = 5    # uu_decode_dialog.nml:53
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # uu_decode_dialog.nml:54
        self.pick.width = 11    # uu_decode_dialog.nml:55
        self.pick.height = 2    # uu_decode_dialog.nml:56
        self.pick.on_click = self.on_pick_click    # uu_decode_dialog.nml:50

        self.abandon.text = 'Cancel'    # uu_decode_dialog.nml:60
        self.abandon.x = 18    # uu_decode_dialog.nml:61
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # uu_decode_dialog.nml:62
        self.abandon.width = 11    # uu_decode_dialog.nml:63
        self.abandon.height = 2    # uu_decode_dialog.nml:64
        self.abandon.on_click = self.on_abandon_click    # uu_decode_dialog.nml:59

        self.tree.text = '~T~ree'    # uu_decode_dialog.nml:68
        self.tree.x = 31    # uu_decode_dialog.nml:69
        self.tree.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # uu_decode_dialog.nml:70
        self.tree.width = 11    # uu_decode_dialog.nml:71
        self.tree.height = 2    # uu_decode_dialog.nml:72
        self.tree.on_click = self.on_tree_click    # uu_decode_dialog.nml:67
