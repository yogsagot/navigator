# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.multi_rename_dialog.multi_rename_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navigator.widgets.file_ops.multi_rename_dialog.rename_preview import RenamePreview
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons
from navml.widgets.dialog.static_text import StaticText

from typing import Any, Hashable, Sequence
from navkit.i18n import tr, tr_n
from navkit.reactive import effect
from navigator.lib.file_ops import multirename


class MultiRenameDialog(Dialog, _Component):
    name_mask: Field
    ext_mask: Field
    search: Field
    replace: Field
    options: CheckBoxes
    case_caption: Label
    case: RadioButtons
    start: Field
    step: Field
    digits: Field
    preview: RenamePreview
    status: StaticText
    def __init__(self, items: Sequence[multirename.Item] = ..., taken: dict[Hashable, set[str]] | None = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def rule(self) -> multirename.Rule: ...
    def _follow_rule(self) -> None: ...
    def valid(self) -> bool: ...
    def accept(self) -> list[multirename.Row]: ...
