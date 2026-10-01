# navml: generated
"""The merged surface of ``navml.widgets.dialog.masked_field.masked_field``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.masked_line import MaskedLine
from navml.widgets.layout.horizontal_layout import HorizontalLayout
from navml.widgets.dialog.label import Label


class MaskedField(HorizontalLayout, _Component):
    label_text: str
    label_width: int
    mask: str
    base: int
    value: str
    caption: Label
    entry: MaskedLine
    def __init__(self, **kwargs: _Any) -> None: ...
