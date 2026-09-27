# navml: generated
"""The merged surface of ``navml.widgets.dialog.field.field``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.history import History
from navml.widgets.layout.horizontal_layout import HorizontalLayout
from navml.widgets.dialog.input_line import InputLine
from navml.widgets.dialog.label import Label


class Field(HorizontalLayout, _Component):
    label_text: str
    label_width: int
    history_id: str
    value: str
    caption: Label
    entry: InputLine
    history: History
    def __init__(self, **kwargs: _Any) -> None: ...
