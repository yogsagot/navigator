# navml: generated
"""The merged surface of ``navigator.widgets.setup.highlight_page.highlight_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.field import Field
from navigator.widgets.setup.settings_page import SettingsPage

from typing import Any
from navkit.i18n import tr
from navigator.lib.appearance.filetypes import CUSTOM


class HighlightPage(SettingsPage, _Component):
    title: str
    image: Field
    media: Field
    document: Field
    source: Field
    temp: Field
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
