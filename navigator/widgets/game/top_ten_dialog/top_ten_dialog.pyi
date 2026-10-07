# navml: generated
"""The merged surface of ``navigator.widgets.game.top_ten_dialog.top_ten_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label

from typing import Any
from navigator import tetris


class TopTenDialog(Dialog, _Component):
    game_style: str
    heading: Label
    def __init__(self, highlight: int | None = ..., **kwargs: Any) -> None: ...
