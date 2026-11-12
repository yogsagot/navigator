# navml: generated
"""The merged surface of ``navigator.widgets.shell.command_history_dialog.command_history_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.shell.command_history_dialog.history_list import HistoryList
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.dialog import Dialog

from typing import Any
from navkit.glyphs import GLYPHS_UNICODE
from navkit.i18n import tr
from navml.history import HISTORY
from navigator.widgets.shell.command_line.command_line import HISTORY_ID


class CommandHistoryDialog(Dialog, _Component):
    commands: HistoryList
    run: Button
    drop: Button
    edit: Button
    kill: Button
    abandon: Button
    def __init__(self, **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    def key_hints(self) -> list[tuple[str, str]]: ...
    def _load(self, focus: str | None) -> None: ...
    buttons_row: tuple[Any, ...]
    def _sync_pins(self) -> None: ...
    def close(self, result: Any = ...) -> None: ...
    def _answer(self, how: str) -> None: ...
    def kill_selected(self) -> None: ...
    async def edit_selected(self) -> None: ...
