# navml: generated
"""Generated from ``attr_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # attr_dialog.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # attr_dialog.nml:2
from navml.widgets.dialog.choice_field import ChoiceField    # attr_dialog.nml:3
from navml.widgets.dialog.date_field import DateField    # attr_dialog.nml:4
from navml.widgets.dialog.dialog import Dialog    # attr_dialog.nml:5
from navml.widgets.dialog.label import Label    # attr_dialog.nml:6
from navml.widgets.dialog.list_viewer import ListViewer    # attr_dialog.nml:7
from navml.widgets.dialog.masked_field import MaskedField    # attr_dialog.nml:8
from navml.widgets.dialog.radio_buttons import RadioButtons    # attr_dialog.nml:9
from navml.widgets.dialog.static_text import StaticText    # attr_dialog.nml:10
from navml.widgets.dialog.tab_page import TabPage    # attr_dialog.nml:11
from navml.widgets.dialog.tab_view import TabView    # attr_dialog.nml:12
from navml.widgets.dialog.time_field import TimeField    # attr_dialog.nml:13

__navml_component__ = "AttrDialog"

__all__ = ["AttrDialog"]


class AttrDialog(Dialog, _Component):
    """Alt+E: *File Attributes*, DOS Navigator's ``dlgFilesAttr`` read for Linux.

    A departure in what it edits -- DN's four DOS bits are the twelve mode bits,
    and the owner and group stand beside DN's date and time -- and DN's in its
    shape: one dialog over every tagged file, where a bit the files disagree on
    is ``[?]`` and left alone unless moved.  The grid is one ``CheckBoxes`` of
    twelve, three tall, which ``Cluster`` lays out in four columns of three:
    owner, group, others and the special bits, each read/write/execute down.

    Behind tabs (a departure on a departure, asked for): *Mode* is all of the
    above, and *ACL*, *Xattrs* and *Flags* are the POSIX ACL, the extended
    attributes and ``chattr``'s inode flags.  The pages are ``TabPage``s in
    this document, so every id is the dialog's whichever page it is on.  What
    the selection is, and *Recurse*, which every page's change obeys, stand
    outside them.  The tabs are simple ones, bare captions over a rule, a row
    less than boxed tabs.
    """

    #: The document this class was generated from.
    __navml_source__ = "attr_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    name_row: StaticText    # attr_dialog.nml:41
    info_row: StaticText    # attr_dialog.nml:49
    tabs: TabView    # attr_dialog.nml:58
    mode_page: TabPage    # attr_dialog.nml:75
    heading: Label    # attr_dialog.nml:82
    bits: CheckBoxes    # attr_dialog.nml:108
    octal: MaskedField    # attr_dialog.nml:120
    symbolic: StaticText    # attr_dialog.nml:131
    user: ChoiceField    # attr_dialog.nml:139
    group: ChoiceField    # attr_dialog.nml:148
    date: DateField    # attr_dialog.nml:164
    clock: TimeField    # attr_dialog.nml:173
    acl_page: TabPage    # attr_dialog.nml:184
    acl_caption: Label    # attr_dialog.nml:188
    acl_list: ListViewer    # attr_dialog.nml:196
    acl_add: Button    # attr_dialog.nml:204
    acl_edit: Button    # attr_dialog.nml:214
    acl_delete: Button    # attr_dialog.nml:224
    acl_clear: Button    # attr_dialog.nml:235
    acl_note: StaticText    # attr_dialog.nml:245
    xattr_page: TabPage    # attr_dialog.nml:252
    xattr_caption: Label    # attr_dialog.nml:256
    xattr_list: ListViewer    # attr_dialog.nml:264
    xattr_add: Button    # attr_dialog.nml:272
    xattr_edit: Button    # attr_dialog.nml:282
    xattr_delete: Button    # attr_dialog.nml:292
    xattr_note: StaticText    # attr_dialog.nml:302
    flags_page: TabPage    # attr_dialog.nml:311
    flags_caption: Label    # attr_dialog.nml:315
    flags: CheckBoxes    # attr_dialog.nml:323
    lsattr: StaticText    # attr_dialog.nml:333
    flags_note: StaticText    # attr_dialog.nml:340
    recurse_caption: Label    # attr_dialog.nml:349
    recurse: RadioButtons    # attr_dialog.nml:357
    root_button: Button    # attr_dialog.nml:371

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_acl_clear_click(self, event: _Event) -> bool:    # attr_dialog.nml:235
        """``acl_clear`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.name_row = StaticText(parent=self)    # attr_dialog.nml:40
        self.info_row = StaticText(parent=self)    # attr_dialog.nml:48
        self.tabs = TabView(parent=self)    # attr_dialog.nml:57
        self.mode_page = TabPage(parent=self.tabs)    # attr_dialog.nml:74
        self.heading = Label(parent=self.mode_page)    # attr_dialog.nml:81
        _w1 = Label(parent=self.mode_page)    # attr_dialog.nml:89
        _w2 = Label(parent=self.mode_page)    # attr_dialog.nml:95
        _w3 = Label(parent=self.mode_page)    # attr_dialog.nml:101
        self.bits = CheckBoxes(parent=self.mode_page)    # attr_dialog.nml:107
        self.octal = MaskedField(parent=self.mode_page)    # attr_dialog.nml:119
        self.symbolic = StaticText(parent=self.mode_page)    # attr_dialog.nml:130
        self.user = ChoiceField(parent=self.mode_page)    # attr_dialog.nml:138
        self.group = ChoiceField(parent=self.mode_page)    # attr_dialog.nml:147
        self.date = DateField(parent=self.mode_page)    # attr_dialog.nml:163
        self.clock = TimeField(parent=self.mode_page)    # attr_dialog.nml:172
        self.acl_page = TabPage(parent=self.tabs)    # attr_dialog.nml:183
        self.acl_caption = Label(parent=self.acl_page)    # attr_dialog.nml:187
        self.acl_list = ListViewer(parent=self.acl_page)    # attr_dialog.nml:195
        self.acl_add = Button(parent=self.acl_page)    # attr_dialog.nml:203
        self.acl_edit = Button(parent=self.acl_page)    # attr_dialog.nml:213
        self.acl_delete = Button(parent=self.acl_page)    # attr_dialog.nml:223
        self.acl_clear = Button(parent=self.acl_page)    # attr_dialog.nml:234
        self.acl_note = StaticText(parent=self.acl_page)    # attr_dialog.nml:244
        self.xattr_page = TabPage(parent=self.tabs)    # attr_dialog.nml:251
        self.xattr_caption = Label(parent=self.xattr_page)    # attr_dialog.nml:255
        self.xattr_list = ListViewer(parent=self.xattr_page)    # attr_dialog.nml:263
        self.xattr_add = Button(parent=self.xattr_page)    # attr_dialog.nml:271
        self.xattr_edit = Button(parent=self.xattr_page)    # attr_dialog.nml:281
        self.xattr_delete = Button(parent=self.xattr_page)    # attr_dialog.nml:291
        self.xattr_note = StaticText(parent=self.xattr_page)    # attr_dialog.nml:301
        self.flags_page = TabPage(parent=self.tabs)    # attr_dialog.nml:310
        self.flags_caption = Label(parent=self.flags_page)    # attr_dialog.nml:314
        self.flags = CheckBoxes(parent=self.flags_page)    # attr_dialog.nml:322
        self.lsattr = StaticText(parent=self.flags_page)    # attr_dialog.nml:332
        self.flags_note = StaticText(parent=self.flags_page)    # attr_dialog.nml:339
        self.recurse_caption = Label(parent=self)    # attr_dialog.nml:348
        self.recurse = RadioButtons(parent=self)    # attr_dialog.nml:356
        self.root_button = Button(parent=self)    # attr_dialog.nml:370

        self.modal_width = 64    # attr_dialog.nml:32
        self.modal_height = 21    # attr_dialog.nml:33
        self.title = _bind(lambda _o: _tr('File Attributes'), yielding=True)    # attr_dialog.nml:34
        self.buttons = 'ok-cancel'    # attr_dialog.nml:35
        self.buttons_row = _bind(    # attr_dialog.nml:37
            lambda _o: (self.ok, self.root_button, self.no, self.cancel, self.info)
        )

        self.name_row.y = 1    # attr_dialog.nml:42
        self.name_row.x = 2    # attr_dialog.nml:44
        self.name_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:45

        self.info_row.y = 2    # attr_dialog.nml:50
        self.info_row.x = 2    # attr_dialog.nml:52
        self.info_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:53

        self.tabs.tooltips = _bind(    # attr_dialog.nml:60
            lambda _o: [_tr('Permissions, owner, group and modification time'), _tr('Access control list: permissions for particular users and groups'), _tr('Extended attributes: names and values kept with the file'), _tr('File system flags, such as immutable and append-only')],
            yielding=True,
        )
        self.tabs.y = 3    # attr_dialog.nml:66
        self.tabs.height = 12    # attr_dialog.nml:67
        self.tabs.side = 'simple'    # attr_dialog.nml:71
        self.tabs.joins_frame = True    # attr_dialog.nml:72
        self.tabs.x = 0    # attr_dialog.nml:69
        self.tabs.width = _bind(lambda _o: max(0, _o.parent.width))    # attr_dialog.nml:70

        self.mode_page.title = _bind(lambda _o: _tr('Mode'), yielding=True)    # attr_dialog.nml:76

        self.heading.x = 3    # attr_dialog.nml:83
        self.heading.y = 1    # attr_dialog.nml:84
        self.heading.width = _bind(    # attr_dialog.nml:85
            lambda _o: max(1, self.bits.column_x(1) - self.bits.column_x(0))
        )
        self.heading.text = _bind(lambda _o: _tr('O~w~ner'), yielding=True)    # attr_dialog.nml:86
        self.heading.link = _bind(lambda _o: self.bits)    # attr_dialog.nml:87

        _w1.x = _bind(lambda _o: 3 + self.bits.column_x(1))    # attr_dialog.nml:90
        _w1.y = 1# attr_dialog.nml:91
        _w1.width = _bind(    # attr_dialog.nml:92
            lambda _o: max(1, self.bits.column_x(2) - self.bits.column_x(1))
        )
        _w1.text = _bind(lambda _o: _tr('Group'), yielding=True)    # attr_dialog.nml:93

        _w2.x = _bind(lambda _o: 3 + self.bits.column_x(2))    # attr_dialog.nml:96
        _w2.y = 1# attr_dialog.nml:97
        _w2.width = _bind(    # attr_dialog.nml:98
            lambda _o: max(1, self.bits.column_x(3) - self.bits.column_x(2))
        )
        _w2.text = _bind(lambda _o: _tr('Others'), yielding=True)    # attr_dialog.nml:99

        _w3.x = _bind(lambda _o: 3 + self.bits.column_x(3))    # attr_dialog.nml:102
        _w3.y = 1# attr_dialog.nml:103
        _w3.width = _bind(    # attr_dialog.nml:104
            lambda _o: max(1, _o.parent.width - 6 - self.bits.column_x(3))
        )
        _w3.text = _bind(lambda _o: _tr('Special'), yielding=True)    # attr_dialog.nml:105

        self.bits.y = 2    # attr_dialog.nml:109
        self.bits.height = 3    # attr_dialog.nml:110
        self.bits.items = _bind(    # attr_dialog.nml:114
            lambda _o: [_tr('Read'), _tr('Write'), _tr('Exec'), _tr('Read'), _tr('Write'), _tr('Exec'), _tr('Read'), _tr('Write'), _tr('Exec'), _tr('Set UID'), _tr('Set GID'), _tr('Sticky')],
            yielding=True,
        )
        self.bits.tooltips = _bind(    # attr_dialog.nml:115
            lambda _o: ['', '', '', '', '', '', '', '', '', _tr("Run with the file owner's rights"), _tr("Run with the group's rights; in a directory, new files take its group"), _tr("In a directory, only a file's owner may delete or rename it")],
            yielding=True,
        )
        self.bits.x = 3    # attr_dialog.nml:112
        self.bits.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:113

        self.octal.x = 2    # attr_dialog.nml:121
        self.octal.y = 6    # attr_dialog.nml:122
        self.octal.width = 17    # attr_dialog.nml:123
        self.octal.label_text = _bind(lambda _o: _tr('~O~ctal'), yielding=True)    # attr_dialog.nml:124
        self.octal.label_width = 11    # attr_dialog.nml:125
        self.octal.mask = '9999'    # attr_dialog.nml:126
        self.octal.base = 8    # attr_dialog.nml:127

        self.symbolic.x = 20    # attr_dialog.nml:132
        self.symbolic.y = 6    # attr_dialog.nml:133
        self.symbolic.width = 12    # attr_dialog.nml:134

        self.user.y = 7    # attr_dialog.nml:140
        self.user.label_text = _bind(lambda _o: _tr('~U~ser'), yielding=True)    # attr_dialog.nml:144
        self.user.label_width = 11    # attr_dialog.nml:145
        self.user.x = 2    # attr_dialog.nml:142
        self.user.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:143

        self.group.y = 8    # attr_dialog.nml:149
        self.group.label_text = _bind(lambda _o: _tr('~G~roup'), yielding=True)    # attr_dialog.nml:153
        self.group.label_width = 11    # attr_dialog.nml:154
        self.group.x = 2    # attr_dialog.nml:151
        self.group.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:152

        self.date.x = 2    # attr_dialog.nml:165
        self.date.y = 9    # attr_dialog.nml:166
        self.date.width = 27    # attr_dialog.nml:167
        self.date.height = 1    # attr_dialog.nml:168
        self.date.label_text = _bind(lambda _o: _tr('~D~ate'), yielding=True)    # attr_dialog.nml:169
        self.date.label_width = 11    # attr_dialog.nml:170

        self.clock.x = 30    # attr_dialog.nml:174
        self.clock.y = 9    # attr_dialog.nml:175
        self.clock.width = 23    # attr_dialog.nml:176
        self.clock.height = 1    # attr_dialog.nml:177
        self.clock.label_text = _bind(lambda _o: _tr('~T~ime'), yielding=True)    # attr_dialog.nml:178
        self.clock.label_width = 7    # attr_dialog.nml:179

        self.acl_page.title = _bind(lambda _o: _tr('ACL'), yielding=True)    # attr_dialog.nml:185

        self.acl_caption.x = 2    # attr_dialog.nml:189
        self.acl_caption.y = 1    # attr_dialog.nml:190
        self.acl_caption.width = 20    # attr_dialog.nml:191
        self.acl_caption.text = _bind(    # attr_dialog.nml:192
            lambda _o: _tr('E~n~tries'),
            yielding=True,
        )
        self.acl_caption.link = _bind(lambda _o: self.acl_list)    # attr_dialog.nml:193

        self.acl_list.y = 2    # attr_dialog.nml:197
        self.acl_list.height = 8    # attr_dialog.nml:198
        self.acl_list.x = 2    # attr_dialog.nml:200
        self.acl_list.width = _bind(lambda _o: max(0, _o.parent.width - 18))    # attr_dialog.nml:201

        self.acl_add.text = _bind(lambda _o: _tr('~A~dd'), yielding=True)    # attr_dialog.nml:205
        self.acl_add.y = 2    # attr_dialog.nml:206
        self.acl_add.width = 12    # attr_dialog.nml:207
        self.acl_add.height = 2    # attr_dialog.nml:208
        self.acl_add.x = _bind(    # attr_dialog.nml:210
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )

        async def _on_click(event):    # attr_dialog.nml:211
            self.spawn(self.add_acl_entry())
            return True
        self.acl_add.on_click = _on_click

        self.acl_edit.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # attr_dialog.nml:215
        self.acl_edit.y = 4    # attr_dialog.nml:216
        self.acl_edit.width = 12    # attr_dialog.nml:217
        self.acl_edit.height = 2    # attr_dialog.nml:218
        self.acl_edit.x = _bind(    # attr_dialog.nml:220
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )

        async def _on_click(event):    # attr_dialog.nml:221
            self.spawn(self.edit_acl_entry())
            return True
        self.acl_edit.on_click = _on_click

        self.acl_delete.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # attr_dialog.nml:225
        self.acl_delete.y = 6    # attr_dialog.nml:226
        self.acl_delete.width = 12    # attr_dialog.nml:227
        self.acl_delete.height = 2    # attr_dialog.nml:228
        self.acl_delete.x = _bind(    # attr_dialog.nml:230
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )

        async def _on_click(event):    # attr_dialog.nml:231
            self.delete_acl_entry()
            return True
        self.acl_delete.on_click = _on_click

        self.acl_clear.text = _bind(lambda _o: _tr('~C~lear'), yielding=True)    # attr_dialog.nml:236
        self.acl_clear.y = 8    # attr_dialog.nml:237
        self.acl_clear.width = 12    # attr_dialog.nml:238
        self.acl_clear.height = 2    # attr_dialog.nml:239
        self.acl_clear.x = _bind(    # attr_dialog.nml:241
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.acl_clear.on_click = self.on_acl_clear_click    # attr_dialog.nml:235

        self.acl_note.y = 10    # attr_dialog.nml:246
        self.acl_note.x = 2    # attr_dialog.nml:248
        self.acl_note.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:249

        self.xattr_page.title = _bind(lambda _o: _tr('Xattrs'), yielding=True)    # attr_dialog.nml:253

        self.xattr_caption.x = 2    # attr_dialog.nml:257
        self.xattr_caption.y = 1    # attr_dialog.nml:258
        self.xattr_caption.width = 20    # attr_dialog.nml:259
        self.xattr_caption.text = _bind(    # attr_dialog.nml:260
            lambda _o: _tr('Na~m~es'),
            yielding=True,
        )
        self.xattr_caption.link = _bind(lambda _o: self.xattr_list)    # attr_dialog.nml:261

        self.xattr_list.y = 2    # attr_dialog.nml:265
        self.xattr_list.height = 8    # attr_dialog.nml:266
        self.xattr_list.x = 2    # attr_dialog.nml:268
        self.xattr_list.width = _bind(lambda _o: max(0, _o.parent.width - 18))    # attr_dialog.nml:269

        self.xattr_add.text = _bind(lambda _o: _tr('~A~dd'), yielding=True)    # attr_dialog.nml:273
        self.xattr_add.y = 2    # attr_dialog.nml:274
        self.xattr_add.width = 12    # attr_dialog.nml:275
        self.xattr_add.height = 2    # attr_dialog.nml:276
        self.xattr_add.x = _bind(    # attr_dialog.nml:278
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )

        async def _on_click(event):    # attr_dialog.nml:279
            self.spawn(self.add_xattr())
            return True
        self.xattr_add.on_click = _on_click

        self.xattr_edit.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # attr_dialog.nml:283
        self.xattr_edit.y = 4    # attr_dialog.nml:284
        self.xattr_edit.width = 12    # attr_dialog.nml:285
        self.xattr_edit.height = 2    # attr_dialog.nml:286
        self.xattr_edit.x = _bind(    # attr_dialog.nml:288
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )

        async def _on_click(event):    # attr_dialog.nml:289
            self.spawn(self.edit_xattr())
            return True
        self.xattr_edit.on_click = _on_click

        self.xattr_delete.text = _bind(    # attr_dialog.nml:293
            lambda _o: _tr('~D~elete'),
            yielding=True,
        )
        self.xattr_delete.y = 6    # attr_dialog.nml:294
        self.xattr_delete.width = 12    # attr_dialog.nml:295
        self.xattr_delete.height = 2    # attr_dialog.nml:296
        self.xattr_delete.x = _bind(    # attr_dialog.nml:298
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )

        async def _on_click(event):    # attr_dialog.nml:299
            self.delete_xattr()
            return True
        self.xattr_delete.on_click = _on_click

        self.xattr_note.y = 10    # attr_dialog.nml:303
        self.xattr_note.x = 2    # attr_dialog.nml:305
        self.xattr_note.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:306

        self.flags_page.title = _bind(lambda _o: _tr('Flags'), yielding=True)    # attr_dialog.nml:312

        self.flags_caption.x = 3    # attr_dialog.nml:316
        self.flags_caption.y = 1    # attr_dialog.nml:317
        self.flags_caption.width = 20    # attr_dialog.nml:318
        self.flags_caption.text = _bind(    # attr_dialog.nml:319
            lambda _o: _tr('~F~lags'),
            yielding=True,
        )
        self.flags_caption.link = _bind(lambda _o: self.flags)    # attr_dialog.nml:320

        self.flags.y = 2    # attr_dialog.nml:324
        self.flags.height = 3    # attr_dialog.nml:325
        self.flags.items = _bind(    # attr_dialog.nml:329
            lambda _o: [_tr('Immutable'), _tr('Append'), _tr('No dump'), _tr('No atime'), _tr('Sync'), _tr('Dir sync'), _tr('No COW'), _tr('Compress'), _tr('Journal'), _tr('Top dir'), _tr('Secure rm'), _tr('Undelete')],
            yielding=True,
        )
        self.flags.tooltips = _bind(    # attr_dialog.nml:330
            lambda _o: [_tr('No one may change, rename or delete it, root included'), _tr('It can only be added to'), _tr('Left out of backups made with dump'), _tr('Its access time is never updated'), _tr('Its changes are written to the disk at once'), _tr('Changes to this directory are written to the disk at once'), _tr('Rewritten in place rather than copied on write (btrfs)'), _tr('Compressed by the file system'), _tr("Its data goes through the file system's journal"), _tr('The top of a directory tree, for where the file system places blocks'), _tr('Its blocks are cleared when it is deleted, where the file system can'), _tr('Its contents are kept when it is deleted, where the file system can')],
            yielding=True,
        )
        self.flags.x = 3    # attr_dialog.nml:327
        self.flags.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:328

        self.lsattr.y = 6    # attr_dialog.nml:334
        self.lsattr.x = 3    # attr_dialog.nml:336
        self.lsattr.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:337

        self.flags_note.y = 8    # attr_dialog.nml:341
        self.flags_note.x = 3    # attr_dialog.nml:343
        self.flags_note.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:344

        self.recurse_caption.x = 2    # attr_dialog.nml:350
        self.recurse_caption.y = 16    # attr_dialog.nml:351
        self.recurse_caption.width = 10    # attr_dialog.nml:352
        self.recurse_caption.text = _bind(    # attr_dialog.nml:353
            lambda _o: _tr('~R~ecurse'),
            yielding=True,
        )
        self.recurse_caption.link = _bind(lambda _o: self.recurse)    # attr_dialog.nml:354

        self.recurse.y = 16    # attr_dialog.nml:358
        self.recurse.height = 1    # attr_dialog.nml:359
        self.recurse.items = _bind(    # attr_dialog.nml:363
            lambda _o: [_tr('No'), _tr('Files'), _tr('Dirs'), _tr('All')],
            yielding=True,
        )
        self.recurse.tooltips = _bind(    # attr_dialog.nml:364
            lambda _o: [_tr('Only the tagged directories themselves change'), _tr('The files under a tagged directory change too, the directories in it not'), _tr('The directories under a tagged directory change too, the files in it not'), _tr('Everything under a tagged directory changes too')],
            yielding=True,
        )
        self.recurse.x = 12    # attr_dialog.nml:361
        self.recurse.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:362

        self.root_button.text = _bind(    # attr_dialog.nml:372
            lambda _o: _tr('A~s~ root'),
            yielding=True,
        )
        self.root_button.tooltip = _bind(    # attr_dialog.nml:373
            lambda _o: _tr('Open root access: any owner and group, and the change made as root'),
            yielding=True,
        )
        self.root_button.visible = False    # attr_dialog.nml:374
        self.root_button.inline_style = 'basis: 11; grow: 0'    # attr_dialog.nml:375

        async def _on_click(event):    # attr_dialog.nml:381
            self.spawn(self._go_root())
            return True
        self.root_button.on_click = _on_click

        self._navml_built(__class__)
