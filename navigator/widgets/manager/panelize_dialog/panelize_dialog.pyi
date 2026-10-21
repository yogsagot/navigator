# navml: generated
"""The merged surface of ``navigator.widgets.manager.panelize_dialog.panelize_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

from typing import Any


class PanelizeDialog(Dialog, _Component):
    caption_label: Label
    line: Field
    def __init__(self, command: str = ..., **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
