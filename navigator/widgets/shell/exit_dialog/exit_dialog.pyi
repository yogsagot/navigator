# navml: generated
"""The merged surface of ``navigator.widgets.shell.exit_dialog.exit_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label

from typing import Any


class ExitDialog(Dialog, _Component):
    prompt_head: Label
    prompt_tail: Label
    options: CheckBoxes
    def __init__(self, **kwargs: _Any) -> None: ...
    def focusable(self) -> list[Any]: ...
    def accept(self) -> dict[str, bool]: ...
