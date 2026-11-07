# navml: generated
"""The merged surface of ``navigator.widgets.setup.viewer_types_page.viewer_types_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.input_line import InputLine
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.static_text import StaticText

from typing import Any
from navkit.widget import Widget
from navigator.settings import SETTINGS, ViewerDefaultsData


class ViewerTypesPage(_Component):
    title: str
    heading: StaticText
    masks_heading: StaticText
    markdown: CheckBoxes
    markdown_masks: InputLine
    rst: CheckBoxes
    rst_masks: InputLine
    html: CheckBoxes
    html_masks: InputLine
    pdf: CheckBoxes
    pdf_masks: InputLine
    images: CheckBoxes
    images_masks: InputLine
    tables: CheckBoxes
    tables_masks: InputLine
    structured: CheckBoxes
    structured_masks: InputLine
    database_caption: Label
    database_masks: InputLine
    def __init__(self, section: ViewerDefaultsData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
