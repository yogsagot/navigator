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

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.drives.commands import DeleteLinkEntry, NewLinkEntry, ReadLiveLinks, SaveLinkEntry    # link_manager.nml:1
from navml.widgets.dialog.button import Button    # link_manager.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # link_manager.nml:3
from navml.widgets.dialog.dialog import Dialog    # link_manager.nml:4
from navml.widgets.dialog.field import Field    # link_manager.nml:5
from navml.widgets.dialog.label import Label    # link_manager.nml:6
from navigator.widgets.drives.link_manager.saved_list import SavedList    # link_manager.nml:7
from navml.widgets.dialog.static_text import StaticText    # link_manager.nml:8

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
    keys = {    # link_manager.nml:36
        'insert': NewLinkEntry,    # link_manager.nml:37
        'f2': SaveLinkEntry,    # link_manager.nml:38
        'delete': DeleteLinkEntry,    # link_manager.nml:39
        'ctrl+r': ReadLiveLinks,    # link_manager.nml:40
    }

    #: Ids, annotated so the hand-written half completes them.
    links_caption: Label    # link_manager.nml:43
    links: SavedList    # link_manager.nml:52
    label: Field    # link_manager.nml:59
    uri: Field    # link_manager.nml:71
    host: Field    # link_manager.nml:83
    user: Field    # link_manager.nml:96
    port: Field    # link_manager.nml:107
    directory: Field    # link_manager.nml:117
    options: Field    # link_manager.nml:131
    forwards_button: Button    # link_manager.nml:146
    copy_key: Button    # link_manager.nml:157
    configure: Button    # link_manager.nml:167
    secure: CheckBoxes    # link_manager.nml:177
    missing: StaticText    # link_manager.nml:189
    create: Button    # link_manager.nml:199
    save: Button    # link_manager.nml:207
    delete: Button    # link_manager.nml:215
    connect: Button    # link_manager.nml:223
    abandon: Button    # link_manager.nml:232

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_forwards_button_click(self, event: _Event) -> bool:    # link_manager.nml:146
        """``forwards_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_copy_key_click(self, event: _Event) -> bool:    # link_manager.nml:157
        """``copy_key`` raised an event whose handler is ``on_click``."""
        return False

    async def on_configure_click(self, event: _Event) -> bool:    # link_manager.nml:167
        """``configure`` raised an event whose handler is ``on_click``."""
        return False

    async def on_create_click(self, event: _Event) -> bool:    # link_manager.nml:199
        """``create`` raised an event whose handler is ``on_click``."""
        return False

    async def on_save_click(self, event: _Event) -> bool:    # link_manager.nml:207
        """``save`` raised an event whose handler is ``on_click``."""
        return False

    async def on_delete_click(self, event: _Event) -> bool:    # link_manager.nml:215
        """``delete`` raised an event whose handler is ``on_click``."""
        return False

    async def on_connect_click(self, event: _Event) -> bool:    # link_manager.nml:223
        """``connect`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # link_manager.nml:232
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.links_caption = Label(parent=self)    # link_manager.nml:42
        self.links = SavedList(parent=self)    # link_manager.nml:51
        self.label = Field(parent=self)    # link_manager.nml:58
        self.uri = Field(parent=self)    # link_manager.nml:70
        self.host = Field(parent=self)    # link_manager.nml:82
        self.user = Field(parent=self)    # link_manager.nml:95
        self.port = Field(parent=self)    # link_manager.nml:106
        self.directory = Field(parent=self)    # link_manager.nml:116
        self.options = Field(parent=self)    # link_manager.nml:130
        self.forwards_button = Button(parent=self)    # link_manager.nml:145
        self.copy_key = Button(parent=self)    # link_manager.nml:156
        self.configure = Button(parent=self)    # link_manager.nml:166
        self.secure = CheckBoxes(parent=self)    # link_manager.nml:176
        self.missing = StaticText(parent=self)    # link_manager.nml:188
        self.create = Button(parent=self)    # link_manager.nml:198
        self.save = Button(parent=self)    # link_manager.nml:206
        self.delete = Button(parent=self)    # link_manager.nml:214
        self.connect = Button(parent=self)    # link_manager.nml:222
        self.abandon = Button(parent=self)    # link_manager.nml:231

        self.modal_width = 76    # link_manager.nml:31
        self.modal_height = 20    # link_manager.nml:32
        self.title = _bind(lambda _o: _tr('SSH link (SFTP)'), yielding=True)    # link_manager.nml:34

        self.links_caption.x = 2    # link_manager.nml:44
        self.links_caption.y = 1    # link_manager.nml:45
        self.links_caption.width = 20    # link_manager.nml:46
        self.links_caption.height = 1    # link_manager.nml:47
        self.links_caption.text = _bind(    # link_manager.nml:48
            lambda _o: _tr('~S~aved'),
            yielding=True,
        )
        self.links_caption.link = _bind(lambda _o: self.links)    # link_manager.nml:49

        self.links.x = 2    # link_manager.nml:53
        self.links.y = 2    # link_manager.nml:54
        self.links.width = 24    # link_manager.nml:55
        self.links.height = 13    # link_manager.nml:56

        self.label.y = 2    # link_manager.nml:60
        self.label.height = 1    # link_manager.nml:61
        self.label.label_text = _bind(lambda _o: _tr('~N~ame'), yielding=True)    # link_manager.nml:65
        self.label.label_width = 12    # link_manager.nml:66
        self.label.history_id = 'ssh_name'    # link_manager.nml:67
        self.label.x = 28    # link_manager.nml:63
        self.label.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:64

        self.uri.y = 4    # link_manager.nml:72
        self.uri.height = 1    # link_manager.nml:73
        self.uri.label_text = _bind(lambda _o: _tr('~U~RI'), yielding=True)    # link_manager.nml:77
        self.uri.label_width = 12    # link_manager.nml:78
        self.uri.history_id = 'gvfs_uri'    # link_manager.nml:79
        self.uri.visible = False    # link_manager.nml:80
        self.uri.x = 28    # link_manager.nml:75
        self.uri.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:76

        self.host.y = 4    # link_manager.nml:84
        self.host.height = 1    # link_manager.nml:85
        self.host.label_text = _bind(lambda _o: _tr('~H~ost'), yielding=True)    # link_manager.nml:89
        self.host.label_width = 12    # link_manager.nml:90
        self.host.history_id = 'ssh_host'    # link_manager.nml:93
        self.host.x = 28    # link_manager.nml:87
        self.host.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:88

        self.user.y = 6    # link_manager.nml:97
        self.user.height = 1    # link_manager.nml:98
        self.user.label_text = _bind(lambda _o: _tr('~L~ogin'), yielding=True)    # link_manager.nml:102
        self.user.label_width = 12    # link_manager.nml:103
        self.user.history_id = 'ssh_login'    # link_manager.nml:104
        self.user.x = 28    # link_manager.nml:100
        self.user.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:101

        self.port.x = 28    # link_manager.nml:108
        self.port.y = 8    # link_manager.nml:109
        self.port.width = 24    # link_manager.nml:110
        self.port.height = 1    # link_manager.nml:111
        self.port.label_text = _bind(lambda _o: _tr('P~o~rt'), yielding=True)    # link_manager.nml:112
        self.port.label_width = 12    # link_manager.nml:113
        self.port.history_id = 'ssh_port'    # link_manager.nml:114

        self.directory.y = 10    # link_manager.nml:118
        self.directory.height = 1    # link_manager.nml:119
        self.directory.label_text = _bind(    # link_manager.nml:123
            lambda _o: _tr('~D~irectory'),
            yielding=True,
        )
        self.directory.label_width = 12    # link_manager.nml:124
        self.directory.history_id = 'ssh_directory'    # link_manager.nml:125
        self.directory.x = 28    # link_manager.nml:121
        self.directory.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:122

        self.options.y = 12    # link_manager.nml:132
        self.options.height = 1    # link_manager.nml:133
        self.options.label_text = _bind(    # link_manager.nml:137
            lambda _o: _tr('ssh opt~i~ons'),
            yielding=True,
        )
        self.options.label_width = 12    # link_manager.nml:138
        self.options.history_id = 'ssh_options'    # link_manager.nml:139
        self.options.visible = False    # link_manager.nml:140
        self.options.x = 28    # link_manager.nml:135
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:136

        self.forwards_button.text = _bind(    # link_manager.nml:147
            lambda _o: _tr('~F~orwards...'),
            yielding=True,
        )
        self.forwards_button.x = 28    # link_manager.nml:148
        self.forwards_button.y = 13    # link_manager.nml:149
        self.forwards_button.width = 19    # link_manager.nml:150
        self.forwards_button.height = 2    # link_manager.nml:151
        self.forwards_button.visible = False    # link_manager.nml:152
        self.forwards_button.on_click = self.on_forwards_button_click    # link_manager.nml:146

        self.copy_key.text = _bind(    # link_manager.nml:158
            lambda _o: _tr('Copy ~k~ey...'),
            yielding=True,
        )
        self.copy_key.x = 48    # link_manager.nml:159
        self.copy_key.y = 13    # link_manager.nml:160
        self.copy_key.width = 16    # link_manager.nml:161
        self.copy_key.height = 2    # link_manager.nml:162
        self.copy_key.visible = False    # link_manager.nml:163
        self.copy_key.on_click = self.on_copy_key_click    # link_manager.nml:157

        self.configure.text = _bind(    # link_manager.nml:168
            lambda _o: _tr('Confi~g~ure...'),
            yielding=True,
        )
        self.configure.x = 28    # link_manager.nml:169
        self.configure.y = 13    # link_manager.nml:170
        self.configure.width = 19    # link_manager.nml:171
        self.configure.height = 2    # link_manager.nml:172
        self.configure.visible = False    # link_manager.nml:173
        self.configure.on_click = self.on_configure_click    # link_manager.nml:167

        self.secure.y = 12    # link_manager.nml:178
        self.secure.height = 1    # link_manager.nml:179
        self.secure.items = _bind(    # link_manager.nml:183
            lambda _o: [_tr('Encr~y~pt with TLS')],
            yielding=True,
        )
        self.secure.visible = False    # link_manager.nml:184
        self.secure.x = 29    # link_manager.nml:181
        self.secure.width = _bind(lambda _o: max(0, _o.parent.width - 32))    # link_manager.nml:182

        self.missing.y = 13    # link_manager.nml:190
        self.missing.height = 2    # link_manager.nml:191
        self.missing.text = ''    # link_manager.nml:195
        self.missing.wrap = True    # link_manager.nml:196
        self.missing.x = 28    # link_manager.nml:193
        self.missing.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # link_manager.nml:194

        self.create.text = _bind(lambda _o: _tr('Ne~w~'), yielding=True)    # link_manager.nml:200
        self.create.x = 2    # link_manager.nml:201
        self.create.y = 16    # link_manager.nml:202
        self.create.width = 13    # link_manager.nml:203
        self.create.height = 2    # link_manager.nml:204
        self.create.on_click = self.on_create_click    # link_manager.nml:199

        self.save.text = _bind(lambda _o: _tr('Sav~e~'), yielding=True)    # link_manager.nml:208
        self.save.x = 16    # link_manager.nml:209
        self.save.y = 16    # link_manager.nml:210
        self.save.width = 12    # link_manager.nml:211
        self.save.height = 2    # link_manager.nml:212
        self.save.on_click = self.on_save_click    # link_manager.nml:207

        self.delete.text = _bind(lambda _o: _tr('Dele~t~e'), yielding=True)    # link_manager.nml:216
        self.delete.x = 29    # link_manager.nml:217
        self.delete.y = 16    # link_manager.nml:218
        self.delete.width = 12    # link_manager.nml:219
        self.delete.height = 2    # link_manager.nml:220
        self.delete.on_click = self.on_delete_click    # link_manager.nml:215

        self.connect.text = _bind(lambda _o: _tr('~C~onnect'), yielding=True)    # link_manager.nml:224
        self.connect.default = True    # link_manager.nml:225
        self.connect.x = 47    # link_manager.nml:226
        self.connect.y = 16    # link_manager.nml:227
        self.connect.width = 13    # link_manager.nml:228
        self.connect.height = 2    # link_manager.nml:229
        self.connect.on_click = self.on_connect_click    # link_manager.nml:223

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # link_manager.nml:233
        self.abandon.x = 61    # link_manager.nml:234
        self.abandon.y = 16    # link_manager.nml:235
        self.abandon.width = 12    # link_manager.nml:236
        self.abandon.height = 2    # link_manager.nml:237
        self.abandon.on_click = self.on_abandon_click    # link_manager.nml:232
