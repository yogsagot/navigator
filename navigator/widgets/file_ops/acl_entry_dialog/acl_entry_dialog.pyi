# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.acl_entry_dialog.acl_entry_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.choice_field import ChoiceField
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any, Sequence
from navkit.i18n import tr
from navkit.reactive import effect, untracked
from navml.widgets.dialog.control import escape_caption
from navigator.lib.file_ops import acl, fileattr
from navigator.widgets.file_ops.attr_dialog.attr_dialog import with_current


class AclEntryDialog(Dialog, _Component):
    kind_caption: Label
    kind: RadioButtons
    who: ChoiceField
    perms_caption: Label
    perms: CheckBoxes
    default_box: CheckBoxes
    def __init__(self, users: Sequence[str] = ..., groups: Sequence[str] = ..., *, kind: str = ..., name: str = ..., perms: int = ..., default: bool = ..., can_default: bool = ..., editing: bool = ..., mask: bool = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def _choices(self, current: str) -> list[str]: ...
    def _kind_changed(self) -> None: ...
    def build(self) -> tuple[bool, str, int | None, int]: ...
    def valid(self) -> bool: ...
    def accept(self) -> tuple[bool, str, int | None, int]: ...
