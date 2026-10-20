# navml: generated
"""Generated from ``extract_dialog.nml``.

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
from navigator.widgets.file_ops.commands import ChooseTarget    # extract_dialog.nml:1
from navml.widgets.dialog.button import Button    # extract_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # extract_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # extract_dialog.nml:4
from navml.widgets.dialog.field import Field    # extract_dialog.nml:5
from navml.widgets.dialog.label import Label    # extract_dialog.nml:6

__navml_component__ = "ExtractDialog"

__all__ = ["ExtractDialog"]


class ExtractDialog(Dialog, _Component):
    """Panel > Extract to, and Shift+F2 on an archive: DOS Navigator's

    ``dlgExtract``.

    Where to, the two options, and OK / Cancel / Tree.  DN's *Password* line
    is left out: Python's zip reader knows only the old ZipCrypto, and 7-Zip
    is asked for none.  Help is left out, having nothing to show yet.  A row
    taller than DN's 49 by 12, for this library's buttons.
    """

    #: The document this class was generated from.
    __navml_source__ = "extract_dialog.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # extract_dialog.nml:20
        'f10': ChooseTarget,    # extract_dialog.nml:21
    }

    #: Ids, annotated so the hand-written half completes them.
    target_caption: Label    # extract_dialog.nml:24
    target: Field    # extract_dialog.nml:34
    options: CheckBoxes    # extract_dialog.nml:44
    pick: Button    # extract_dialog.nml:52
    abandon: Button    # extract_dialog.nml:61
    tree: Button    # extract_dialog.nml:69

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # extract_dialog.nml:52
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # extract_dialog.nml:61
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_tree_click(self, event: _Event) -> bool:    # extract_dialog.nml:69
        """``tree`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.target_caption = Label(parent=self)    # extract_dialog.nml:23
        self.target = Field(parent=self)    # extract_dialog.nml:33
        self.options = CheckBoxes(parent=self)    # extract_dialog.nml:43
        self.pick = Button(parent=self)    # extract_dialog.nml:51
        self.abandon = Button(parent=self)    # extract_dialog.nml:60
        self.tree = Button(parent=self)    # extract_dialog.nml:68

        self.modal_width = 49    # extract_dialog.nml:16
        self.modal_height = 11    # extract_dialog.nml:17
        self.title = _bind(lambda _o: _tr('Extract files'), yielding=True)    # extract_dialog.nml:18

        self.target_caption.x = 2    # extract_dialog.nml:25
        self.target_caption.y = 1    # extract_dialog.nml:26
        self.target_caption.width = 20    # extract_dialog.nml:27
        self.target_caption.height = 1    # extract_dialog.nml:28
        self.target_caption.text = _bind(    # extract_dialog.nml:29
            lambda _o: _tr('E~x~tract to'),
            yielding=True,
        )
        self.target_caption.link = _bind(lambda _o: self.target.entry)    # extract_dialog.nml:30

        self.target.x = 2    # extract_dialog.nml:35
        self.target.y = 2    # extract_dialog.nml:36
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # extract_dialog.nml:37
        self.target.height = 1    # extract_dialog.nml:38
        self.target.label_text = ''    # extract_dialog.nml:39
        self.target.label_width = 0    # extract_dialog.nml:40
        self.target.history_id = 'copy'    # extract_dialog.nml:41

        self.options.x = 2    # extract_dialog.nml:45
        self.options.y = 4    # extract_dialog.nml:46
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # extract_dialog.nml:47
        self.options.height = 2    # extract_dialog.nml:48
        self.options.items = _bind(    # extract_dialog.nml:49
            lambda _o: [_tr('Extract with ~p~ath names'), _tr('T~e~st only')],
            yielding=True,
        )

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # extract_dialog.nml:53
        self.pick.default = True    # extract_dialog.nml:54
        self.pick.x = 5    # extract_dialog.nml:55
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # extract_dialog.nml:56
        self.pick.width = 11    # extract_dialog.nml:57
        self.pick.height = 2    # extract_dialog.nml:58
        self.pick.on_click = self.on_pick_click    # extract_dialog.nml:52

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # extract_dialog.nml:62
        self.abandon.x = 18    # extract_dialog.nml:63
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # extract_dialog.nml:64
        self.abandon.width = 11    # extract_dialog.nml:65
        self.abandon.height = 2    # extract_dialog.nml:66
        self.abandon.on_click = self.on_abandon_click    # extract_dialog.nml:61

        self.tree.text = _bind(lambda _o: _tr('~T~ree'), yielding=True)    # extract_dialog.nml:70
        self.tree.x = 31    # extract_dialog.nml:71
        self.tree.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # extract_dialog.nml:72
        self.tree.width = 11    # extract_dialog.nml:73
        self.tree.height = 2    # extract_dialog.nml:74
        self.tree.on_click = self.on_tree_click    # extract_dialog.nml:69
