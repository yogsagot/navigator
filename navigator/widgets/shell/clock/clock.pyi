# navml: generated
"""The merged surface of ``navigator.widgets.shell.clock.clock``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.timer import Timer

from datetime import datetime
from navkit.events import MouseClickEvent
from navkit.i18n import tr
from navkit.screen import Surface
from navkit.widget import Widget
from navml.widgets.dialog.date_button.date_button import weekday_full_names
from navigator.lib.config import country
from navigator.widgets.shell.commands import OpenCalendar


class Clock(_Component):
    blink: bool
    tick: Timer
    def __init__(self, **kwargs: _Any) -> None: ...
    def text(self) -> str: ...
    def tooltip_at(self, x: int, y: int) -> str: ...
    async def on_mouse_click(self, event: MouseClickEvent) -> bool: ...
    def render(self, surface: Surface) -> None: ...
