# navml: generated
"""The merged surface of ``navigator.widgets.setup.interface_page.interface_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.choice_field import ChoiceField
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.masked_field import MaskedField
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.i18n import languages, tr
from navkit.widget import Widget
from navigator.lib.config.language import AUTOMATIC
from navigator.settings import COLOR_DEPTHS, SETTINGS, AppearanceData, InterfaceData


class InterfacePage(_Component):
    title: str
    options: CheckBoxes
    history_size: MaskedField
    language: ChoiceField
    colors: ChoiceField
    settings_tabs_caption: Label
    settings_tabs: RadioButtons
    window_strip_caption: Label
    window_strip: RadioButtons
    def __init__(self, section: InterfaceData | None = ..., appearance: AppearanceData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, dict[str, Any]]: ...
