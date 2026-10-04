# navml: generated
"""The merged surface of ``navigator.widgets.editor.replace_query.replace_query``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog

from typing import Any
from navkit.events import Event


class ReplaceQuery(Dialog, _Component):
    pick: Button
    every: Button
    skip: Button
    abandon: Button
    def __init__(self, **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_every_click(self, event: Event) -> bool: ...
    async def on_skip_click(self, event: Event) -> bool: ...
