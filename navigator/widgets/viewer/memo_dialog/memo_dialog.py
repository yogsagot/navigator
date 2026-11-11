"""The viewer behind ``memo_dialog.nml``: a memo's bytes, and the view commands.

The commands are ``viewer_host``'s, their handlers written out here as the
quick view's are, since a component's hand-written half has one base.
"""

from __future__ import annotations

from typing import Any

from navkit.commands import Command
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent

from navigator.lib.viewer import MemorySource
from navigator.settings import SETTINGS
from navigator.widgets.viewer import viewer_host
from navigator.widgets.viewer.commands import (
    AddFilter,
    ChooseEncoding,
    ContinueSearch,
    GotoAddress,
    HexMode,
    ReverseSearch,
    SearchAgain,
    SearchFor,
    SetViewFilter,
    SetViewMode,
    Unwrap,
)


class MemoDialog(Dialog):
    """*Memo view*: *data*, the memo's bytes, in a viewer read in *codec*.

    *name* is what the viewer calls its file; it is not shown.  Opened in the
    text view, wrapped if Viewer setup's *Wrap lines* says, as
    ``TFileViewer.Init`` read ``ViOpt``; the viewer has the keyboard first
    (``SelectNext(False)``), since a dialog's buttons come last.
    """

    def __init__(self, data: bytes = b"", name: str = "memo", codec: str = "utf-8", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        viewer = self.viewer
        viewer.set_encoding(codec)
        viewer.open(name, source=MemorySource(data, name))
        viewer.wrap = SETTINGS.viewer.wrap_lines

    async def on_bar_scroll(self, event: ScrollEvent) -> bool:
        """The scroll bar was worked: its value is a byte offset, snapped to a row."""
        self.viewer.seek(event.value)
        return True

    def refusal(self, command: Command) -> str:
        if isinstance(command, viewer_host.COMMANDS):
            return viewer_host.refusal(self, command) or super().refusal(command)
        return super().refusal(command)

    def checks(self, command: Command) -> bool | None:
        checked = viewer_host.checks(self, command)
        return checked if checked is not None else super().checks(command)

    # -- the view commands (``viewer_host``, written out: one base) ------------

    async def on_unwrap(self, event: Unwrap) -> bool:
        self.viewer.toggle_wrap()
        return True

    async def on_hex_mode(self, event: HexMode) -> bool:
        self.viewer.cycle_mode()
        return True

    async def on_add_filter(self, event: AddFilter) -> bool:
        self.viewer.cycle_filter()
        return True

    async def on_set_view_mode(self, event: SetViewMode) -> bool:
        self.viewer.set_mode(event.mode)
        return True

    async def on_set_view_filter(self, event: SetViewFilter) -> bool:
        self.viewer.set_filter(event.filter)
        return True

    async def on_goto_address(self, event: GotoAddress) -> bool:
        self.spawn(viewer_host.goto_address(self))
        return True

    async def on_choose_encoding(self, event: ChooseEncoding) -> bool:
        self.spawn(viewer_host.choose_encoding(self))
        return True

    async def on_search_for(self, event: SearchFor) -> bool:
        self.spawn(viewer_host.search_for(self))
        return True

    async def on_continue_search(self, event: ContinueSearch) -> bool:
        self.spawn(viewer_host.search_again(self, reverse=False))
        return True

    async def on_search_again(self, event: SearchAgain) -> bool:
        self.spawn(viewer_host.search_again(self, reverse=False))
        return True

    async def on_reverse_search(self, event: ReverseSearch) -> bool:
        self.spawn(viewer_host.search_again(self, reverse=True))
        return True
