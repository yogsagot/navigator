# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.checksum_progress.checksum_progress``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.progress_bar import ProgressBar
from navml.widgets.spinner import Spinner

from typing import Any
from navkit.i18n import tr, tr_n
from navkit.reactive import unbind
from navml.widgets.dialog.button import Button
from navigator.widgets.file_ops.copy_progress.copy_progress import fit_path


class ChecksumProgress(Dialog, _Component):
    current: str
    position: int
    total: int
    files_done: int
    files_total: int
    spinner: Spinner
    current_row: StaticText
    bar: ProgressBar
    count_row: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def fit(self, path: str) -> str: ...
    def counted(done: int, total: int, percent: int) -> str: ...
    def accept(self) -> Any: ...
