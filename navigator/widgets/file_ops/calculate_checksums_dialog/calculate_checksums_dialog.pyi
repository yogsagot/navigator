# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.calculate_checksums_dialog.calculate_checksums_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.events import Event
from navkit.reactive import effect
from navigator.lib.file_ops.checksum import default_list_name, with_extension
from navigator.settings import SETTINGS, ChecksumData


class CalculateChecksumsDialog(Dialog, _Component):
    algorithm_caption: Label
    algorithm: RadioButtons
    mode_caption: Label
    mode: RadioButtons
    list_name: Field
    pick: Button
    abandon: Button
    def __init__(self, directory_name: str = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    def mounted(self) -> None: ...
    def _follow_algorithm(self) -> None: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> dict[str, str] | None: ...
    async def on_pick_click(self, event: Event) -> bool: ...
