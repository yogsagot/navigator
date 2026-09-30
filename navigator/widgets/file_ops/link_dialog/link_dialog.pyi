# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.link_dialog.link_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.commands import ChooseTarget
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

from pathlib import Path
from typing import Any, Sequence
from navkit.events import Event
from navml.history import HISTORY
from navml.widgets.dialog.control import escape_caption
from navigator.filelink import LinkRequest
from navigator.widgets.file_ops.copy_dialog.copy_dialog import choose_target_line, target_for


class LinkDialog(Dialog, _Component):
    prompt_caption: Label
    target: Field
    options: CheckBoxes
    pick: Button
    abandon: Button
    tree: Button
    help: Button
    def __init__(self, entries: Sequence[Any] = ..., here: Path | None = ..., other: Path | None = ..., hidden: bool = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_help_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> LinkRequest | None: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def on_tree_click(self, event: Event) -> bool: ...
    async def on_choose_target(self, event: ChooseTarget) -> bool: ...
