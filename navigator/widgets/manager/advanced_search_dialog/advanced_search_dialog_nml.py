# navml: generated
"""Generated from ``advanced_search_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # advanced_search_dialog.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # advanced_search_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # advanced_search_dialog.nml:3
from navml.widgets.dialog.field import Field    # advanced_search_dialog.nml:4
from navml.widgets.dialog.label import Label    # advanced_search_dialog.nml:5

__navml_component__ = "AdvancedSearchDialog"

__all__ = ["AdvancedSearchDialog"]


class AdvancedSearchDialog(Dialog, _Component):
    """*Find File*'s *Advanced...*: DOS Navigator's ``dlgAdvanceSearch``.

    Its four lines and its kinds, and OK, *Clear all* and Cancel -- along the
    bottom, where this library puts a dialog's buttons, rather than down the
    right.  Dates are ``YYYY-MM-DD`` with an optional ``HH:MM``; the kinds are
    POSIX's, where DN's were the four DOS attributes (:mod:`navigator.filefind`).
    """

    #: The document this class was generated from.
    __navml_source__ = "advanced_search_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    after: Field    # advanced_search_dialog.nml:20
    before: Field    # advanced_search_dialog.nml:31
    greater: Field    # advanced_search_dialog.nml:41
    less: Field    # advanced_search_dialog.nml:50
    kinds_caption: Label    # advanced_search_dialog.nml:59
    kinds: CheckBoxes    # advanced_search_dialog.nml:68
    pick: Button    # advanced_search_dialog.nml:76
    clear: Button    # advanced_search_dialog.nml:86
    abandon: Button    # advanced_search_dialog.nml:94

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # advanced_search_dialog.nml:76
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_clear_click(self, event: _Event) -> bool:    # advanced_search_dialog.nml:86
        """``clear`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # advanced_search_dialog.nml:94
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.after = Field(parent=self)    # advanced_search_dialog.nml:19
        self.before = Field(parent=self)    # advanced_search_dialog.nml:30
        self.greater = Field(parent=self)    # advanced_search_dialog.nml:40
        self.less = Field(parent=self)    # advanced_search_dialog.nml:49
        self.kinds_caption = Label(parent=self)    # advanced_search_dialog.nml:58
        self.kinds = CheckBoxes(parent=self)    # advanced_search_dialog.nml:67
        self.pick = Button(parent=self)    # advanced_search_dialog.nml:75
        self.clear = Button(parent=self)    # advanced_search_dialog.nml:85
        self.abandon = Button(parent=self)    # advanced_search_dialog.nml:93

        self.modal_width = 52    # advanced_search_dialog.nml:14
        self.modal_height = 16    # advanced_search_dialog.nml:15
        self.title = 'Advanced search'    # advanced_search_dialog.nml:16

        self.after.x = 2    # advanced_search_dialog.nml:21
        self.after.y = 2    # advanced_search_dialog.nml:22
        self.after.width = 38    # advanced_search_dialog.nml:23
        self.after.height = 1    # advanced_search_dialog.nml:24
        self.after.label_text = 'Date is ~a~fter'    # advanced_search_dialog.nml:25
        self.after.label_width = 22    # advanced_search_dialog.nml:26
        self.after.history_id = 'find_after'    # advanced_search_dialog.nml:27

        self.before.x = 2    # advanced_search_dialog.nml:32
        self.before.y = 3    # advanced_search_dialog.nml:33
        self.before.width = 38    # advanced_search_dialog.nml:34
        self.before.height = 1    # advanced_search_dialog.nml:35
        self.before.label_text = 'Date is ~b~efore'    # advanced_search_dialog.nml:36
        self.before.label_width = 22    # advanced_search_dialog.nml:37
        self.before.history_id = 'find_before'    # advanced_search_dialog.nml:38

        self.greater.x = 2    # advanced_search_dialog.nml:42
        self.greater.y = 5    # advanced_search_dialog.nml:43
        self.greater.width = 36    # advanced_search_dialog.nml:44
        self.greater.height = 1    # advanced_search_dialog.nml:45
        self.greater.label_text = 'Size is ~g~reater than'    # advanced_search_dialog.nml:46
        self.greater.label_width = 22    # advanced_search_dialog.nml:47

        self.less.x = 2    # advanced_search_dialog.nml:51
        self.less.y = 6    # advanced_search_dialog.nml:52
        self.less.width = 36    # advanced_search_dialog.nml:53
        self.less.height = 1    # advanced_search_dialog.nml:54
        self.less.label_text = 'Size is ~l~ess than'    # advanced_search_dialog.nml:55
        self.less.label_width = 22    # advanced_search_dialog.nml:56

        self.kinds_caption.x = 3    # advanced_search_dialog.nml:60
        self.kinds_caption.y = 8    # advanced_search_dialog.nml:61
        self.kinds_caption.width = 12    # advanced_search_dialog.nml:62
        self.kinds_caption.height = 1    # advanced_search_dialog.nml:63
        self.kinds_caption.text = 'Kind'    # advanced_search_dialog.nml:64
        self.kinds_caption.link = _bind(lambda _o: self.kinds)    # advanced_search_dialog.nml:65

        self.kinds.x = 3    # advanced_search_dialog.nml:69
        self.kinds.y = 9    # advanced_search_dialog.nml:70
        self.kinds.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # advanced_search_dialog.nml:71
        self.kinds.height = 2    # advanced_search_dialog.nml:72
        self.kinds.items = ['E~x~ecutable', 'S~y~mbolic link', 'H~i~dden', 'R~e~ad-only']    # advanced_search_dialog.nml:73

        self.pick.text = 'O~K~'    # advanced_search_dialog.nml:77
        self.pick.default = True    # advanced_search_dialog.nml:78
        self.pick.x = 3    # advanced_search_dialog.nml:79
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # advanced_search_dialog.nml:80
        self.pick.width = 11    # advanced_search_dialog.nml:81
        self.pick.height = 2    # advanced_search_dialog.nml:82
        self.pick.on_click = self.on_pick_click    # advanced_search_dialog.nml:76

        self.clear.text = '~C~lear all'    # advanced_search_dialog.nml:87
        self.clear.x = 16    # advanced_search_dialog.nml:88
        self.clear.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # advanced_search_dialog.nml:89
        self.clear.width = 14    # advanced_search_dialog.nml:90
        self.clear.height = 2    # advanced_search_dialog.nml:91
        self.clear.on_click = self.on_clear_click    # advanced_search_dialog.nml:86

        self.abandon.text = 'Cancel'    # advanced_search_dialog.nml:95
        self.abandon.x = 32    # advanced_search_dialog.nml:96
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # advanced_search_dialog.nml:97
        self.abandon.width = 11    # advanced_search_dialog.nml:98
        self.abandon.height = 2    # advanced_search_dialog.nml:99
        self.abandon.on_click = self.on_abandon_click    # advanced_search_dialog.nml:94
