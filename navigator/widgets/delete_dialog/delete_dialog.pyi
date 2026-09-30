# navml: generated
"""The merged surface of ``navigator.widgets.delete_dialog.delete_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label

from pathlib import Path
from typing import Any, Sequence
from navkit.reactive import unbind
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import escape_caption
from navigator.fileerase import EraseRequest


class DeleteDialog(Dialog, _Component):
    prompt_head: Label
    prompt_caption: Label
    options: CheckBoxes
    def __init__(self, entries: Sequence[Any] = ..., here: Path | None = ..., **kwargs: Any) -> None: ...
    def focusable(self) -> list[Any]: ...
    def accept(self) -> EraseRequest: ...
