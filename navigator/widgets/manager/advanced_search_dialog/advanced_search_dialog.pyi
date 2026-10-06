# navml: generated
"""The merged surface of ``navigator.widgets.manager.advanced_search_dialog.advanced_search_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

from typing import Any
from navkit.events import Event


class AdvancedSearchDialog(Dialog, _Component):
    after: Field
    before: Field
    greater: Field
    less: Field
    kinds_caption: Label
    kinds: CheckBoxes
    pick: Button
    clear: Button
    abandon: Button
    def __init__(self, limits: dict[str, Any] | None = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> dict[str, Any]: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_clear_click(self, event: Event) -> bool: ...
