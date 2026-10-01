# navml: generated
"""The merged surface of ``navml.widgets.dialog.date_field.date_field``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.date_button import DateButton
from navml.widgets.dialog.masked_line import MaskedLine, mask_for
from navml.widgets.layout.horizontal_layout import HorizontalLayout
from navml.widgets.dialog.label import Label


class DateField(HorizontalLayout, _Component):
    label_text: str
    label_width: int
    date_format: str
    value: str
    caption: Label
    entry: MaskedLine
    picker: DateButton
    def __init__(self, **kwargs: _Any) -> None: ...
