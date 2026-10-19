# navml: generated
"""The merged surface of ``navigator.widgets.setup.drive_info_page.drive_info_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.label import Label

from typing import Any
from navkit.widget import Widget
from navigator.settings import SETTINGS, DriveInfoData


class DriveInfoPage(_Component):
    title: str
    items_caption: Label
    options: CheckBoxes
    def __init__(self, section: DriveInfoData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
