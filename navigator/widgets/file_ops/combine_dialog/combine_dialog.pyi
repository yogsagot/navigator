# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.combine_dialog.combine_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.file_ops.commands import ChooseTarget
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

from pathlib import Path
from typing import Any
from navkit.events import Event
from navkit.i18n import tr
from navkit.text import escape_caption
from navigator.lib.drives import Location


class CombineDialog(Dialog, _Component):
    target_caption: Label
    target: Field
    pick: Button
    abandon: Button
    tree: Button
    def __init__(self, name: str = ..., here: Path | Location | None = ..., other: Path | None = ..., hidden: bool = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_choose_target(self, event: _Any) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> dict[str, Any]: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def choose_target(self) -> None: ...
