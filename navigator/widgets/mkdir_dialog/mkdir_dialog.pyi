# navml: generated
"""The merged surface of ``navigator.widgets.mkdir_dialog.mkdir_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog import Dialog
from navml.widgets.field import Field

from typing import Any


class MkdirDialog(Dialog, _Component):
    entry: Field
    def __init__(self, **kwargs: _Any) -> None: ...
    def accept(self) -> Any: ...
