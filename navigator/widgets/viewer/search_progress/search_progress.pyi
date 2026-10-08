# navml: generated
"""The merged surface of ``navigator.widgets.viewer.search_progress.search_progress``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.progress_bar import ProgressBar

from typing import Any
from navkit.i18n import tr
from navkit.reactive import unbind
from navml.widgets.dialog.button import Button


class SearchProgress(Dialog, _Component):
    position: int
    total: int
    bar: ProgressBar
    percent_row: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
