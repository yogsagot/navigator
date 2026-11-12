# navml: generated
"""The merged surface of ``navigator.widgets.setup.editor_defaults_page.editor_defaults_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.choice_field import ChoiceField
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.masked_field import MaskedField
from navml.widgets.dialog.radio_buttons import RadioButtons
from navigator.widgets.setup.settings_page import SettingsPage

from typing import Any
from navkit.i18n import tr
from navigator.lib.editor import encodings


class EditorDefaultsPage(SettingsPage, _Component):
    title: str
    editor_caption: Label
    editor: CheckBoxes
    viewer_caption: Label
    viewer: CheckBoxes
    left_margin: MaskedField
    right_margin: MaskedField
    paragraph: MaskedField
    tab_size: MaskedField
    divisor_caption: Label
    line_divisor: RadioButtons
    fallback_encoding: ChoiceField
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any]: ...
