# navml: generated
"""The merged surface of ``navigator.widgets.shell.file_history_dialog.file_history_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.shell.file_record_list import FileRecordList
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog

from typing import Any
from navkit.events import Event


class FileHistoryDialog(Dialog, _Component):
    records: FileRecordList
    pick: Button
    drop: Button
    abandon: Button
    def __init__(self, model: Any = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> Any: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_records_chosen(self, event: Any) -> bool: ...
    async def on_drop_click(self, event: Event) -> bool: ...
