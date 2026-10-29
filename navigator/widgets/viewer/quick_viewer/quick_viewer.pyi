# navml: generated
"""The merged surface of ``navigator.widgets.viewer.quick_viewer.quick_viewer``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.viewer.commands import SwitchRendered
from navigator.widgets.viewer.file_viewer import FileViewer
from navml.widgets.dialog.scroll_bar import ScrollBar

from pathlib import Path
from typing import Any
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.bidi import display_width, reveal
from navkit.glyphs import BOX_CHARSETS, hidden_mark
from navkit.widget import Widget
from navml.background import Background, Outcome
from navml.widgets.dialog.scroll_bar import ScrollEvent
from navigator.lib.viewer import ViewSource


class QuickViewer(_Component):
    title_margin: int
    viewer: FileViewer
    bar: ScrollBar
    _wanted: Any
    _use: Any
    border: _Any
    parts: _Any
    def __init__(self, **kwargs: Any) -> None: ...
    def context_menu(self) -> Any: ...
    def show(self, path: Any) -> None: ...
    def _show_elsewhere(self, origin: Any) -> None: ...
    def _fetched(self, origin: Any, outcome: Outcome) -> None: ...
    def _let_go(self) -> None: ...
    def unmounting(self) -> None: ...
    def _opened(self, path: Path, outcome: Outcome, *, as_root: bool = ...) -> None: ...
    async def on_bar_scroll(self, event: ScrollEvent) -> bool: ...
    async def on_switch_rendered(self, event: SwitchRendered) -> bool: ...
    def title_text(self) -> str: ...
    def render(self, surface: Surface) -> None: ...
