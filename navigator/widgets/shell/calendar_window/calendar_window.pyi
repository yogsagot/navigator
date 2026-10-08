# navml: generated
"""The merged surface of ``navigator.widgets.shell.calendar_window.calendar_window``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.commands import CloseWindow
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.date_button import CalendarView
from navml.widgets.window import Window

import datetime
from navkit.events import Event, KeyEvent


class CalendarWindow(Window, _Component):
    month: CalendarView
    today_button: Button
    def __init__(self, **kwargs: _Any) -> None: ...
    def go_to_today(self) -> None: ...
    async def on_today_button_click(self, event: Event) -> bool: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
