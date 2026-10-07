# navml: generated
"""The merged surface of ``navigator.widgets.setup.highlight_dialog.highlight_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any
from navigator.filetypes import CUSTOM
from navigator.settings import SETTINGS, HighlightGroupsData


class HighlightDialog(Dialog, _Component):
    image: Field
    media: Field
    document: Field
    source: Field
    temp: Field
    def __init__(self, section: HighlightGroupsData | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
