# navml: generated
"""The merged surface of ``navigator.widgets.shell.execute_command_dialog.execute_command_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

from dataclasses import dataclass
from typing import Any
from navkit.i18n import tr


class CommandChoice(object): ...


class ExecuteCommandDialog(Dialog, _Component):
    caption: str
    caption_label: Label
    line: Field
    options: CheckBoxes
    def __init__(self, text: str = ..., *, in_window: bool = ..., zoomed: bool = ..., modal: bool = ..., **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
