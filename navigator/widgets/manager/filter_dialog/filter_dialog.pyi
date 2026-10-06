# navml: generated
"""The merged surface of ``navigator.widgets.manager.filter_dialog.filter_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.manager.filter_dialog.filter_list import FilterList
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog

from typing import Any
from navkit.events import Event


class FilterDialog(Dialog, _Component):
    masks: FilterList
    show: Button
    hide: Button
    abandon: Button
    def __init__(self, masks: list[str] | None = ..., cursor: int = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def chosen(self) -> list[str]: ...
    def _answer(self, show: bool) -> None: ...
    async def on_show_click(self, event: Event) -> bool: ...
    async def on_hide_click(self, event: Event) -> bool: ...
