# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.encrypt_dialog.encrypt_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

import asyncio
from typing import Any
from navkit.events import Event
from navkit.i18n import tr
from navml.widgets.dialog.control import escape_caption
from navigator.lib.file_ops import encrypt
from navigator.settings import SETTINGS, EncryptionData


class EncryptDialog(Dialog, _Component):
    tool_caption: Label
    tool: RadioButtons
    method_caption: Label
    method: RadioButtons
    passphrase: Field
    confirm: Field
    recipients: Field
    choose_keys: Button
    options: CheckBoxes
    pick: Button
    abandon: Button
    def __init__(self, **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def problem(self) -> str: ...
    def accept(self) -> dict[str, Any] | None: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    async def _say(self, problem: str) -> None: ...
    async def on_choose_keys_click(self, event: Event) -> bool: ...
    async def _choose_key(self) -> None: ...
