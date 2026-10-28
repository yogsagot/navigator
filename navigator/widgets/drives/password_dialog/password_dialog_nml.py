# navml: generated
"""Generated from ``password_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # password_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # password_dialog.nml:2
from navml.widgets.dialog.field import Field    # password_dialog.nml:3

__navml_component__ = "PasswordDialog"

__all__ = ["PasswordDialog"]


class PasswordDialog(Dialog, _Component):
    """A server's password, or a private key's passphrase, asked when a

    connection needs one (``navigator/lib/drives/sessions.py``).

    Not DN's: its Navigator Link needed no password across a cable.  The
    shape of F7's ``InputBox``, with the line masked and one box under it.
    """

    #: The document this class was generated from.
    __navml_source__ = "password_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    entry: Field    # password_dialog.nml:16
    keep: CheckBoxes    # password_dialog.nml:26

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.entry = Field(parent=self)    # password_dialog.nml:15
        self.keep = CheckBoxes(parent=self)    # password_dialog.nml:25

        self.modal_width = 58    # password_dialog.nml:11
        self.modal_height = 10    # password_dialog.nml:12
        self.title = _bind(lambda _o: _tr('Password'), yielding=True)    # password_dialog.nml:13

        self.entry.x = 2    # password_dialog.nml:17
        self.entry.y = 3    # password_dialog.nml:18
        self.entry.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # password_dialog.nml:19
        self.entry.height = 1    # password_dialog.nml:20
        self.entry.label_text = _bind(    # password_dialog.nml:21
            lambda _o: _tr('~P~assword'),
            yielding=True,
        )
        self.entry.label_width = 11    # password_dialog.nml:22

        self.keep.x = 3    # password_dialog.nml:27
        self.keep.y = 5    # password_dialog.nml:28
        self.keep.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # password_dialog.nml:29
        self.keep.height = 1    # password_dialog.nml:30
        self.keep.items = _bind(    # password_dialog.nml:31
            lambda _o: [_tr('~S~ave in keyring')],
            yielding=True,
        )
        self.keep.tooltips = _bind(    # password_dialog.nml:32
            lambda _o: [_tr("Remember the password in the desktop's keyring, so it is not asked again")],
            yielding=True,
        )
