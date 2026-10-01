# navml: generated
"""The merged surface of ``navml.widgets.dialog.choice_field.choice_field``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.choice_line import ChoiceLine
from navml.widgets.dialog.history import History
from navml.widgets.layout.horizontal_layout import HorizontalLayout
from navml.widgets.dialog.label import Label


class ChoiceField(HorizontalLayout, _Component):
    label_text: str
    label_width: int
    value: str
    choices: _Any
    caption: Label
    entry: ChoiceLine
    history: History
    def __init__(self, **kwargs: _Any) -> None: ...
