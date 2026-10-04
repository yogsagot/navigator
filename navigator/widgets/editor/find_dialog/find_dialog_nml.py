# navml: generated
"""Generated from ``find_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # find_dialog.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # find_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # find_dialog.nml:3
from navml.widgets.dialog.field import Field    # find_dialog.nml:4
from navml.widgets.dialog.label import Label    # find_dialog.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # find_dialog.nml:6

__navml_component__ = "FindDialog"

__all__ = ["FindDialog"]


class FindDialog(Dialog, _Component):
    """DOS Navigator's ``dlgEditorFind`` (55 by 15) and ``dlgEditorReplace`` (55 by

    18), one document because they differ only by the *New text* line, a third
    option and *Change all*: every rectangle is the resource's, the replace
    dialog's two rows lower where it says so.  Both lines keep ``hsFindText``.
    """

    #: The document this class was generated from.
    __navml_source__ = "find_dialog.nml"

    #: Which of the two: *Find* (F7) or *Replace* (Ctrl+F7).
    replace: bool = _reactive(False)    # find_dialog.nml:14

    #: Ids, annotated so the hand-written half completes them.
    text: Field    # find_dialog.nml:21
    new: Field    # find_dialog.nml:31
    options_caption: Label    # find_dialog.nml:42
    options: CheckBoxes    # find_dialog.nml:51
    direction_caption: Label    # find_dialog.nml:59
    direction: RadioButtons    # find_dialog.nml:68
    scope_caption: Label    # find_dialog.nml:76
    scope: RadioButtons    # find_dialog.nml:85
    origin_caption: Label    # find_dialog.nml:93
    origin: RadioButtons    # find_dialog.nml:102
    pick: Button    # find_dialog.nml:110
    all: Button    # find_dialog.nml:120
    abandon: Button    # find_dialog.nml:129
    helper: Button    # find_dialog.nml:138

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # find_dialog.nml:110
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_all_click(self, event: _Event) -> bool:    # find_dialog.nml:120
        """``all`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # find_dialog.nml:129
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # find_dialog.nml:138
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.text = Field(parent=self)    # find_dialog.nml:20
        self.new = Field(parent=self)    # find_dialog.nml:30
        self.options_caption = Label(parent=self)    # find_dialog.nml:41
        self.options = CheckBoxes(parent=self)    # find_dialog.nml:50
        self.direction_caption = Label(parent=self)    # find_dialog.nml:58
        self.direction = RadioButtons(parent=self)    # find_dialog.nml:67
        self.scope_caption = Label(parent=self)    # find_dialog.nml:75
        self.scope = RadioButtons(parent=self)    # find_dialog.nml:84
        self.origin_caption = Label(parent=self)    # find_dialog.nml:92
        self.origin = RadioButtons(parent=self)    # find_dialog.nml:101
        self.pick = Button(parent=self)    # find_dialog.nml:109
        self.all = Button(parent=self)    # find_dialog.nml:119
        self.abandon = Button(parent=self)    # find_dialog.nml:128
        self.helper = Button(parent=self)    # find_dialog.nml:137

        self.modal_width = 55    # find_dialog.nml:16
        self.modal_height = _bind(lambda _o: 18 if self.replace else 15)    # find_dialog.nml:17
        self.title = _bind(lambda _o: 'Replace' if self.replace else 'Find')    # find_dialog.nml:18

        self.text.x = 3    # find_dialog.nml:22
        self.text.y = 2    # find_dialog.nml:23
        self.text.width = 49    # find_dialog.nml:24
        self.text.height = 1    # find_dialog.nml:25
        self.text.label_text = '~T~ext to find'    # find_dialog.nml:26
        self.text.label_width = 14    # find_dialog.nml:27
        self.text.history_id = 'find_text'    # find_dialog.nml:28

        self.new.visible = _bind(lambda _o: self.replace)    # find_dialog.nml:32
        self.new.x = 7    # find_dialog.nml:33
        self.new.y = 4    # find_dialog.nml:34
        self.new.width = 45    # find_dialog.nml:35
        self.new.height = 1    # find_dialog.nml:36
        self.new.label_text = '~N~ew text'    # find_dialog.nml:37
        self.new.label_width = 10    # find_dialog.nml:38
        self.new.history_id = 'find_text'    # find_dialog.nml:39

        self.options_caption.text = 'Options'    # find_dialog.nml:43
        self.options_caption.link = _bind(lambda _o: self.options)    # find_dialog.nml:44
        self.options_caption.x = 3    # find_dialog.nml:45
        self.options_caption.y = _bind(lambda _o: 6 if self.replace else 4)    # find_dialog.nml:46
        self.options_caption.width = 24    # find_dialog.nml:47
        self.options_caption.height = 1    # find_dialog.nml:48

        self.options.x = 3    # find_dialog.nml:52
        self.options.y = _bind(lambda _o: 7 if self.replace else 5)    # find_dialog.nml:53
        self.options.width = 24    # find_dialog.nml:54
        self.options.height = _bind(lambda _o: 3 if self.replace else 2)    # find_dialog.nml:55
        self.options.items = _bind(    # find_dialog.nml:56
            lambda _o: ['~C~ase sensitive', '~W~hole words only', '~P~rompt on replace'] if self.replace else ['~C~ase sensitive', '~W~hole words only']
        )

        self.direction_caption.text = 'Direction'    # find_dialog.nml:60
        self.direction_caption.link = _bind(lambda _o: self.direction)    # find_dialog.nml:61
        self.direction_caption.x = 30    # find_dialog.nml:62
        self.direction_caption.y = _bind(lambda _o: 6 if self.replace else 4)    # find_dialog.nml:63
        self.direction_caption.width = 22    # find_dialog.nml:64
        self.direction_caption.height = 1    # find_dialog.nml:65

        self.direction.x = 30    # find_dialog.nml:69
        self.direction.y = _bind(lambda _o: 7 if self.replace else 5)    # find_dialog.nml:70
        self.direction.width = 22    # find_dialog.nml:71
        self.direction.height = 2    # find_dialog.nml:72
        self.direction.items = ['Forwar~d~', '~B~ackward']    # find_dialog.nml:73

        self.scope_caption.text = 'Scope'    # find_dialog.nml:77
        self.scope_caption.link = _bind(lambda _o: self.scope)    # find_dialog.nml:78
        self.scope_caption.x = 3    # find_dialog.nml:79
        self.scope_caption.y = _bind(lambda _o: 11 if self.replace else 8)    # find_dialog.nml:80
        self.scope_caption.width = 24    # find_dialog.nml:81
        self.scope_caption.height = 1    # find_dialog.nml:82

        self.scope.x = 3    # find_dialog.nml:86
        self.scope.y = _bind(lambda _o: 12 if self.replace else 9)    # find_dialog.nml:87
        self.scope.width = 24    # find_dialog.nml:88
        self.scope.height = 2    # find_dialog.nml:89
        self.scope.items = ['~G~lobal', '~S~elected text']    # find_dialog.nml:90

        self.origin_caption.text = 'Origin'    # find_dialog.nml:94
        self.origin_caption.link = _bind(lambda _o: self.origin)    # find_dialog.nml:95
        self.origin_caption.x = 30    # find_dialog.nml:96
        self.origin_caption.y = _bind(lambda _o: 11 if self.replace else 8)    # find_dialog.nml:97
        self.origin_caption.width = 22    # find_dialog.nml:98
        self.origin_caption.height = 1    # find_dialog.nml:99

        self.origin.x = 30    # find_dialog.nml:103
        self.origin.y = _bind(lambda _o: 12 if self.replace else 9)    # find_dialog.nml:104
        self.origin.width = 22    # find_dialog.nml:105
        self.origin.height = 2    # find_dialog.nml:106
        self.origin.items = ['~E~ntire scope', '~F~rom cursor']    # find_dialog.nml:107

        self.pick.text = 'O~K~'    # find_dialog.nml:111
        self.pick.default = True    # find_dialog.nml:112
        self.pick.x = _bind(lambda _o: 6 if self.replace else 22)    # find_dialog.nml:113
        self.pick.y = _bind(lambda _o: 15 if self.replace else 12)    # find_dialog.nml:114
        self.pick.width = 10    # find_dialog.nml:115
        self.pick.height = 2    # find_dialog.nml:116
        self.pick.on_click = self.on_pick_click    # find_dialog.nml:110

        self.all.text = 'Change ~a~ll'    # find_dialog.nml:121
        self.all.visible = _bind(lambda _o: self.replace)    # find_dialog.nml:122
        self.all.x = 16    # find_dialog.nml:123
        self.all.y = 15    # find_dialog.nml:124
        self.all.width = 16    # find_dialog.nml:125
        self.all.height = 2    # find_dialog.nml:126
        self.all.on_click = self.on_all_click    # find_dialog.nml:120

        self.abandon.text = 'Cancel'    # find_dialog.nml:130
        self.abandon.x = 32    # find_dialog.nml:131
        self.abandon.y = _bind(lambda _o: 15 if self.replace else 12)    # find_dialog.nml:132
        self.abandon.width = 10    # find_dialog.nml:133
        self.abandon.height = 2    # find_dialog.nml:134
        self.abandon.on_click = self.on_abandon_click    # find_dialog.nml:129

        self.helper.text = 'Help'    # find_dialog.nml:139
        self.helper.disabled = True    # find_dialog.nml:140
        self.helper.x = 42    # find_dialog.nml:141
        self.helper.y = _bind(lambda _o: 15 if self.replace else 12)    # find_dialog.nml:142
        self.helper.width = 10    # find_dialog.nml:143
        self.helper.height = 2    # find_dialog.nml:144
        self.helper.on_click = self.on_helper_click    # find_dialog.nml:138
