# navml: generated
"""The merged surface of ``navigator.widgets.setup.confirmations_page.confirmations_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes

from typing import Any
from navkit.widget import Widget
from navigator.settings import SETTINGS, ConfirmsData


class ConfirmationsPage(_Component):
    title: str
    options: CheckBoxes
    def __init__(self, section: ConfirmsData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
