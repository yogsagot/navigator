# navml: generated
"""The merged surface of ``navml.widgets.window_manager.window_manager``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.window_list import WindowList

from typing import Any
from navkit.events import Event
from navkit.reactive import effect


class WindowManagerDialog(Dialog, _Component):
    caption: Label
    windows: WindowList
    pick: Button
    shut: Button
    abandon: Button
    helper: Button
    def __init__(self, desktop: Any = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_helper_click(self, event: _Event) -> bool: ...
    def mounted(self) -> None: ...
    def _close_follows_window(self) -> None: ...
    def refresh(self) -> None: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> Any: ...
    def close_selected(self) -> None: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_windows_chosen(self, event: Any) -> bool: ...
    async def on_shut_click(self, event: Event) -> bool: ...
