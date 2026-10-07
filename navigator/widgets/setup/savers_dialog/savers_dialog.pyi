# navml: generated
"""The merged surface of ``navigator.widgets.setup.savers_dialog.savers_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.events import Event
from navigator import savers
from navigator.settings import SETTINGS, SaversData


class SaversDialog(Dialog, _Component):
    chosen_caption: Label
    chosen: ListViewer
    join: Button
    drop: Button
    offered_caption: Label
    offered: ListViewer
    time_caption: Label
    time: RadioButtons
    mouse: CheckBoxes
    def __init__(self, section: SaversData | None = ..., available: list[str] | None = ..., **kwargs: Any) -> None: ...
    buttons_row: tuple[Any, ...]
    async def on_join_click(self, event: Event) -> bool: ...
    async def on_drop_click(self, event: Event) -> bool: ...
    def accept(self) -> dict[str, Any]: ...
