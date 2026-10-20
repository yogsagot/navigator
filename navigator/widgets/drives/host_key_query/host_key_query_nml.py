# navml: generated
"""Generated from ``host_key_query.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # host_key_query.nml:1

__navml_component__ = "HostKeyQuery"

__all__ = ["HostKeyQuery"]


class HostKeyQuery(Dialog, _Component):
    """A server whose host key ``known_hosts`` does not have: what ``ssh`` asks

    as *Are you sure you want to continue connecting?*, as a box.

    *Accept* trusts the key for this connection, *Save* writes it to
    ``~/.ssh/known_hosts`` too, and Cancel does not connect.
    """

    #: The document this class was generated from.
    __navml_source__ = "host_key_query.nml"

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)

        self.modal_width = 64    # host_key_query.nml:9
        self.modal_height = 11    # host_key_query.nml:10
        self.title = _bind(lambda _o: _tr('Unknown SSH host'), yielding=True)    # host_key_query.nml:11
        self.buttons = 'yes-no-cancel'    # host_key_query.nml:12
