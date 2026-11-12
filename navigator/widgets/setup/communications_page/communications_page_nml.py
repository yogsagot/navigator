# navml: generated
"""Generated from ``communications_page.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.field import Field    # communications_page.nml:1
from navml.widgets.dialog.label import Label    # communications_page.nml:2
from navml.widgets.dialog.masked_field import MaskedField    # communications_page.nml:3
from navml.widgets.dialog.radio_buttons import RadioButtons    # communications_page.nml:4
from navml.widgets.dialog.static_text import StaticText    # communications_page.nml:5
from navigator.widgets.setup.settings_page import SettingsPage    # communications_page.nml:6

__navml_component__ = "CommunicationsPage"

__all__ = ["CommunicationsPage"]


class CommunicationsPage(SettingsPage, _Component):
    """Options > Configuration > *Communications*: where DOS Navigator set up the

    modem and the cable its Navigator Link ran over (``cmSetupModem``) --
    here, connections to servers (``[remote]``, ``RemoteData``).  Nothing of
    DN's resource is left: a port, a speed and an init string have no meaning
    for SSH.  *Desktop integration* is not DN's: whose plumbing -- GIO's or
    KDE's KIO -- mounts volumes, reaches GVfs/KIO links and opens files in the
    desktop's applications (``[system] desktop_vfs``,
    ``navigator.lib.system.desktop``); here, System Setup having no room left.
    *Notify when a long operation ends* is not DN's either: a desktop
    notification once the terminal is in the background (``[system]
    notifications``, ``Shell.notify_away``).
    """

    #: The document this class was generated from.
    __navml_source__ = "communications_page.nml"

    section_name = 'remote'    # communications_page.nml:20

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # communications_page.nml:23

    #: Ids, annotated so the hand-written half completes them.
    keepalive: MaskedField    # communications_page.nml:26
    keepalive_unit: StaticText    # communications_page.nml:37
    timeout: MaskedField    # communications_page.nml:45
    timeout_unit: StaticText    # communications_page.nml:56
    idle_disconnect: MaskedField    # communications_page.nml:64
    idle_unit: StaticText    # communications_page.nml:75
    refresh: MaskedField    # communications_page.nml:83
    refresh_unit: StaticText    # communications_page.nml:94
    upload_caption: Label    # communications_page.nml:102
    upload_changed: RadioButtons    # communications_page.nml:110
    desktop_vfs_caption: Label    # communications_page.nml:120
    desktop_vfs: RadioButtons    # communications_page.nml:130
    ssh_options: Field    # communications_page.nml:141
    notifications_caption: Label    # communications_page.nml:153
    notifications: RadioButtons    # communications_page.nml:162

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.keepalive = MaskedField(parent=self)    # communications_page.nml:25
        self.keepalive_unit = StaticText(parent=self)    # communications_page.nml:36
        self.timeout = MaskedField(parent=self)    # communications_page.nml:44
        self.timeout_unit = StaticText(parent=self)    # communications_page.nml:55
        self.idle_disconnect = MaskedField(parent=self)    # communications_page.nml:63
        self.idle_unit = StaticText(parent=self)    # communications_page.nml:74
        self.refresh = MaskedField(parent=self)    # communications_page.nml:82
        self.refresh_unit = StaticText(parent=self)    # communications_page.nml:93
        self.upload_caption = Label(parent=self)    # communications_page.nml:101
        self.upload_changed = RadioButtons(parent=self)    # communications_page.nml:109
        self.desktop_vfs_caption = Label(parent=self)    # communications_page.nml:119
        self.desktop_vfs = RadioButtons(parent=self)    # communications_page.nml:129
        self.ssh_options = Field(parent=self)    # communications_page.nml:140
        self.notifications_caption = Label(parent=self)    # communications_page.nml:152
        self.notifications = RadioButtons(parent=self)    # communications_page.nml:161

        self.keepalive.key = 'keepalive'    # communications_page.nml:27
        self.keepalive.x = 3    # communications_page.nml:28
        self.keepalive.y = 1    # communications_page.nml:29
        self.keepalive.width = 33    # communications_page.nml:30
        self.keepalive.label_text = _bind(    # communications_page.nml:31
            lambda _o: _tr('~K~eep-alive every'),
            yielding=True,
        )
        self.keepalive.label_width = 28    # communications_page.nml:32
        self.keepalive.mask = '999'    # communications_page.nml:33
        self.keepalive.page_keys = False    # communications_page.nml:34

        self.keepalive_unit.y = 1    # communications_page.nml:38
        self.keepalive_unit.text = _bind(    # communications_page.nml:42
            lambda _o: _tr('seconds (0: never)'),
            yielding=True,
        )
        self.keepalive_unit.x = 37    # communications_page.nml:40
        self.keepalive_unit.width = _bind(    # communications_page.nml:41
            lambda _o: max(0, _o.parent.width - 40)
        )

        self.timeout.key = 'timeout'    # communications_page.nml:46
        self.timeout.x = 3    # communications_page.nml:47
        self.timeout.y = 2    # communications_page.nml:48
        self.timeout.width = 33    # communications_page.nml:49
        self.timeout.label_text = _bind(    # communications_page.nml:50
            lambda _o: _tr('Connecting ~w~aits'),
            yielding=True,
        )
        self.timeout.label_width = 28    # communications_page.nml:51
        self.timeout.mask = '999'    # communications_page.nml:52
        self.timeout.page_keys = False    # communications_page.nml:53

        self.timeout_unit.y = 2    # communications_page.nml:57
        self.timeout_unit.text = _bind(    # communications_page.nml:61
            lambda _o: _tr('seconds'),
            yielding=True,
        )
        self.timeout_unit.x = 37    # communications_page.nml:59
        self.timeout_unit.width = _bind(    # communications_page.nml:60
            lambda _o: max(0, _o.parent.width - 40)
        )

        self.idle_disconnect.key = 'idle_disconnect'    # communications_page.nml:65
        self.idle_disconnect.x = 3    # communications_page.nml:66
        self.idle_disconnect.y = 3    # communications_page.nml:67
        self.idle_disconnect.width = 33    # communications_page.nml:68
        self.idle_disconnect.label_text = _bind(    # communications_page.nml:69
            lambda _o: _tr('~C~lose an idle connection'),
            yielding=True,
        )
        self.idle_disconnect.label_width = 28    # communications_page.nml:70
        self.idle_disconnect.mask = '999'    # communications_page.nml:71
        self.idle_disconnect.page_keys = False    # communications_page.nml:72

        self.idle_unit.y = 3    # communications_page.nml:76
        self.idle_unit.text = _bind(    # communications_page.nml:80
            lambda _o: _tr('minutes (0: never)'),
            yielding=True,
        )
        self.idle_unit.x = 37    # communications_page.nml:78
        self.idle_unit.width = _bind(lambda _o: max(0, _o.parent.width - 40))    # communications_page.nml:79

        self.refresh.key = 'refresh'    # communications_page.nml:84
        self.refresh.x = 3    # communications_page.nml:85
        self.refresh.y = 4    # communications_page.nml:86
        self.refresh.width = 33    # communications_page.nml:87
        self.refresh.label_text = _bind(    # communications_page.nml:88
            lambda _o: _tr('~L~ook for changes every'),
            yielding=True,
        )
        self.refresh.label_width = 28    # communications_page.nml:89
        self.refresh.mask = '999'    # communications_page.nml:90
        self.refresh.page_keys = False    # communications_page.nml:91

        self.refresh_unit.y = 4    # communications_page.nml:95
        self.refresh_unit.text = _bind(    # communications_page.nml:99
            lambda _o: _tr('seconds (0: never)'),
            yielding=True,
        )
        self.refresh_unit.x = 37    # communications_page.nml:97
        self.refresh_unit.width = _bind(    # communications_page.nml:98
            lambda _o: max(0, _o.parent.width - 40)
        )

        self.upload_caption.x = 3    # communications_page.nml:103
        self.upload_caption.y = 6    # communications_page.nml:104
        self.upload_caption.width = 50    # communications_page.nml:105
        self.upload_caption.text = _bind(    # communications_page.nml:106
            lambda _o: _tr('A fetched file a program changed goes ~b~ack'),
            yielding=True,
        )
        self.upload_caption.link = _bind(lambda _o: self.upload_changed)    # communications_page.nml:107

        self.upload_changed.key = 'upload_changed'    # communications_page.nml:111
        self.upload_changed.y = 7    # communications_page.nml:112
        self.upload_changed.height = 1    # communications_page.nml:113
        self.upload_changed.items = _bind(    # communications_page.nml:117
            lambda _o: [_tr('~A~sk first'), _tr('Alwa~y~s'), _tr('Ne~v~er')],
            yielding=True,
        )
        self.upload_changed.x = 3    # communications_page.nml:115
        self.upload_changed.width = _bind(    # communications_page.nml:116
            lambda _o: max(0, _o.parent.width - 6)
        )

        self.desktop_vfs_caption.y = 9    # communications_page.nml:121
        self.desktop_vfs_caption.text = _bind(    # communications_page.nml:125
            lambda _o: _tr('~D~esktop integration: volumes, links, opening files'),
            yielding=True,
        )
        self.desktop_vfs_caption.link = _bind(lambda _o: self.desktop_vfs)    # communications_page.nml:126
        self.desktop_vfs_caption.x = 3    # communications_page.nml:123
        self.desktop_vfs_caption.width = _bind(    # communications_page.nml:124
            lambda _o: max(0, _o.parent.width - 6)
        )

        self.desktop_vfs.key = 'system.desktop_vfs'    # communications_page.nml:131
        self.desktop_vfs.y = 10    # communications_page.nml:132
        self.desktop_vfs.height = 2    # communications_page.nml:133
        self.desktop_vfs.items = _bind(    # communications_page.nml:137
            lambda _o: [_tr('Au~t~o'), _tr('~G~IO (GNOME, Xfce...)'), _tr('K~I~O (KDE)'), _tr('~O~ff')],
            yielding=True,
        )
        self.desktop_vfs.x = 3    # communications_page.nml:135
        self.desktop_vfs.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # communications_page.nml:136

        self.ssh_options.key = 'ssh_options'    # communications_page.nml:142
        self.ssh_options.y = 13    # communications_page.nml:143
        self.ssh_options.label_text = _bind(    # communications_page.nml:147
            lambda _o: _tr("Remote shell's ss~h~ options"),
            yielding=True,
        )
        self.ssh_options.label_width = 28    # communications_page.nml:148
        self.ssh_options.x = 3    # communications_page.nml:145
        self.ssh_options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # communications_page.nml:146

        self.notifications_caption.y = 14    # communications_page.nml:154
        self.notifications_caption.text = _bind(    # communications_page.nml:158
            lambda _o: _tr('~N~otify when a long operation ends unwatched'),
            yielding=True,
        )
        self.notifications_caption.link = _bind(lambda _o: self.notifications)    # communications_page.nml:159
        self.notifications_caption.x = 3    # communications_page.nml:156
        self.notifications_caption.width = _bind(    # communications_page.nml:157
            lambda _o: max(0, _o.parent.width - 6)
        )

        self.notifications.key = 'system.notifications'    # communications_page.nml:163
        self.notifications.y = 15    # communications_page.nml:164
        self.notifications.height = 2    # communications_page.nml:165
        self.notifications.items = _bind(    # communications_page.nml:169
            lambda _o: [_tr('A~u~to'), _tr('Te~r~minal (OSC 9/777)'), _tr('notify-~s~end'), _tr('O~f~f')],
            yielding=True,
        )
        self.notifications.x = 3    # communications_page.nml:167
        self.notifications.width = _bind(    # communications_page.nml:168
            lambda _o: max(0, _o.parent.width - 6)
        )

        self._navml_built(__class__)
