# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.split_dialog.split_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.file_ops.commands import ChooseTarget
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.commands import Help
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

from pathlib import Path
from typing import Any
from navkit.events import Event
from navkit.i18n import tr
from navkit.text import escape_caption
from navml.history import HISTORY
from navigator.lib.drives import Location
from navigator.lib.file_ops.splitfile import SplitError, parse_size
from navigator.settings import SETTINGS


class SplitDialog(Dialog, _Component):
    target_caption: Label
    target: Field
    size: Field
    options: CheckBoxes
    pick: Button
    abandon: Button
    tree: Button
    help: Button
    def __init__(self, name: str = ..., here: Path | Location | None = ..., other: Path | None = ..., hidden: bool = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_help_click(self, event: _Event) -> bool: ...
    async def on_choose_target(self, event: _Any) -> bool: ...
    def valid(self) -> bool: ...
    def accept(self) -> dict[str, Any]: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def choose_target(self) -> None: ...
    _here: _Any
    _hidden: _Any
