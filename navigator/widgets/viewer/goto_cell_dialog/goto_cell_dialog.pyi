# navml: generated
"""The merged surface of ``navigator.widgets.viewer.goto_cell_dialog.goto_cell_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any
from navigator.lib.viewer.table import parse_cell


class GotoCellDialog(Dialog, _Component):
    cell: Field
    def __init__(self, cell: str = ..., **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
