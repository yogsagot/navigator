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
    mask: Field    # find_file_dialog.nml:29
    text: Field    # find_file_dialog.nml:40
    replacement: Field    # find_file_dialog.nml:51
    options_caption: Label    # find_file_dialog.nml:62
    options: CheckBoxes    # find_file_dialog.nml:71
    scope_caption: Label    # find_file_dialog.nml:81
    scope: RadioButtons    # find_file_dialog.nml:90
    pick: Button    # find_file_dialog.nml:99
    advanced: Button    # find_file_dialog.nml:110
    abandon: Button    # find_file_dialog.nml:119

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # find_file_dialog.nml:99
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_advanced_click(self, event: _Event) -> bool:    # find_file_dialog.nml:110
        """``advanced`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # find_file_dialog.nml:119
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.mask = Field(parent=self)    # find_file_dialog.nml:28
        self.text = Field(parent=self)    # find_file_dialog.nml:39
        self.replacement = Field(parent=self)    # find_file_dialog.nml:50
        self.options_caption = Label(parent=self)    # find_file_dialog.nml:61
        self.options = CheckBoxes(parent=self)    # find_file_dialog.nml:70
        self.scope_caption = Label(parent=self)    # find_file_dialog.nml:80
        self.scope = RadioButtons(parent=self)    # find_file_dialog.nml:89
        self.pick = Button(parent=self)    # find_file_dialog.nml:98
        self.advanced = Button(parent=self)    # find_file_dialog.nml:109
        self.abandon = Button(parent=self)    # find_file_dialog.nml:118

        self.modal_width = 52    # find_file_dialog.nml:22
        self.modal_height = _bind(lambda _o: 21 if self.replacing else 19)    # find_file_dialog.nml:23
        self.title = _bind(    # find_file_dialog.nml:24
            lambda _o: _tr('Replace in Files') if self.replacing else _tr('Find File'),
            yielding=True,
        )
        self.buttons = 'none'    # find_file_dialog.nml:25

        self.mask.y = 2    # find_file_dialog.nml:30
        self.mask.label_text = _bind(    # find_file_dialog.nml:34
            lambda _o: _tr('~F~ile mask'),
            yielding=True,
        )
        self.mask.label_width = 14    # find_file_dialog.nml:35
        self.mask.history_id = 'find_mask'    # find_file_dialog.nml:36
        self.mask.x = 2    # find_file_dialog.nml:32
        self.mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:33

        self.text.y = 4    # find_file_dialog.nml:41
        self.text.label_text = _bind(    # find_file_dialog.nml:45
            lambda _o: _tr('~T~ext to find'),
            yielding=True,
        )
        self.text.label_width = 14    # find_file_dialog.nml:46
        self.text.history_id = 'find_text'    # find_file_dialog.nml:47
        self.text.x = 2    # find_file_dialog.nml:43
        self.text.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:44

        self.replacement.visible = _bind(lambda _o: self.replacing)    # find_file_dialog.nml:52
        self.replacement.y = 6    # find_file_dialog.nml:53
        self.replacement.label_text = _bind(    # find_file_dialog.nml:57
            lambda _o: _tr('Rep~l~ace with'),
            yielding=True,
        )
        self.replacement.label_width = 14    # find_file_dialog.nml:58
        self.replacement.history_id = 'replace_text'    # find_file_dialog.nml:59
        self.replacement.x = 2    # find_file_dialog.nml:55
        self.replacement.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:56

        self.options_caption.x = 3    # find_file_dialog.nml:63
        self.options_caption.width = 12    # find_file_dialog.nml:64
        self.options_caption.text = _bind(    # find_file_dialog.nml:67
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # find_file_dialog.nml:68
        self.options_caption.y = _bind(    # find_file_dialog.nml:66
            lambda _o: self.replacement.y + self.replacement.height + 1 if self.replacement.visible and self.replacement.height else self.text.y + self.text.height + 1
        )

        self.options.height = 3    # find_file_dialog.nml:72
        self.options.items = _bind(    # find_file_dialog.nml:77
            lambda _o: [_tr('Adva~n~ced search'), _tr('~C~ase sensitive'), _tr('~R~ecursive search'), _tr('~W~hole words'), _tr('Regular e~x~pression')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # find_file_dialog.nml:78
            lambda _o: [_tr('Also match the size, date and kind set by Advanced...'), '', _tr('Search the subdirectories too'), '', _tr('The text is a Python regular expression, matched across lines')],
            yielding=True,
        )
        self.options.x = 3    # find_file_dialog.nml:74
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # find_file_dialog.nml:75
        self.options.y = _bind(    # find_file_dialog.nml:76
            lambda _o: self.options_caption.y + self.options_caption.height
        )

        self.scope_caption.x = 3    # find_file_dialog.nml:82
        self.scope_caption.width = 10    # find_file_dialog.nml:83
        self.scope_caption.text = _bind(lambda _o: _tr('Scope'), yielding=True)    # find_file_dialog.nml:86
        self.scope_caption.link = _bind(lambda _o: self.scope)    # find_file_dialog.nml:87
        self.scope_caption.y = _bind(    # find_file_dialog.nml:85
            lambda _o: self.options.y + self.options.height + 1
        )

        self.scope.height = 2    # find_file_dialog.nml:91
        self.scope.items = _bind(    # find_file_dialog.nml:96
            lambda _o: [_tr('~E~ntire disk'), _tr('Current ~d~irectory'), _tr('~A~ll drives')],
            yielding=True,
        )
        self.scope.x = 3    # find_file_dialog.nml:93
        self.scope.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # find_file_dialog.nml:94
        self.scope.y = _bind(    # find_file_dialog.nml:95
            lambda _o: self.scope_caption.y + self.scope_caption.height
        )

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # find_file_dialog.nml:100
        self.pick.default = True    # find_file_dialog.nml:101
        self.pick.x = 3    # find_file_dialog.nml:102
        self.pick.width = 11    # find_file_dialog.nml:103
        self.pick.height = 2    # find_file_dialog.nml:104
        self.pick.y = _bind(    # find_file_dialog.nml:106
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.pick.on_click = self.on_pick_click    # find_file_dialog.nml:99

        self.advanced.text = _bind(    # find_file_dialog.nml:111
            lambda _o: _tr('Ad~v~anced...'),
            yielding=True,
        )
        self.advanced.x = 16    # find_file_dialog.nml:112
        self.advanced.width = 15    # find_file_dialog.nml:113
        self.advanced.height = 2    # find_file_dialog.nml:114
        self.advanced.y = _bind(    # find_file_dialog.nml:116
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.advanced.on_click = self.on_advanced_click    # find_file_dialog.nml:110

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # find_file_dialog.nml:120
        self.abandon.x = 33    # find_file_dialog.nml:121
        self.abandon.width = 11    # find_file_dialog.nml:122
        self.abandon.height = 2    # find_file_dialog.nml:123
        self.abandon.y = _bind(    # find_file_dialog.nml:125
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.abandon.on_click = self.on_abandon_click    # find_file_dialog.nml:119
