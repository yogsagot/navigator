# navml: generated
"""The merged surface of ``navigator.widgets.viewer.quick_viewer.quick_viewer``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.viewer.file_viewer import FileViewer
from navml.widgets.dialog.scroll_bar import ScrollBar

from pathlib import Path
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.glyphs import BOX_CHARSETS
from navkit.widget import Widget
from navml.background import Background, Outcome
from navml.widgets.dialog.scroll_bar import ScrollEvent
from navigator.viewer import ViewSource


class QuickViewer(_Component):
    title_margin: int
    viewer: FileViewer
    bar: ScrollBar
    _wanted: Path | None
    border: _Any
    parts: _Any
    def __init__(self, **kwargs: _Any) -> None: ...
    def show(self, path: Path | None) -> None: ...
    def _opened(self, path: Path, outcome: Outcome) -> None: ...
    async def on_bar_scroll(self, event: ScrollEvent) -> bool: ...
    def title_text(self) -> str: ...
    def render(self, surface: Surface) -> None: ...
