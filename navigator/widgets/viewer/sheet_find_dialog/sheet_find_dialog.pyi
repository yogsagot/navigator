# navml: generated
"""The merged surface of ``navigator.widgets.viewer.sheet_find_dialog.sheet_find_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navigator.lib.viewer.table import CellSearch


class SheetFindDialog(Dialog, _Component):
    pattern: Field
    search_as_caption: Label
    search_as: RadioButtons
    options: CheckBoxes
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> CellSearch | None: ...
