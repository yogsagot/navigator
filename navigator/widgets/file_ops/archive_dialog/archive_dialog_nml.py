# navml: generated
"""Generated from ``archive_dialog.nml``.

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
from navigator.widgets.file_ops.commands import ChooseTarget    # archive_dialog.nml:1
from navml.widgets.dialog.button import Button    # archive_dialog.nml:2
from navml.widgets.dialog.button_row import ButtonRow    # archive_dialog.nml:3
from navml.widgets.dialog.check_boxes import CheckBoxes    # archive_dialog.nml:4
from navml.widgets.dialog.dialog import Dialog    # archive_dialog.nml:5
from navml.widgets.dialog.field import Field    # archive_dialog.nml:6
from navml.widgets.dialog.label import Label    # archive_dialog.nml:7
from navml.widgets.dialog.radio_buttons import RadioButtons    # archive_dialog.nml:8
from navml.widgets.dialog.static_text import StaticText    # archive_dialog.nml:9

__navml_component__ = "ArchiveDialog"

__all__ = ["ArchiveDialog"]


class ArchiveDialog(Dialog, _Component):
    """File > Archive > *Create archive...* (Shift+F1): DOS Navigator's ``dlgArchiveFiles``,

    64 by 18 as the resource had it.

    Laid out where DN put things: the name on the second row, *Password* under
    it on the right, *Archive type* down the left, *Compression* beside it, and
    OK / Cancel / Tree / Help along the bottom.  Departures, each because
    Navigator packs no archive through a DOS archiver of the user's choosing:
    the archive types are today's (DN's were ARC, ARJ, ... RAR ... ZOO; RAR the one kept), *Compression*
    has *Store* and *Ultra* either side of DN's Normal/Faster/Maximum, and
    *Additional options* (the archiver's own switches) and *Force mode* are
    left out.  *Follow symlinks* is F5's, added.  The row above the buttons
    says which types are greyed for want of a tool.
    """

    #: The document this class was generated from.
    __navml_source__ = "archive_dialog.nml"

    #: ``StatusDef hcArchiveFiles``' ``F10 Tree``, as Copy's.
    keys = {    # archive_dialog.nml:30
        'f10': ChooseTarget,    # archive_dialog.nml:31
    }

    #: Ids, annotated so the hand-written half completes them.
    target_caption: Label    # archive_dialog.nml:40
    target: Field    # archive_dialog.nml:49
    kind_caption: Label    # archive_dialog.nml:59
    kind: RadioButtons    # archive_dialog.nml:68
    level_caption: Label    # archive_dialog.nml:76
    level: RadioButtons    # archive_dialog.nml:85
    password_caption: Label    # archive_dialog.nml:93
    password: Field    # archive_dialog.nml:101
    options: CheckBoxes    # archive_dialog.nml:110
    note: StaticText    # archive_dialog.nml:121
    pick: Button    # archive_dialog.nml:135
    abandon: Button    # archive_dialog.nml:141
    tree: Button    # archive_dialog.nml:145
    help: Button    # archive_dialog.nml:151

    #: The commands this component handles itself.
    async def on_choose_target(self, event: _Any) -> bool:    # archive_dialog.nml:35
        """``ChooseTarget``."""
        self.spawn(self.choose_target())
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_abandon_click(self, event: _Event) -> bool:    # archive_dialog.nml:141
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_help_click(self, event: _Event) -> bool:    # archive_dialog.nml:151
        """``help`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.target_caption = Label(parent=self)    # archive_dialog.nml:39
        self.target = Field(parent=self)    # archive_dialog.nml:48
        self.kind_caption = Label(parent=self)    # archive_dialog.nml:58
        self.kind = RadioButtons(parent=self)    # archive_dialog.nml:67
        self.level_caption = Label(parent=self)    # archive_dialog.nml:75
        self.level = RadioButtons(parent=self)    # archive_dialog.nml:84
        self.password_caption = Label(parent=self)    # archive_dialog.nml:92
        self.password = Field(parent=self)    # archive_dialog.nml:100
        self.options = CheckBoxes(parent=self)    # archive_dialog.nml:109
        self.note = StaticText(parent=self)    # archive_dialog.nml:120
        _w1 = ButtonRow(parent=self)    # archive_dialog.nml:127
        self.pick = Button(parent=_w1)    # archive_dialog.nml:134
        self.abandon = Button(parent=_w1)    # archive_dialog.nml:140
        self.tree = Button(parent=_w1)    # archive_dialog.nml:144
        self.help = Button(parent=_w1)    # archive_dialog.nml:150

        self.modal_width = 64    # archive_dialog.nml:24
        self.modal_height = 18    # archive_dialog.nml:25
        self.title = _bind(lambda _o: _tr('Create archive'), yielding=True)    # archive_dialog.nml:26
        self.buttons = 'none'    # archive_dialog.nml:27
        self.buttons_row = _bind(    # archive_dialog.nml:37
            lambda _o: (self.pick, self.abandon, self.tree, self.help)
        )

        self.target_caption.x = 2    # archive_dialog.nml:41
        self.target_caption.y = 1    # archive_dialog.nml:42
        self.target_caption.width = 20    # archive_dialog.nml:43
        self.target_caption.text = _bind(    # archive_dialog.nml:44
            lambda _o: _tr('Archiv~e~ to'),
            yielding=True,
        )
        self.target_caption.link = _bind(lambda _o: self.target.entry)    # archive_dialog.nml:45

        self.target.y = 2    # archive_dialog.nml:50
        self.target.label_text = ''    # archive_dialog.nml:54
        self.target.label_width = 0    # archive_dialog.nml:55
        self.target.history_id = 'copy'    # archive_dialog.nml:56
        self.target.x = 2    # archive_dialog.nml:52
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # archive_dialog.nml:53

        self.kind_caption.x = 2    # archive_dialog.nml:60
        self.kind_caption.y = 4    # archive_dialog.nml:61
        self.kind_caption.width = 16    # archive_dialog.nml:62
        self.kind_caption.text = _bind(    # archive_dialog.nml:63
            lambda _o: _tr('Archive type'),
            yielding=True,
        )
        self.kind_caption.link = _bind(lambda _o: self.kind)    # archive_dialog.nml:64

        self.kind.x = 3    # archive_dialog.nml:69
        self.kind.y = 5    # archive_dialog.nml:70
        self.kind.width = 16    # archive_dialog.nml:71
        self.kind.height = 8    # archive_dialog.nml:72
        self.kind.items = _bind(    # archive_dialog.nml:73
            lambda _o: [_tr('~Z~IP'), _tr('~7~Z'), _tr('T~A~R'), _tr('TAR.~G~Z'), _tr('TAR.~B~Z2'), _tr('TAR.~X~Z'), _tr('TAR.Z~S~T'), _tr('~R~AR')],
            yielding=True,
        )

        self.level_caption.x = 21    # archive_dialog.nml:77
        self.level_caption.y = 4    # archive_dialog.nml:78
        self.level_caption.width = 16    # archive_dialog.nml:79
        self.level_caption.text = _bind(    # archive_dialog.nml:80
            lambda _o: _tr('Compression'),
            yielding=True,
        )
        self.level_caption.link = _bind(lambda _o: self.level)    # archive_dialog.nml:81

        self.level.x = 22    # archive_dialog.nml:86
        self.level.y = 5    # archive_dialog.nml:87
        self.level.width = 15    # archive_dialog.nml:88
        self.level.height = 5    # archive_dialog.nml:89
        self.level.items = _bind(    # archive_dialog.nml:90
            lambda _o: [_tr('N~o~ne'), _tr('~F~astest'), _tr('Nor~m~al'), _tr('Max~i~mum'), _tr('~U~ltra')],
            yielding=True,
        )

        self.password_caption.x = 39    # archive_dialog.nml:94
        self.password_caption.y = 4    # archive_dialog.nml:95
        self.password_caption.width = 20    # archive_dialog.nml:96
        self.password_caption.text = _bind(    # archive_dialog.nml:97
            lambda _o: _tr('Pass~w~ord'),
            yielding=True,
        )
        self.password_caption.link = _bind(lambda _o: self.password.entry)    # archive_dialog.nml:98

        self.password.y = 5    # archive_dialog.nml:102
        self.password.label_text = ''    # archive_dialog.nml:106
        self.password.label_width = 0    # archive_dialog.nml:107
        self.password.x = 39    # archive_dialog.nml:104
        self.password.width = _bind(lambda _o: max(0, _o.parent.width - 41))    # archive_dialog.nml:105

        self.options.y = 7    # archive_dialog.nml:111
        self.options.height = 3    # archive_dialog.nml:112
        self.options.items = _bind(    # archive_dialog.nml:116
            lambda _o: [_tr('Store path~n~ames'), _tr('Mo~v~e files'), _tr('Follow s~y~mlinks')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # archive_dialog.nml:117
            lambda _o: [_tr("Keep each file's directories inside the archive, not its name alone"), _tr('Delete the files once they are in the archive'), _tr('Pack what a link points to, not the link itself')],
            yielding=True,
        )
        self.options.x = 40    # archive_dialog.nml:114
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 42))    # archive_dialog.nml:115

        self.note.y = 13    # archive_dialog.nml:122
        self.note.x = 2    # archive_dialog.nml:124
        self.note.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # archive_dialog.nml:125

        _w1.justify = 'start'    # archive_dialog.nml:128
        _w1.x = 6# archive_dialog.nml:130
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # archive_dialog.nml:131
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # archive_dialog.nml:132

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # archive_dialog.nml:136
        self.pick.default = True    # archive_dialog.nml:137

        async def _on_click(event):    # archive_dialog.nml:138
            self.spawn(self.confirm())
            return True
        self.pick.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # archive_dialog.nml:142
        self.abandon.on_click = self.on_abandon_click    # archive_dialog.nml:141

        self.tree.text = _bind(lambda _o: _tr('~T~ree'), yielding=True)    # archive_dialog.nml:146

        async def _on_click(event):    # archive_dialog.nml:147
            self.spawn(self.choose_target())
            return True
        self.tree.on_click = _on_click

        self.help.text = _bind(lambda _o: _tr('Help'), yielding=True)    # archive_dialog.nml:152
        self.help.disabled = True    # archive_dialog.nml:153
        self.help.on_click = self.on_help_click    # archive_dialog.nml:151

        self._navml_built(__class__)
