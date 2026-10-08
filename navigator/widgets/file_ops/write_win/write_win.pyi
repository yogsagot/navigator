# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.write_win.write_win``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.progress_bar import ProgressBar
from navml.widgets.spinner import Spinner

from typing import Any
from navkit.i18n import tr
from navkit.reactive import bind, unbind
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.commands import Cancel, Default


class WriteWin(Dialog, _Component):
    notice: str
    position: int
    total: int
    cancellable: bool
    spinner: Spinner
    notice_row: StaticText
    bar: ProgressBar
    percent_row: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
    async def on_cancel(self, event: Cancel) -> bool: ...
    async def on_default(self, event: Default) -> bool: ...
