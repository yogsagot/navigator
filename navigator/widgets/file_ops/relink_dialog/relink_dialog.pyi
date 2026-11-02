# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.relink_dialog.relink_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navigator.widgets.file_ops.relink_dialog.relink_preview import RelinkPreview
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.static_text import StaticText

from typing import Any, Sequence
from navkit.i18n import tr_n
from navkit.reactive import effect
from navigator.lib.file_ops import filelink


class RelinkDialog(Dialog, _Component):
    search: Field
    replace: Field
    preview: RelinkPreview
    status: StaticText
    def __init__(self, links: Sequence[tuple[Any, str]] = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def _follow(self) -> None: ...
    def valid(self) -> bool: ...
    def accept(self) -> list[filelink.Retarget]: ...
