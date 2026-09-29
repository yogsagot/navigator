# navml: generated
"""The merged surface of ``navigator.widgets.quick_viewer.quick_viewer``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.file_viewer import FileViewer
from navml.widgets.dialog.scroll_bar import ScrollBar

from pathlib import Path
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.glyphs import BOX_CHARSETS
from navkit.widget import Widget
from navml.widgets.dialog.scroll_bar import ScrollEvent


class QuickViewer(_Component):
    title_margin: int
    viewer: FileViewer
    bar: ScrollBar
    border: _Any
    parts: _Any
    def __init__(self, **kwargs: _Any) -> None: ...
    def show(self, path: Path | None) -> None: ...
    async def on_bar_scroll(self, event: ScrollEvent) -> bool: ...
    def title_text(self) -> str: ...
    def render(self, surface: Surface) -> None: ...
