# navml: generated
"""Generated from ``forward_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # forward_dialog.nml:1
from navml.widgets.dialog.field import Field    # forward_dialog.nml:2
from navml.widgets.dialog.label import Label    # forward_dialog.nml:3
from navml.widgets.dialog.radio_buttons import RadioButtons    # forward_dialog.nml:4
from navml.widgets.dialog.static_text import StaticText    # forward_dialog.nml:5

__navml_component__ = "ForwardDialog"

__all__ = ["ForwardDialog"]


class ForwardDialog(Dialog, _Component):
    """One port forward of an SSH connection, as ``ssh``'s ``-L``, ``-R`` or

    ``-D`` would take it (``navigator/lib/drives/forwards.py``).  Ours: DN's
    link was a cable, with no ports to forward.  The kind down the left with
    what it does beside it, the two ends under them; a dynamic forward has
    no destination, its SOCKS client says where.
    """

    #: The document this class was generated from.
    __navml_source__ = "forward_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    kind_caption: Label    # forward_dialog.nml:18
    kind: RadioButtons    # forward_dialog.nml:26
    about: StaticText    # forward_dialog.nml:35
    bind: Field    # forward_dialog.nml:45
    port: Field    # forward_dialog.nml:55
    host: Field    # forward_dialog.nml:64
    host_port: Field    # forward_dialog.nml:74
    problem: StaticText    # forward_dialog.nml:84

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.kind_caption = Label(parent=self)    # forward_dialog.nml:17
        self.kind = RadioButtons(parent=self)    # forward_dialog.nml:25
        self.about = StaticText(parent=self)    # forward_dialog.nml:34
        self.bind = Field(parent=self)    # forward_dialog.nml:44
        self.port = Field(parent=self)    # forward_dialog.nml:54
        self.host = Field(parent=self)    # forward_dialog.nml:63
        self.host_port = Field(parent=self)    # forward_dialog.nml:73
        self.problem = StaticText(parent=self)    # forward_dialog.nml:83

        self.modal_width = 62    # forward_dialog.nml:13
        self.modal_height = 16    # forward_dialog.nml:14
        self.title = _bind(lambda _o: _tr('Port forward'), yielding=True)    # forward_dialog.nml:15

        self.kind_caption.x = 2    # forward_dialog.nml:19
        self.kind_caption.y = 1    # forward_dialog.nml:20
        self.kind_caption.width = 20    # forward_dialog.nml:21
        self.kind_caption.text = _bind(lambda _o: _tr('Kind'), yielding=True)    # forward_dialog.nml:22
        self.kind_caption.link = _bind(lambda _o: self.kind)    # forward_dialog.nml:23

        self.kind.x = 3    # forward_dialog.nml:27
        self.kind.y = 2    # forward_dialog.nml:28
        self.kind.width = 24    # forward_dialog.nml:29
        self.kind.height = 3    # forward_dialog.nml:30
        self.kind.items = _bind(    # forward_dialog.nml:31
            lambda _o: [_tr('~L~ocal (-L)'), _tr('~R~emote (-R)'), _tr('~D~ynamic, SOCKS (-D)')],
            yielding=True,
        )

        self.about.y = 2    # forward_dialog.nml:36
        self.about.height = 3    # forward_dialog.nml:37
        self.about.text = ''    # forward_dialog.nml:41
        self.about.wrap = True    # forward_dialog.nml:42
        self.about.x = 29    # forward_dialog.nml:39
        self.about.width = _bind(lambda _o: max(0, _o.parent.width - 31))    # forward_dialog.nml:40

        self.bind.y = 6    # forward_dialog.nml:46
        self.bind.label_text = _bind(    # forward_dialog.nml:50
            lambda _o: _tr('Listen ~a~ddress'),
            yielding=True,
        )
        self.bind.label_width = 19    # forward_dialog.nml:51
        self.bind.history_id = 'forward_bind'    # forward_dialog.nml:52
        self.bind.x = 2    # forward_dialog.nml:48
        self.bind.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # forward_dialog.nml:49

        self.port.x = 2    # forward_dialog.nml:56
        self.port.y = 7    # forward_dialog.nml:57
        self.port.width = 30    # forward_dialog.nml:58
        self.port.label_text = _bind(    # forward_dialog.nml:59
            lambda _o: _tr('Listen ~p~ort'),
            yielding=True,
        )
        self.port.label_width = 19    # forward_dialog.nml:60
        self.port.history_id = 'forward_port'    # forward_dialog.nml:61

        self.host.y = 8    # forward_dialog.nml:65
        self.host.label_text = _bind(    # forward_dialog.nml:69
            lambda _o: _tr('Destination ~h~ost'),
            yielding=True,
        )
        self.host.label_width = 19    # forward_dialog.nml:70
        self.host.history_id = 'forward_host'    # forward_dialog.nml:71
        self.host.x = 2    # forward_dialog.nml:67
        self.host.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # forward_dialog.nml:68

        self.host_port.x = 2    # forward_dialog.nml:75
        self.host_port.y = 9    # forward_dialog.nml:76
        self.host_port.width = 30    # forward_dialog.nml:77
        self.host_port.label_text = _bind(    # forward_dialog.nml:78
            lambda _o: _tr('Destination p~o~rt'),
            yielding=True,
        )
        self.host_port.label_width = 19    # forward_dialog.nml:79
        self.host_port.history_id = 'forward_host_port'    # forward_dialog.nml:80

        self.problem.y = 10    # forward_dialog.nml:85
        self.problem.height = 2    # forward_dialog.nml:86
        self.problem.text = ''    # forward_dialog.nml:90
        self.problem.wrap = True    # forward_dialog.nml:91
        self.problem.x = 2    # forward_dialog.nml:88
        self.problem.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # forward_dialog.nml:89
