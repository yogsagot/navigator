# navml: generated
"""The merged surface of ``navigator.widgets.game.winner_dialog.winner_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field

from typing import Any
from navkit.i18n import tr
from navigator.tetris import ANONYMOUS


class WinnerDialog(Dialog, _Component):
    player: Field
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> str: ...
