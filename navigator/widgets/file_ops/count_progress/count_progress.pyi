# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.count_progress.count_progress``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.spinner import Spinner

from typing import Any
from navkit.bidi import display_width, pad_cells
from navkit.i18n import tr
from navkit.reactive import unbind
from navml.widgets.dialog.button import Button
from navigator.widgets.file_ops.copy_progress.copy_progress import fit_path
from navigator.widgets.manager.panel.panel import human_size


class CountProgress(Dialog, _Component):
    directory: str
    several: bool
    here_size: int
    here_files: int
    here_directories: int
    size: int
    files: int
    directories: int
    spinner: Spinner
    directory_row: StaticText
    table: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def box_width(self, screen: int, several: bool, *counts: int) -> int: ...
    def fit(self, path: str) -> str: ...
    def table_width(self, several: bool, here_size: int, size: int, here_files: int, files: int, here_directories: int, directories: int) -> int: ...
    def counts(self, width: int, several: bool, here_size: int, size: int, here_files: int, files: int, here_directories: int, directories: int) -> str: ...
    def _rows(several: bool, here_size: int, size: int, here_files: int, files: int, here_directories: int, directories: int) -> tuple[list[tuple[str, str, str]], int, int]: ...
    def accept(self) -> Any: ...
