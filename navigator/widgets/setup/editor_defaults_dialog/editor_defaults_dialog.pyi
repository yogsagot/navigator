# navml: generated
"""The merged surface of ``navigator.widgets.setup.editor_defaults_dialog.editor_defaults_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.masked_field import MaskedField
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navigator.settings import SETTINGS, EditorDefaultsData, ViewerDefaultsData


class EditorDefaultsDialog(Dialog, _Component):
    editor_caption: Label
    editor: CheckBoxes
    viewer_caption: Label
    viewer: CheckBoxes
    left_margin: MaskedField
    right_margin: MaskedField
    paragraph: MaskedField
    tab_size: MaskedField
    divisor_caption: Label
    line_divisor: RadioButtons
    def __init__(self, editor: EditorDefaultsData | None = ..., viewer: ViewerDefaultsData | None = ..., **kwargs: Any) -> None: ...
    def _number(self, name: str) -> int: ...
    def accept(self) -> dict[str, Any]: ...
