# navml: generated
"""Generated from ``split_dialog.nml``.

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
from navigator.widgets.file_ops.commands import ChooseTarget    # split_dialog.nml:1
from navml.widgets.dialog.button import Button    # split_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # split_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # split_dialog.nml:4
from navml.widgets.dialog.field import Field    # split_dialog.nml:5
from navml.widgets.dialog.label import Label    # split_dialog.nml:6

__navml_component__ = "SplitDialog"

__all__ = ["SplitDialog"]


class SplitDialog(Dialog, _Component):
    """File > Split/combine on a file that is not a part: DOS Navigator's

    ``dlgSplitFile``.

    *Split NAME to* over the target line, as ``LongCopy``'s ``CopyDialog``
    inserted the name into the label, and OK / Cancel / Tree along the bottom;
    Help is left out, having nothing to show yet.  A row taller than DN's 50
    by 11, for this library's buttons.

    **A departure**: *Part size* is new -- DN split where each floppy filled,
    and a POSIX disk does not fill a part at a time -- and its two boxes,
    *Binary splitting only* (the ``.D01`` header, which the ``.001`` parts do
    not have) and *Verify disk writes* (as Copy's was), are dropped for *Write
    checksum file*, the set's ``NAME.crc`` (``navigator/lib/file_ops/splitfile.py``).
    """

    #: The document this class was generated from.
    __navml_source__ = "split_dialog.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # split_dialog.nml:26
        'f10': ChooseTarget,    # split_dialog.nml:27
    }

    #: Ids, annotated so the hand-written half completes them.
    target_caption: Label    # split_dialog.nml:30
    target: Field    # split_dialog.nml:40
    size: Field    # split_dialog.nml:50
    options: CheckBoxes    # split_dialog.nml:60
    pick: Button    # split_dialog.nml:68
    abandon: Button    # split_dialog.nml:77
    tree: Button    # split_dialog.nml:85

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # split_dialog.nml:68
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # split_dialog.nml:77
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_tree_click(self, event: _Event) -> bool:    # split_dialog.nml:85
        """``tree`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.target_caption = Label(parent=self)    # split_dialog.nml:29
        self.target = Field(parent=self)    # split_dialog.nml:39
        self.size = Field(parent=self)    # split_dialog.nml:49
        self.options = CheckBoxes(parent=self)    # split_dialog.nml:59
        self.pick = Button(parent=self)    # split_dialog.nml:67
        self.abandon = Button(parent=self)    # split_dialog.nml:76
        self.tree = Button(parent=self)    # split_dialog.nml:84

        self.modal_width = 50    # split_dialog.nml:22
        self.modal_height = 12    # split_dialog.nml:23
        self.title = _bind(lambda _o: _tr('Split file'), yielding=True)    # split_dialog.nml:24

        self.target_caption.x = 2    # split_dialog.nml:31
        self.target_caption.y = 1    # split_dialog.nml:32
        self.target_caption.width = _bind(    # split_dialog.nml:33
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.target_caption.height = 1    # split_dialog.nml:34
        self.target_caption.text = _bind(    # split_dialog.nml:35
            lambda _o: _tr('~S~plit to'),
            yielding=True,
        )
        self.target_caption.link = _bind(lambda _o: self.target.entry)    # split_dialog.nml:36

        self.target.x = 2    # split_dialog.nml:41
        self.target.y = 2    # split_dialog.nml:42
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # split_dialog.nml:43
        self.target.height = 1    # split_dialog.nml:44
        self.target.label_text = ''    # split_dialog.nml:45
        self.target.label_width = 0    # split_dialog.nml:46
        self.target.history_id = 'splitfile'    # split_dialog.nml:47

        self.size.x = 2    # split_dialog.nml:51
        self.size.y = 4    # split_dialog.nml:52
        self.size.width = 28    # split_dialog.nml:53
        self.size.height = 1    # split_dialog.nml:54
        self.size.label_text = _bind(    # split_dialog.nml:55
            lambda _o: _tr('Part si~z~e'),
            yielding=True,
        )
        self.size.label_width = 12    # split_dialog.nml:56
        self.size.history_id = 'split_size'    # split_dialog.nml:57

        self.options.x = 2    # split_dialog.nml:61
        self.options.y = 6    # split_dialog.nml:62
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # split_dialog.nml:63
        self.options.height = 1    # split_dialog.nml:64
        self.options.items = _bind(    # split_dialog.nml:65
            lambda _o: [_tr('~W~rite checksum file (.crc)')],
            yielding=True,
        )

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # split_dialog.nml:69
        self.pick.default = True    # split_dialog.nml:70
        self.pick.x = 5    # split_dialog.nml:71
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # split_dialog.nml:72
        self.pick.width = 11    # split_dialog.nml:73
        self.pick.height = 2    # split_dialog.nml:74
        self.pick.on_click = self.on_pick_click    # split_dialog.nml:68

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # split_dialog.nml:78
        self.abandon.x = 18    # split_dialog.nml:79
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # split_dialog.nml:80
        self.abandon.width = 11    # split_dialog.nml:81
        self.abandon.height = 2    # split_dialog.nml:82
        self.abandon.on_click = self.on_abandon_click    # split_dialog.nml:77

        self.tree.text = _bind(lambda _o: _tr('~T~ree'), yielding=True)    # split_dialog.nml:86
        self.tree.x = 31    # split_dialog.nml:87
        self.tree.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # split_dialog.nml:88
        self.tree.width = 11    # split_dialog.nml:89
        self.tree.height = 2    # split_dialog.nml:90
        self.tree.on_click = self.on_tree_click    # split_dialog.nml:85
