# navml: generated
"""Generated from ``link_manager.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.drives.commands import DeleteLinkEntry, NewLinkEntry, ReadLiveLinks, SaveLinkEntry    # link_manager.nml:1
from navml.widgets.dialog.button import Button    # link_manager.nml:2
from navml.widgets.dialog.button_row import ButtonRow    # link_manager.nml:3
from navml.widgets.dialog.check_boxes import CheckBoxes    # link_manager.nml:4
from navml.widgets.dialog.dialog import Dialog    # link_manager.nml:5
from navml.widgets.dialog.field import Field    # link_manager.nml:6
from navml.widgets.dialog.label import Label    # link_manager.nml:7
from navigator.widgets.drives.link_manager.saved_list import SavedList    # link_manager.nml:8
from navml.widgets.dialog.static_text import StaticText    # link_manager.nml:9

__navml_component__ = "LinkManagerDialog"

__all__ = ["LinkManagerDialog"]


class LinkManagerDialog(Dialog, _Component):
    """Utilities > *SSH link (SFTP)* (Alt+F11, DN's ``cmNavyLink``), *FTP link*,

    *SMB link*, *S3 link*, *GVfs/KIO link* and *Remote shell* (DN's
    ``cmTerminal``): one protocol's kept connections down the left, and the one
    to connect to on the right -- a connection manager after FileZilla's Site
    Manager, asked for, one a protocol (``LinkManagerDialog.family``).  A
    departure: DN's link was one cable, with nothing to keep or choose.

    It opens with the lines empty, a one-off connection kept by nothing;
    choosing one in the list -- the cursor moved, a row clicked, Space -- makes
    the lines that connection, kept by *Save* once changed (the row says ``*``,
    and leaving it asks); a double click connects to it.  *New* makes one at
    once, under a placeholder name ready to be typed over (or from the one-off
    lines), and *Delete* takes one away.  Every line remembers what it held when
    *Connect*, *Save* or *New* was pressed, under its protocol's history ids,
    dropped by its ``▐↓▌`` or Down.  *Connect* sends the panel there, or opens
    ``ssh`` in a command window (Remote shell).

    The lines are ``ConnectDialog``'s, under the same ids; the protocol's
    captions and TLS box are put in by the hand-written half.  GVfs/KIO places
    have no host-and-login form: their box shows *Name* and *URI* alone.
    """

    #: The document this class was generated from.
    __navml_source__ = "link_manager.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # link_manager.nml:38
        'insert': NewLinkEntry,    # link_manager.nml:39
        'f2': SaveLinkEntry,    # link_manager.nml:40
        'delete': DeleteLinkEntry,    # link_manager.nml:41
        'ctrl+r': ReadLiveLinks,    # link_manager.nml:42
    }

    #: Ids, annotated so the hand-written half completes them.
    links_caption: Label    # link_manager.nml:57
    links: SavedList    # link_manager.nml:65
    label: Field    # link_manager.nml:72
    uri: Field    # link_manager.nml:83
    host: Field    # link_manager.nml:94
    user: Field    # link_manager.nml:106
    port: Field    # link_manager.nml:116
    directory: Field    # link_manager.nml:125
    options: Field    # link_manager.nml:138
    forwards_button: Button    # link_manager.nml:152
    copy_key: Button    # link_manager.nml:164
    configure: Button    # link_manager.nml:175
    secure: CheckBoxes    # link_manager.nml:186
    missing: StaticText    # link_manager.nml:198
    create: Button    # link_manager.nml:208
    save: Button    # link_manager.nml:226
    delete: Button    # link_manager.nml:231
    connect: Button    # link_manager.nml:236
    abandon: Button    # link_manager.nml:246

    #: The commands this component handles itself.
    async def on_new_link_entry(self, event: _Any) -> bool:    # link_manager.nml:46
        """``NewLinkEntry``."""
        self.spawn(self.new_link())
        return True

    async def on_save_link_entry(self, event: _Any) -> bool:    # link_manager.nml:47
        """``SaveLinkEntry``."""
        self.spawn(self.save_link())
        return True

    async def on_delete_link_entry(self, event: _Any) -> bool:    # link_manager.nml:48
        """``DeleteLinkEntry``."""
        self.spawn(self.delete_link())
        return True

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.links_caption = Label(parent=self)    # link_manager.nml:56
        self.links = SavedList(parent=self)    # link_manager.nml:64
        self.label = Field(parent=self)    # link_manager.nml:71
        self.uri = Field(parent=self)    # link_manager.nml:82
        self.host = Field(parent=self)    # link_manager.nml:93
        self.user = Field(parent=self)    # link_manager.nml:105
        self.port = Field(parent=self)    # link_manager.nml:115
        self.directory = Field(parent=self)    # link_manager.nml:124
        self.options = Field(parent=self)    # link_manager.nml:137
        self.forwards_button = Button(parent=self)    # link_manager.nml:151
        self.copy_key = Button(parent=self)    # link_manager.nml:163
        self.configure = Button(parent=self)    # link_manager.nml:174
        self.secure = CheckBoxes(parent=self)    # link_manager.nml:185
        self.missing = StaticText(parent=self)    # link_manager.nml:197
        self.create = Button(parent=self)    # link_manager.nml:207
        _w1 = ButtonRow(parent=self)    # link_manager.nml:216
        self.save = Button(parent=_w1)    # link_manager.nml:225
        self.delete = Button(parent=_w1)    # link_manager.nml:230
        self.connect = Button(parent=self)    # link_manager.nml:235
        self.abandon = Button(parent=self)    # link_manager.nml:245

        self.modal_width = 76    # link_manager.nml:32
        self.modal_height = 20    # link_manager.nml:33
        self.title = _bind(lambda _o: _tr('SSH link (SFTP)'), yielding=True)    # link_manager.nml:35
        self.buttons = 'none'    # link_manager.nml:36
        self.first_focus = _bind(    # link_manager.nml:54
            lambda _o: self.links if self.chosen is not None else self.label.entry
        )

        self.links_caption.x = 2    # link_manager.nml:58
        self.links_caption.y = 1    # link_manager.nml:59
        self.links_caption.width = 20    # link_manager.nml:60
        self.links_caption.text = _bind(    # link_manager.nml:61
            lambda _o: _tr('~S~aved'),
            yielding=True,
        )
        self.links_caption.link = _bind(lambda _o: self.links)    # link_manager.nml:62

        self.links.x = 2    # link_manager.nml:66
        self.links.y = 2    # link_manager.nml:67
        self.links.width = 24    # link_manager.nml:68
        self.links.height = 13    # link_manager.nml:69

        self.label.y = 2    # link_manager.nml:73
        self.label.label_text = _bind(lambda _o: _tr('~N~ame'), yielding=True)    # link_manager.nml:77
        self.label.label_width = 12    # link_manager.nml:78
        self.label.history_id = 'ssh_name'    # link_manager.nml:79
        self.label.x = 28    # link_manager.nml:75
        self.label.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:76

        self.uri.y = 4    # link_manager.nml:84
        self.uri.label_text = _bind(lambda _o: _tr('~U~RI'), yielding=True)    # link_manager.nml:88
        self.uri.label_width = 12    # link_manager.nml:89
        self.uri.history_id = 'gvfs_uri'    # link_manager.nml:90
        self.uri.visible = False    # link_manager.nml:91
        self.uri.x = 28    # link_manager.nml:86
        self.uri.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:87

        self.host.y = 4    # link_manager.nml:95
        self.host.label_text = _bind(lambda _o: _tr('~H~ost'), yielding=True)    # link_manager.nml:99
        self.host.label_width = 12    # link_manager.nml:100
        self.host.history_id = 'ssh_host'    # link_manager.nml:103
        self.host.x = 28    # link_manager.nml:97
        self.host.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:98

        self.user.y = 6    # link_manager.nml:107
        self.user.label_text = _bind(lambda _o: _tr('~L~ogin'), yielding=True)    # link_manager.nml:111
        self.user.label_width = 12    # link_manager.nml:112
        self.user.history_id = 'ssh_login'    # link_manager.nml:113
        self.user.x = 28    # link_manager.nml:109
        self.user.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:110

        self.port.x = 28    # link_manager.nml:117
        self.port.y = 8    # link_manager.nml:118
        self.port.width = 24    # link_manager.nml:119
        self.port.label_text = _bind(lambda _o: _tr('P~o~rt'), yielding=True)    # link_manager.nml:120
        self.port.label_width = 12    # link_manager.nml:121
        self.port.history_id = 'ssh_port'    # link_manager.nml:122

        self.directory.y = 10    # link_manager.nml:126
        self.directory.label_text = _bind(    # link_manager.nml:130
            lambda _o: _tr('~D~irectory'),
            yielding=True,
        )
        self.directory.label_width = 12    # link_manager.nml:131
        self.directory.history_id = 'ssh_directory'    # link_manager.nml:132
        self.directory.x = 28    # link_manager.nml:128
        self.directory.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:129

        self.options.y = 12    # link_manager.nml:139
        self.options.label_text = _bind(    # link_manager.nml:143
            lambda _o: _tr('ssh opt~i~ons'),
            yielding=True,
        )
        self.options.label_width = 12    # link_manager.nml:144
        self.options.history_id = 'ssh_options'    # link_manager.nml:145
        self.options.visible = False    # link_manager.nml:146
        self.options.x = 28    # link_manager.nml:141
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:142

        self.forwards_button.text = _bind(    # link_manager.nml:153
            lambda _o: _tr('~F~orwards...'),
            yielding=True,
        )
        self.forwards_button.x = 28    # link_manager.nml:154
        self.forwards_button.y = 13    # link_manager.nml:155
        self.forwards_button.width = 19    # link_manager.nml:156
        self.forwards_button.height = 2    # link_manager.nml:157
        self.forwards_button.visible = False    # link_manager.nml:158

        async def _on_click(event):    # link_manager.nml:159
            self.spawn(self.edit_forwards())
            return True
        self.forwards_button.on_click = _on_click

        self.copy_key.text = _bind(    # link_manager.nml:165
            lambda _o: _tr('Copy ~k~ey...'),
            yielding=True,
        )
        self.copy_key.x = 48    # link_manager.nml:166
        self.copy_key.y = 13    # link_manager.nml:167
        self.copy_key.width = 16    # link_manager.nml:168
        self.copy_key.height = 2    # link_manager.nml:169
        self.copy_key.visible = False    # link_manager.nml:170

        async def _on_click(event):    # link_manager.nml:171
            self.spawn(self.copy_key_to_server())
            return True
        self.copy_key.on_click = _on_click

        self.configure.text = _bind(    # link_manager.nml:176
            lambda _o: _tr('Confi~g~ure...'),
            yielding=True,
        )
        self.configure.x = 28    # link_manager.nml:177
        self.configure.y = 13    # link_manager.nml:178
        self.configure.width = 19    # link_manager.nml:179
        self.configure.height = 2    # link_manager.nml:180
        self.configure.visible = False    # link_manager.nml:181

        async def _on_click(event):    # link_manager.nml:182
            self.spawn(self.configure_remotes())
            return True
        self.configure.on_click = _on_click

        self.secure.y = 12    # link_manager.nml:187
        self.secure.height = 1    # link_manager.nml:188
        self.secure.items = _bind(    # link_manager.nml:192
            lambda _o: [_tr('Encr~y~pt with TLS')],
            yielding=True,
        )
        self.secure.visible = False    # link_manager.nml:193
        self.secure.x = 29    # link_manager.nml:190
        self.secure.width = _bind(lambda _o: max(0, _o.parent.width - 32))    # link_manager.nml:191

        self.missing.y = 13    # link_manager.nml:199
        self.missing.height = 2    # link_manager.nml:200
        self.missing.text = ''    # link_manager.nml:204
        self.missing.wrap = True    # link_manager.nml:205
        self.missing.x = 28    # link_manager.nml:202
        self.missing.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:203

        self.create.text = _bind(lambda _o: _tr('Ne~w~'), yielding=True)    # link_manager.nml:209
        self.create.x = 2    # link_manager.nml:210
        self.create.y = 16    # link_manager.nml:211
        self.create.width = 13    # link_manager.nml:212
        self.create.height = 2    # link_manager.nml:213

        async def _on_click(event):    # link_manager.nml:214
            self.spawn(self.new_link())
            return True
        self.create.on_click = _on_click

        _w1.justify = 'start'    # link_manager.nml:217
        _w1.button_width = 12    # link_manager.nml:218
        _w1.spacing = 1    # link_manager.nml:219
        _w1.y = 16# link_manager.nml:220
        _w1.x = 16# link_manager.nml:222
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 16))    # link_manager.nml:223

        self.save.text = _bind(lambda _o: _tr('Sav~e~'), yielding=True)    # link_manager.nml:227

        async def _on_click(event):    # link_manager.nml:228
            self.spawn(self.save_link())
            return True
        self.save.on_click = _on_click

        self.delete.text = _bind(lambda _o: _tr('Dele~t~e'), yielding=True)    # link_manager.nml:232

        async def _on_click(event):    # link_manager.nml:233
            self.spawn(self.delete_link())
            return True
        self.delete.on_click = _on_click

        self.connect.text = _bind(lambda _o: _tr('~C~onnect'), yielding=True)    # link_manager.nml:237
        self.connect.default = True    # link_manager.nml:238
        self.connect.x = 47    # link_manager.nml:239
        self.connect.y = 16    # link_manager.nml:240
        self.connect.width = 13    # link_manager.nml:241
        self.connect.height = 2    # link_manager.nml:242

        async def _on_click(event):    # link_manager.nml:243
            self.spawn(self.connect_to())
            return True
        self.connect.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # link_manager.nml:247
        self.abandon.x = 61    # link_manager.nml:248
        self.abandon.y = 16    # link_manager.nml:249
        self.abandon.width = 12    # link_manager.nml:250
        self.abandon.height = 2    # link_manager.nml:251

        async def _on_click(event):    # link_manager.nml:252
            self.spawn(self._cancel())
            return True
        self.abandon.on_click = _on_click
