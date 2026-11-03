"""The handlers behind ``process_window.nml``.

The processes are read on a thread (:class:`navigator.lib.system.processes.Sampler`,
through ``Background``) when the window opens, on Ctrl+R, and every
``[processes] refresh`` seconds -- a tick is let go while a read is still
under way, or while a box is up over the desktop.  Only the newest read is
listed, and the cursor stays on the process it was on, by number, however the
order moved.  *Mine only*, *Tree*, the filter and the sort change what is
shown, never what was read, so they need no read.

**The filter is the only search** (htop's F4): a line across the top whose
text, anywhere in a process's command, name, user or number, keeps it in the
list.  It replaced a quick search that moved the cursor as letters were typed
on the list with nothing to show it but the status line.  In a tree a match
keeps the parents above it, dimmed (``.context``), so it is still seen where it
runs.

**A signal is sent to the process that was read, not to its number**:
:func:`~navigator.lib.system.processes.signal_process` reads it again first
and refuses one whose start time changed -- its number given to another --
which ``kill`` alone cannot tell.  One the user may not signal (``EPERM``) is
offered *As root*, as a refused file step is, and sent by the root helper's
``kill``.  **Enter in the list is handled here** (F3's *Details*), so the
list's ``ChosenEvent`` does not walk up to the screen, which would take it
for a directory.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from navkit.bidi import display_width
from navkit.events import ContextMenuEvent, Event, KeyEvent
from navkit.i18n import tr, tr_n
from navkit.reactive import effect, peek
from navkit.text import caption_runs
from navml.background import Background, Outcome
from navml.commands import CloseWindow
from navml.widgets.dialog.commands import QuickSearch, SelectNext, SelectPrevious
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent
from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click, open_on_key
from navml.widgets.menu.sub_menu import SubMenu
from navml.widgets.window import Window

from navigator.lib.system import processes
from navigator.lib.system.elevate import ELEVATION, refused
from navigator.widgets.manager.commands import Rescan
from navigator.widgets.shell.commands import (
    FilterProcesses, KillProcess, ProcessDetails, ProcessMineOnly, ProcessSortCommand, ProcessSortCpu, ProcessSortMemory,
    ProcessSortPid, ProcessSortState, ProcessSortUser, ProcessTree, SendSignal, SignalProcess,
)
from navigator.widgets.shell.process_list import SortChosen

#: Where the window reads the processes.
_READER = Background("nav-processes", workers=1)

#: Each sort command's key.
_SORTS = ((ProcessSortPid, "pid"), (ProcessSortUser, "user"), (ProcessSortState, "state"),
          (ProcessSortCpu, "cpu"), (ProcessSortMemory, "memory"), (ProcessSortCommand, "command"))


def _refresh() -> float:
    """``[processes] refresh``: seconds between reads, 0 for none."""
    from navigator.settings import SETTINGS

    try:
        return max(0.0, float(SETTINGS.processes.refresh))
    except (AttributeError, TypeError, ValueError):
        return 2.0


class ProcessWindow(Window):
    """The running processes in a window of their own."""

    def __init__(self, mine_only: bool = False, tree: bool = False, sort: str = "pid",
                 descending: bool = False, **kwargs: Any) -> None:
        """*mine_only* ticks *Mine only*, *tree* ticks *Tree*; *sort* is one of
        :data:`~navigator.lib.system.processes.SORTS`, *descending* its way round."""
        super().__init__(**kwargs)
        self.mine_only = mine_only
        self.tree = tree
        self.sort = sort if sort in processes.SORTS else "pid"
        self.descending = descending
        self.uid = os.getuid()
        self._found: list[processes.Process] = []
        self._sampler = processes.Sampler()
        self._reads = 0
        self._reading = False
        self._ticker: Any = None

    @staticmethod
    def caption_width(text: str) -> int:
        """How many cells *text* takes drawn as a caption, its ``~`` marks gone."""
        return sum(display_width(run) for run, _ in caption_runs(text))

    @property
    def mine_only(self) -> bool:
        """Whether *Mine only* is ticked."""
        return bool(self.mine_box.value & 1)

    @mine_only.setter
    def mine_only(self, value: bool) -> None:
        self.mine_box.value = 1 if value else 0

    @property
    def tree(self) -> bool:
        """Whether *Tree* is ticked."""
        return bool(self.tree_box.value & 1)

    @tree.setter
    def tree(self, value: bool) -> None:
        self.tree_box.value = 1 if value else 0

    def mounted(self) -> None:
        super().mounted()
        self.processes.uid = self.uid
        self.processes.filter_line = self.filter
        self.filter.rows = self.processes
        # A symbol, not a word: set here because a markup literal is translated.
        self.clear_filter.text = "X"
        effect(self, ProcessWindow._follow_view)
        # Not from ``__init__``: until the window is on the desktop it has no
        # application, and ``Background`` would read on the loop instead.
        self.reload()
        app = self.application
        seconds = _refresh()
        if app is not None and seconds > 0:
            self._ticker = app.call_every(seconds, self._tick)

    def unmounting(self) -> None:
        if self._ticker is not None:
            self._ticker.cancel()
            self._ticker = None
        super().unmounting()

    def take_keyboard(self) -> None:
        # Not from ``mounted()``, for the reason ``TreeWindow`` gives.
        self.processes.focus()

    def _follow_view(self) -> None:
        """*Mine only* or *Tree* ticked or cleared, by a key, a click or the
        menu, or the filter typed: list again."""
        self.mine_box.value  # noqa: B018 -- what this effect follows
        self.tree_box.value  # noqa: B018
        self.filter.value  # noqa: B018
        self._show()

    # -- reading ----------------------------------------------------------------------

    def reload(self) -> None:
        """Read the processes again, on a thread; only the newest read is listed."""
        self._reads += 1
        self._reading = True
        _READER.run(self, self._sampler, done=lambda outcome, n=self._reads: self._read(n, outcome))

    async def _tick(self) -> None:
        """The clock's read -- let go while one is under way or a box is up."""
        app = self.application
        if self._reading or app is None or app.modal is not None:
            return
        self.reload()

    def _read(self, read: int, outcome: Outcome) -> None:
        if read != self._reads:
            return
        self._reading = False
        try:
            self._found = outcome.result()
        except OSError:
            self._found = []
        self._show()

    def _show(self) -> None:
        """List what was read, keeping the cursor on the process it was on.

        The list's items and cursor are peeked: ``_follow_view`` calls this,
        and an effect that read them would run again at every cursor move.
        A process the filter hid, or kept only as a match's parent, takes
        the cursor to the first match.
        """
        listing = self.processes
        items = peek(listing, ListViewer.items)
        cursor = peek(listing, ListViewer.cursor)
        current = items[cursor].process.pid if 0 <= cursor < len(items) else None
        found = [each for each in self._found if not self.mine_only or each.uid == self.uid]
        text = peek(self.filter, type(self.filter).value)
        picked = [each for each in found if processes.matches(each, text)]
        tree = self.tree
        if tree:
            kept, context = processes.with_ancestors(found, picked)
            shown = processes.tree(kept, self.sort, self.descending, context)
        else:
            shown = [processes.Row(each) for each in processes.ordered(picked, self.sort, self.descending)]
        listing.tree = tree
        listing.sort = self.sort
        listing.descending = self.descending
        listing.items = shown
        at = next((index for index, row in enumerate(shown)
                   if row.process.pid == current and not row.context), None)
        if at is None:
            at = next((index for index, row in enumerate(shown) if not row.context), 0)
        listing.cursor = at
        mine = sum(1 for each in self._found if each.uid == self.uid)
        summary = tr_n("{count} process, {mine} yours", "{count} processes, {mine} yours",
                       len(self._found), count=f"{len(self._found):,}", mine=f"{mine:,}")
        if text.strip():
            summary = tr_n("{shown} of {count} process match the filter",
                           "{shown} of {count} processes match the filter", len(found),
                           shown=f"{len(picked):,}", count=f"{len(found):,}")
        self.status.text = escape_caption(summary)

    # -- sorting ------------------------------------------------------------------------

    def _sort_by(self, by: str) -> None:
        """Sort *by* that; already so, the other way round.  CPU and memory
        start with the biggest, the rest with the smallest."""
        if self.sort == by:
            self.descending = not self.descending
        else:
            self.sort, self.descending = by, by in processes.DESCENDING_FIRST
        self._show()

    async def on_sort_chosen(self, event: SortChosen) -> bool:
        self._sort_by(event.by)
        return True

    async def on_process_sort_pid(self, command: ProcessSortPid) -> bool:
        self._sort_by("pid")
        return True

    async def on_process_sort_user(self, command: ProcessSortUser) -> bool:
        self._sort_by("user")
        return True

    async def on_process_sort_state(self, command: ProcessSortState) -> bool:
        self._sort_by("state")
        return True

    async def on_process_sort_cpu(self, command: ProcessSortCpu) -> bool:
        self._sort_by("cpu")
        return True

    async def on_process_sort_memory(self, command: ProcessSortMemory) -> bool:
        self._sort_by("memory")
        return True

    async def on_process_sort_command(self, command: ProcessSortCommand) -> bool:
        self._sort_by("command")
        return True

    async def on_process_tree(self, command: ProcessTree) -> bool:
        self.tree = not self.tree
        return True

    async def on_process_mine_only(self, command: ProcessMineOnly) -> bool:
        self.mine_only = not self.mine_only
        return True

    async def on_filter_processes(self, command: FilterProcesses) -> bool:
        """F4, Ctrl+S or the menu's *Filter*: the keyboard to the filter line, its text picked."""
        self.filter.focus()
        self.filter.select_all()
        return True

    async def on_quick_search(self, command: QuickSearch) -> bool:
        """The list's own Ctrl+S, which it has no search for: the filter's."""
        return await self.on_filter_processes(FilterProcesses())

    async def on_clear_filter_click(self, event: Event) -> bool:
        self.filter.value = ""
        self.filter.cursor = 0
        self.filter.focus()
        return True

    async def on_rescan(self, event: Rescan) -> bool:
        self.reload()
        return True

    def checks(self, command: Any) -> bool | None:
        """The *Processes* menu ticks the sort in force, *Tree* and *Mine only*."""
        for kind, by in _SORTS:
            if isinstance(command, kind):
                return self.sort == by
        if isinstance(command, ProcessTree):
            return self.tree
        if isinstance(command, ProcessMineOnly):
            return self.mine_only
        return super().checks(command)

    # -- what can be done to the one under the cursor -------------------------------------

    @property
    def selected(self) -> processes.Process | None:
        row = self.processes.selected
        return row.process if row is not None else None

    def allows(self, action: str) -> bool:
        """Whether ``"signal"`` or ``"details"`` can be done to the process
        under the cursor -- what the buttons' ``disabled`` follows."""
        process = self.selected
        if process is None:
            return False
        if action == "signal":
            return not processes.protected(process.pid)
        return True

    def refusal(self, command: Any) -> str:
        if isinstance(command, (SignalProcess, KillProcess, SendSignal, ProcessDetails)):
            process = self.selected
            if process is None:
                return tr("The cursor is on no process")
            if not isinstance(command, ProcessDetails) and processes.protected(process.pid):
                return tr("Navigator does not signal that process")
            return ""
        return super().refusal(command)

    async def on_chosen(self, event: ChosenEvent) -> bool:
        """Enter or a double click on a row: its details."""
        await self.on_process_details(ProcessDetails())
        return True

    async def on_process_details(self, command: ProcessDetails) -> bool:
        process = self.selected
        if process is not None:
            self.spawn(self._details(process))
        return True

    async def _details(self, process: processes.Process) -> None:
        """What ``/proc`` says of *process*, in a box."""
        app = self.application
        try:
            lines = await asyncio.to_thread(processes.details, process.pid)
        except OSError as error:
            await self._say(error)
            self.reload()
            return
        label = max(display_width(caption) for caption, _ in lines) + 2
        rows = [caption + ":" + " " * (label - display_width(caption) - 1) + value for caption, value in lines]
        # As wide as the longest line, within the screen; a line still too
        # long wraps, and the box is as tall as the wrapped lines.
        desktop = self.parent
        screen_width = desktop.width if desktop is not None else 80
        screen_height = desktop.height if desktop is not None else 25
        width = max(40, min(max(display_width(row) for row in rows) + 4, screen_width - 4))
        room = width - 4
        tall = sum(max(1, -(-display_width(row) // room)) for row in rows)
        await Dialog(title=tr("Process {pid}").format(pid=process.pid), buttons="ok",
                     prompt=escape_caption("\n".join(rows)), modal_width=width,
                     modal_height=min(tall + 6, max(10, screen_height - 2))).execute(app)

    async def on_kill_process(self, command: KillProcess) -> bool:
        process = self.selected
        if process is not None and not processes.protected(process.pid):
            self.spawn(self._kill(process))
        return True

    async def _kill(self, process: processes.Process) -> None:
        """F8: SIGTERM to *process*, once the user says yes."""
        import signal

        question = tr("Ask process {pid} ({name}) to end?").format(pid=process.pid, name=process.name)
        answer = await Dialog(title=tr("Kill"), buttons="yes-no",
                              prompt=escape_caption(question)).execute(self.application)
        if answer is True:
            await self._signal(process, signal.SIGTERM)

    async def on_signal_process(self, command: SignalProcess) -> bool:
        process = self.selected
        if process is not None and not processes.protected(process.pid):
            self.spawn(self._choose_signal(process))
        return True

    def signal_menu(self) -> SubMenu:
        """*Signal*'s box: one entry per signal it offers."""
        menu = SubMenu()
        for sig in processes.SIGNALS:
            menu.add_item(escape_caption(processes.signal_caption(sig)), SendSignal(int(sig)))
        return menu

    async def _choose_signal(self, process: processes.Process) -> None:
        """F7: the signals in a box centred on the window; the one chosen sent."""
        from navml.widgets.menu.popup_menu import PopupMenu

        app = self.application
        menu = self.signal_menu()
        title = tr("Signal {pid}").format(pid=process.pid)
        width, height = PopupMenu.measure(menu, app, self, title)
        ox, oy = self.offset()
        x = ox + self.x + max(0, (self.width - width) // 2)
        y = oy + self.y + max(0, (self.height - height) // 2)
        chosen = await PopupMenu(menu, x, y, current=0, behind=self, title=title).execute(app)
        if chosen is None or not isinstance(chosen.command, SendSignal):
            return
        await self._signal(process, chosen.command.signal)

    async def on_send_signal(self, command: SendSignal) -> bool:
        process = self.selected
        if process is not None and not processes.protected(process.pid):
            self.spawn(self._signal(process, command.signal))
        return True

    async def _signal(self, process: processes.Process, sig: int) -> None:
        """*sig* to *process*; refused, offered as root; failed, said in a box.
        The processes are read again either way."""
        try:
            await asyncio.to_thread(processes.signal_process, process, sig)
        except OSError as error:
            if refused(error) and not processes.protected(process.pid) \
                    and await asyncio.to_thread(ELEVATION.available):
                await self._signal_as_root(process, sig, error)
            else:
                await self._say(error)
        self.reload()

    async def _signal_as_root(self, process: processes.Process, sig: int, error: OSError) -> None:
        from navigator.widgets.file_ops.as_root import ask_as_root

        message = tr("Cannot signal process {pid} ({name}): {error}").format(
            pid=process.pid, name=process.name, error=error.strerror or error)
        if not await ask_as_root(self.application, message):
            return

        def as_root() -> None:
            try:
                processes.still(process)
                ELEVATION.call("kill", pid=process.pid, signal=int(sig))
            finally:
                ELEVATION.release()

        try:
            await asyncio.to_thread(as_root)
        except OSError as failure:
            await self._say(failure)

    async def _say(self, error: OSError) -> None:
        await Dialog(title=tr("Process list"), buttons="ok",
                     prompt=escape_caption(error.strerror or str(error))).execute(self.application)

    # -- the buttons --------------------------------------------------------------------

    async def on_signal_button_click(self, event: Event) -> bool:
        return await self.on_signal_process(SignalProcess())

    async def on_kill_button_click(self, event: Event) -> bool:
        return await self.on_kill_process(KillProcess())

    async def on_details_button_click(self, event: Event) -> bool:
        return await self.on_process_details(ProcessDetails())

    async def on_close_button_click(self, event: Event) -> bool:
        self.request_close()
        return True

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # ``VolumesWindow``'s are.

    def prepare_context(self, x: int, y: int) -> None:
        """A right click on a row puts the list's cursor there."""
        index = self.processes.row_at(y - self.processes.y)
        if index is not None and self.processes.x <= x < self.processes.x + self.processes.width:
            self.processes.cursor = index

    def context_menu(self) -> ContextMenu:
        """The *Processes* menu's entries, built each time so its captions follow the language."""
        menu = ContextMenu()
        menu.add_item(tr("~R~e-read"), Rescan)
        menu.add_line()
        menu.add_item(tr("Tr~e~e"), ProcessTree)
        menu.add_item(tr("M~i~ne only"), ProcessMineOnly)
        menu.add_item(tr("~F~ilter"), FilterProcesses)
        menu.add_line()
        menu.add_item(tr("~D~etails..."), ProcessDetails)
        menu.add_item(tr("~S~ignal..."), SignalProcess)
        menu.add_item(tr("~K~ill..."), KillProcess)
        menu.add_line()
        menu.add_item(tr("~C~lose"), CloseWindow)
        return menu

    def context_point(self) -> tuple[int, int]:
        """Under the list's cursor row."""
        view = self.processes
        return view.x + 2, view.y + view.inset + view.header + max(0, view.cursor - view.scroll) + 1

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        return open_on_key(self)

    # -- Tab and Alt+letter ---------------------------------------------------------------

    async def on_select_next(self, event: SelectNext) -> bool:
        self._step(1)
        return True

    async def on_select_previous(self, event: SelectPrevious) -> bool:
        self._step(-1)
        return True

    def _step(self, by: int) -> None:
        """Tab within this window, wrapping, as a dialog's Tab stays in it."""
        order = [widget for widget in self.focusable() if widget is not self]
        if not order:
            return
        app = self.application
        focused = app.focused if app is not None else None
        index = order.index(focused) if focused in order else (-1 if by > 0 else 0)
        order[(index + by) % len(order)].focus()

    async def on_key(self, event: KeyEvent) -> bool:
        """Alt and a marked letter: that control, as a dialog's ``Alt+letter`` walk."""
        if event.alt and not event.ctrl and len(event.key) == 1 and event.key.isalpha():
            for control in (self.filter_caption, self.mine_box, self.tree_box, self.signal_button,
                            self.kill_button, self.details_button, self.close_button):
                if control.shortcut_match(event.key):
                    return await control.activate(event.key)
        return await super().on_key(event)
