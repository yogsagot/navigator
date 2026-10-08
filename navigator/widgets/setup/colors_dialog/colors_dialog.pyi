# navml: generated
"""The merged surface of ``navigator.widgets.setup.colors_dialog.colors_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.color_selector import ColorDisplay, ColorSelector
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.static_text import StaticText

from typing import Any, Callable, Mapping
from navkit.i18n import tr
from navkit.reactive import effect
from navkit.style import Style
from navkit.stylesheet import StylesheetError, parse_value
from navml.widgets.dialog.color_selector import COLORS
from navigator.palette import ATTRIBUTES, groups


class ColorsDialog(Dialog, _Component):
    group_caption: Label
    groups: ListViewer
    item_caption: Label
    items: ListViewer
    foreground_caption: Label
    foreground: ColorSelector
    background_caption: Label
    background: ColorSelector
    sample: ColorDisplay
    hint: StaticText
    foreground_value: Field
    background_value: Field
    attributes: CheckBoxes
    def __init__(self, values: Mapping[str, str] | None = ..., apply: Callable[[dict[str, str]], None] | None = ..., **kwargs: Any) -> None: ...
    def mounted(self) -> None: ...
    def _list_items(self, group: int) -> None: ...
    def _follow_group(self) -> None: ...
    def _follow_item(self) -> None: ...
    stem: str | None
    def value(self, key: str) -> str: ...
    def _show(self, stem: str) -> None: ...
    def _set(self, key: str, text: str) -> None: ...
    def _follow_selectors(self) -> None: ...
    def _follow_values(self) -> None: ...
    def _follow_attributes(self) -> None: ...
    def _sample(self) -> None: ...
    def accept(self) -> dict[str, str]: ...
