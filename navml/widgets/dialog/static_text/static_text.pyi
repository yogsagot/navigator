# navml: generated
"""The merged surface of ``navml.widgets.dialog.static_text.static_text``."""

from typing import Any as _Any

from navml.component import Component as _Component

import re
from navkit.screen import Surface, char_width
from navkit.style import Style
from navkit.widget import Widget
from navml.widgets.dialog.control import parse_shortcut


class StaticText(_Component):
    text: str
    align: str
    wrap: bool
    links: bool
    parts: _Any
    def __init__(self, **kwargs: _Any) -> None: ...
    def render(self, surface: Surface) -> None: ...
