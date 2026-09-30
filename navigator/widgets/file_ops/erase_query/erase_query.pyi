# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.erase_query.erase_query``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText

from typing import Any
from navkit.events import Event
from navml.widgets.dialog.control import escape_caption
from navigator.fileerase import ALL, NO, YES, NotEmpty, ReadOnly
from navigator.widgets.file_ops.delete_dialog.delete_dialog import cut


class EraseQuery(Dialog, _Component):
    kind: str
    details: StaticText
    refuse: Button
    agree: Button
    every: Button
    abandon: Button
    def __init__(self, question: NotEmpty | ReadOnly | None = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    def slot(self, index: int) -> int: ...
    buttons_row: tuple[Any, ...]
    async def on_refuse_click(self, event: Event) -> bool: ...
    async def on_agree_click(self, event: Event) -> bool: ...
    async def on_every_click(self, event: Event) -> bool: ...
