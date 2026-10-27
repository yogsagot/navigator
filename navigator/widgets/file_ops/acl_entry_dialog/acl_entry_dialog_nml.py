# navml: generated
"""Generated from ``acl_entry_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # acl_entry_dialog.nml:1
from navml.widgets.dialog.choice_field import ChoiceField    # acl_entry_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # acl_entry_dialog.nml:3
from navml.widgets.dialog.label import Label    # acl_entry_dialog.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # acl_entry_dialog.nml:5

__navml_component__ = "AclEntryDialog"

__all__ = ["AclEntryDialog"]


class AclEntryDialog(Dialog, _Component):
    """Alt+E's *ACL* page, *Add* or *Edit*: one entry of a POSIX ACL.  Not DN's.

    Whom it names is picked, never typed, as the *Mode* page's owner and group
    are: *Type* says from which list, the passwd database's or the group
    database's -- all of either, since an ACL may name anyone -- and any key on
    *Name* drops it, typing searching it.  *Default* puts the entry in a
    directory's default ACL, which what is made in it inherits.
    """

    #: The document this class was generated from.
    __navml_source__ = "acl_entry_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    kind_caption: Label    # acl_entry_dialog.nml:21
    kind: RadioButtons    # acl_entry_dialog.nml:30
    who: ChoiceField    # acl_entry_dialog.nml:38
    perms_caption: Label    # acl_entry_dialog.nml:47
    perms: CheckBoxes    # acl_entry_dialog.nml:56
    default_box: CheckBoxes    # acl_entry_dialog.nml:64

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.kind_caption = Label(parent=self)    # acl_entry_dialog.nml:20
        self.kind = RadioButtons(parent=self)    # acl_entry_dialog.nml:29
        self.who = ChoiceField(parent=self)    # acl_entry_dialog.nml:37
        self.perms_caption = Label(parent=self)    # acl_entry_dialog.nml:46
        self.perms = CheckBoxes(parent=self)    # acl_entry_dialog.nml:55
        self.default_box = CheckBoxes(parent=self)    # acl_entry_dialog.nml:63

        self.modal_width = 56    # acl_entry_dialog.nml:15
        self.modal_height = 13    # acl_entry_dialog.nml:16
        self.title = _bind(lambda _o: _tr('ACL Entry'), yielding=True)    # acl_entry_dialog.nml:17
        self.buttons = 'ok-cancel'    # acl_entry_dialog.nml:18

        self.kind_caption.x = 2    # acl_entry_dialog.nml:22
        self.kind_caption.y = 1    # acl_entry_dialog.nml:23
        self.kind_caption.width = 12    # acl_entry_dialog.nml:24
        self.kind_caption.height = 1    # acl_entry_dialog.nml:25
        self.kind_caption.text = _bind(lambda _o: _tr('~T~ype'), yielding=True)    # acl_entry_dialog.nml:26
        self.kind_caption.link = _bind(lambda _o: self.kind)    # acl_entry_dialog.nml:27

        self.kind.x = 14    # acl_entry_dialog.nml:31
        self.kind.y = 1    # acl_entry_dialog.nml:32
        self.kind.width = _bind(lambda _o: max(0, _o.parent.width - 16))    # acl_entry_dialog.nml:33
        self.kind.height = 1    # acl_entry_dialog.nml:34
        self.kind.items = _bind(    # acl_entry_dialog.nml:35
            lambda _o: [_tr('User'), _tr('Group')],
            yielding=True,
        )

        self.who.x = 2    # acl_entry_dialog.nml:39
        self.who.y = 3    # acl_entry_dialog.nml:40
        self.who.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # acl_entry_dialog.nml:41
        self.who.height = 1    # acl_entry_dialog.nml:42
        self.who.label_text = _bind(lambda _o: _tr('~N~ame'), yielding=True)    # acl_entry_dialog.nml:43
        self.who.label_width = 12    # acl_entry_dialog.nml:44

        self.perms_caption.x = 2    # acl_entry_dialog.nml:48
        self.perms_caption.y = 5    # acl_entry_dialog.nml:49
        self.perms_caption.width = 12    # acl_entry_dialog.nml:50
        self.perms_caption.height = 1    # acl_entry_dialog.nml:51
        self.perms_caption.text = _bind(    # acl_entry_dialog.nml:52
            lambda _o: _tr('~P~ermissions'),
            yielding=True,
        )
        self.perms_caption.link = _bind(lambda _o: self.perms)    # acl_entry_dialog.nml:53

        self.perms.x = 14    # acl_entry_dialog.nml:57
        self.perms.y = 5    # acl_entry_dialog.nml:58
        self.perms.width = _bind(lambda _o: max(0, _o.parent.width - 16))    # acl_entry_dialog.nml:59
        self.perms.height = 1    # acl_entry_dialog.nml:60
        self.perms.items = _bind(    # acl_entry_dialog.nml:61
            lambda _o: [_tr('Read'), _tr('Write'), _tr('Exec')],
            yielding=True,
        )

        self.default_box.x = 14    # acl_entry_dialog.nml:65
        self.default_box.y = 7    # acl_entry_dialog.nml:66
        self.default_box.width = _bind(lambda _o: max(0, _o.parent.width - 16))    # acl_entry_dialog.nml:67
        self.default_box.height = 1    # acl_entry_dialog.nml:68
        self.default_box.items = _bind(    # acl_entry_dialog.nml:69
            lambda _o: [_tr('~D~efault, inherited by new files')],
            yielding=True,
        )
