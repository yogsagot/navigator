# navml: generated
"""The merged surface of ``navigator.widgets.setup.drive_info_page.drive_info_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.label import Label
from navigator.widgets.setup.settings_page import SettingsPage


class DriveInfoPage(SettingsPage, _Component):
    title: str
    items_caption: Label
    options: CheckBoxes
    def __init__(self, **kwargs: _Any) -> None: ...
