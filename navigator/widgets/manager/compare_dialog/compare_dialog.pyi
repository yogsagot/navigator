# navml: generated
"""The merged surface of ``navigator.widgets.manager.compare_dialog.compare_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navigator.dircompare import CompareRequest


class CompareDialog(Dialog, _Component):
    options_caption: Label
    options: CheckBoxes
    mode_caption: Label
    mode: RadioButtons
    def __init__(self, **kwargs: _Any) -> None: ...
    def accept(self) -> Any: ...
