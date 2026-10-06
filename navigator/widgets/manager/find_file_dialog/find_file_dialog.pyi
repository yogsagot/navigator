# navml: generated
"""The merged surface of ``navigator.widgets.manager.find_file_dialog.find_file_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.events import Event
from navigator import filefind


class FindFileDialog(Dialog, _Component):
    mask: Field
    text: Field
    options_caption: Label
    options: CheckBoxes
    scope_caption: Label
    scope: RadioButtons
    pick: Button
    advanced: Button
    abandon: Button
    def __init__(self, **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> filefind.FindRequest: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_advanced_click(self, event: Event) -> bool: ...
    async def ask_advanced(self) -> None: ...
