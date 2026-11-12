# navml: generated
"""The merged surface of ``navigator.widgets.setup.startup_page.startup_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.label import Label
from navigator.widgets.setup.settings_page import SettingsPage


class StartupPage(SettingsPage, _Component):
    title: str
    startup_caption: Label
    startup: CheckBoxes
    shutdown_caption: Label
    shutdown: CheckBoxes
    def __init__(self, **kwargs: _Any) -> None: ...
