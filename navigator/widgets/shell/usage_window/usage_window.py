"""The handlers behind ``usage_window.nml``.

The tree is read on a thread (:func:`navigator.lib.file_ops.dirusage.scan`),
through ``Background``; a timer meanwhile puts what the walk has met so far
on the status line from the job's plain fields, the only thing the thread
and the loop share.  Only the newest scan counts, and closing the window or
reading again stops the one under way.  What was read stays listed while a
second read runs, and when it lands the window goes back to the same
directory and the cursor to the same name, as far as they still exist.

F8 is the file manager's (:meth:`Manager.erase_located`), which is why the
window is given the manager that opened it, as the Synchronize window is.
"""

from __future__ import annotations

from typing import Any

from navkit import glyphs as glyphs_module
from navkit.bidi import display_width
from navkit.events import ContextMenuEvent, KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect, peek
from navml.background import Background, Outcome
from navml.commands import CloseWindow
from navml.widgets.dialog.commands import SelectNext, SelectPrevious
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent
from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click, open_on_key
from navml.widgets.window import Window

from navigator.lib.drives import Location
from navigator.lib.drives.listing import DirEntry
from navigator.lib.file_ops import dirusage
from navigator.lib.system.progress import PROGRESS_TICK
from navigator.widgets.manager.commands import Delete, Rescan
from navigator.widgets.manager.panel.panel import human_size
from navigator.widgets.shell.commands import (
    GoToUsage, ToggleApparentSize, UsageSortItems, UsageSortName, UsageSortSize,
)
from navigator.widgets.shell.usage_list.usage_list import UP

#: Where the window walks its tree.
_SCANNER = Background("nav-usage", workers=1)


class UsageWindow(Window):
    """What takes the room under a directory, in a window of its own."""

    def __init__(self, start: Any = None, manager: Any = None, apparent: bool = False, **kwargs: Any) -> None:
        """*start* is the directory to read -- a ``Path`` or a ``Location``,
        the home directory if None; *manager* the file manager whose F8 and
        panels the window uses; *apparent* ticks *Apparent size*."""
        super().__init__(**kwargs)
        from pathlib import Path

        self.start = Location.of(start if start is not None else Path.home())
        self.manager = manager
        self.apparent = apparent
        self.sort = "size"
        self.descending = True
        #: The tree read last, and the directory of it listed.
        self.tree: dirusage.UsageNode | None = None
        self.here: dirusage.UsageNode | None = None
        self._job: dirusage.UsageJob | None = None
        self._scans = 0
        self._ticker: Any = None
        self.title = str(self.start)

    @property
    def apparent(self) -> bool:
        """Whether *Apparent size* is ticked."""
        return bool(self.apparent_box.value & 1)

    @apparent.setter
    def apparent(self, value: bool) -> None:
        self.apparent_box.value = 1 if value else 0

    @property
    def scanning(self) -> bool:
        """Whether a read is under way."""
        return self._job is not None

    def mounted(self) -> None:
        super().mounted()
        effect(self, UsageWindow._follow_box)
        # Not from ``__init__``: until the window is on the desktop it has no
        # application, and ``Background`` would walk on the loop instead.
        self.rescan()

    def unmounting(self) -> None:
        self._stop()
        super().unmounting()

    def _follow_box(self) -> None:
        """*Apparent size* ticked or cleared, by a key, a click or Ctrl+A: list again."""
        self.entries.apparent = self.apparent
        self._show()

    def take_keyboard(self) -> None:
        # Not from ``mounted()``, for the reason ``TreeWindow`` gives.
        self.entries.focus()

    # -- reading ----------------------------------------------------------------------

    def rescan(self) -> None:
        """Walk the tree again, on a thread; only the newest walk is listed."""
        self._stop()
        self._scans += 1
        job = self._job = dirusage.UsageJob()
        app = self.application
        if app is not None:
            self._ticker = app.call_every(PROGRESS_TICK, self._tick_later)
        self._tick()
        _SCANNER.run(self, dirusage.scan, self.start, job,
                     done=lambda outcome, n=self._scans: self._scanned(n, outcome))

    def _stop(self) -> None:
        if self._job is not None:
            self._job.stop()
            self._job = None
        if self._ticker is not None:
            self._ticker.cancel()
            self._ticker = None

    async def _tick_later(self) -> None:
        self._tick()

    def _tick(self) -> None:
        """The status line while the walk goes: where it is, and what it has met."""
        job = self._job
        if job is None:
            return
        amount = job.size if self.apparent else job.usage
        self._say(tr("Reading {path} - {count} entries, {size}"), job.current or str(self.start),
                  count=f"{job.items:,}", size=human_size(amount))

    def _say(self, sentence: str, path: str, **values: str) -> None:
        """*sentence* on the status line, its ``{path}`` cut at its start --
        where a long one differs least -- so that the figures stay in sight."""
        room = self.status.width - display_width(sentence.format(path="", **values))
        marker = glyphs_module.ellipsis(self.glyphs)
        if display_width(path) > room:
            path = marker + path[-max(0, room - len(marker)):] if room > len(marker) else ""
        self.status.text = escape_caption(sentence.format(path=path, **values))

    def _scanned(self, scan: int, outcome: Outcome) -> None:
        if scan != self._scans:
            return
        self._stop()
        try:
            tree = outcome.result()
        except OSError as error:
            self.status.text = escape_caption(f"{self.start}: {error.strerror or error}")
            return
        if tree is None:
            return
        # Back where the last tree was listed, as far as it still goes.
        names = self.here.names() if self.here is not None else []
        here: dirusage.UsageNode | None = tree
        while names and (here := tree.find(names)) is None:
            names.pop()
        self.tree = tree
        self.here = here or tree
        self._show()

    # -- listing ----------------------------------------------------------------------

    def _show(self, cursor_on: str | None = None) -> None:
        """List the directory being shown, keeping the cursor on the name it
        was on -- or putting it on *cursor_on*.

        The list's items and cursor are peeked: ``_follow_box`` calls this,
        and an effect that read them would run again at every cursor move.
        """
        listing = self.entries
        if self.here is None:
            return
        if cursor_on is None:
            items = peek(listing, ListViewer.items)
            cursor = peek(listing, ListViewer.cursor)
            cursor_on = items[cursor].name if 0 <= cursor < len(items) else None
        shown: list[Any] = [] if self.here is self.tree else [UP]
        shown += dirusage.ordered(self.here, self.sort, self.descending, self.apparent)
        listing.whole = self.here.amount(self.apparent)
        listing.items = shown
        index = next((i for i, item in enumerate(shown) if item.name == cursor_on), 0)
        listing.cursor = index
        self._summary()

    def _summary(self) -> None:
        """The status line once read: the directory listed and what it holds."""
        here = self.here
        if here is None:
            return
        # Below the scanned directory -- the window's title -- by its names alone.
        path = "/".join(here.names()) or "."
        self._say(tr("{path}: {size} in {count} entries"), path,
                  size=human_size(here.amount(self.apparent)), count=f"{here.items:,}")

    def location_of(self, node: dirusage.UsageNode) -> Location:
        """Where *node* is on its drive."""
        return dirusage.location_of(self.start, node)

    def descend(self, node: dirusage.UsageNode) -> None:
        """List *node*, a directory, the cursor on its first entry."""
        if node.children is None:
            return
        self.here = node
        # Another directory's names: from their start again.
        self.entries.x_delta = 0
        self._show(cursor_on="")

    def ascend(self) -> None:
        """List the directory above, the cursor on the one just left."""
        here = self.here
        if here is None or here.parent is None:
            return
        self.here = here.parent
        self.entries.x_delta = 0
        self._show(cursor_on=here.name)

    # -- what the keys do ---------------------------------------------------------------

    async def on_chosen(self, event: ChosenEvent) -> bool:
        """Enter or a double click: ``..`` goes up, a directory down, and a file is gone to."""
        node = event.node
        if node is UP:
            self.ascend()
        elif isinstance(node, dirusage.UsageNode) and node.children is not None:
            self.descend(node)
        elif isinstance(node, dirusage.UsageNode):
            self.go(node)
        return True

    async def on_hbar_scroll(self, event: Any) -> bool:
        """The bottom bar was worked: the *Name* column scrolled to its column."""
        self.entries.x_delta = max(0, event.value)
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        """Right goes down, Left and Backspace up -- in the list only; Alt and
        a marked letter takes that control, as a dialog's ``Alt+letter`` walk."""
        app = self.application
        if app is not None and app.focused is self.entries and not (event.alt or event.ctrl or event.shift):
            selected = self.entries.selected
            if event.key == "right" and isinstance(selected, dirusage.UsageNode):
                self.descend(selected)
                return True
            if event.key in ("left", "backspace"):
                self.ascend()
                return True
        if event.alt and not event.ctrl and len(event.key) == 1 and event.key.isalpha():
            for control in (self.apparent_box, self.go_button, self.close_button):
                if control.shortcut_match(event.key):
                    return await control.activate(event.key)
        return await super().on_key(event)

    def go(self, node: dirusage.UsageNode | None, *, close: bool = False) -> bool:
        """The active panel to *node*: into it, a directory; to its directory,
        the cursor on it, anything else.  False with no panel to send."""
        manager = self.manager
        if node is None or manager is None or manager.parent is None:
            return False
        panel = manager.active_panel
        where = self.location_of(node)
        if node.children is not None:
            panel.location = where
        else:
            panel.go_to_entry(DirEntry(node.name, False, node.size, directory=where.parent))
        if close:
            self.request_close()
        return True

    async def on_go_to_usage(self, command: GoToUsage) -> bool:
        selected = self.entries.selected
        self.go(self.here if selected is UP else selected, close=True)
        return True

    async def on_rescan(self, event: Rescan) -> bool:
        self.rescan()
        return True

    async def on_toggle_apparent_size(self, command: ToggleApparentSize) -> bool:
        self.apparent = not self.apparent
        return True

    def _sort_by(self, by: str) -> None:
        """Sort *by* that; already so, the other way round."""
        if self.sort == by:
            self.descending = not self.descending
        else:
            self.sort, self.descending = by, True
        self._show()

    async def on_usage_sort_name(self, command: UsageSortName) -> bool:
        self._sort_by("name")
        return True

    async def on_usage_sort_size(self, command: UsageSortSize) -> bool:
        self._sort_by("size")
        return True

    async def on_usage_sort_items(self, command: UsageSortItems) -> bool:
        self._sort_by("items")
        return True

    def checks(self, command: Any) -> bool | None:
        """The *Sizes* menu ticks the sort in force and *Apparent size*."""
        for kind, by in ((UsageSortName, "name"), (UsageSortSize, "size"), (UsageSortItems, "items")):
            if isinstance(command, kind):
                return self.sort == by
        if isinstance(command, ToggleApparentSize):
            return self.apparent
        return super().checks(command)

    def refusal(self, command: Any) -> str:
        """Delete and Go on an entry, once the tree is read; Go with a file manager to send."""
        if isinstance(command, (Delete, GoToUsage)):
            if not isinstance(self.entries.selected, dirusage.UsageNode) and not (
                    isinstance(command, GoToUsage) and self.entries.selected is UP):
                return tr("The cursor is on no entry")
            if self.manager is None or self.manager.parent is None:
                return tr("No file manager is open")
            if isinstance(command, Delete) and self.scanning:
                return tr("Wait for the directory to be read")
        return super().refusal(command)

    # -- F8 ---------------------------------------------------------------------------

    async def on_delete(self, command: Delete) -> bool:
        node = self.entries.selected
        if (not isinstance(node, dirusage.UsageNode) or self.manager is None
                or self.manager.parent is None or self.scanning):
            return True
        self.spawn(self._erase(node))
        return True

    async def _erase(self, node: dirusage.UsageNode) -> None:
        """*node* erased by the file manager; gone, off the tree and its totals."""
        manager = self.manager
        where = self.location_of(node)
        entry = DirEntry(node.name, node.children is not None, node.size, is_link=node.is_link)
        try:
            done = await manager.erase_located(where.parent, [entry])
        except OSError as error:
            await Dialog(title=tr("Directory sizes"), buttons="ok",
                         prompt=escape_caption(error.strerror or str(error))).execute(self.application)
            return
        finally:
            for panel in (manager.left, manager.right):
                panel.reload()
        if not done:
            return
        index = peek(self.entries, ListViewer.cursor)
        dirusage.remove(node)
        self._show(cursor_on="")
        self.entries.cursor = min(index, max(0, len(self.entries.items) - 1))

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # ``VolumesWindow``'s are.

    def prepare_context(self, x: int, y: int) -> None:
        """A right click on a row puts the list's cursor there."""
        index = self.entries.row_at(y - self.entries.y)
        if index is not None and self.entries.x <= x < self.entries.x + self.entries.width:
            self.entries.cursor = index

    def context_menu(self) -> ContextMenu:
        """The *Sizes* menu's entries, built each time so its captions follow the language."""
        menu = ContextMenu()
        menu.add_item(tr("~R~e-read"), Rescan)
        menu.add_line()
        menu.add_item(tr("Sort by ~n~ame"), UsageSortName)
        menu.add_item(tr("Sort by ~s~ize"), UsageSortSize)
        menu.add_item(tr("Sort by ~e~ntries"), UsageSortItems)
        menu.add_item(tr("~A~pparent size"), ToggleApparentSize)
        menu.add_line()
        menu.add_item(tr("~G~o to directory"), GoToUsage)
        menu.add_item(tr("~D~elete..."), Delete)
        menu.add_line()
        menu.add_item(tr("~C~lose"), CloseWindow)
        return menu

    def context_point(self) -> tuple[int, int]:
        """Under the list's cursor row."""
        view = self.entries
        return view.x + 2, view.y + view.inset + view.header + max(0, view.cursor - view.scroll) + 1

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        return open_on_key(self)

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
