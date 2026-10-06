# navml: generated
"""The merged surface of ``navigator.widgets.manager.columns_dialog.columns_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label

from typing import Any
from navkit.events import Event


class ColumnsDialog(Dialog, _Component):
    show_caption: Label
    show: CheckBoxes
    brief: Button
    full: Button
    pick: Button
    abandon: Button
    def __init__(self, columns: frozenset[str] = ..., listing: bool = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> tuple[str, frozenset[str]]: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_brief_click(self, event: Event) -> bool: ...
    async def on_full_click(self, event: Event) -> bool: ...
