# navml: generated
"""The merged surface of ``navigator.widgets.viewer.table_format_dialog.table_format_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.choice_field import ChoiceField
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from dataclasses import replace
from typing import Any
from navigator.lib.viewer import ENCODINGS
from navigator.lib.viewer.table import DELIMITERS, Dialect


class TableFormatDialog(Dialog, _Component):
    delimiter_caption: Label
    delimiter: RadioButtons
    other: Field
    options: CheckBoxes
    encoding: ChoiceField
    def __init__(self, dialect: Dialect, **kwargs: Any) -> None: ...
    def accept(self) -> Dialect | None: ...
