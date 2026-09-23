# navml: generated
"""The merged surface of ``navml.widgets.field.field``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.static_text import StaticText


class Field(_Component):
    label_text: str
    value_text: str
    label_width: int
    caption: StaticText
    value: StaticText
    def __init__(self, **kwargs: _Any) -> None: ...
