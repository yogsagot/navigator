# navml: generated
"""The merged surface of ``navigator.widgets.setup.interface_dialog.interface_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.masked_field import MaskedField

from typing import Any
from navigator.settings import SETTINGS, InterfaceData


class InterfaceDialog(Dialog, _Component):
    options: CheckBoxes
    history_size: MaskedField
    def __init__(self, section: InterfaceData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
