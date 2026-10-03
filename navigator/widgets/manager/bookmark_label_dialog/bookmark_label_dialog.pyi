# navml: generated
"""The merged surface of ``navigator.widgets.manager.bookmark_label_dialog.bookmark_label_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any


class BookmarkLabelDialog(Dialog, _Component):
    entry: Field
    def __init__(self, **kwargs: _Any) -> None: ...
    def accept(self) -> Any: ...
