# navml: generated
"""The merged surface of ``navigator.widgets.viewer.viewer_find_dialog.viewer_find_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.hex_line import HexLine
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navigator.lib.viewer import ViewSearch


class ViewerFindDialog(Dialog, _Component):
    what_caption: Label
    what: Field
    hex_caption: Label
    hex: HexLine
    options_caption: Label
    options: CheckBoxes
    direction_caption: Label
    direction: RadioButtons
    def __init__(self, last: ViewSearch | None = ..., *, encoding: str = ..., **kwargs: Any) -> None: ...
    def _bytes_of(self, text: str) -> bytes: ...
    def accept(self) -> Any: ...
