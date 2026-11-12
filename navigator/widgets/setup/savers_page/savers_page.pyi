# navml: generated
"""The merged surface of ``navigator.widgets.setup.savers_page.savers_page``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.radio_buttons import RadioButtons
from navigator.widgets.setup.settings_page import SettingsPage

from typing import Any
from navkit.events import Event
from navkit.i18n import tr
from navigator.lib.appearance import savers


class SaversPage(SettingsPage, _Component):
    title: str
    chosen_caption: Label
    chosen: ListViewer
    join: Button
    drop: Button
    offered_caption: Label
    offered: ListViewer
    time_caption: Label
    time: RadioButtons
    mouse: CheckBoxes
    def __init__(self, available: list[str] | None = ..., **kwargs: Any) -> None: ...
    async def on_join_click(self, event: Event) -> bool: ...
    async def on_drop_click(self, event: Event) -> bool: ...
    def accept(self) -> dict[str, Any]: ...
