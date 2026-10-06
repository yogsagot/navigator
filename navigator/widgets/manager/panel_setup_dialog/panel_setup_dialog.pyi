# navml: generated
"""The merged surface of ``navigator.widgets.manager.panel_setup_dialog.panel_setup_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navigator.settings import PanelDefaultsData


class PanelSetupDialog(Dialog, _Component):
    sort_caption: Label
    sort_by: RadioButtons
    display_caption: Label
    display: CheckBoxes
    mask_caption: Label
    mask: Field
    def __init__(self, panel: Any = ..., **kwargs: Any) -> None: ...
    def accept(self) -> tuple[str, frozenset[str], str]: ...
