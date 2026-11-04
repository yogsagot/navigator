# navml: generated
"""The merged surface of ``navigator.widgets.viewer.filter_lines_dialog.filter_lines_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

import re
from typing import Any
from navkit.i18n import tr
from navkit.text import escape_caption
from navigator.lib.viewer.lines import LinePattern


class FilterLinesDialog(Dialog, _Component):
    what_caption: Label
    what: Field
    options_caption: Label
    options: CheckBoxes
    def __init__(self, last: LinePattern | None = ..., **kwargs: Any) -> None: ...
    def pattern(self) -> LinePattern | None: ...
    def valid(self) -> bool: ...
    def accept(self) -> LinePattern | str: ...
