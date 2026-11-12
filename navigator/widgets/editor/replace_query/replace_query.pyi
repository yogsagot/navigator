# navml: generated
"""The merged surface of ``navigator.widgets.editor.replace_query.replace_query``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.dialog import Dialog

from typing import Any


class ReplaceQuery(Dialog, _Component):
    pick: Button
    skip: Button
    every: Button
    abandon: Button
    dims_behind: _Any
    def __init__(self, **kwargs: _Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
