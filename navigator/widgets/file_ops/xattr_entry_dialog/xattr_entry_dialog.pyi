# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.xattr_entry_dialog.xattr_entry_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.static_text import StaticText

from typing import Any
from navkit.i18n import tr
from navml.widgets.dialog.control import escape_caption
from navigator.lib.file_ops import fileattr


class XattrEntryDialog(Dialog, _Component):
    attr_name: Field
    data: Field
    hint: StaticText
    def __init__(self, name: str = ..., value: bytes | None = ..., *, editing: bool = ..., **kwargs: Any) -> None: ...
    def build(self) -> tuple[str, bytes]: ...
    def valid(self) -> bool: ...
    def accept(self) -> tuple[str, bytes]: ...
