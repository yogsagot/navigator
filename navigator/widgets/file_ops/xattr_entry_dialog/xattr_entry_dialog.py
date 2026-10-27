"""What the extended attribute box means: ``(name, value)``, the value as bytes.

The value is written as ``getfattr`` writes one
(:func:`~navigator.lib.file_ops.fileattr.spell_value`): text, quoted where it
would read otherwise, ``0x`` and hex digits, or ``0s`` and base64.  Editing,
the name stays as it was -- another name is another attribute, *Add*.
"""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops import fileattr


class XattrEntryDialog(Dialog):
    """One extended attribute: its name, seeded ``user.``, and its value."""

    def __init__(self, name: str = "user.", value: bytes | None = b"", *, editing: bool = False,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        self.attr_name.value = name
        self.data.value = "" if value is None else fileattr.spell_value(value)
        if editing:
            self.title = tr("Edit Extended Attribute")
            self.attr_name.disabled = True

    def build(self) -> tuple[str, bytes]:
        """The name and value, or ``ValueError`` naming what is wrong."""
        return fileattr.check_xattr_name(self.attr_name.value), fileattr.parse_value(self.data.value)

    def valid(self) -> bool:
        try:
            self.build()
        except ValueError as error:
            if self.application is not None:
                box = Dialog(title=tr("Error"), prompt=escape_caption(str(error)), buttons="ok")
                self.spawn(box.execute(self.application))
            return False
        return True

    def accept(self) -> tuple[str, bytes]:
        return self.build()
