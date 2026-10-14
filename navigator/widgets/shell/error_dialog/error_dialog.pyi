# navml: generated
"""The merged surface of ``navigator.widgets.shell.error_dialog.error_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navigator.widgets.shell.error_dialog.trace_list import TraceList

from pathlib import Path
from typing import Any
from navkit.events import Event
from navkit.i18n import tr
from navkit.reactive import effect
from navigator.lib.highlight import Span, lex_text
from navigator.lib.system.errorlog import format_error


class ErrorDialog(Dialog, _Component):
    summary: StaticText
    trace: TraceList
    logged: StaticText
    resume: Button
    copy: Button
    quit: Button
    def __init__(self, error: BaseException | None = ..., log: Path | None = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def _wrap(self) -> None: ...
    buttons_row: tuple[Any, ...]
    async def on_resume_click(self, event: Event) -> bool: ...
    async def on_copy_click(self, event: Event) -> bool: ...
    async def on_quit_click(self, event: Event) -> bool: ...
