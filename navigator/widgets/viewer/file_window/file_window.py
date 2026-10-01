"""The handlers behind ``file_window.nml``: the viewer's commands.

The keys that *move* are ``FileViewer``'s own and reach it first along the
focus path; what is here is what the key bar names -- the switches, and the
two dialogs.  Both dialogs are started, never awaited, for the reason
``Manager.on_make_directory`` gives: a handler that waits on a dialog holds the
only consumer of the queue the dialog's keys arrive on.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from navkit.commands import Command
from navkit.events import DoubleClickEvent
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent
from navml.widgets.window import Window

import navigator.viewer as viewer_model
from navigator.widgets.viewer.commands import (
    AddFilter,
    CloseViewer,
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
from navigator.viewer import SearchJob, ViewSearch

#: How long a search runs before it shows its progress: DN's two timer ticks
#: (``NewTimer(Tmr, 2)``) at 18.2 Hz.
PROGRESS_DELAY = 2 / 18.2

#: How often the gauge is brought up to date.
PROGRESS_TICK = 0.1


class FileWindow(Window):
    """A file in a viewer window: F3, and File > View > As Text / As Hex.

    Raises ``OSError`` from the constructor if *path* cannot be read, so the
    caller can say so before a window that shows nothing is opened.
    """

    def __init__(self, path: Path | str, *, mode: str = "text", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Seeded, never bound: the viewer navigates both.
        self.viewer.open(path)
        self.viewer.mode = mode
        if mode == "hex":
            self.viewer.cursor = 0
        # ``TWindow.Init(R, FileName, 0)``: the title is the whole name.
        self.title = str(self.viewer.path)

    def take_keyboard(self) -> None:
        # Not from ``mounted()``: that runs inside ``Desktop.open``'s ``add()``,
        # before ``activate`` has saved which panel the window below had, so
        # closing this one would hand the keyboard to the left panel.
        self.viewer.focus()

    def list_name(self) -> str:
        """Window > List's line: DN's ``dlViewFile``, ``View - `` and the name."""
        return f"View - {self.viewer.path}"

    async def on_close_viewer(self, event: CloseViewer) -> bool:
        """F3 again: Midnight Commander's way out, beside DN's Esc."""
        self.close()
        return True

    # -- the switches ----------------------------------------------------------

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

    def checks(self, command: Command) -> bool | None:
        """The *View* menu ticks the mode, the filter and wrapping in force."""
        if isinstance(command, SetViewMode):
            return self.viewer.mode == command.mode
        if isinstance(command, SetViewFilter):
            return self.viewer.filter == command.filter
        if isinstance(command, Unwrap):
            return self.viewer.wrap
        return super().checks(command)

    def enables(self, command: Command) -> bool:
        """F5 is hex and dump only, and F2 text only, as ``Draw`` switched them."""
        if isinstance(command, GotoAddress):
            return self.viewer.mode != "text"
        if isinstance(command, Unwrap):
            return self.viewer.mode == "text"
        if isinstance(command, (ContinueSearch, ReverseSearch, SearchAgain)):
            return viewer_model.last_search is not None
        return super().enables(command)

    async def on_bar_scroll(self, event: ScrollEvent) -> bool:
        """The scroll bar was worked: its value is a byte offset, snapped to a row."""
        self.viewer.seek(event.value)
        return True

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        """A double click on the ``[<=>]`` at the info line's start toggles wrap."""
        if event.y == self.height - 1 and 1 <= event.x < 6 and self.viewer.mode == "text":
            self.viewer.toggle_wrap()
            return True
        return await super().on_double_click(event)

    # -- goto ------------------------------------------------------------------

    async def on_goto_address(self, event: GotoAddress) -> bool:
        self.spawn(self.goto_address())
        return True

    async def goto_address(self) -> None:
        from navigator.widgets.viewer.goto_dialog import GotoDialog

        address = await GotoDialog().execute(self.application)
        if address is None:
            return
        viewer = self.viewer
        address = min(max(0, address), max(0, viewer.size - 1))
        viewer.cursor = address
        viewer.seek(address)
        viewer.cursor = address
        viewer.follow_cursor()

    # -- searching -------------------------------------------------------------

    async def on_search_for(self, event: SearchFor) -> bool:
        self.spawn(self.search_for())
        return True

    async def on_continue_search(self, event: ContinueSearch) -> bool:
        self.spawn(self.search_again(reverse=False))
        return True

    async def on_search_again(self, event: SearchAgain) -> bool:
        self.spawn(self.search_again(reverse=False))
        return True

    async def on_reverse_search(self, event: ReverseSearch) -> bool:
        self.spawn(self.search_again(reverse=True))
        return True

    async def search_for(self) -> None:
        """F7: ask, remember the answer for every viewer, and look."""
        from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

        search = await ViewerFindDialog(last=viewer_model.last_search).execute(self.application)
        if search is None:
            return
        viewer_model.last_search = search
        # A new search starts from the view rather than from the last hit.
        self.viewer.hit = None
        await self.search(search, search.backward)

    async def search_again(self, *, reverse: bool) -> None:
        """Shift+F7 and Ctrl+L the same way, Ctrl+F7 the other: DN's ``ContinueSearch``."""
        search = viewer_model.last_search
        if search is None:
            return
        await self.search(search, search.backward != reverse)

    async def search(self, search: ViewSearch, backward: bool) -> None:
        """Look for *search* from the hit, or from the view, and show what is found.

        Run on a thread, because a gigabyte is not searched between two frames;
        the loop keeps painting -- the clock keeps ticking -- while it looks.
        A search still going after ``PROGRESS_DELAY`` puts up *Search
        Progress*, and *Stop* in it ends the search where it is.
        """
        viewer = self.viewer
        source = viewer.source
        if source is None:
            return
        if viewer.hit is not None:
            start = viewer.hit[0] + (0 if backward else 1)
        elif viewer.mode == "text":
            start = viewer.top
        else:
            start = viewer.cursor
        pattern, span = search.compile()
        job = SearchJob()
        job.position = start
        work = asyncio.ensure_future(asyncio.to_thread(
            source.find, pattern, start, backward=backward, span=span, job=job
        ))
        done, _ = await asyncio.wait({work}, timeout=PROGRESS_DELAY)
        if not done:
            await self._watch(work, job, source.size)
        found = await work
        if job.stopped:
            # DN's -2: stopped, so nothing is said about finding nothing.
            return
        if found is None:
            await Dialog(
                title="Search", prompt="Search string not found", buttons="ok"
            ).execute(self.application)
            return
        viewer.show_hit(*found)

    async def _watch(self, work: asyncio.Future[Any], job: SearchJob, total: int) -> None:
        """Show *Search Progress* until *work* ends, or stop it if *Stop* comes first."""
        from navigator.widgets.viewer.search_progress import SearchProgress

        app = self.application
        if app is None:
            return
        box = SearchProgress(total=total, position=job.position)

        async def tick() -> None:
            box.position = job.position

        repeat = app.call_every(PROGRESS_TICK, tick)
        answer = asyncio.ensure_future(box.execute(app))
        try:
            await asyncio.wait({work, answer}, return_when=asyncio.FIRST_COMPLETED)
            if answer.done():
                job.stop()
            else:
                box.close(None)
                await answer
        finally:
            repeat.cancel()
