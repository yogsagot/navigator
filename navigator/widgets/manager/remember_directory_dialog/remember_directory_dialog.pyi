# navml: generated
"""The merged surface of ``navigator.widgets.manager.remember_directory_dialog.remember_directory_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label

from typing import Any
from navml.widgets.dialog.control import escape_caption


class RememberDirectoryDialog(Dialog, _Component):
    prompt_head: Label
    prompt_tail: Label
    options: CheckBoxes
    def __init__(self, name: str = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, bool]: ...
