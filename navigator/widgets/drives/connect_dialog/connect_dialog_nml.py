# navml: generated
"""Generated from ``connect_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # connect_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # connect_dialog.nml:2
from navml.widgets.dialog.field import Field    # connect_dialog.nml:3
from navml.widgets.dialog.static_text import StaticText    # connect_dialog.nml:4

__navml_component__ = "ConnectDialog"

__all__ = ["ConnectDialog"]


class ConnectDialog(Dialog, _Component):
    """Utilities > *SSH link (SFTP)* (Alt+F11, DN's ``cmNavyLink``), *FTP link* and

    *SMB link*, and the Link box's *New ... link*: where to connect, over which
    protocol -- the box is the protocol's, and says so -- and the name to keep
    it under.

    DN's Navigator Link had a cable to set up and nothing to ask; a server has
    a host, a user and a port.  ``~/.ssh/config``'s ``Host`` names work as the
    host, and what it says fills in a user and a port left empty.
    """

    #: The document this class was generated from.
    __navml_source__ = "connect_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    host: Field    # connect_dialog.nml:21
    user: Field    # connect_dialog.nml:33
    port: Field    # connect_dialog.nml:42
    directory: Field    # connect_dialog.nml:51
    label: Field    # connect_dialog.nml:60
    keep: CheckBoxes    # connect_dialog.nml:69
    secure: CheckBoxes    # connect_dialog.nml:79
    missing: StaticText    # connect_dialog.nml:90

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.host = Field(parent=self)    # connect_dialog.nml:20
        self.user = Field(parent=self)    # connect_dialog.nml:32
        self.port = Field(parent=self)    # connect_dialog.nml:41
        self.directory = Field(parent=self)    # connect_dialog.nml:50
        self.label = Field(parent=self)    # connect_dialog.nml:59
        self.keep = CheckBoxes(parent=self)    # connect_dialog.nml:68
        self.secure = CheckBoxes(parent=self)    # connect_dialog.nml:78
        self.missing = StaticText(parent=self)    # connect_dialog.nml:89

        self.modal_width = 60    # connect_dialog.nml:15
        self.modal_height = 16    # connect_dialog.nml:16
        self.title = _bind(lambda _o: _tr('SSH link (SFTP)'), yielding=True)    # connect_dialog.nml:18

        self.host.x = 2    # connect_dialog.nml:22
        self.host.y = 2    # connect_dialog.nml:23
        self.host.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # connect_dialog.nml:24
        self.host.height = 1    # connect_dialog.nml:25
        self.host.label_text = _bind(lambda _o: _tr('~H~ost'), yielding=True)    # connect_dialog.nml:26
        self.host.label_width = 12    # connect_dialog.nml:27

        self.user.x = 2    # connect_dialog.nml:34
        self.user.y = 3    # connect_dialog.nml:35
        self.user.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # connect_dialog.nml:36
        self.user.height = 1    # connect_dialog.nml:37
        self.user.label_text = _bind(lambda _o: _tr('~L~ogin'), yielding=True)    # connect_dialog.nml:38
        self.user.label_width = 12    # connect_dialog.nml:39

        self.port.x = 2    # connect_dialog.nml:43
        self.port.y = 4    # connect_dialog.nml:44
        self.port.width = 20    # connect_dialog.nml:45
        self.port.height = 1    # connect_dialog.nml:46
        self.port.label_text = _bind(lambda _o: _tr('P~o~rt'), yielding=True)    # connect_dialog.nml:47
        self.port.label_width = 12    # connect_dialog.nml:48

        self.directory.x = 2    # connect_dialog.nml:52
        self.directory.y = 5    # connect_dialog.nml:53
        self.directory.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # connect_dialog.nml:54
        self.directory.height = 1    # connect_dialog.nml:55
        self.directory.label_text = _bind(    # connect_dialog.nml:56
            lambda _o: _tr('~D~irectory'),
            yielding=True,
        )
        self.directory.label_width = 12    # connect_dialog.nml:57

        self.label.x = 2    # connect_dialog.nml:61
        self.label.y = 7    # connect_dialog.nml:62
        self.label.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # connect_dialog.nml:63
        self.label.height = 1    # connect_dialog.nml:64
        self.label.label_text = _bind(lambda _o: _tr('~N~ame'), yielding=True)    # connect_dialog.nml:65
        self.label.label_width = 12    # connect_dialog.nml:66

        self.keep.x = 3    # connect_dialog.nml:70
        self.keep.y = 9    # connect_dialog.nml:71
        self.keep.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # connect_dialog.nml:72
        self.keep.height = 1    # connect_dialog.nml:73
        self.keep.items = _bind(    # connect_dialog.nml:74
            lambda _o: [_tr('~K~eep in the Link list')],
            yielding=True,
        )
        self.keep.tooltips = _bind(    # connect_dialog.nml:75
            lambda _o: [_tr('Save it under its name in the Link list, to connect again in one step')],
            yielding=True,
        )

        self.secure.x = 3    # connect_dialog.nml:80
        self.secure.y = 10    # connect_dialog.nml:81
        self.secure.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # connect_dialog.nml:82
        self.secure.height = 1    # connect_dialog.nml:83
        self.secure.items = _bind(    # connect_dialog.nml:84
            lambda _o: [_tr('~E~ncrypt with TLS (FTPS)')],
            yielding=True,
        )
        self.secure.tooltips = _bind(    # connect_dialog.nml:85
            lambda _o: [_tr('Encrypt the connection: FTPS rather than plain FTP')],
            yielding=True,
        )
        self.secure.visible = False    # connect_dialog.nml:86

        self.missing.x = 2    # connect_dialog.nml:91
        self.missing.y = 11    # connect_dialog.nml:92
        self.missing.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # connect_dialog.nml:93
        self.missing.height = 1    # connect_dialog.nml:94
        self.missing.text = ''    # connect_dialog.nml:95
