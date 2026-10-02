# navml: generated
"""The merged surface of ``navigator.widgets.setup.confirmations_dialog.confirmations_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog

from typing import Any
from navigator.settings import SETTINGS, ConfirmsData


class ConfirmationsDialog(Dialog, _Component):
    options: CheckBoxes
    def __init__(self, section: ConfirmsData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
