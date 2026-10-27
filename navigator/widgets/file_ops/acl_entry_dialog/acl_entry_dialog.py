"""What the ACL entry box opens on and what OK means: ``(default, kind, id, perms)``.

**The name is picked from the list *Type* chooses**: switching *Type* swaps
the list, and keeps the name only if the other list has it too.  An entry
naming an id with no name -- a user since removed -- is still offered, as
the *Mode* page offers a file's nameless owner (``with_current``).

**The mask names no one**: editing it, *Type* and *Name* are inert and only
*Permissions* counts.  Editing any entry, whom it names and whether it is a
default stay as they were -- a different entry is a new one, *Add*.
"""

from __future__ import annotations

from typing import Any, Sequence

from navkit.i18n import tr
from navkit.reactive import effect, untracked

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops import acl, fileattr
from navigator.widgets.file_ops.attr_dialog.attr_dialog import with_current

#: *Type*'s items, as keys spell them.
KINDS = (acl.KIND_USER, acl.KIND_GROUP)


class AclEntryDialog(Dialog):
    """One ACL entry: whom it names, what it allows, and whether it is a default."""

    def __init__(
        self,
        users: Sequence[str] = (),
        groups: Sequence[str] = (),
        *,
        kind: str = acl.KIND_USER,
        name: str = "",
        perms: int = acl.READ,
        default: bool = False,
        can_default: bool = False,
        editing: bool = False,
        mask: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        self._users = list(users)
        self._groups = list(groups)
        self._mask = mask
        self.kind.value = KINDS.index(kind) if kind in KINDS else 0
        self.who.value = name
        self.who.choices = self._choices(name)
        self.perms.value = perms & acl.RWX
        self.default_box.value = 1 if default else 0
        self.default_box.disabled = editing or not can_default
        if editing:
            self.title = tr("Edit ACL Entry")
        if editing or mask:
            self.kind.disabled = True
            self.kind_caption.disabled = True
            self.who.disabled = True
        if mask:
            self.who.value = tr("mask")

    def mounted(self) -> None:
        super().mounted()
        effect(self, AclEntryDialog._kind_changed)

    def _choices(self, current: str) -> list[str]:
        names = self._users if KINDS[self.kind.value] == acl.KIND_USER else self._groups
        return with_current(names, current)

    def _kind_changed(self) -> None:
        self.kind.value  # noqa: B018 -- what the list follows
        with untracked():
            if self._mask or self.who.disabled:
                return
            current = self.who.value
            names = self._users if KINDS[self.kind.value] == acl.KIND_USER else self._groups
            if current not in names:
                current = ""
                self.who.value = ""
            self.who.choices = self._choices(current)

    def build(self) -> tuple[bool, str, int | None, int]:
        """The entry, or ``ValueError`` naming what is wrong."""
        perms = self.perms.value & acl.RWX
        default = bool(self.default_box.value)
        if self._mask:
            return default, acl.MASK_KEY[0], None, perms
        kind = KINDS[self.kind.value]
        if not self.who.value.strip():
            raise ValueError(tr("Choose a user") if kind == acl.KIND_USER else tr("Choose a group"))
        parse = fileattr.parse_user if kind == acl.KIND_USER else fileattr.parse_group
        ident = parse(self.who.value)
        return default, kind, ident, perms

    def valid(self) -> bool:
        try:
            self.build()
        except ValueError as error:
            if self.application is not None:
                box = Dialog(title=tr("Error"), prompt=escape_caption(str(error)), buttons="ok")
                self.spawn(box.execute(self.application))
            return False
        return True

    def accept(self) -> tuple[bool, str, int | None, int]:
        return self.build()
