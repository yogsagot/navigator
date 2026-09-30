# navml: generated
"""The merged surface of ``navigator.widgets.delete_progress.delete_progress``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.progress_bar import ProgressBar

from typing import Any
from navkit.reactive import unbind
from navml.widgets.dialog.button import Button
from navigator.widgets.copy_progress.copy_progress import fit_path


class DeleteProgress(Dialog, _Component):
    action: str
    path: str
    done: int
    total: int
    action_row: StaticText
    path_row: StaticText
    bar: ProgressBar
    count_row: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def fit(self, path: str) -> str: ...
    def count(self, done: int, total: int, percent: int) -> str: ...
    def accept(self) -> Any: ...
