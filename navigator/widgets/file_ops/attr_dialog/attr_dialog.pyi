# navml: generated
"""The merged surface of ``navigator.widgets.file_ops.attr_dialog.attr_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.choice_field import ChoiceField
from navml.widgets.dialog.date_field import DateField
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.masked_field import MaskedField
from navml.widgets.dialog.radio_buttons import RadioButtons
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.dialog.time_field import TimeField

import stat
from pathlib import Path
from typing import Any, Sequence
from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import effect, untracked
from navml.widgets.dialog.control import escape_caption
from navigator import fileattr


class AttrDialog(Dialog, _Component):
    name_row: StaticText
    info_row: StaticText
    heading: Label
    bits: CheckBoxes
    octal: MaskedField
    symbolic: StaticText
    user: ChoiceField
    group: ChoiceField
    date: DateField
    clock: TimeField
    recurse_caption: Label
    recurse: RadioButtons
    def __init__(self, entries: Sequence[Any] = ..., here: Path | None = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    lines: tuple[Any, ...]
    async def on_key(self, event: KeyEvent) -> bool: ...
    async def _on_symbolic_click(self, event: MouseClickEvent) -> bool: ...
    async def _on_bits_key(self, event: KeyEvent) -> bool: ...
    def _grid_changed(self) -> None: ...
    def _octal_changed(self) -> None: ...
    def _state(self) -> tuple[Any, ...]: ...
    def must_ask(self) -> bool: ...
    async def ask_to_close(self) -> bool: ...
    def build(self) -> fileattr.AttrRequest: ...
    def valid(self) -> bool: ...
    def accept(self) -> fileattr.AttrRequest | None: ...
