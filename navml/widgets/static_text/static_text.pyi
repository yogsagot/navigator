# navml: generated
"""The merged surface of ``navml.widgets.static_text.static_text``."""

from typing import Any as _Any

from navml.component import Component as _Component

from navkit.screen import Surface
from navkit.style import Style
from navkit.widget import Widget
from navml.widgets.control import parse_shortcut


class StaticText(_Component):
    text: str
    align: str
    wrap: bool
    parts: _Any
    def __init__(self, **kwargs: _Any) -> None: ...
    def render(self, surface: Surface) -> None: ...
