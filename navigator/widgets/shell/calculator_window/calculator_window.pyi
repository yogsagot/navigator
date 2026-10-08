# navml: generated
"""The merged surface of ``navigator.widgets.shell.calculator_window.calculator_window``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.shell.calculator_window.calc_line import CalcLine
from navml.widgets.dialog.button import Button
from navml.widgets.dialog.commands import Cancel, Default, SelectNext, SelectPrevious
from navml.widgets.dialog.history import History
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.window import Window

from typing import Any
from navkit.events import Event, KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect
from navml.history import HISTORY
from navml.widgets.dialog.control.control import Control
from navigator import calculator


class CalculatorWindow(Window, _Component):
    rows: _Any
    expression_caption: Label
    line: CalcLine
    history: History
    copy_caption: Label
    copy_as: RadioButtons
    row0: StaticText
    row1: StaticText
    row2: StaticText
    row3: StaticText
    row4: StaticText
    evaluate_button: Button
    copy_button: Button
    close_button: Button
    def __init__(self, **kwargs: _Any) -> None: ...
    def mounted(self) -> None: ...
    def _recalculate(self) -> None: ...
    def indicator(text: str) -> list[str]: ...
    def evaluate(self) -> None: ...
    def copy_value(self) -> None: ...
    def leave(self) -> None: ...
    async def on_default(self, event: Default) -> bool: ...
    async def on_cancel(self, event: Cancel) -> bool: ...
    async def on_evaluate_button_click(self, event: Event) -> bool: ...
    async def on_copy_button_click(self, event: Event) -> bool: ...
    async def on_close_button_click(self, event: Event) -> bool: ...
    async def on_select_next(self, event: SelectNext) -> bool: ...
    async def on_select_previous(self, event: SelectPrevious) -> bool: ...
    def _step(self, by: int) -> None: ...
    async def on_key(self, event: KeyEvent) -> bool: ...
    def _controls(cls, widget: Any) -> list[Control]: ...
