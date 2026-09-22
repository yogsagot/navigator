# navml: generated
"""The merged surface of ``navml.widgets.label``."""

from typing import Any as _Any

from navml.component import Component as _Component

from navkit.screen import Surface
from navkit.widget import Widget


class Label(_Component):
    text: str
    align: str
    def __init__(self, **kwargs: _Any) -> None: ...
    def render(self, surface: Surface) -> None: ...
