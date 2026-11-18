# navml: generated
"""The merged surface of ``navigator.widgets.viewer.goto_dialog.goto_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.commands import Help
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any
from navkit.events import Event


class GotoDialog(Dialog, _Component):
    address: Field
    pick: Button
    abandon: Button
    helper: Button
    def __init__(self, **kwargs: _Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_helper_click(self, event: _Event) -> bool: ...
    def accept(self) -> Any: ...
    async def on_pick_click(self, event: Event) -> bool: ...
