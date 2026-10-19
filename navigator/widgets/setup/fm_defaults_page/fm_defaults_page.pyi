# navml: generated
"""The merged surface of ``navigator.widgets.setup.fm_defaults_page.fm_defaults_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.reactive import bind
from navkit.widget import Widget
from navigator.settings import SETTINGS, PanelDefaultsData
from navigator.widgets.manager.manager.manager import sort_radio_captions


class FMDefaultsPage(_Component):
    title: str
    sort_caption: Label
    reverse: CheckBoxes
    sort_by: RadioButtons
    display_caption: Label
    display: CheckBoxes
    left_caption: Label
    left_panel: RadioButtons
    mode_caption: Label
    view_mode: RadioButtons
    def __init__(self, section: PanelDefaultsData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
