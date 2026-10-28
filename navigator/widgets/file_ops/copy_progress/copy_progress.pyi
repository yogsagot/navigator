# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.copy_progress.copy_progress``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.progress_bar import ProgressBar

from typing import Any
from navkit.i18n import tr, tr_n
from navkit.reactive import unbind
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import escape_caption
from navigator.lib.system.progress import duration_text
from navigator.widgets.manager.panel.panel import human_size


class CopyProgress(Dialog, _Component):
    move: bool
    packing: bool
    source: str
    dest: str
    file_done: int
    file_bytes: int
    done: int
    total: int
    speed: float
    left: float
    source_row: StaticText
    dest_row: StaticText
    file_bar: ProgressBar
    file_count: StaticText
    total_bar: ProgressBar
    total_count: StaticText
    pace_row: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def fit(self, label: str, path: str) -> str: ...
    def count(self, done: int, percent: int) -> str: ...
    def pace(self, speed: float, left: float) -> str: ...
    def accept(self) -> Any: ...
