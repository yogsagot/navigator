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
from navml.widgets.dialog.commands import Help    # find_file_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # find_file_dialog.nml:4
from navml.widgets.dialog.field import Field    # find_file_dialog.nml:5
from navml.widgets.dialog.label import Label    # find_file_dialog.nml:6
from navml.widgets.dialog.radio_buttons import RadioButtons    # find_file_dialog.nml:7

__navml_component__ = "FindFileDialog"

__all__ = ["FindFileDialog"]


class FindFileDialog(Dialog, _Component):
    """Alt+F7, File > Find...: DOS Navigator's ``dlgFileFind``.

    Its rows as ``DN.DNR`` lays them, two columns wider and a row taller for
    this library's buttons; DN's own row of OK, *Advanced...*, Cancel and
    Help, ten wide and touching from column 3 as the resource has them.
    Cancel carries no letter, as the resource's did: ``~C~`` is *Case
    sensitive*'s.

    Not DN's: *Regular expression* among the options, a row lower for it, and,
    with *replacing*, File > Replace in files' *Replace with* line under the
    text, the rest two rows lower (``navigator.lib.file_ops.filereplace``).
    """

    #: The document this class was generated from.
    __navml_source__ = "find_file_dialog.nml"

    #: File > Replace in files rather than Find file.
    replacing: bool = _reactive(False)    # find_file_dialog.nml:22

    #: Ids, annotated so the hand-written half completes them.
    mask: Field    # find_file_dialog.nml:34
    text: Field    # find_file_dialog.nml:45
    replacement: Field    # find_file_dialog.nml:56
    options_caption: Label    # find_file_dialog.nml:67
    options: CheckBoxes    # find_file_dialog.nml:76
    scope_caption: Label    # find_file_dialog.nml:86
    scope: RadioButtons    # find_file_dialog.nml:95
    pick: Button    # find_file_dialog.nml:104
    advanced: Button    # find_file_dialog.nml:115
    abandon: Button    # find_file_dialog.nml:125
    helper: Button    # find_file_dialog.nml:135

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # find_file_dialog.nml:104
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # find_file_dialog.nml:125
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # find_file_dialog.nml:135
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.mask = Field(parent=self)    # find_file_dialog.nml:33
        self.text = Field(parent=self)    # find_file_dialog.nml:44
        self.replacement = Field(parent=self)    # find_file_dialog.nml:55
        self.options_caption = Label(parent=self)    # find_file_dialog.nml:66
        self.options = CheckBoxes(parent=self)    # find_file_dialog.nml:75
        self.scope_caption = Label(parent=self)    # find_file_dialog.nml:85
        self.scope = RadioButtons(parent=self)    # find_file_dialog.nml:94
        self.pick = Button(parent=self)    # find_file_dialog.nml:103
        self.advanced = Button(parent=self)    # find_file_dialog.nml:114
        self.abandon = Button(parent=self)    # find_file_dialog.nml:124
        self.helper = Button(parent=self)    # find_file_dialog.nml:134

        self.modal_width = 52    # find_file_dialog.nml:24
        self.modal_height = _bind(lambda _o: 21 if self.replacing else 19)    # find_file_dialog.nml:25
        self.title = _bind(    # find_file_dialog.nml:26
            lambda _o: _tr('Replace in Files') if self.replacing else _tr('Find File'),
            yielding=True,
        )
        self.help_topic = _bind(    # find_file_dialog.nml:27
            lambda _o: 'panels.md#replace-in-files' if self.replacing else 'panels.md#find-file'
        )
        self.buttons = 'none'    # find_file_dialog.nml:28
        self.buttons_row = _bind(    # find_file_dialog.nml:30
            lambda _o: (self.pick, self.advanced, self.abandon, self.helper)
        )

        self.mask.y = 2    # find_file_dialog.nml:35
        self.mask.label_text = _bind(    # find_file_dialog.nml:39
            lambda _o: _tr('~F~ile mask'),
            yielding=True,
        )
        self.mask.label_width = 14    # find_file_dialog.nml:40
        self.mask.history_id = 'find_mask'    # find_file_dialog.nml:41
        self.mask.x = 2    # find_file_dialog.nml:37
        self.mask.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:38

        self.text.y = 4    # find_file_dialog.nml:46
        self.text.label_text = _bind(    # find_file_dialog.nml:50
            lambda _o: _tr('~T~ext to find'),
            yielding=True,
        )
        self.text.label_width = 14    # find_file_dialog.nml:51
        self.text.history_id = 'find_text'    # find_file_dialog.nml:52
        self.text.x = 2    # find_file_dialog.nml:48
        self.text.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:49

        self.replacement.visible = _bind(lambda _o: self.replacing)    # find_file_dialog.nml:57
        self.replacement.y = 6    # find_file_dialog.nml:58
        self.replacement.label_text = _bind(    # find_file_dialog.nml:62
            lambda _o: _tr('Rep~l~ace with'),
            yielding=True,
        )
        self.replacement.label_width = 14    # find_file_dialog.nml:63
        self.replacement.history_id = 'replace_text'    # find_file_dialog.nml:64
        self.replacement.x = 2    # find_file_dialog.nml:60
        self.replacement.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # find_file_dialog.nml:61

        self.options_caption.x = 3    # find_file_dialog.nml:68
        self.options_caption.width = 12    # find_file_dialog.nml:69
        self.options_caption.text = _bind(    # find_file_dialog.nml:72
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # find_file_dialog.nml:73
        self.options_caption.y = _bind(    # find_file_dialog.nml:71
            lambda _o: self.replacement.y + self.replacement.height + 1 if self.replacement.visible and self.replacement.height else self.text.y + self.text.height + 1
        )

        self.options.height = 3    # find_file_dialog.nml:77
        self.options.items = _bind(    # find_file_dialog.nml:82
            lambda _o: [_tr('Adva~n~ced search'), _tr('~C~ase sensitive'), _tr('~R~ecursive search'), _tr('~W~hole words'), _tr('Regular e~x~pression')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # find_file_dialog.nml:83
            lambda _o: [_tr('Also match the size, date and kind set by Advanced...'), '', _tr('Search the subdirectories too'), '', _tr('The text is a Python regular expression, matched across lines')],
            yielding=True,
        )
        self.options.x = 3    # find_file_dialog.nml:79
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # find_file_dialog.nml:80
        self.options.y = _bind(    # find_file_dialog.nml:81
            lambda _o: self.options_caption.y + self.options_caption.height
        )

        self.scope_caption.x = 3    # find_file_dialog.nml:87
        self.scope_caption.width = 10    # find_file_dialog.nml:88
        self.scope_caption.text = _bind(lambda _o: _tr('Scope'), yielding=True)    # find_file_dialog.nml:91
        self.scope_caption.link = _bind(lambda _o: self.scope)    # find_file_dialog.nml:92
        self.scope_caption.y = _bind(    # find_file_dialog.nml:90
            lambda _o: self.options.y + self.options.height + 1
        )

        self.scope.height = 2    # find_file_dialog.nml:96
        self.scope.items = _bind(    # find_file_dialog.nml:101
            lambda _o: [_tr('~E~ntire disk'), _tr('Current ~d~irectory'), _tr('~A~ll drives')],
            yielding=True,
        )
        self.scope.x = 3    # find_file_dialog.nml:98
        self.scope.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # find_file_dialog.nml:99
        self.scope.y = _bind(    # find_file_dialog.nml:100
            lambda _o: self.scope_caption.y + self.scope_caption.height
        )

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # find_file_dialog.nml:105
        self.pick.default = True    # find_file_dialog.nml:106
        self.pick.x = 3    # find_file_dialog.nml:107
        self.pick.width = 10    # find_file_dialog.nml:108
        self.pick.height = 2    # find_file_dialog.nml:109
        self.pick.y = _bind(    # find_file_dialog.nml:111
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.pick.on_click = self.on_pick_click    # find_file_dialog.nml:104

        self.advanced.text = _bind(    # find_file_dialog.nml:116
            lambda _o: _tr('Ad~v~anced...'),
            yielding=True,
        )
        self.advanced.x = 13    # find_file_dialog.nml:117
        self.advanced.width = 15    # find_file_dialog.nml:118
        self.advanced.height = 2    # find_file_dialog.nml:119
        self.advanced.y = _bind(    # find_file_dialog.nml:121
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )

        async def _on_click(event):    # find_file_dialog.nml:122
            self.spawn(self.ask_advanced())
            return True
        self.advanced.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # find_file_dialog.nml:126
        self.abandon.x = 28    # find_file_dialog.nml:127
        self.abandon.width = 10    # find_file_dialog.nml:128
        self.abandon.height = 2    # find_file_dialog.nml:129
        self.abandon.y = _bind(    # find_file_dialog.nml:131
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.abandon.on_click = self.on_abandon_click    # find_file_dialog.nml:125

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # find_file_dialog.nml:136
        self.helper.command = Help    # find_file_dialog.nml:137
        self.helper.x = 38    # find_file_dialog.nml:138
        self.helper.width = 10    # find_file_dialog.nml:139
        self.helper.height = 2    # find_file_dialog.nml:140
        self.helper.y = _bind(    # find_file_dialog.nml:142
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.helper.on_click = self.on_helper_click    # find_file_dialog.nml:135

        self._navml_built(__class__)
