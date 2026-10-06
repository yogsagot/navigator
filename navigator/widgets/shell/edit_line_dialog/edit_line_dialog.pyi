# navml: generated
"""The merged surface of ``navigator.widgets.shell.edit_line_dialog.edit_line_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

from typing import Any


class EditLineDialog(Dialog, _Component):
    caption: str
    caption_label: Label
    line: Field
    def __init__(self, text: str = ..., **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
