# navml: generated
"""The merged surface of ``navigator.widgets.drives.password_dialog.password_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any


class PasswordDialog(Dialog, _Component):
    entry: Field
    keep: CheckBoxes
    def __init__(self, prompt: str = ..., *, can_keep: bool = ..., **kwargs: Any) -> None: ...
    def accept(self) -> tuple[str, bool]: ...
