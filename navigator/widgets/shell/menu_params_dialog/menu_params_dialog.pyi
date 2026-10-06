# navml: generated
"""The merged surface of ``navigator.widgets.shell.menu_params_dialog.menu_params_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

from typing import Any


class MenuParamsDialog(Dialog, _Component):
    caption: str
    caption_label: Label
    entry: Field
    def __init__(self, caption: str = ..., default: str = ..., **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
