# navml: generated
"""The merged surface of ``navigator.widgets.setup.column_defaults_page.column_defaults_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.label import Label

from typing import Any
from navkit.widget import Widget
from navigator.settings import SETTINGS, ColumnDefaultsData


class ColumnDefaultsPage(_Component):
    title: str
    disk_caption: Label
    disk: CheckBoxes
    find_caption: Label
    find: CheckBoxes
    arc_caption: Label
    arc: CheckBoxes
    def __init__(self, section: ColumnDefaultsData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
