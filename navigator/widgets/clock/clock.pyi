# navml: generated
"""The merged surface of ``navigator.widgets.clock.clock``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.timer import Timer

from datetime import datetime
from navkit.screen import Surface
from navkit.widget import Widget


class Clock(_Component):
    blink: bool
    tick: Timer
    def __init__(self, **kwargs: _Any) -> None: ...
    def text(self) -> str: ...
    def render(self, surface: Surface) -> None: ...
