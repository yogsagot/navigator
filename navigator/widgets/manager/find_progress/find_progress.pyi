# navml: generated
"""The merged surface of ``navigator.widgets.manager.find_progress.find_progress``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText

from typing import Any
from navkit import glyphs


class FindProgress(Dialog, _Component):
    directory: str
    count: int
    directory_row: StaticText
    count_row: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def fit(self, path: str) -> str: ...
