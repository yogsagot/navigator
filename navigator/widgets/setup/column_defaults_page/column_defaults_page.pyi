# navml: generated
"""The merged surface of ``navigator.widgets.setup.column_defaults_page.column_defaults_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.label import Label
from navigator.widgets.setup.settings_page import SettingsPage


class ColumnDefaultsPage(SettingsPage, _Component):
    title: str
    disk_caption: Label
    disk: CheckBoxes
    find_caption: Label
    find: CheckBoxes
    arc_caption: Label
    arc: CheckBoxes
    def __init__(self, **kwargs: _Any) -> None: ...
