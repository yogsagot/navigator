# navml: generated
"""The merged surface of ``navigator.widgets.overwrite_query.overwrite_query``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText

import time
from typing import Any
from navkit.events import Event
from navml.widgets.dialog.control import escape_caption
from navigator.filecopy import Overwrite, OverwriteAnswer


class OverwriteQuery(Dialog, _Component):
    details: StaticText
    for_all: CheckBoxes
    overwrite: Button
    append: Button
    rename: Button
    skip: Button
    abandon: Button
    def __init__(self, question: Overwrite | None = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def _answer(self, action: str, name: str = ...) -> None: ...
    async def on_overwrite_click(self, event: Event) -> bool: ...
    async def on_append_click(self, event: Event) -> bool: ...
    async def on_skip_click(self, event: Event) -> bool: ...
    async def on_rename_click(self, event: Event) -> bool: ...
    async def ask_name(self) -> None: ...
