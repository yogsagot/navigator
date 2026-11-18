# navml: generated
"""The merged surface of ``navigator.widgets.manager.compare_dialog.compare_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.commands import Help
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.events import Event
from navigator.lib.file_ops.dircompare import CompareRequest


class CompareDialog(Dialog, _Component):
    options_caption: Label
    options: CheckBoxes
    mode_caption: Label
    mode: RadioButtons
    pick: Button
    abandon: Button
    helper: Button
    def __init__(self, **kwargs: _Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_helper_click(self, event: _Event) -> bool: ...
    def accept(self) -> Any: ...
    async def on_pick_click(self, event: Event) -> bool: ...
