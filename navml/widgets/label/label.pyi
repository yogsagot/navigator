# navml: generated
"""The merged surface of ``navml.widgets.label.label``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.control import Control

from navkit.reactive import computed
from navkit.screen import Surface
from navkit.widget import Widget
from navml.widgets.control import Control, parse_shortcut
from navml.widgets.static_text import draw_caption


class Label(Control, _Component):
    text: str
    align: str
    link: _Any
    parts: _Any
    accepts_focus: _Any
    def __init__(self, **kwargs: _Any) -> None: ...
    selected: bool
    async def activate(self, letter: str = ...) -> bool: ...
    async def on_mouse_click(self, event) -> bool: ...
    def render(self, surface: Surface) -> None: ...
