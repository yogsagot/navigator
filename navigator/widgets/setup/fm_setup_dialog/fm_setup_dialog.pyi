# navml: generated
"""The merged surface of ``navigator.widgets.setup.fm_setup_dialog.fm_setup_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navigator.settings import SETTINGS, FMSetupData


class FMSetupDialog(Dialog, _Component):
    behavior_caption: Label
    behavior: CheckBoxes
    display_caption: Label
    display: CheckBoxes
    quick_caption: Label
    quick_search: RadioButtons
    tag_sign: Field
    description_caption: Label
    description_files: Field
    def __init__(self, section: FMSetupData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
