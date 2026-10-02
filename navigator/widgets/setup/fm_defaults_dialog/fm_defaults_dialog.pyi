# navml: generated
"""The merged surface of ``navigator.widgets.setup.fm_defaults_dialog.fm_defaults_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navigator.settings import SETTINGS, PanelDefaultsData


class FMDefaultsDialog(Dialog, _Component):
    sort_caption: Label
    sort_by: RadioButtons
    display_caption: Label
    display: CheckBoxes
    left_caption: Label
    left_panel: RadioButtons
    def __init__(self, section: PanelDefaultsData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
