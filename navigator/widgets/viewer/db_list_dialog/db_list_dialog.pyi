# navml: generated
"""The merged surface of ``navigator.widgets.viewer.db_list_dialog.db_list_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.static_text import StaticText

from typing import Any


class DBListDialog(Dialog, _Component):
    heading: StaticText
    lines: ListViewer
    def __init__(self, heading: str = ..., lines: list[str] | None = ..., **kwargs: Any) -> None: ...
