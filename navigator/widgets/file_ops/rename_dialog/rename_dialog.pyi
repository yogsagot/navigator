# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.rename_dialog.rename_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

import os
from typing import Any
from navkit.i18n import tr
from navml.widgets.dialog.control import escape_caption


class RenameDialog(Dialog, _Component):
    caption: str
    caption_label: Label
    line: Field
    def __init__(self, name: str = ..., *, is_dir: bool = ..., **kwargs: Any) -> None: ...
    def accept(self) -> Any: ...
