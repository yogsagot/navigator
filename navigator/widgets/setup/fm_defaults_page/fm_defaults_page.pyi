# navml: generated
"""The merged surface of ``navigator.widgets.setup.fm_defaults_page.fm_defaults_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons
from navigator.widgets.manager.manager.manager import sort_radio_captions
from navigator.widgets.setup.settings_page import SettingsPage


class FMDefaultsPage(SettingsPage, _Component):
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
    def __init__(self, **kwargs: _Any) -> None: ...
