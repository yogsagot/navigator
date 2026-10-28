"""The handlers behind ``sync_window.nml``, and :func:`walk_trees`, which fills one.

The two trees are walked on a thread (:func:`navigator.lib.file_ops.dirsync.walk`),
under *Compare directories* if it takes a while, whose Cancel stops it.
Every path is kept, the same ones too; *Show identical* only changes which
are listed.  An action changed replaces its row in a new list -- a
collection must be replaced to count as changed.

*Synchronize* is the file manager's (``Manager.synchronize``): the copies
and deletes go through F5's and F8's own workers, boxes and questions.
"""

from __future__ import annotations

from typing import Any

from navkit.events import ContextMenuEvent, Event, KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect, peek
from navml.commands import CloseWindow
from navml.widgets.dialog.commands import SelectNext, SelectPrevious
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click, open_on_key
from navml.widgets.window import Window

from navigator.lib.file_ops import dirsync
from navigator.lib.system.job import Stopped
from navigator.widgets.manager.commands import (
    DiffFiles,
    Rescan,
    SetAllSyncActions,
    SetSyncAction,
    Synchronize,
    ToggleHidden,
    ToggleTree,
)
from navigator.widgets.manager.panel.panel import human_size
from navigator.widgets.manager.sync_list import SyncList


async def walk_trees(app: Any, left: Any, right: Any, request: Any, show_hidden: bool) -> list[Any] | None:
    """``dirsync.walk`` on a thread, under its box if it takes a while; None
    when cancelled, or when a directory could not be read (said)."""
    from navigator.lib.file_ops.filecopy import error_message
    from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress
    from navigator.widgets.manager.compare_progress import CompareProgress

    job = dirsync.SyncJob()

    def refresh(box: Any) -> None:
        box.directory = job.directory
        box.count = job.found

    try:
        return await run_with_progress(
            app, lambda: dirsync.walk(left, right, request, job, show_hidden), job,
            CompareProgress, refresh, delay=SLOW_PROGRESS_DELAY,
        )
    except Stopped:
        return None
    except OSError as error:
        if app is not None:
            await Dialog(title=tr("Error"), prompt=escape_caption(error_message(error)), buttons="ok").execute(app)
        return None


def _name(place: Any) -> str:
    return getattr(place, "name", "") or str(place)


class SyncWindow(Window):
    """Two trees compared: what differs, and what is to be done with it."""

    #: The actions, merged with the markup's ``keys:`` block, which names a
    #: command and cannot construct one.  Total Commander's keys.
    keys = {
        "right": SetSyncAction("right"),
        "left": SetSyncAction("left"),
        "space": SetSyncAction("skip"),
        "delete": SetSyncAction("delete"),
        "backspace": SetSyncAction("default"),
        "ctrl+right": SetAllSyncActions("right"),
        "ctrl+left": SetAllSyncActions("left"),
        "ctrl+backspace": SetAllSyncActions("default"),
    }

    #: Whether the next window opens in the tree view: the last one's choice,
    #: for the session.
    tree_view = False

    def __init__(self, manager: Any = None, left: Any = None, right: Any = None, request: Any = None,
                 rows: list[Any] | None = None, show_hidden: bool = True, **kwargs: Any) -> None:
        """*manager* does the synchronizing; *left* and *right* are the two
        directories, *request* the compare's checks and *rows* what
        ``dirsync.walk`` found; *show_hidden* walks dot-files too."""
        super().__init__(**kwargs)
        self.manager = manager
        self.left_place = left
        self.right_place = right
        self.request = request
        self.show_hidden = show_hidden
        self.all_rows: list[Any] = list(rows or ())
        #: The rows as a tree, for the tree view: built when first asked for,
        #: dropped whenever the rows change.
        self._tree: dirsync.DirNode | None = None
        self.rows.tree = SyncWindow.tree_view
        self.tree_box.value = 1 if SyncWindow.tree_view else 0
        #: What the rows' actions come to, counted again whenever a row
        #: changes: what the summary line says, and what F5's ``enables`` --
        #: asked at every repaint of the key bar -- reads instead of a plan.
        self.totals = dirsync.summary(self.all_rows)
        # The directories' names alone: the whole paths are Window > List's.
        self.title = tr("Synchronize {left} and {right}").format(left=_name(left), right=_name(right))
        self._show()

    @property
    def show_identical(self) -> bool:
        """Whether *Show identical* is ticked."""
        return bool(self.identical.value & 1)

    @show_identical.setter
    def show_identical(self, value: bool) -> None:
        self.identical.value = 1 if value else 0

    def mounted(self) -> None:
        super().mounted()
        effect(self, SyncWindow._follow_box)
        effect(self, SyncWindow._follow_cursor)

    def _follow_box(self) -> None:
        """A box ticked or cleared, by a key, a click, Ctrl+H or Ctrl+T: list again."""
        self.identical.value  # noqa: B018 -- what this effect follows
        tree = bool(self.tree_box.value & 1)
        SyncWindow.tree_view = self.rows.tree = tree
        self._show()

    def _follow_cursor(self) -> None:
        """The cursor moved, or the rows changed: the bottom frame says of the row it is on."""
        self.info.text = self.rows.footer_text()

    def take_keyboard(self) -> None:
        self.rows.focus()

    def list_name(self) -> str:
        return tr("Synchronize - {left}, {right}").format(left=self.left_place, right=self.right_place)

    def short_name(self) -> str:
        return tr("Synchronize")

    # -- what is listed ----------------------------------------------------------

    def _show(self) -> None:
        """List the rows -- as a tree in the tree view -- keeping the cursor on
        the path it was on; the summary follows.  The list peeks at its items
        and cursor, as ``_follow_box`` calls this and must not run again at
        every cursor move."""
        listing = self.rows
        root = None
        if peek(listing, SyncList.tree):
            if self._tree is None:
                self._tree = dirsync.build_tree(self.all_rows)
            root = self._tree
        listing.show_rows(self.all_rows, root, self.show_identical)
        listing.error = None if peek(listing, ListViewer.items) else tr("The directories are the same.")
        self.totals = dirsync.summary(self.all_rows)
        self.summary.text = self.summary_text()

    def summary_text(self) -> str:
        totals = self.totals
        return tr("{right} right ({right_size}), {left} left ({left_size}), {delete} to delete").format(
            right=totals.right, right_size=human_size(totals.right_bytes), left=totals.left,
            left_size=human_size(totals.left_bytes), delete=totals.delete)

    def _replace(self, changed: dict[Any, Any]) -> None:
        """The rows in *changed* (old row -> new row) put in place."""
        if changed:
            self.all_rows = [changed.get(id(row), row) for row in self.all_rows]
            if self._tree is not None:
                dirsync.replace_rows(self._tree, changed)
            self._show()

    # -- the actions ---------------------------------------------------------------

    async def on_set_sync_action(self, command: SetSyncAction) -> bool:
        """The row at the cursor -- or, on a directory, every row beneath it
        that allows it -- given the action."""
        changed = {}
        for row in self.rows.selected_rows():
            new = dirsync.with_action(row, command.action)
            if new is not row:
                changed[id(row)] = new
        self._replace(changed)
        return True

    async def on_set_all_sync_actions(self, command: SetAllSyncActions) -> bool:
        changed = {}
        for row in self.all_rows:
            new = dirsync.with_action(row, command.action)
            if new is not row:
                changed[id(row)] = new
        self._replace(changed)
        return True

    def plan(self) -> dirsync.SyncPlan:
        return dirsync.plan(self.all_rows, self.left_place, self.right_place)

    def _comparable(self) -> Any:
        """The row under the cursor, when it is two files to compare."""
        row = self.rows.selected_row
        if (row is None or row.left is None or row.right is None
                or row.left.kind != "file" or row.right.kind != "file"):
            return None
        return row

    def refusal(self, command: Any) -> str:
        if isinstance(command, SetSyncAction):
            return "" if self.rows.selected_allows(command.action) else tr("Not for this row")
        if isinstance(command, Synchronize):
            totals = self.totals
            if self.manager is None or self.manager.parent is None:
                return tr("The file panels these were compared from are closed")
            return "" if totals.right or totals.left or totals.delete else tr("Nothing is set to copy or delete")
        if isinstance(command, DiffFiles):
            return "" if self._comparable() is not None else tr("The cursor is not on two files")
        return super().refusal(command)

    def checks(self, command: Any) -> bool | None:
        """The menu ticks *Show identical* and *Tree view* while they are on."""
        if isinstance(command, ToggleHidden):
            return self.show_identical
        if isinstance(command, ToggleTree):
            return self.rows.tree
        return super().checks(command)

    async def on_toggle_hidden(self, event: ToggleHidden) -> bool:
        self.show_identical = not self.show_identical
        return True

    async def on_toggle_tree(self, event: ToggleTree) -> bool:
        """Ctrl+T: *Tree view* ticked or cleared -- the box's effect lists again,
        the cursor on the same path."""
        self.tree_box.value = 0 if self.tree_box.value & 1 else 1
        return True

    async def on_diff_files(self, event: DiffFiles) -> bool:
        """Enter, F3: the two files side by side; the same two said to be so."""
        row = self._comparable()
        desktop = self.desktop
        if row is not None and desktop is not None:
            from navigator.lib.file_ops.filecopy import shown
            from navigator.widgets.viewer.diff_window import open_diff

            left, right = (shown(dirsync.below(place, row.path)) for place in (self.left_place, self.right_place))
            self.spawn(open_diff(desktop, left, right))
        return True

    async def on_rescan(self, event: Rescan) -> bool:
        self.spawn(self.rescan())
        return True

    async def rescan(self) -> None:
        """Ctrl+R: both trees walked again, the actions back to their defaults."""
        rows = await walk_trees(self.application, self.left_place, self.right_place, self.request,
                                self.show_hidden)
        if rows is not None:
            self.all_rows = rows
            self._tree = None
            self._show()

    async def on_synchronize(self, event: Synchronize) -> bool:
        self.spawn(self.synchronize())
        return True

    async def synchronize(self) -> None:
        """F5: the rows' copies and deletes done by the file manager, then both trees compared again."""
        plan = self.plan()
        if self.manager is None or not (plan.pairs or plan.deletes):
            return
        if await self.manager.synchronize(plan):
            await self.rescan()

    async def on_sync_button_click(self, event: Event) -> bool:
        """*Synchronize*: F5's work, started and not awaited -- it asks first,
        and a handler waiting on a dialog holds the loop that would show it."""
        if self.enables(Synchronize()):
            self.spawn(self.synchronize())
        return True

    async def on_close_button_click(self, event: Event) -> bool:
        self.request_close()
        return True

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # ``VolumesWindow``'s are.

    def prepare_context(self, x: int, y: int) -> None:
        """A right click on a row puts the list's cursor there."""
        index = self.rows.row_at(y - self.rows.y)
        if index is not None and self.rows.x <= x < self.rows.x + self.rows.width:
            self.rows.cursor = index

    def context_menu(self) -> ContextMenu:
        menu = ContextMenu()
        menu.add_item(tr("~C~ompare files"), DiffFiles)
        menu.add_line()
        menu.add_item(tr("Copy ~r~ight"), SetSyncAction("right"))
        menu.add_item(tr("Copy ~l~eft"), SetSyncAction("left"))
        menu.add_item(tr("~D~elete"), SetSyncAction("delete"))
        menu.add_item(tr("S~k~ip"), SetSyncAction("skip"))
        menu.add_item(tr("D~e~fault action"), SetSyncAction("default"))
        menu.add_line()
        menu.add_item(tr("~T~ree view"), ToggleTree)
        menu.add_item(tr("~S~ynchronize"), Synchronize)
        menu.add_item(tr("Cl~o~se"), CloseWindow)
        return menu

    def context_point(self) -> tuple[int, int]:
        view = self.rows
        return view.x + 2, view.y + view.inset + view.header + max(0, view.cursor - view.scroll) + 1

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        return open_on_key(self)

    # -- a dialog's row: Tab and Alt+letter ------------------------------------------

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
            for control in (self.identical, self.tree_box, self.sync_button, self.close_button):
                if control.shortcut_match(event.key):
                    return await control.activate(event.key)
        return await super().on_key(event)
