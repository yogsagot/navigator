# navml: generated
"""The merged surface of ``navigator.widgets.viewer.db_search_dialog.db_search_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any


class DBSearchDialog(Dialog, _Component):
    text: Field
    options_caption: Label
    options: CheckBoxes
    scope_caption: Label
    scope: RadioButtons
    direction_caption: Label
    direction: RadioButtons
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, Any] | None: ...
