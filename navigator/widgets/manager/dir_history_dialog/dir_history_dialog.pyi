# navml: generated
"""The merged surface of ``navigator.widgets.manager.dir_history_dialog.dir_history_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.manager.dir_history_dialog.dir_list import DirList
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog

from typing import Any
from navkit.events import Event
from navml.history import HISTORY


class DirHistoryDialog(Dialog, _Component):
    places: DirList
    pick: Button
    drop: Button
    abandon: Button
    def __init__(self, **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> str | None: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_places_chosen(self, event: Event) -> bool: ...
    async def on_drop_click(self, event: Event) -> bool: ...
