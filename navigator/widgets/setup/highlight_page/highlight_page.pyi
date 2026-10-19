# navml: generated
"""The merged surface of ``navigator.widgets.setup.highlight_page.highlight_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.field import Field

from typing import Any
from navkit.widget import Widget
from navigator.lib.appearance.filetypes import CUSTOM
from navigator.settings import SETTINGS, HighlightGroupsData


class HighlightPage(_Component):
    title: str
    image: Field
    media: Field
    document: Field
    source: Field
    temp: Field
    def __init__(self, section: HighlightGroupsData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
