# navml: generated
"""The merged surface of ``navigator.widgets.viewer.db_search_dialog.db_search_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.commands import Help
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.events import Event


class DBSearchDialog(Dialog, _Component):
    text: Field
    options_caption: Label
    options: CheckBoxes
    scope_caption: Label
    scope: RadioButtons
    direction_caption: Label
    direction: RadioButtons
    pick: Button
    abandon: Button
    helper: Button
    def __init__(self, **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_helper_click(self, event: _Event) -> bool: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    def accept(self) -> dict[str, Any] | None: ...
