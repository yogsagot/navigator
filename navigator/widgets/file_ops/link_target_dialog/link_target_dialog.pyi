# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.link_target_dialog.link_target_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label

import posixpath
from typing import Any
from navkit.i18n import tr
from navkit.reactive import effect, peek
from navml.widgets.dialog.control import escape_caption
from navigator.lib.file_ops.filelink import absolute_target, relative_target


class LinkTargetDialog(Dialog, _Component):
    caption: str
    caption_label: Label
    line: Field
    options: CheckBoxes
    def __init__(self, name: str = ..., target: str = ..., base: str = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def _follow_relative(self) -> None: ...
    def accept(self) -> Any: ...
