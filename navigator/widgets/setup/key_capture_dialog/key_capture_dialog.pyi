# navml: generated
"""The merged surface of ``navigator.widgets.setup.key_capture_dialog.key_capture_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.static_text import StaticText
from navigator.widgets.setup.key_capture_dialog.key_catcher import KeyCatcher

from typing import Any


class KeyCaptureDialog(Dialog, _Component):
    hint: StaticText
    catcher: KeyCatcher
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> str | None: ...
