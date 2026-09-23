# navml: generated
"""The merged surface of ``navml.widgets.field.field``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.input_line import InputLine
from navml.widgets.label import Label


class Field(_Component):
    label_text: str
    label_width: int
    value: str
    caption: Label
    entry: InputLine
    def __init__(self, **kwargs: _Any) -> None: ...
