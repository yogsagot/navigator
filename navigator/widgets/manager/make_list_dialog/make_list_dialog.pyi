# navml: generated
"""The merged surface of ``navigator.widgets.manager.make_list_dialog.make_list_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any
from navml.history import HISTORY
from navigator.makelist import DEFAULT_NAME


class MakeListDialog(Dialog, _Component):
    file_name: Field
    action: Field
    options: CheckBoxes
    def __init__(self, options: int = ..., **kwargs: Any) -> None: ...
    def accept(self) -> tuple[str, str, int] | None: ...
