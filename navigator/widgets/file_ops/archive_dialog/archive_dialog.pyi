# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.archive_dialog.archive_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.file_ops.commands import ChooseTarget
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons
from navml.widgets.dialog.static_text import StaticText

import asyncio
from pathlib import Path, PurePosixPath
from typing import Any, Sequence
from navkit.events import Event
from navkit.i18n import tr
from navkit.reactive import effect, unbind, untracked
from navml.history import HISTORY
from navml.widgets.dialog.control import escape_caption
from navigator.lib.drives import Location, drive_of
from navigator.lib.drives import archive
from navigator.lib.file_ops.filecopy import ASK, FOLLOW_LINKS, MOVE, PRESERVE, CopyRequest, shown, target_location
from navigator.settings import SETTINGS


class ArchiveDialog(Dialog, _Component):
    target_caption: Label
    target: Field
    kind_caption: Label
    kind: RadioButtons
    level_caption: Label
    level: RadioButtons
    password_caption: Label
    password: Field
    options: CheckBoxes
    note: StaticText
    pick: Button
    abandon: Button
    tree: Button
    help: Button
    def __init__(self, entries: Sequence[Any] = ..., here: Path | Location | None = ..., directory: str = ..., stem: str = ..., hidden: bool = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_help_click(self, event: _Event) -> bool: ...
    def mounted(self) -> None: ...
    buttons_row: tuple[Any, ...]
    format: tuple[str, str]
    def _kind_changed(self) -> None: ...
    def _name_changed(self) -> None: ...
    def _request(self, outer: Location, password: str) -> CopyRequest: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def confirm(self) -> None: ...
    async def _password_again(self, password: str) -> bool: ...
    async def on_tree_click(self, event: Event) -> bool: ...
    async def on_choose_target(self, event: ChooseTarget) -> bool: ...
    async def choose_target(self) -> None: ...
