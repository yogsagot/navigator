# navml: generated
"""The merged surface of ``navigator.widgets.editor.margins_dialog.margins_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any
from navkit.events import Event
from navigator.editor.paragraph import fix_margins


class MarginsDialog(Dialog, _Component):
    left: Field
    right: Field
    indent: Field
    pick: Button
    abandon: Button
    helper: Button
    def __init__(self, margins: tuple[int, int, int] = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_helper_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> tuple[int, int, int]: ...
    async def on_pick_click(self, event: Event) -> bool: ...
