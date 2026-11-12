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
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # find_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # find_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # find_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # find_dialog.nml:4
from navml.widgets.dialog.field import Field    # find_dialog.nml:5
from navml.widgets.dialog.label import Label    # find_dialog.nml:6
from navml.widgets.dialog.radio_buttons import RadioButtons    # find_dialog.nml:7

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
    replace: bool = _reactive(False)    # find_dialog.nml:15

    #: Ids, annotated so the hand-written half completes them.
    text: Field    # find_dialog.nml:23
    new: Field    # find_dialog.nml:32
    options_caption: Label    # find_dialog.nml:42
    options: CheckBoxes    # find_dialog.nml:51
    direction_caption: Label    # find_dialog.nml:61
    direction: RadioButtons    # find_dialog.nml:70
    scope_caption: Label    # find_dialog.nml:79
    scope: RadioButtons    # find_dialog.nml:88
    origin_caption: Label    # find_dialog.nml:97
    origin: RadioButtons    # find_dialog.nml:106
    pick: Button    # find_dialog.nml:115
    all: Button    # find_dialog.nml:126
    rest_row: ButtonRow    # find_dialog.nml:136
    abandon: Button    # find_dialog.nml:146
    helper: Button    # find_dialog.nml:151

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # find_dialog.nml:115
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_all_click(self, event: _Event) -> bool:    # find_dialog.nml:126
        """``all`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # find_dialog.nml:146
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # find_dialog.nml:151
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.text = Field(parent=self)    # find_dialog.nml:22
        self.new = Field(parent=self)    # find_dialog.nml:31
        self.options_caption = Label(parent=self)    # find_dialog.nml:41
        self.options = CheckBoxes(parent=self)    # find_dialog.nml:50
        self.direction_caption = Label(parent=self)    # find_dialog.nml:60
        self.direction = RadioButtons(parent=self)    # find_dialog.nml:69
        self.scope_caption = Label(parent=self)    # find_dialog.nml:78
        self.scope = RadioButtons(parent=self)    # find_dialog.nml:87
        self.origin_caption = Label(parent=self)    # find_dialog.nml:96
        self.origin = RadioButtons(parent=self)    # find_dialog.nml:105
        self.pick = Button(parent=self)    # find_dialog.nml:114
        self.all = Button(parent=self)    # find_dialog.nml:125
        self.rest_row = ButtonRow(parent=self)    # find_dialog.nml:135
        self.abandon = Button(parent=self.rest_row)    # find_dialog.nml:145
        self.helper = Button(parent=self.rest_row)    # find_dialog.nml:150

        self.modal_width = 55    # find_dialog.nml:17
        self.modal_height = _bind(lambda _o: 18 if self.replace else 15)    # find_dialog.nml:18
        self.title = _bind(    # find_dialog.nml:19
            lambda _o: _tr('Replace') if self.replace else _tr('Find'),
            yielding=True,
        )
        self.buttons = 'none'    # find_dialog.nml:20

        self.text.x = 3    # find_dialog.nml:24
        self.text.y = 2    # find_dialog.nml:25
        self.text.width = 49    # find_dialog.nml:26
        self.text.label_text = _bind(    # find_dialog.nml:27
            lambda _o: _tr('~T~ext to find'),
            yielding=True,
        )
        self.text.label_width = 14    # find_dialog.nml:28
        self.text.history_id = 'find_text'    # find_dialog.nml:29

        self.new.visible = _bind(lambda _o: self.replace)    # find_dialog.nml:33
        self.new.x = 7    # find_dialog.nml:34
        self.new.y = 4    # find_dialog.nml:35
        self.new.width = 45    # find_dialog.nml:36
        self.new.label_text = _bind(    # find_dialog.nml:37
            lambda _o: _tr('~N~ew text'),
            yielding=True,
        )
        self.new.label_width = 10    # find_dialog.nml:38
        self.new.history_id = 'find_text'    # find_dialog.nml:39

        self.options_caption.text = _bind(    # find_dialog.nml:43
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # find_dialog.nml:44
        self.options_caption.x = 3    # find_dialog.nml:45
        self.options_caption.width = 24    # find_dialog.nml:46
        self.options_caption.y = _bind(    # find_dialog.nml:48
            lambda _o: self.new.y + self.new.height + 1 if self.new.visible and self.new.height else self.text.y + self.text.height + 1
        )

        self.options.x = 3    # find_dialog.nml:52
        self.options.width = 24    # find_dialog.nml:53
        self.options.height = _bind(lambda _o: 3 if self.replace else 2)    # find_dialog.nml:54
        self.options.items = _bind(    # find_dialog.nml:55
            lambda _o: [_tr('~C~ase sensitive'), _tr('~W~hole words only'), _tr('~P~rompt on replace')] if self.replace else [_tr('~C~ase sensitive'), _tr('~W~hole words only')]
        )
        self.options.tooltips = _bind(    # find_dialog.nml:56
            lambda _o: ['', '', _tr('Ask before each replacement')],
            yielding=True,
        )
        self.options.y = _bind(    # find_dialog.nml:58
            lambda _o: self.options_caption.y + self.options_caption.height
        )

        self.direction_caption.text = _bind(    # find_dialog.nml:62
            lambda _o: _tr('Direction'),
            yielding=True,
        )
        self.direction_caption.link = _bind(lambda _o: self.direction)    # find_dialog.nml:63
        self.direction_caption.x = 30    # find_dialog.nml:64
        self.direction_caption.width = 22    # find_dialog.nml:65
        self.direction_caption.y = _bind(    # find_dialog.nml:67
            lambda _o: self.new.y + self.new.height + 1 if self.new.visible and self.new.height else self.text.y + self.text.height + 1
        )

        self.direction.x = 30    # find_dialog.nml:71
        self.direction.width = 22    # find_dialog.nml:72
        self.direction.height = 2    # find_dialog.nml:73
        self.direction.items = _bind(    # find_dialog.nml:74
            lambda _o: [_tr('Forwar~d~'), _tr('~B~ackward')],
            yielding=True,
        )
        self.direction.y = _bind(    # find_dialog.nml:76
            lambda _o: self.direction_caption.y + self.direction_caption.height
        )

        self.scope_caption.text = _bind(lambda _o: _tr('Scope'), yielding=True)    # find_dialog.nml:80
        self.scope_caption.link = _bind(lambda _o: self.scope)    # find_dialog.nml:81
        self.scope_caption.x = 3    # find_dialog.nml:82
        self.scope_caption.width = 24    # find_dialog.nml:83
        self.scope_caption.y = _bind(    # find_dialog.nml:85
            lambda _o: self.options.y + self.options.height + 1
        )

        self.scope.x = 3    # find_dialog.nml:89
        self.scope.width = 24    # find_dialog.nml:90
        self.scope.height = 2    # find_dialog.nml:91
        self.scope.items = _bind(    # find_dialog.nml:92
            lambda _o: [_tr('~G~lobal'), _tr('~S~elected text')],
            yielding=True,
        )
        self.scope.y = _bind(    # find_dialog.nml:94
            lambda _o: self.scope_caption.y + self.scope_caption.height
        )

        self.origin_caption.text = _bind(    # find_dialog.nml:98
            lambda _o: _tr('Origin'),
            yielding=True,
        )
        self.origin_caption.link = _bind(lambda _o: self.origin)    # find_dialog.nml:99
        self.origin_caption.x = 30    # find_dialog.nml:100
        self.origin_caption.width = 22    # find_dialog.nml:101
        self.origin_caption.y = _bind(    # find_dialog.nml:103
            lambda _o: self.options.y + self.options.height + 1
        )

        self.origin.x = 30    # find_dialog.nml:107
        self.origin.width = 22    # find_dialog.nml:108
        self.origin.height = 2    # find_dialog.nml:109
        self.origin.items = _bind(    # find_dialog.nml:110
            lambda _o: [_tr('~E~ntire scope'), _tr('~F~rom cursor')],
            yielding=True,
        )
        self.origin.y = _bind(    # find_dialog.nml:112
            lambda _o: self.origin_caption.y + self.origin_caption.height
        )

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # find_dialog.nml:116
        self.pick.default = True    # find_dialog.nml:117
        self.pick.width = 10    # find_dialog.nml:118
        self.pick.height = 2    # find_dialog.nml:119
        self.pick.x = _bind(    # find_dialog.nml:121
            lambda _o: max(0, (self.all.x if self.all.visible and self.all.width else self.rest_row.x) - _o.width)
        )
        self.pick.y = _bind(lambda _o: self.scope.y + self.scope.height + 1)    # find_dialog.nml:122
        self.pick.on_click = self.on_pick_click    # find_dialog.nml:115

        self.all.text = _bind(lambda _o: _tr('Change ~a~ll'), yielding=True)    # find_dialog.nml:127
        self.all.visible = _bind(lambda _o: self.replace)    # find_dialog.nml:128
        self.all.x = 16    # find_dialog.nml:129
        self.all.width = 16    # find_dialog.nml:130
        self.all.height = 2    # find_dialog.nml:131
        self.all.y = _bind(lambda _o: self.scope.y + self.scope.height + 1)    # find_dialog.nml:133
        self.all.on_click = self.on_all_click    # find_dialog.nml:126

        self.rest_row.justify = 'start'    # find_dialog.nml:137
        self.rest_row.button_width = 10    # find_dialog.nml:138
        self.rest_row.spacing = 0    # find_dialog.nml:139
        self.rest_row.x = 32    # find_dialog.nml:141
        self.rest_row.width = _bind(lambda _o: max(0, _o.parent.width - 32))    # find_dialog.nml:142
        self.rest_row.y = _bind(    # find_dialog.nml:143
            lambda _o: self.scope.y + self.scope.height + 1
        )

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # find_dialog.nml:147
        self.abandon.on_click = self.on_abandon_click    # find_dialog.nml:146

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # find_dialog.nml:152
        self.helper.disabled = True    # find_dialog.nml:153
        self.helper.on_click = self.on_helper_click    # find_dialog.nml:151
