# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.convert_text_dialog.convert_text_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.choice_field import ChoiceField
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.i18n import tr
from navigator.lib.editor import encodings
from navigator.settings import SETTINGS, TextConversionData


class ConvertTextDialog(Dialog, _Component):
    encoding: ChoiceField
    fallback: ChoiceField
    ending_caption: Label
    ending: RadioButtons
    options: CheckBoxes
    pick: Button
    abandon: Button
    def __init__(self, **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    def mounted(self) -> None: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> dict[str, Any]: ...
