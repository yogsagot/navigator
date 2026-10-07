# navml: generated
"""The merged surface of ``navigator.widgets.game.game_setup_dialog.game_setup_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.events import Event
from navigator.settings import SETTINGS, TetrisData


class GameSetupDialog(Dialog, _Component):
    level_caption: Label
    level: RadioButtons
    style_caption: Label
    game_style: RadioButtons
    options_caption: Label
    options: CheckBoxes
    pick: Button
    abandon: Button
    def __init__(self, level: int | None = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    buttons_row: tuple[Any, ...]
    def accept(self) -> dict[str, Any]: ...
    async def on_pick_click(self, event: Event) -> bool: ...
