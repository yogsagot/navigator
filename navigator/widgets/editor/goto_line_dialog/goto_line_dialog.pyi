# navml: generated
"""The merged surface of ``navigator.widgets.editor.goto_line_dialog.goto_line_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any


class GotoLineDialog(Dialog, _Component):
    number: Field
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
