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
