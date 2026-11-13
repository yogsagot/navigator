# navml: generated
"""The merged surface of ``navigator.widgets.viewer.diff_window.diff_window``."""

from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navkit.bidi import display_width
from navigator.widgets.manager.commands import Rescan
from navigator.widgets.viewer.commands import CloseViewer, NextDifference, PreviousDifference
from navigator.widgets.viewer.diff_view import DiffView
from navml.commands import CloseWindow
from navml.widgets.dialog.scroll_bar import ScrollBar
from navml.widgets.dialog.static_text import StaticText
from navml.widgets.menu.menu_item import MenuItem
from navml.widgets.menu.menu_line import MenuLine
from navml.widgets.menu.sub_menu import SubMenu
from navml.widgets.window import Window

from typing import Any
from navkit.i18n import tr
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent
from navigator.lib.file_ops import filediff
from navigator.lib.system.job import Stopped


class DiffWindow(Window, _Component):
    view: DiffView
    bar: ScrollBar
    info: StaticText
    hbar: ScrollBar
    compare_menu: SubMenu
    def __init__(self, left: Any = ..., right: Any = ..., *, model: Any = ..., **kwargs: Any) -> None: ...
    async def on_close_viewer(self, event: _Any) -> bool: ...
    async def on_rescan(self, event: _Any) -> bool: ...
    def list_name(self) -> str: ...
    def short_name(self) -> str: ...
    async def on_next_difference(self, event: NextDifference) -> bool: ...
    async def on_previous_difference(self, event: PreviousDifference) -> bool: ...
    async def compare_again(self) -> None: ...
    def refusal(self, command: Any) -> str: ...
    async def on_bar_scroll(self, event: ScrollEvent) -> bool: ...
    async def on_hbar_scroll(self, event: ScrollEvent) -> bool: ...
    def prepare_context(self, x: int, y: int) -> None: ...
    def context_point(self) -> tuple[int, int]: ...
    left_path: _Any
    right_path: _Any
