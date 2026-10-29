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
    name_row: StaticText    # attr_dialog.nml:39
    info_row: StaticText    # attr_dialog.nml:47
    tabs: TabView    # attr_dialog.nml:56
    mode_page: TabPage    # attr_dialog.nml:72
    heading: Label    # attr_dialog.nml:79
    bits: CheckBoxes    # attr_dialog.nml:109
    octal: MaskedField    # attr_dialog.nml:120
    symbolic: StaticText    # attr_dialog.nml:132
    user: ChoiceField    # attr_dialog.nml:141
    group: ChoiceField    # attr_dialog.nml:150
    date: DateField    # attr_dialog.nml:166
    clock: TimeField    # attr_dialog.nml:175
    acl_page: TabPage    # attr_dialog.nml:186
    acl_caption: Label    # attr_dialog.nml:190
    acl_list: ListViewer    # attr_dialog.nml:199
    acl_add: Button    # attr_dialog.nml:206
    acl_edit: Button    # attr_dialog.nml:214
    acl_delete: Button    # attr_dialog.nml:222
    acl_clear: Button    # attr_dialog.nml:231
    acl_note: StaticText    # attr_dialog.nml:240
    xattr_page: TabPage    # attr_dialog.nml:247
    xattr_caption: Label    # attr_dialog.nml:251
    xattr_list: ListViewer    # attr_dialog.nml:260
    xattr_add: Button    # attr_dialog.nml:267
    xattr_edit: Button    # attr_dialog.nml:275
    xattr_delete: Button    # attr_dialog.nml:283
    xattr_note: StaticText    # attr_dialog.nml:291
    flags_page: TabPage    # attr_dialog.nml:300
    flags_caption: Label    # attr_dialog.nml:304
    flags: CheckBoxes    # attr_dialog.nml:313
    lsattr: StaticText    # attr_dialog.nml:322
    flags_note: StaticText    # attr_dialog.nml:329
    recurse_caption: Label    # attr_dialog.nml:338
    recurse: RadioButtons    # attr_dialog.nml:347

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_acl_add_click(self, event: _Event) -> bool:    # attr_dialog.nml:206
        """``acl_add`` raised an event whose handler is ``on_click``."""
        return False

    async def on_acl_edit_click(self, event: _Event) -> bool:    # attr_dialog.nml:214
        """``acl_edit`` raised an event whose handler is ``on_click``."""
        return False

    async def on_acl_delete_click(self, event: _Event) -> bool:    # attr_dialog.nml:222
        """``acl_delete`` raised an event whose handler is ``on_click``."""
        return False

    async def on_acl_clear_click(self, event: _Event) -> bool:    # attr_dialog.nml:231
        """``acl_clear`` raised an event whose handler is ``on_click``."""
        return False

    async def on_xattr_add_click(self, event: _Event) -> bool:    # attr_dialog.nml:267
        """``xattr_add`` raised an event whose handler is ``on_click``."""
        return False

    async def on_xattr_edit_click(self, event: _Event) -> bool:    # attr_dialog.nml:275
        """``xattr_edit`` raised an event whose handler is ``on_click``."""
        return False

    async def on_xattr_delete_click(self, event: _Event) -> bool:    # attr_dialog.nml:283
        """``xattr_delete`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.name_row = StaticText(parent=self)    # attr_dialog.nml:38
        self.info_row = StaticText(parent=self)    # attr_dialog.nml:46
        self.tabs = TabView(parent=self)    # attr_dialog.nml:55
        self.mode_page = TabPage(parent=self.tabs)    # attr_dialog.nml:71
        self.heading = Label(parent=self.mode_page)    # attr_dialog.nml:78
        _w1 = Label(parent=self.mode_page)    # attr_dialog.nml:87
        _w2 = Label(parent=self.mode_page)    # attr_dialog.nml:94
        _w3 = Label(parent=self.mode_page)    # attr_dialog.nml:101
        self.bits = CheckBoxes(parent=self.mode_page)    # attr_dialog.nml:108
        self.octal = MaskedField(parent=self.mode_page)    # attr_dialog.nml:119
        self.symbolic = StaticText(parent=self.mode_page)    # attr_dialog.nml:131
        self.user = ChoiceField(parent=self.mode_page)    # attr_dialog.nml:140
        self.group = ChoiceField(parent=self.mode_page)    # attr_dialog.nml:149
        self.date = DateField(parent=self.mode_page)    # attr_dialog.nml:165
        self.clock = TimeField(parent=self.mode_page)    # attr_dialog.nml:174
        self.acl_page = TabPage(parent=self.tabs)    # attr_dialog.nml:185
        self.acl_caption = Label(parent=self.acl_page)    # attr_dialog.nml:189
        self.acl_list = ListViewer(parent=self.acl_page)    # attr_dialog.nml:198
        self.acl_add = Button(parent=self.acl_page)    # attr_dialog.nml:205
        self.acl_edit = Button(parent=self.acl_page)    # attr_dialog.nml:213
        self.acl_delete = Button(parent=self.acl_page)    # attr_dialog.nml:221
        self.acl_clear = Button(parent=self.acl_page)    # attr_dialog.nml:230
        self.acl_note = StaticText(parent=self.acl_page)    # attr_dialog.nml:239
        self.xattr_page = TabPage(parent=self.tabs)    # attr_dialog.nml:246
        self.xattr_caption = Label(parent=self.xattr_page)    # attr_dialog.nml:250
        self.xattr_list = ListViewer(parent=self.xattr_page)    # attr_dialog.nml:259
        self.xattr_add = Button(parent=self.xattr_page)    # attr_dialog.nml:266
        self.xattr_edit = Button(parent=self.xattr_page)    # attr_dialog.nml:274
        self.xattr_delete = Button(parent=self.xattr_page)    # attr_dialog.nml:282
        self.xattr_note = StaticText(parent=self.xattr_page)    # attr_dialog.nml:290
        self.flags_page = TabPage(parent=self.tabs)    # attr_dialog.nml:299
        self.flags_caption = Label(parent=self.flags_page)    # attr_dialog.nml:303
        self.flags = CheckBoxes(parent=self.flags_page)    # attr_dialog.nml:312
        self.lsattr = StaticText(parent=self.flags_page)    # attr_dialog.nml:321
        self.flags_note = StaticText(parent=self.flags_page)    # attr_dialog.nml:328
        self.recurse_caption = Label(parent=self)    # attr_dialog.nml:337
        self.recurse = RadioButtons(parent=self)    # attr_dialog.nml:346

        self.modal_width = 64    # attr_dialog.nml:32
        self.modal_height = 21    # attr_dialog.nml:33
        self.title = _bind(lambda _o: _tr('File Attributes'), yielding=True)    # attr_dialog.nml:34
        self.buttons = 'ok-cancel'    # attr_dialog.nml:35

        self.name_row.x = 2    # attr_dialog.nml:40
        self.name_row.y = 1    # attr_dialog.nml:41
        self.name_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:42
        self.name_row.height = 1    # attr_dialog.nml:43

        self.info_row.x = 2    # attr_dialog.nml:48
        self.info_row.y = 2    # attr_dialog.nml:49
        self.info_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:50
        self.info_row.height = 1    # attr_dialog.nml:51

        self.tabs.tooltips = _bind(    # attr_dialog.nml:58
            lambda _o: [_tr('Permissions, owner, group and modification time'), _tr('Access control list: permissions for particular users and groups'), _tr('Extended attributes: names and values kept with the file'), _tr('File system flags, such as immutable and append-only')],
            yielding=True,
        )
        self.tabs.x = 0    # attr_dialog.nml:64
        self.tabs.y = 3    # attr_dialog.nml:65
        self.tabs.width = _bind(lambda _o: _o.parent.width)    # attr_dialog.nml:66
        self.tabs.height = 12    # attr_dialog.nml:67
        self.tabs.side = 'simple'    # attr_dialog.nml:68
        self.tabs.joins_frame = True    # attr_dialog.nml:69

        self.mode_page.title = _bind(lambda _o: _tr('Mode'), yielding=True)    # attr_dialog.nml:73

        self.heading.x = 3    # attr_dialog.nml:80
        self.heading.y = 1    # attr_dialog.nml:81
        self.heading.width = _bind(    # attr_dialog.nml:82
            lambda _o: max(1, self.bits.column_x(1) - self.bits.column_x(0))
        )
        self.heading.height = 1    # attr_dialog.nml:83
        self.heading.text = _bind(lambda _o: _tr('O~w~ner'), yielding=True)    # attr_dialog.nml:84
        self.heading.link = _bind(lambda _o: self.bits)    # attr_dialog.nml:85

        _w1.x = _bind(lambda _o: 3 + self.bits.column_x(1))    # attr_dialog.nml:88
        _w1.y = 1# attr_dialog.nml:89
        _w1.width = _bind(    # attr_dialog.nml:90
            lambda _o: max(1, self.bits.column_x(2) - self.bits.column_x(1))
        )
        _w1.height = 1    # attr_dialog.nml:91
        _w1.text = _bind(lambda _o: _tr('Group'), yielding=True)    # attr_dialog.nml:92

        _w2.x = _bind(lambda _o: 3 + self.bits.column_x(2))    # attr_dialog.nml:95
        _w2.y = 1# attr_dialog.nml:96
        _w2.width = _bind(    # attr_dialog.nml:97
            lambda _o: max(1, self.bits.column_x(3) - self.bits.column_x(2))
        )
        _w2.height = 1    # attr_dialog.nml:98
        _w2.text = _bind(lambda _o: _tr('Others'), yielding=True)    # attr_dialog.nml:99

        _w3.x = _bind(lambda _o: 3 + self.bits.column_x(3))    # attr_dialog.nml:102
        _w3.y = 1# attr_dialog.nml:103
        _w3.width = _bind(    # attr_dialog.nml:104
            lambda _o: max(1, _o.parent.width - 6 - self.bits.column_x(3))
        )
        _w3.height = 1    # attr_dialog.nml:105
        _w3.text = _bind(lambda _o: _tr('Special'), yielding=True)    # attr_dialog.nml:106

        self.bits.x = 3    # attr_dialog.nml:110
        self.bits.y = 2    # attr_dialog.nml:111
        self.bits.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:112
        self.bits.height = 3    # attr_dialog.nml:113
        self.bits.items = _bind(    # attr_dialog.nml:114
            lambda _o: [_tr('Read'), _tr('Write'), _tr('Exec'), _tr('Read'), _tr('Write'), _tr('Exec'), _tr('Read'), _tr('Write'), _tr('Exec'), _tr('Set UID'), _tr('Set GID'), _tr('Sticky')],
            yielding=True,
        )
        self.bits.tooltips = _bind(    # attr_dialog.nml:115
            lambda _o: ['', '', '', '', '', '', '', '', '', _tr("Run with the file owner's rights"), _tr("Run with the group's rights; in a directory, new files take its group"), _tr("In a directory, only a file's owner may delete or rename it")],
            yielding=True,
        )

        self.octal.x = 2    # attr_dialog.nml:121
        self.octal.y = 6    # attr_dialog.nml:122
        self.octal.width = 16    # attr_dialog.nml:123
        self.octal.height = 1    # attr_dialog.nml:124
        self.octal.label_text = _bind(lambda _o: _tr('~O~ctal'), yielding=True)    # attr_dialog.nml:125
        self.octal.label_width = 10    # attr_dialog.nml:126
        self.octal.mask = '9999'    # attr_dialog.nml:127
        self.octal.base = 8    # attr_dialog.nml:128

        self.symbolic.x = 20    # attr_dialog.nml:133
        self.symbolic.y = 6    # attr_dialog.nml:134
        self.symbolic.width = 12    # attr_dialog.nml:135
        self.symbolic.height = 1    # attr_dialog.nml:136

        self.user.x = 2    # attr_dialog.nml:142
        self.user.y = 7    # attr_dialog.nml:143
        self.user.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:144
        self.user.height = 1    # attr_dialog.nml:145
        self.user.label_text = _bind(lambda _o: _tr('~U~ser'), yielding=True)    # attr_dialog.nml:146
        self.user.label_width = 10    # attr_dialog.nml:147

        self.group.x = 2    # attr_dialog.nml:151
        self.group.y = 8    # attr_dialog.nml:152
        self.group.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:153
        self.group.height = 1    # attr_dialog.nml:154
        self.group.label_text = _bind(lambda _o: _tr('~G~roup'), yielding=True)    # attr_dialog.nml:155
        self.group.label_width = 10    # attr_dialog.nml:156

        self.date.x = 2    # attr_dialog.nml:167
        self.date.y = 9    # attr_dialog.nml:168
        self.date.width = 26    # attr_dialog.nml:169
        self.date.height = 1    # attr_dialog.nml:170
        self.date.label_text = _bind(lambda _o: _tr('~D~ate'), yielding=True)    # attr_dialog.nml:171
        self.date.label_width = 10    # attr_dialog.nml:172

        self.clock.x = 30    # attr_dialog.nml:176
        self.clock.y = 9    # attr_dialog.nml:177
        self.clock.width = 22    # attr_dialog.nml:178
        self.clock.height = 1    # attr_dialog.nml:179
        self.clock.label_text = _bind(lambda _o: _tr('~T~ime'), yielding=True)    # attr_dialog.nml:180
        self.clock.label_width = 6    # attr_dialog.nml:181

        self.acl_page.title = _bind(lambda _o: _tr('ACL'), yielding=True)    # attr_dialog.nml:187

        self.acl_caption.x = 2    # attr_dialog.nml:191
        self.acl_caption.y = 1    # attr_dialog.nml:192
        self.acl_caption.width = 20    # attr_dialog.nml:193
        self.acl_caption.height = 1    # attr_dialog.nml:194
        self.acl_caption.text = _bind(    # attr_dialog.nml:195
            lambda _o: _tr('E~n~tries'),
            yielding=True,
        )
        self.acl_caption.link = _bind(lambda _o: self.acl_list)    # attr_dialog.nml:196

        self.acl_list.x = 2    # attr_dialog.nml:200
        self.acl_list.y = 2    # attr_dialog.nml:201
        self.acl_list.width = _bind(lambda _o: max(0, _o.parent.width - 18))    # attr_dialog.nml:202
        self.acl_list.height = 8    # attr_dialog.nml:203

        self.acl_add.text = _bind(lambda _o: _tr('~A~dd'), yielding=True)    # attr_dialog.nml:207
        self.acl_add.x = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:208
        self.acl_add.y = 2    # attr_dialog.nml:209
        self.acl_add.width = 12    # attr_dialog.nml:210
        self.acl_add.height = 2    # attr_dialog.nml:211
        self.acl_add.on_click = self.on_acl_add_click    # attr_dialog.nml:206

        self.acl_edit.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # attr_dialog.nml:215
        self.acl_edit.x = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:216
        self.acl_edit.y = 4    # attr_dialog.nml:217
        self.acl_edit.width = 12    # attr_dialog.nml:218
        self.acl_edit.height = 2    # attr_dialog.nml:219
        self.acl_edit.on_click = self.on_acl_edit_click    # attr_dialog.nml:214

        self.acl_delete.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # attr_dialog.nml:223
        self.acl_delete.x = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:224
        self.acl_delete.y = 6    # attr_dialog.nml:225
        self.acl_delete.width = 12    # attr_dialog.nml:226
        self.acl_delete.height = 2    # attr_dialog.nml:227
        self.acl_delete.on_click = self.on_acl_delete_click    # attr_dialog.nml:222

        self.acl_clear.text = _bind(lambda _o: _tr('~C~lear'), yielding=True)    # attr_dialog.nml:232
        self.acl_clear.x = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:233
        self.acl_clear.y = 8    # attr_dialog.nml:234
        self.acl_clear.width = 12    # attr_dialog.nml:235
        self.acl_clear.height = 2    # attr_dialog.nml:236
        self.acl_clear.on_click = self.on_acl_clear_click    # attr_dialog.nml:231

        self.acl_note.x = 2    # attr_dialog.nml:241
        self.acl_note.y = 10    # attr_dialog.nml:242
        self.acl_note.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:243
        self.acl_note.height = 1    # attr_dialog.nml:244

        self.xattr_page.title = _bind(lambda _o: _tr('Xattrs'), yielding=True)    # attr_dialog.nml:248

        self.xattr_caption.x = 2    # attr_dialog.nml:252
        self.xattr_caption.y = 1    # attr_dialog.nml:253
        self.xattr_caption.width = 20    # attr_dialog.nml:254
        self.xattr_caption.height = 1    # attr_dialog.nml:255
        self.xattr_caption.text = _bind(    # attr_dialog.nml:256
            lambda _o: _tr('Na~m~es'),
            yielding=True,
        )
        self.xattr_caption.link = _bind(lambda _o: self.xattr_list)    # attr_dialog.nml:257

        self.xattr_list.x = 2    # attr_dialog.nml:261
        self.xattr_list.y = 2    # attr_dialog.nml:262
        self.xattr_list.width = _bind(lambda _o: max(0, _o.parent.width - 18))    # attr_dialog.nml:263
        self.xattr_list.height = 8    # attr_dialog.nml:264

        self.xattr_add.text = _bind(lambda _o: _tr('~A~dd'), yielding=True)    # attr_dialog.nml:268
        self.xattr_add.x = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:269
        self.xattr_add.y = 2    # attr_dialog.nml:270
        self.xattr_add.width = 12    # attr_dialog.nml:271
        self.xattr_add.height = 2    # attr_dialog.nml:272
        self.xattr_add.on_click = self.on_xattr_add_click    # attr_dialog.nml:267

        self.xattr_edit.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # attr_dialog.nml:276
        self.xattr_edit.x = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:277
        self.xattr_edit.y = 4    # attr_dialog.nml:278
        self.xattr_edit.width = 12    # attr_dialog.nml:279
        self.xattr_edit.height = 2    # attr_dialog.nml:280
        self.xattr_edit.on_click = self.on_xattr_edit_click    # attr_dialog.nml:275

        self.xattr_delete.text = _bind(    # attr_dialog.nml:284
            lambda _o: _tr('~D~elete'),
            yielding=True,
        )
        self.xattr_delete.x = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:285
        self.xattr_delete.y = 6    # attr_dialog.nml:286
        self.xattr_delete.width = 12    # attr_dialog.nml:287
        self.xattr_delete.height = 2    # attr_dialog.nml:288
        self.xattr_delete.on_click = self.on_xattr_delete_click    # attr_dialog.nml:283

        self.xattr_note.x = 2    # attr_dialog.nml:292
        self.xattr_note.y = 10    # attr_dialog.nml:293
        self.xattr_note.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # attr_dialog.nml:294
        self.xattr_note.height = 1    # attr_dialog.nml:295

        self.flags_page.title = _bind(lambda _o: _tr('Flags'), yielding=True)    # attr_dialog.nml:301

        self.flags_caption.x = 3    # attr_dialog.nml:305
        self.flags_caption.y = 1    # attr_dialog.nml:306
        self.flags_caption.width = 20    # attr_dialog.nml:307
        self.flags_caption.height = 1    # attr_dialog.nml:308
        self.flags_caption.text = _bind(    # attr_dialog.nml:309
            lambda _o: _tr('~F~lags'),
            yielding=True,
        )
        self.flags_caption.link = _bind(lambda _o: self.flags)    # attr_dialog.nml:310

        self.flags.x = 3    # attr_dialog.nml:314
        self.flags.y = 2    # attr_dialog.nml:315
        self.flags.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:316
        self.flags.height = 3    # attr_dialog.nml:317
        self.flags.items = _bind(    # attr_dialog.nml:318
            lambda _o: [_tr('Immutable'), _tr('Append'), _tr('No dump'), _tr('No atime'), _tr('Sync'), _tr('Dir sync'), _tr('No COW'), _tr('Compress'), _tr('Journal'), _tr('Top dir'), _tr('Secure rm'), _tr('Undelete')],
            yielding=True,
        )
        self.flags.tooltips = _bind(    # attr_dialog.nml:319
            lambda _o: [_tr('No one may change, rename or delete it, root included'), _tr('It can only be added to'), _tr('Left out of backups made with dump'), _tr('Its access time is never updated'), _tr('Its changes are written to the disk at once'), _tr('Changes to this directory are written to the disk at once'), _tr('Rewritten in place rather than copied on write (btrfs)'), _tr('Compressed by the file system'), _tr("Its data goes through the file system's journal"), _tr('The top of a directory tree, for where the file system places blocks'), _tr('Its blocks are cleared when it is deleted, where the file system can'), _tr('Its contents are kept when it is deleted, where the file system can')],
            yielding=True,
        )

        self.lsattr.x = 3    # attr_dialog.nml:323
        self.lsattr.y = 6    # attr_dialog.nml:324
        self.lsattr.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:325
        self.lsattr.height = 1    # attr_dialog.nml:326

        self.flags_note.x = 3    # attr_dialog.nml:330
        self.flags_note.y = 8    # attr_dialog.nml:331
        self.flags_note.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # attr_dialog.nml:332
        self.flags_note.height = 1    # attr_dialog.nml:333

        self.recurse_caption.x = 2    # attr_dialog.nml:339
        self.recurse_caption.y = 16    # attr_dialog.nml:340
        self.recurse_caption.width = 10    # attr_dialog.nml:341
        self.recurse_caption.height = 1    # attr_dialog.nml:342
        self.recurse_caption.text = _bind(    # attr_dialog.nml:343
            lambda _o: _tr('~R~ecurse'),
            yielding=True,
        )
        self.recurse_caption.link = _bind(lambda _o: self.recurse)    # attr_dialog.nml:344

        self.recurse.x = 12    # attr_dialog.nml:348
        self.recurse.y = 16    # attr_dialog.nml:349
        self.recurse.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # attr_dialog.nml:350
        self.recurse.height = 1    # attr_dialog.nml:351
        self.recurse.items = _bind(    # attr_dialog.nml:352
            lambda _o: [_tr('No'), _tr('Files'), _tr('Dirs'), _tr('All')],
            yielding=True,
        )
        self.recurse.tooltips = _bind(    # attr_dialog.nml:353
            lambda _o: [_tr('Only the tagged directories themselves change'), _tr('The files under a tagged directory change too, the directories in it not'), _tr('The directories under a tagged directory change too, the files in it not'), _tr('Everything under a tagged directory changes too')],
            yielding=True,
        )
