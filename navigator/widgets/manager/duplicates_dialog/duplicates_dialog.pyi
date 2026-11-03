# navml: generated
"""The merged surface of ``navigator.widgets.manager.duplicates_dialog.duplicates_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any
from navkit.i18n import tr
from navigator.lib.file_ops import filefind
from navigator.lib.file_ops.duplicates import DuplicatesRequest


class DuplicatesDialog(Dialog, _Component):
    mask: Field
    min_size: Field
    options: CheckBoxes
    def __init__(self, **kwargs: Any) -> None: ...
    def valid(self) -> bool: ...
    def accept(self) -> DuplicatesRequest: ...
