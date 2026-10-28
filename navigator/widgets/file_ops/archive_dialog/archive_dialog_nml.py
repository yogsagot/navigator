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
from navml.widgets.dialog.check_boxes import CheckBoxes    # archive_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # archive_dialog.nml:4
from navml.widgets.dialog.field import Field    # archive_dialog.nml:5
from navml.widgets.dialog.label import Label    # archive_dialog.nml:6
from navml.widgets.dialog.radio_buttons import RadioButtons    # archive_dialog.nml:7
from navml.widgets.dialog.static_text import StaticText    # archive_dialog.nml:8

__navml_component__ = "ArchiveDialog"

__all__ = ["ArchiveDialog"]


class ArchiveDialog(Dialog, _Component):
    """File > *Create archive...* (Shift+F1): DOS Navigator's ``dlgArchiveFiles``,

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
    keys = {    # archive_dialog.nml:28
        'f10': ChooseTarget,    # archive_dialog.nml:29
    }

    #: Ids, annotated so the hand-written half completes them.
    target_caption: Label    # archive_dialog.nml:32
    target: Field    # archive_dialog.nml:42
    kind_caption: Label    # archive_dialog.nml:52
    kind: RadioButtons    # archive_dialog.nml:62
    level_caption: Label    # archive_dialog.nml:70
    level: RadioButtons    # archive_dialog.nml:80
    password_caption: Label    # archive_dialog.nml:88
    password: Field    # archive_dialog.nml:97
    options: CheckBoxes    # archive_dialog.nml:106
    note: StaticText    # archive_dialog.nml:116
    pick: Button    # archive_dialog.nml:123
    abandon: Button    # archive_dialog.nml:132
    tree: Button    # archive_dialog.nml:140
    help: Button    # archive_dialog.nml:149

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # archive_dialog.nml:123
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # archive_dialog.nml:132
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_tree_click(self, event: _Event) -> bool:    # archive_dialog.nml:140
        """``tree`` raised an event whose handler is ``on_click``."""
        return False

    async def on_help_click(self, event: _Event) -> bool:    # archive_dialog.nml:149
        """``help`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.target_caption = Label(parent=self)    # archive_dialog.nml:31
        self.target = Field(parent=self)    # archive_dialog.nml:41
        self.kind_caption = Label(parent=self)    # archive_dialog.nml:51
        self.kind = RadioButtons(parent=self)    # archive_dialog.nml:61
        self.level_caption = Label(parent=self)    # archive_dialog.nml:69
        self.level = RadioButtons(parent=self)    # archive_dialog.nml:79
        self.password_caption = Label(parent=self)    # archive_dialog.nml:87
        self.password = Field(parent=self)    # archive_dialog.nml:96
        self.options = CheckBoxes(parent=self)    # archive_dialog.nml:105
        self.note = StaticText(parent=self)    # archive_dialog.nml:115
        self.pick = Button(parent=self)    # archive_dialog.nml:122
        self.abandon = Button(parent=self)    # archive_dialog.nml:131
        self.tree = Button(parent=self)    # archive_dialog.nml:139
        self.help = Button(parent=self)    # archive_dialog.nml:148

        self.modal_width = 64    # archive_dialog.nml:23
        self.modal_height = 18    # archive_dialog.nml:24
        self.title = _bind(lambda _o: _tr('Create archive'), yielding=True)    # archive_dialog.nml:25

        self.target_caption.x = 2    # archive_dialog.nml:33
        self.target_caption.y = 1    # archive_dialog.nml:34
        self.target_caption.width = 20    # archive_dialog.nml:35
        self.target_caption.height = 1    # archive_dialog.nml:36
        self.target_caption.text = _bind(    # archive_dialog.nml:37
            lambda _o: _tr('Archiv~e~ to'),
            yielding=True,
        )
        self.target_caption.link = _bind(lambda _o: self.target.entry)    # archive_dialog.nml:38

        self.target.x = 2    # archive_dialog.nml:43
        self.target.y = 2    # archive_dialog.nml:44
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # archive_dialog.nml:45
        self.target.height = 1    # archive_dialog.nml:46
        self.target.label_text = ''    # archive_dialog.nml:47
        self.target.label_width = 0    # archive_dialog.nml:48
        self.target.history_id = 'copy'    # archive_dialog.nml:49

        self.kind_caption.x = 2    # archive_dialog.nml:53
        self.kind_caption.y = 4    # archive_dialog.nml:54
        self.kind_caption.width = 16    # archive_dialog.nml:55
        self.kind_caption.height = 1    # archive_dialog.nml:56
        self.kind_caption.text = _bind(    # archive_dialog.nml:57
            lambda _o: _tr('Archive type'),
            yielding=True,
        )
        self.kind_caption.link = _bind(lambda _o: self.kind)    # archive_dialog.nml:58

        self.kind.x = 3    # archive_dialog.nml:63
        self.kind.y = 5    # archive_dialog.nml:64
        self.kind.width = 16    # archive_dialog.nml:65
        self.kind.height = 8    # archive_dialog.nml:66
        self.kind.items = _bind(    # archive_dialog.nml:67
            lambda _o: [_tr('~Z~IP'), _tr('~7~Z'), _tr('T~A~R'), _tr('TAR.~G~Z'), _tr('TAR.~B~Z2'), _tr('TAR.~X~Z'), _tr('TAR.Z~S~T'), _tr('~R~AR')],
            yielding=True,
        )

        self.level_caption.x = 21    # archive_dialog.nml:71
        self.level_caption.y = 4    # archive_dialog.nml:72
        self.level_caption.width = 16    # archive_dialog.nml:73
        self.level_caption.height = 1    # archive_dialog.nml:74
        self.level_caption.text = _bind(    # archive_dialog.nml:75
            lambda _o: _tr('Compression'),
            yielding=True,
        )
        self.level_caption.link = _bind(lambda _o: self.level)    # archive_dialog.nml:76

        self.level.x = 22    # archive_dialog.nml:81
        self.level.y = 5    # archive_dialog.nml:82
        self.level.width = 15    # archive_dialog.nml:83
        self.level.height = 5    # archive_dialog.nml:84
        self.level.items = _bind(    # archive_dialog.nml:85
            lambda _o: [_tr('N~o~ne'), _tr('~F~astest'), _tr('Nor~m~al'), _tr('Max~i~mum'), _tr('~U~ltra')],
            yielding=True,
        )

        self.password_caption.x = 39    # archive_dialog.nml:89
        self.password_caption.y = 4    # archive_dialog.nml:90
        self.password_caption.width = 20    # archive_dialog.nml:91
        self.password_caption.height = 1    # archive_dialog.nml:92
        self.password_caption.text = _bind(    # archive_dialog.nml:93
            lambda _o: _tr('Pass~w~ord'),
            yielding=True,
        )
        self.password_caption.link = _bind(lambda _o: self.password.entry)    # archive_dialog.nml:94

        self.password.x = 39    # archive_dialog.nml:98
        self.password.y = 5    # archive_dialog.nml:99
        self.password.width = _bind(lambda _o: max(0, _o.parent.width - 41))    # archive_dialog.nml:100
        self.password.height = 1    # archive_dialog.nml:101
        self.password.label_text = ''    # archive_dialog.nml:102
        self.password.label_width = 0    # archive_dialog.nml:103

        self.options.x = 40    # archive_dialog.nml:107
        self.options.y = 7    # archive_dialog.nml:108
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 42))    # archive_dialog.nml:109
        self.options.height = 3    # archive_dialog.nml:110
        self.options.items = _bind(    # archive_dialog.nml:111
            lambda _o: [_tr('Store path~n~ames'), _tr('Mo~v~e files'), _tr('Follow s~y~mlinks')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # archive_dialog.nml:112
            lambda _o: [_tr("Keep each file's directories inside the archive, not its name alone"), _tr('Delete the files once they are in the archive'), _tr('Pack what a link points to, not the link itself')],
            yielding=True,
        )

        self.note.x = 2    # archive_dialog.nml:117
        self.note.y = 13    # archive_dialog.nml:118
        self.note.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # archive_dialog.nml:119
        self.note.height = 1    # archive_dialog.nml:120

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # archive_dialog.nml:124
        self.pick.default = True    # archive_dialog.nml:125
        self.pick.x = 6    # archive_dialog.nml:126
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # archive_dialog.nml:127
        self.pick.width = 11    # archive_dialog.nml:128
        self.pick.height = 2    # archive_dialog.nml:129
        self.pick.on_click = self.on_pick_click    # archive_dialog.nml:123

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # archive_dialog.nml:133
        self.abandon.x = 19    # archive_dialog.nml:134
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # archive_dialog.nml:135
        self.abandon.width = 11    # archive_dialog.nml:136
        self.abandon.height = 2    # archive_dialog.nml:137
        self.abandon.on_click = self.on_abandon_click    # archive_dialog.nml:132

        self.tree.text = _bind(lambda _o: _tr('~T~ree'), yielding=True)    # archive_dialog.nml:141
        self.tree.x = 32    # archive_dialog.nml:142
        self.tree.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # archive_dialog.nml:143
        self.tree.width = 11    # archive_dialog.nml:144
        self.tree.height = 2    # archive_dialog.nml:145
        self.tree.on_click = self.on_tree_click    # archive_dialog.nml:140

        self.help.text = _bind(lambda _o: _tr('Help'), yielding=True)    # archive_dialog.nml:150
        self.help.disabled = True    # archive_dialog.nml:151
        self.help.x = 45    # archive_dialog.nml:152
        self.help.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # archive_dialog.nml:153
        self.help.width = 11    # archive_dialog.nml:154
        self.help.height = 2    # archive_dialog.nml:155
        self.help.on_click = self.on_help_click    # archive_dialog.nml:149
