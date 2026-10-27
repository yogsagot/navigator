# navml: generated
"""Generated from ``xattr_entry_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # xattr_entry_dialog.nml:1
from navml.widgets.dialog.field import Field    # xattr_entry_dialog.nml:2
from navml.widgets.dialog.static_text import StaticText    # xattr_entry_dialog.nml:3

__navml_component__ = "XattrEntryDialog"

__all__ = ["XattrEntryDialog"]


class XattrEntryDialog(Dialog, _Component):
    """Alt+E's *Xattrs* page, *Add* or *Edit*: one extended attribute, its name

    and its value in ``getfattr``'s spellings.  Not DN's.
    """

    #: The document this class was generated from.
    __navml_source__ = "xattr_entry_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    attr_name: Field    # xattr_entry_dialog.nml:14
    data: Field    # xattr_entry_dialog.nml:23
    hint: StaticText    # xattr_entry_dialog.nml:33

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.attr_name = Field(parent=self)    # xattr_entry_dialog.nml:13
        self.data = Field(parent=self)    # xattr_entry_dialog.nml:22
        self.hint = StaticText(parent=self)    # xattr_entry_dialog.nml:32

        self.modal_width = 60    # xattr_entry_dialog.nml:8
        self.modal_height = 11    # xattr_entry_dialog.nml:9
        self.title = _bind(lambda _o: _tr('Extended Attribute'), yielding=True)    # xattr_entry_dialog.nml:10
        self.buttons = 'ok-cancel'    # xattr_entry_dialog.nml:11

        self.attr_name.x = 2    # xattr_entry_dialog.nml:15
        self.attr_name.y = 1    # xattr_entry_dialog.nml:16
        self.attr_name.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # xattr_entry_dialog.nml:17
        self.attr_name.height = 1    # xattr_entry_dialog.nml:18
        self.attr_name.label_text = _bind(    # xattr_entry_dialog.nml:19
            lambda _o: _tr('~N~ame'),
            yielding=True,
        )
        self.attr_name.label_width = 8    # xattr_entry_dialog.nml:20

        self.data.x = 2    # xattr_entry_dialog.nml:24
        self.data.y = 3    # xattr_entry_dialog.nml:25
        self.data.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # xattr_entry_dialog.nml:26
        self.data.height = 1    # xattr_entry_dialog.nml:27
        self.data.label_text = _bind(lambda _o: _tr('Va~l~ue'), yielding=True)    # xattr_entry_dialog.nml:28
        self.data.label_width = 8    # xattr_entry_dialog.nml:29

        self.hint.x = 10    # xattr_entry_dialog.nml:34
        self.hint.y = 5    # xattr_entry_dialog.nml:35
        self.hint.width = _bind(lambda _o: max(0, _o.parent.width - 12))    # xattr_entry_dialog.nml:36
        self.hint.height = 2    # xattr_entry_dialog.nml:37
        self.hint.text = _bind(    # xattr_entry_dialog.nml:38
            lambda _o: _tr('Text, or 0x and hex digits, or 0s and base64; quotes round text keep it text'),
            yielding=True,
        )
