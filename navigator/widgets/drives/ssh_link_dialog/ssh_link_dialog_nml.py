# navml: generated
"""Generated from ``ssh_link_dialog.nml``.

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
from navigator.widgets.drives.commands import DeleteSshLink, NewSshLink, SaveSshLink    # ssh_link_dialog.nml:1
from navml.widgets.dialog.button import Button    # ssh_link_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # ssh_link_dialog.nml:3
from navml.widgets.dialog.field import Field    # ssh_link_dialog.nml:4
from navml.widgets.dialog.label import Label    # ssh_link_dialog.nml:5
from navigator.widgets.drives.ssh_link_dialog.saved_list import SavedList    # ssh_link_dialog.nml:6
from navml.widgets.dialog.static_text import StaticText    # ssh_link_dialog.nml:7

__navml_component__ = "SshLinkDialog"

__all__ = ["SshLinkDialog"]


class SshLinkDialog(Dialog, _Component):
    """Utilities > *SSH link (SFTP)* (Alt+F11, DN's ``cmNavyLink``) and

    Utilities > *Remote shell* (DN's ``cmTerminal``): the SSH connections kept,
    down the left, and the one to connect to on the right -- a connection
    manager after FileZilla's Site Manager, asked for.  A departure: DN's link
    was one cable, with nothing to keep or choose.

    It opens with the lines empty, a one-off connection kept by nothing;
    choosing one in the list -- the cursor moved, a row clicked, Space -- makes
    the lines that connection, kept by *Save* once changed (the row says ``*``,
    and leaving it asks); a double click connects to it.  *New* makes one at
    once, under a placeholder name ready to be typed over (or from the one-off
    lines), and *Delete* takes one away.  Every line remembers what it held when *Connect*, *Save* or *New*
    was pressed (``ssh_name``, ``ssh_host``, ``ssh_login``, ``ssh_port``,
    ``ssh_directory``), dropped by its ``▐↓▌`` or Down.
    *Connect* sends the panel there (SSH link) or opens ``ssh`` in a command
    window (Remote shell).  The lines are ``ConnectDialog``'s, under the same
    ids; ``~/.ssh/config``'s ``Host`` names work as the host.
    """

    #: The document this class was generated from.
    __navml_source__ = "ssh_link_dialog.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # ssh_link_dialog.nml:32
        'insert': NewSshLink,    # ssh_link_dialog.nml:33
        'f2': SaveSshLink,    # ssh_link_dialog.nml:34
        'delete': DeleteSshLink,    # ssh_link_dialog.nml:35
    }

    #: Ids, annotated so the hand-written half completes them.
    links_caption: Label    # ssh_link_dialog.nml:38
    links: SavedList    # ssh_link_dialog.nml:47
    label: Field    # ssh_link_dialog.nml:54
    host: Field    # ssh_link_dialog.nml:64
    user: Field    # ssh_link_dialog.nml:76
    port: Field    # ssh_link_dialog.nml:86
    directory: Field    # ssh_link_dialog.nml:96
    missing: StaticText    # ssh_link_dialog.nml:108
    create: Button    # ssh_link_dialog.nml:117
    save: Button    # ssh_link_dialog.nml:125
    delete: Button    # ssh_link_dialog.nml:133
    connect: Button    # ssh_link_dialog.nml:141
    abandon: Button    # ssh_link_dialog.nml:150

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_create_click(self, event: _Event) -> bool:    # ssh_link_dialog.nml:117
        """``create`` raised an event whose handler is ``on_click``."""
        return False

    async def on_save_click(self, event: _Event) -> bool:    # ssh_link_dialog.nml:125
        """``save`` raised an event whose handler is ``on_click``."""
        return False

    async def on_delete_click(self, event: _Event) -> bool:    # ssh_link_dialog.nml:133
        """``delete`` raised an event whose handler is ``on_click``."""
        return False

    async def on_connect_click(self, event: _Event) -> bool:    # ssh_link_dialog.nml:141
        """``connect`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # ssh_link_dialog.nml:150
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.links_caption = Label(parent=self)    # ssh_link_dialog.nml:37
        self.links = SavedList(parent=self)    # ssh_link_dialog.nml:46
        self.label = Field(parent=self)    # ssh_link_dialog.nml:53
        self.host = Field(parent=self)    # ssh_link_dialog.nml:63
        self.user = Field(parent=self)    # ssh_link_dialog.nml:75
        self.port = Field(parent=self)    # ssh_link_dialog.nml:85
        self.directory = Field(parent=self)    # ssh_link_dialog.nml:95
        self.missing = StaticText(parent=self)    # ssh_link_dialog.nml:107
        self.create = Button(parent=self)    # ssh_link_dialog.nml:116
        self.save = Button(parent=self)    # ssh_link_dialog.nml:124
        self.delete = Button(parent=self)    # ssh_link_dialog.nml:132
        self.connect = Button(parent=self)    # ssh_link_dialog.nml:140
        self.abandon = Button(parent=self)    # ssh_link_dialog.nml:149

        self.modal_width = 76    # ssh_link_dialog.nml:27
        self.modal_height = 19    # ssh_link_dialog.nml:28
        self.title = _bind(lambda _o: _tr('SSH link (SFTP)'), yielding=True)    # ssh_link_dialog.nml:30

        self.links_caption.x = 2    # ssh_link_dialog.nml:39
        self.links_caption.y = 1    # ssh_link_dialog.nml:40
        self.links_caption.width = 20    # ssh_link_dialog.nml:41
        self.links_caption.height = 1    # ssh_link_dialog.nml:42
        self.links_caption.text = _bind(    # ssh_link_dialog.nml:43
            lambda _o: _tr('~S~aved'),
            yielding=True,
        )
        self.links_caption.link = _bind(lambda _o: self.links)    # ssh_link_dialog.nml:44

        self.links.x = 2    # ssh_link_dialog.nml:48
        self.links.y = 2    # ssh_link_dialog.nml:49
        self.links.width = 24    # ssh_link_dialog.nml:50
        self.links.height = 12    # ssh_link_dialog.nml:51

        self.label.x = 28    # ssh_link_dialog.nml:55
        self.label.y = 2    # ssh_link_dialog.nml:56
        self.label.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # ssh_link_dialog.nml:57
        self.label.height = 1    # ssh_link_dialog.nml:58
        self.label.label_text = _bind(lambda _o: _tr('~N~ame'), yielding=True)    # ssh_link_dialog.nml:59
        self.label.label_width = 12    # ssh_link_dialog.nml:60
        self.label.history_id = 'ssh_name'    # ssh_link_dialog.nml:61

        self.host.x = 28    # ssh_link_dialog.nml:65
        self.host.y = 4    # ssh_link_dialog.nml:66
        self.host.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # ssh_link_dialog.nml:67
        self.host.height = 1    # ssh_link_dialog.nml:68
        self.host.label_text = _bind(lambda _o: _tr('~H~ost'), yielding=True)    # ssh_link_dialog.nml:69
        self.host.label_width = 12    # ssh_link_dialog.nml:70
        self.host.history_id = 'ssh_host'    # ssh_link_dialog.nml:73

        self.user.x = 28    # ssh_link_dialog.nml:77
        self.user.y = 6    # ssh_link_dialog.nml:78
        self.user.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # ssh_link_dialog.nml:79
        self.user.height = 1    # ssh_link_dialog.nml:80
        self.user.label_text = _bind(lambda _o: _tr('~L~ogin'), yielding=True)    # ssh_link_dialog.nml:81
        self.user.label_width = 12    # ssh_link_dialog.nml:82
        self.user.history_id = 'ssh_login'    # ssh_link_dialog.nml:83

        self.port.x = 28    # ssh_link_dialog.nml:87
        self.port.y = 8    # ssh_link_dialog.nml:88
        self.port.width = 24    # ssh_link_dialog.nml:89
        self.port.height = 1    # ssh_link_dialog.nml:90
        self.port.label_text = _bind(lambda _o: _tr('P~o~rt'), yielding=True)    # ssh_link_dialog.nml:91
        self.port.label_width = 12    # ssh_link_dialog.nml:92
        self.port.history_id = 'ssh_port'    # ssh_link_dialog.nml:93

        self.directory.x = 28    # ssh_link_dialog.nml:97
        self.directory.y = 10    # ssh_link_dialog.nml:98
        self.directory.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # ssh_link_dialog.nml:99
        self.directory.height = 1    # ssh_link_dialog.nml:100
        self.directory.label_text = _bind(    # ssh_link_dialog.nml:101
            lambda _o: _tr('~D~irectory'),
            yielding=True,
        )
        self.directory.label_width = 12    # ssh_link_dialog.nml:102
        self.directory.history_id = 'ssh_directory'    # ssh_link_dialog.nml:103

        self.missing.x = 28    # ssh_link_dialog.nml:109
        self.missing.y = 12    # ssh_link_dialog.nml:110
        self.missing.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # ssh_link_dialog.nml:111
        self.missing.height = 2    # ssh_link_dialog.nml:112
        self.missing.text = ''    # ssh_link_dialog.nml:113
        self.missing.wrap = True    # ssh_link_dialog.nml:114

        self.create.text = _bind(lambda _o: _tr('Ne~w~'), yielding=True)    # ssh_link_dialog.nml:118
        self.create.x = 2    # ssh_link_dialog.nml:119
        self.create.y = 15    # ssh_link_dialog.nml:120
        self.create.width = 13    # ssh_link_dialog.nml:121
        self.create.height = 2    # ssh_link_dialog.nml:122
        self.create.on_click = self.on_create_click    # ssh_link_dialog.nml:117

        self.save.text = _bind(lambda _o: _tr('Sav~e~'), yielding=True)    # ssh_link_dialog.nml:126
        self.save.x = 16    # ssh_link_dialog.nml:127
        self.save.y = 15    # ssh_link_dialog.nml:128
        self.save.width = 12    # ssh_link_dialog.nml:129
        self.save.height = 2    # ssh_link_dialog.nml:130
        self.save.on_click = self.on_save_click    # ssh_link_dialog.nml:125

        self.delete.text = _bind(lambda _o: _tr('Dele~t~e'), yielding=True)    # ssh_link_dialog.nml:134
        self.delete.x = 29    # ssh_link_dialog.nml:135
        self.delete.y = 15    # ssh_link_dialog.nml:136
        self.delete.width = 12    # ssh_link_dialog.nml:137
        self.delete.height = 2    # ssh_link_dialog.nml:138
        self.delete.on_click = self.on_delete_click    # ssh_link_dialog.nml:133

        self.connect.text = _bind(lambda _o: _tr('~C~onnect'), yielding=True)    # ssh_link_dialog.nml:142
        self.connect.default = True    # ssh_link_dialog.nml:143
        self.connect.x = 47    # ssh_link_dialog.nml:144
        self.connect.y = 15    # ssh_link_dialog.nml:145
        self.connect.width = 13    # ssh_link_dialog.nml:146
        self.connect.height = 2    # ssh_link_dialog.nml:147
        self.connect.on_click = self.on_connect_click    # ssh_link_dialog.nml:141

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # ssh_link_dialog.nml:151
        self.abandon.x = 61    # ssh_link_dialog.nml:152
        self.abandon.y = 15    # ssh_link_dialog.nml:153
        self.abandon.width = 12    # ssh_link_dialog.nml:154
        self.abandon.height = 2    # ssh_link_dialog.nml:155
        self.abandon.on_click = self.on_abandon_click    # ssh_link_dialog.nml:150
