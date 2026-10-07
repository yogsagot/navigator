# navml: generated
"""The merged surface of ``navml.widgets.dialog.group_box.group_box``."""

from typing import Any as _Any

from navml.component import Component as _Component

from navkit import glyphs as glyphs_module
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget
from navml.widgets.dialog.static_text import draw_caption


class GroupBox(_Component):
    title: str
    border: _Any
    parts: _Any
    def __init__(self, **kwargs: _Any) -> None: ...
    def render(self, surface: Surface) -> None: ...
