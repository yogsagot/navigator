# navml: generated
"""The merged surface of ``navigator.widgets.manager.sync_options_dialog.sync_options_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navigator.lib.file_ops.dirsync import TOLERANCES, SyncOptions
from navigator.settings import SynchronizeData


class SyncOptionsDialog(Dialog, _Component):
    mask_caption: Label
    mask: Field
    times_caption: Label
    times: RadioButtons
    options: CheckBoxes
    def __init__(self, options: SyncOptions | None = ..., **kwargs: Any) -> None: ...
    def accept(self) -> SyncOptions: ...
