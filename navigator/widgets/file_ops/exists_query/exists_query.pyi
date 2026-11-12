# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.exists_query.exists_query``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText

from pathlib import Path
from typing import Any
from navkit.i18n import tr
from navml.widgets.dialog.control import escape_caption
from navigator.widgets.file_ops.delete_dialog.delete_dialog import cut


class ExistsQuery(Dialog, _Component):
    details: StaticText
    agree: Button
    refuse: Button
    every: Button
    abandon: Button
    def __init__(self, path: Path | None = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
