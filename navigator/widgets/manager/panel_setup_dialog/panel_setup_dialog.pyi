# navml: generated
"""The merged surface of ``navigator.widgets.manager.panel_setup_dialog.panel_setup_dialog``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.button_row import ButtonRow
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.commands import Help
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons

from typing import Any
from navkit.events import Event
from navkit.reactive import bind
from navigator.settings import PanelDefaultsData
from navigator.widgets.manager.manager.helpers import sort_radio_captions


class PanelSetupDialog(Dialog, _Component):
    sort_caption: Label
    reverse: CheckBoxes
    sort_by: RadioButtons
    display_caption: Label
    display: CheckBoxes
    mask_caption: Label
    mask: Field
    pick: Button
    abandon: Button
    helper: Button
    def __init__(self, panel: Any = ..., **kwargs: Any) -> None: ...
    async def on_abandon_click(self, event: _Event) -> bool: ...
    async def on_helper_click(self, event: _Event) -> bool: ...
    async def on_pick_click(self, event: Event) -> bool: ...
    def accept(self) -> tuple[str, frozenset[str], str, bool]: ...
