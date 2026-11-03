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
from navkit.reactive import reactive as _reactive

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

    Not DN's: *Regular expression* among the options, a row lower for it, and,
    with *replacing*, File > Replace in files' *Replace with* line under the
    text, the rest two rows lower (``navigator.lib.file_ops.filereplace``).
    """

    #: The document this class was generated from.
    __navml_source__ = "find_file_dialog.nml"

    #: File > Replace in files rather than Find file.
    replacing: bool = _reactive(False)    # find_file_dialog.nml:20

    #: Ids, annotated so the hand-written half completes them.
    mask: Field    # find_file_dialog.nml:28
    text: Field    # find_file_dialog.nml:39
    replacement: Field    # find_file_dialog.nml:50
    options_caption: Label    # find_file_dialog.nml:61
    options: CheckBoxes    # find_file_dialog.nml:70
    scope_caption: Label    # find_file_dialog.nml:79
    scope: RadioButtons    # find_file_dialog.nml:88
    pick: Button    # find_file_dialog.nml:96
    advanced: Button    # find_file_dialog.nml:106
    abandon: Button    # find_file_dialog.nml:114

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # find_file_dialog.nml:96
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_advanced_click(self, event: _Event) -> bool:    # find_file_dialog.nml:106
        """``advanced`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # find_file_dialog.nml:114
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.mask = Field(parent=self)    # find_file_dialog.nml:27
        self.text = Field(parent=self)    # find_file_dialog.nml:38
        self.replacement = Field(parent=self)    # find_file_dialog.nml:49
        self.options_caption = Label(parent=self)    # find_file_dialog.nml:60
        self.options = CheckBoxes(parent=self)    # find_file_dialog.nml:69
        self.scope_caption = Label(parent=self)    # find_file_dialog.nml:78
        self.scope = RadioButtons(parent=self)    # find_file_dialog.nml:87
        self.pick = Button(parent=self)    # find_file_dialog.nml:95
        self.advanced = Button(parent=self)    # find_file_dialog.nml:105
        self.abandon = Button(parent=self)    # find_file_dialog.nml:113

        self.modal_width = 52    # find_file_dialog.nml:22
        self.modal_height = _bind(lambda _o: 21 if self.replacing else 19)    # find_file_dialog.nml:23
        self.title = _bind(    # find_file_dialog.nml:24
            lambda _o: _tr('Replace in Files') if self.replacing else _tr('Find File'),
            yielding=True,
        )

        self.mask.x = 2    # find_file_dialog.nml:29
        self.mask.y = 2    # find_file_dialog.nml:30
        self.mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:31
        self.mask.height = 1    # find_file_dialog.nml:32
        self.mask.label_text = _bind(    # find_file_dialog.nml:33
            lambda _o: _tr('~F~ile mask'),
            yielding=True,
        )
        self.mask.label_width = 14    # find_file_dialog.nml:34
        self.mask.history_id = 'find_mask'    # find_file_dialog.nml:35

        self.text.x = 2    # find_file_dialog.nml:40
        self.text.y = 4    # find_file_dialog.nml:41
        self.text.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:42
        self.text.height = 1    # find_file_dialog.nml:43
        self.text.label_text = _bind(    # find_file_dialog.nml:44
            lambda _o: _tr('~T~ext to find'),
            yielding=True,
        )
        self.text.label_width = 14    # find_file_dialog.nml:45
        self.text.history_id = 'find_text'    # find_file_dialog.nml:46

        self.replacement.visible = _bind(lambda _o: self.replacing)    # find_file_dialog.nml:51
        self.replacement.x = 2    # find_file_dialog.nml:52
        self.replacement.y = 6    # find_file_dialog.nml:53
        self.replacement.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:54
        self.replacement.height = 1    # find_file_dialog.nml:55
        self.replacement.label_text = _bind(    # find_file_dialog.nml:56
            lambda _o: _tr('Rep~l~ace with'),
            yielding=True,
        )
        self.replacement.label_width = 14    # find_file_dialog.nml:57
        self.replacement.history_id = 'replace_text'    # find_file_dialog.nml:58

        self.options_caption.x = 3    # find_file_dialog.nml:62
        self.options_caption.y = _bind(lambda _o: 8 if self.replacing else 6)    # find_file_dialog.nml:63
        self.options_caption.width = 12    # find_file_dialog.nml:64
        self.options_caption.height = 1    # find_file_dialog.nml:65
        self.options_caption.text = _bind(    # find_file_dialog.nml:66
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # find_file_dialog.nml:67

        self.options.x = 3    # find_file_dialog.nml:71
        self.options.y = _bind(lambda _o: 9 if self.replacing else 7)    # find_file_dialog.nml:72
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # find_file_dialog.nml:73
        self.options.height = 3    # find_file_dialog.nml:74
        self.options.items = _bind(    # find_file_dialog.nml:75
            lambda _o: [_tr('Adva~n~ced search'), _tr('~C~ase sensitive'), _tr('~R~ecursive search'), _tr('~W~hole words'), _tr('Regular e~x~pression')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # find_file_dialog.nml:76
            lambda _o: [_tr('Also match the size, date and kind set by Advanced...'), '', _tr('Search the subdirectories too'), '', _tr('The text is a Python regular expression, matched across lines')],
            yielding=True,
        )

        self.scope_caption.x = 3    # find_file_dialog.nml:80
        self.scope_caption.y = _bind(lambda _o: 13 if self.replacing else 11)    # find_file_dialog.nml:81
        self.scope_caption.width = 10    # find_file_dialog.nml:82
        self.scope_caption.height = 1    # find_file_dialog.nml:83
        self.scope_caption.text = _bind(lambda _o: _tr('Scope'), yielding=True)    # find_file_dialog.nml:84
        self.scope_caption.link = _bind(lambda _o: self.scope)    # find_file_dialog.nml:85

        self.scope.x = 3    # find_file_dialog.nml:89
        self.scope.y = _bind(lambda _o: 14 if self.replacing else 12)    # find_file_dialog.nml:90
        self.scope.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # find_file_dialog.nml:91
        self.scope.height = 2    # find_file_dialog.nml:92
        self.scope.items = _bind(    # find_file_dialog.nml:93
            lambda _o: [_tr('~E~ntire disk'), _tr('Current ~d~irectory'), _tr('~A~ll drives')],
            yielding=True,
        )

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # find_file_dialog.nml:97
        self.pick.default = True    # find_file_dialog.nml:98
        self.pick.x = 3    # find_file_dialog.nml:99
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # find_file_dialog.nml:100
        self.pick.width = 11    # find_file_dialog.nml:101
        self.pick.height = 2    # find_file_dialog.nml:102
        self.pick.on_click = self.on_pick_click    # find_file_dialog.nml:96

        self.advanced.text = _bind(    # find_file_dialog.nml:107
            lambda _o: _tr('Ad~v~anced...'),
            yielding=True,
        )
        self.advanced.x = 16    # find_file_dialog.nml:108
        self.advanced.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # find_file_dialog.nml:109
        self.advanced.width = 15    # find_file_dialog.nml:110
        self.advanced.height = 2    # find_file_dialog.nml:111
        self.advanced.on_click = self.on_advanced_click    # find_file_dialog.nml:106

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # find_file_dialog.nml:115
        self.abandon.x = 33    # find_file_dialog.nml:116
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # find_file_dialog.nml:117
        self.abandon.width = 11    # find_file_dialog.nml:118
        self.abandon.height = 2    # find_file_dialog.nml:119
        self.abandon.on_click = self.on_abandon_click    # find_file_dialog.nml:114
