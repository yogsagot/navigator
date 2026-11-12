# navml: generated
"""The merged surface of ``navigator.widgets.shell.ascii_chart.ascii_chart``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navigator.widgets.shell.char_table import CharTable

from typing import Any
from navkit.events import KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect
from navigator.widgets.shell.char_table.char_table import glyph


class AsciiChart(Dialog, _Component):
    table: CharTable
    report: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def _report(self) -> None: ...
    def accept(self) -> int: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
