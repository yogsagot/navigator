# navml: generated
"""The merged surface of ``navigator.widgets.setup.column_defaults_dialog.column_defaults_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label

from typing import Any
from navigator.settings import SETTINGS, ColumnDefaultsData


class ColumnDefaultsDialog(Dialog, _Component):
    disk_caption: Label
    disk: CheckBoxes
    find_caption: Label
    find: CheckBoxes
    def __init__(self, section: ColumnDefaultsData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
