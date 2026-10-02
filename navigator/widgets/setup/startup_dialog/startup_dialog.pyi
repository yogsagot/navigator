# navml: generated
"""The merged surface of ``navigator.widgets.setup.startup_dialog.startup_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label

from typing import Any
from navigator.settings import SETTINGS, StartupData


class StartupDialog(Dialog, _Component):
    startup_caption: Label
    startup: CheckBoxes
    shutdown_caption: Label
    shutdown: CheckBoxes
    def __init__(self, section: StartupData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
