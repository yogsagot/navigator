# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.delete_progress.delete_progress``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.progress_bar import ProgressBar

from typing import Any
from navkit.i18n import tr, tr_n
from navigator.lib.system.progress import duration_text
from navigator.widgets.file_ops import background_button
from navigator.widgets.file_ops.copy_progress.copy_progress import fit_path, whole_path


class DeleteProgress(Dialog, _Component):
    background: bool
    action: str
    path: str
    done: int
    total: int
    speed: float
    left: float
    action_row: StaticText
    path_row: StaticText
    bar: ProgressBar
    count_row: StaticText
    pace_row: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def fit(self, path: str) -> str: ...
    def whole(self, path: str) -> str: ...
    def count(self, done: int, total: int, percent: int) -> str: ...
    def pace(self, speed: float, left: float) -> str: ...
    def accept(self) -> Any: ...
