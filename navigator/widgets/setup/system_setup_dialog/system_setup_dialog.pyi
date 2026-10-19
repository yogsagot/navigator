# navml: generated
"""The merged surface of ``navigator.widgets.setup.system_setup_dialog.system_setup_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.masked_field import MaskedField
from navml.widgets.dialog.radio_buttons import RadioButtons
from navml.widgets.dialog.static_text import StaticText

from typing import Any
from navigator.settings import ON_ERROR, SETTINGS, SystemData


class SystemSetupDialog(Dialog, _Component):
    options_caption: Label
    options: CheckBoxes
    temp_caption: Label
    temp_dir: Field
    on_error_caption: Label
    on_error: RadioButtons
    stall_report: MaskedField
    stall_unit: StaticText
    def __init__(self, section: SystemData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
