# navml: generated
"""The merged surface of ``navigator.widgets.setup.confirmations_page.confirmations_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navigator.widgets.setup.settings_page import SettingsPage


class ConfirmationsPage(SettingsPage, _Component):
    title: str
    options: CheckBoxes
    def __init__(self, **kwargs: _Any) -> None: ...
