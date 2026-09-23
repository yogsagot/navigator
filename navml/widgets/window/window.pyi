# navml: generated
"""The merged surface of ``navml.widgets.window.window``."""

from typing import Any as _Any

from navml.component import Component as _Component

from typing import Iterator
from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import BOX_CHARSETS
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget
from navml.widgets.control import Control


class Window(_Component):
    title: str
    closable: bool
    border: _Any
    parts: _Any
    def __init__(self, **kwargs: _Any) -> None: ...
    def controls(self) -> Iterator[Control]: ...
    async def activate_shortcut(self, letter: str) -> bool: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
    async def on_mouse_click(self, event: MouseClickEvent) -> bool: ...
    def close(self) -> None: ...
    def render(self, surface: Surface) -> None: ...
