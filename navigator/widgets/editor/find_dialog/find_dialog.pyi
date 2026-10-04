# navml: generated
"""The merged surface of ``navigator.widgets.editor.find_dialog.find_dialog``."""

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
from navigator.editor import search
from navigator.editor.search import SearchData


class FindDialog(Dialog, _Component):
    replace: bool
    text: Field
    new: Field
    options_caption: Label
    options: CheckBoxes
    direction_caption: Label
    direction: RadioButtons
    scope_caption: Label
    scope: RadioButtons
    origin_caption: Label
    origin: RadioButtons
    pick: Button
    all: Button
    abandon: Button
    helper: Button
    def __init__(self, *, word: str = ..., data: SearchData | None = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_helper_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def _store(self) -> None: ...
    def accept(self) -> str: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_all_click(self, event: Event) -> bool: ...
