# navml: generated
"""The merged surface of ``navigator.widgets.drives.connect_dialog.connect_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.static_text import StaticText

from dataclasses import dataclass
from typing import Any
from navkit.i18n import tr


class ConnectRequest(object): ...


class ConnectDialog(Dialog, _Component):
    host: Field
    user: Field
    port: Field
    directory: Field
    label: Field
    keep: CheckBoxes
    secure: CheckBoxes
    missing: StaticText
    def __init__(self, request: ConnectRequest | None = ..., *, missing: str | None = ..., recent: list[Any] = ..., editing: bool = ..., scheme: str = ..., **kwargs: Any) -> None: ...
    def _choose_recent(self, text: str) -> None: ...
    def accept(self) -> ConnectRequest | None: ...
