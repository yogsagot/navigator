# navml: generated
"""Generated from ``find_file_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # find_file_dialog.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # find_file_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # find_file_dialog.nml:3
from navml.widgets.dialog.field import Field    # find_file_dialog.nml:4
from navml.widgets.dialog.label import Label    # find_file_dialog.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # find_file_dialog.nml:6

__navml_component__ = "FindFileDialog"

__all__ = ["FindFileDialog"]


class FindFileDialog(Dialog, _Component):
    """Alt+F7, Disk > Find file: DOS Navigator's ``dlgFileFind``.

    Its rows as ``DN.DNR`` lays them, two columns wider and a row taller for
    this library's buttons; DN's own row of OK, *Advanced...* and Cancel,
    Help left out with nothing to show yet.  Cancel carries no letter, as the
    resource's did: ``~C~`` is *Case sensitive*'s.
    """

    #: The document this class was generated from.
    __navml_source__ = "find_file_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    mask: Field    # find_file_dialog.nml:21
    text: Field    # find_file_dialog.nml:32
    options_caption: Label    # find_file_dialog.nml:42
    options: CheckBoxes    # find_file_dialog.nml:51
    scope_caption: Label    # find_file_dialog.nml:59
    scope: RadioButtons    # find_file_dialog.nml:68
    pick: Button    # find_file_dialog.nml:76
    advanced: Button    # find_file_dialog.nml:86
    abandon: Button    # find_file_dialog.nml:94

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # find_file_dialog.nml:76
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_advanced_click(self, event: _Event) -> bool:    # find_file_dialog.nml:86
        """``advanced`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # find_file_dialog.nml:94
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.mask = Field(parent=self)    # find_file_dialog.nml:20
        self.text = Field(parent=self)    # find_file_dialog.nml:31
        self.options_caption = Label(parent=self)    # find_file_dialog.nml:41
        self.options = CheckBoxes(parent=self)    # find_file_dialog.nml:50
        self.scope_caption = Label(parent=self)    # find_file_dialog.nml:58
        self.scope = RadioButtons(parent=self)    # find_file_dialog.nml:67
        self.pick = Button(parent=self)    # find_file_dialog.nml:75
        self.advanced = Button(parent=self)    # find_file_dialog.nml:85
        self.abandon = Button(parent=self)    # find_file_dialog.nml:93

        self.modal_width = 52    # find_file_dialog.nml:15
        self.modal_height = 18    # find_file_dialog.nml:16
        self.title = _bind(lambda _o: _tr('Find File'), yielding=True)    # find_file_dialog.nml:17

        self.mask.x = 2    # find_file_dialog.nml:22
        self.mask.y = 2    # find_file_dialog.nml:23
        self.mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:24
        self.mask.height = 1    # find_file_dialog.nml:25
        self.mask.label_text = _bind(    # find_file_dialog.nml:26
            lambda _o: _tr('~F~ile mask'),
            yielding=True,
        )
        self.mask.label_width = 14    # find_file_dialog.nml:27
        self.mask.history_id = 'find_mask'    # find_file_dialog.nml:28

        self.text.x = 2    # find_file_dialog.nml:33
        self.text.y = 4    # find_file_dialog.nml:34
        self.text.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:35
        self.text.height = 1    # find_file_dialog.nml:36
        self.text.label_text = _bind(    # find_file_dialog.nml:37
            lambda _o: _tr('~T~ext to find'),
            yielding=True,
        )
        self.text.label_width = 14    # find_file_dialog.nml:38
        self.text.history_id = 'find_text'    # find_file_dialog.nml:39

        self.options_caption.x = 3    # find_file_dialog.nml:43
        self.options_caption.y = 6    # find_file_dialog.nml:44
        self.options_caption.width = 12    # find_file_dialog.nml:45
        self.options_caption.height = 1    # find_file_dialog.nml:46
        self.options_caption.text = _bind(    # find_file_dialog.nml:47
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # find_file_dialog.nml:48

        self.options.x = 3    # find_file_dialog.nml:52
        self.options.y = 7    # find_file_dialog.nml:53
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # find_file_dialog.nml:54
        self.options.height = 2    # find_file_dialog.nml:55
        self.options.items = _bind(    # find_file_dialog.nml:56
            lambda _o: [_tr('Adva~n~ced search'), _tr('~C~ase sensitive'), _tr('~R~ecursive search'), _tr('~W~hole words')],
            yielding=True,
        )

        self.scope_caption.x = 3    # find_file_dialog.nml:60
        self.scope_caption.y = 10    # find_file_dialog.nml:61
        self.scope_caption.width = 10    # find_file_dialog.nml:62
        self.scope_caption.height = 1    # find_file_dialog.nml:63
        self.scope_caption.text = _bind(lambda _o: _tr('Scope'), yielding=True)    # find_file_dialog.nml:64
        self.scope_caption.link = _bind(lambda _o: self.scope)    # find_file_dialog.nml:65

        self.scope.x = 3    # find_file_dialog.nml:69
        self.scope.y = 11    # find_file_dialog.nml:70
        self.scope.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # find_file_dialog.nml:71
        self.scope.height = 2    # find_file_dialog.nml:72
        self.scope.items = _bind(    # find_file_dialog.nml:73
            lambda _o: [_tr('~E~ntire disk'), _tr('Current ~d~irectory'), _tr('~A~ll drives')],
            yielding=True,
        )

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # find_file_dialog.nml:77
        self.pick.default = True    # find_file_dialog.nml:78
        self.pick.x = 3    # find_file_dialog.nml:79
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # find_file_dialog.nml:80
        self.pick.width = 11    # find_file_dialog.nml:81
        self.pick.height = 2    # find_file_dialog.nml:82
        self.pick.on_click = self.on_pick_click    # find_file_dialog.nml:76

        self.advanced.text = _bind(    # find_file_dialog.nml:87
            lambda _o: _tr('Ad~v~anced...'),
            yielding=True,
        )
        self.advanced.x = 16    # find_file_dialog.nml:88
        self.advanced.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # find_file_dialog.nml:89
        self.advanced.width = 15    # find_file_dialog.nml:90
        self.advanced.height = 2    # find_file_dialog.nml:91
        self.advanced.on_click = self.on_advanced_click    # find_file_dialog.nml:86

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # find_file_dialog.nml:95
        self.abandon.x = 33    # find_file_dialog.nml:96
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # find_file_dialog.nml:97
        self.abandon.width = 11    # find_file_dialog.nml:98
        self.abandon.height = 2    # find_file_dialog.nml:99
        self.abandon.on_click = self.on_abandon_click    # find_file_dialog.nml:94
