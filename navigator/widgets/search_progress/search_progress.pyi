# navml: generated
"""The merged surface of ``navigator.widgets.search_progress.search_progress``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText

from typing import Any


class SearchProgress(Dialog, _Component):
    position: int
    total: int
    gauge_row: StaticText
    percent_row: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def percent(self) -> int: ...
    def gauge_text(self) -> str: ...
    def accept(self) -> Any: ...
