# navml: generated
"""The merged surface of ``navml.widgets.dialog.time_field.time_field``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.time_button import TimeButton
from navml.widgets.dialog.masked_line import MaskedLine, mask_for
from navml.widgets.layout.horizontal_layout import HorizontalLayout
from navml.widgets.dialog.label import Label


class TimeField(HorizontalLayout, _Component):
    label_text: str
    label_width: int
    time_format: str
    value: str
    caption: Label
    entry: MaskedLine
    picker: TimeButton
    def __init__(self, **kwargs: _Any) -> None: ...
