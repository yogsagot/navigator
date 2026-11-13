# navml: generated
"""The merged surface of ``navigator.widgets.drives.forwards_dialog.forward_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons
from navml.widgets.dialog.static_text import StaticText

from typing import Any
from navkit.i18n import tr
from navkit.reactive import effect, untracked
from navml.widgets.dialog.control import escape_caption
from navigator.lib.drives.forwards import KINDS, Forward


class ForwardDialog(Dialog, _Component):
    kind_caption: Label
    kind: RadioButtons
    about: StaticText
    bind: Field
    port: Field
    host: Field
    host_port: Field
    problem: StaticText
    def __init__(self, forward: Forward | None = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def _kind_changed(self) -> None: ...
    def _about(self) -> None: ...
    def forward(self) -> Forward: ...
    @staticmethod
    def _port(text: str, missing: str, *, zero: bool = ...) -> int: ...
    def valid(self) -> bool: ...
    def accept(self) -> Forward: ...
