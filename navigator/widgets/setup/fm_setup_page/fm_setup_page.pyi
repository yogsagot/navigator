# navml: generated
"""The merged surface of ``navigator.widgets.setup.fm_setup_page.fm_setup_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.widget import Widget
from navigator.settings import SETTINGS, FMSetupData


class FMSetupPage(_Component):
    title: str
    behavior_caption: Label
    behavior: CheckBoxes
    miller_width: Field
    display_caption: Label
    display: CheckBoxes
    tag_sign: Field
    right_button_caption: Label
    right_button: RadioButtons
    def __init__(self, section: FMSetupData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
    def _miller_width(self) -> int: ...
