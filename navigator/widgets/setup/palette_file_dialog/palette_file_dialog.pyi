# navml: generated
"""The merged surface of ``navigator.widgets.setup.palette_file_dialog.palette_file_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.file_dialog import FileDialog

from pathlib import Path
from typing import Any, Callable
from navkit.reactive import effect, unbind
from navml.background import Background, Outcome


class PaletteFileDialog(FileDialog, _Component):
    preview: CheckBoxes
    def __init__(self, *, preview: Callable[[tuple[Path, str] | None], None] | None = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def _follow_cursor(self) -> None: ...
