# navml: generated
"""The merged surface of ``navigator.widgets.select_dialog.select_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

from typing import Any
from navml.history import HISTORY


class SelectDialog(Dialog, _Component):
    select: bool
    mask_caption: Label
    mask: Field
    options: CheckBoxes
    DEFAULT_MASK: _Any
    def __init__(self, invert: bool = ..., **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
