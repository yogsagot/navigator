"""The handlers behind ``manager.nml``.

The file manager window.  What the document says is the two panels, their
geometry and the keys; what is left here is the logic -- what the commands
do, which panel is active, and where the panels open.

This file never names the generated class.  ``class Manager(Window)`` is the
base the markup's ``Manager(Window):`` head asks for.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Awaitable, Callable

from navkit.reactive import computed, effect, reactive, untracked

from navml.widgets.dialog.dialog import Dialog
from navml.widgets.window import Window

from navigator.commands import (
    ChangeDirectory,
    Copy,
    Delete,
    DeleteSingle,
    Edit,
    GoParent,
    MakeDirectory,
    MakeLink,
    QuickSearch,
    QuickView,
    RenameMove,
    Rescan,
    ScrollNames,
    InvertSelection,
    SelectGroup,
    SwitchPanel,
    ToggleHidden,
    ToggleMark,
    ToggleShowMode,
    ToggleTree,
    UnselectGroup,
    View,
    ViewAsHex,
    ViewAsText,
)
from navigator.widgets.mkdir_dialog import MkdirDialog
from navigator.widgets.panel import Panel


class Manager(Window):
    """The file manager: two panels, in a window on the desktop."""

    #: The panels' frames are this window's frame.
    framed = False

    #: The Gray keys, merged with the markup's ``keys:`` block, which names a
    #: command and cannot construct one.  Each says ``by_key``, so it steps
    #: aside while the command line has text; Shift+Gray ``+``/``-`` open the
    #: dialog with *Except mask* ticked, as DN's ``ShiftState and 3 <> 0``
    #: did, and Ctrl+Gray ``*`` inverts the directories too (``kbCtrlGAst``).
    #:
    #: **And the plain ``+``, ``-`` and ``*``**, Midnight Commander's rule.
    #: Only a terminal that reports the keypad on its own -- the kitty
    #: protocol, or application keypad mode honoured -- can tell Gray ``+``
    #: from the other one, and VTE (xfce4-terminal, GNOME Terminal) and
    #: PyCharm's JediTerm send a bare ``+`` for both.  Binding the character
    #: too makes the keys work everywhere; what it costs is starting a command
    #: with one of the three from the panel, and after any other character
    #: they type as usual.
    keys = {
        "plus": SelectGroup(by_key=True),
        "-": UnselectGroup(by_key=True),
        "*": InvertSelection(by_key=True),
        "kp_plus": SelectGroup(by_key=True),
        "kp_minus": UnselectGroup(by_key=True),
        "kp_multiply": InvertSelection(by_key=True),
        "shift+kp_plus": SelectGroup(invert=True, by_key=True),
        "shift+kp_minus": UnselectGroup(invert=True, by_key=True),
        "ctrl+kp_multiply": InvertSelection(directories=True, by_key=True),
        #: DN's ``fmoBackGoesBack``: Backspace goes up while the command line
        #: is empty, and Shift+Backspace and Ctrl+PgUp whatever it holds.
        "backspace": GoParent(by_key=True),
        "shift+backspace": GoParent(),
        "ctrl+pageup": GoParent(),
        #: DN's ``fmoDelErase``: Del deletes while the command line is empty,
        #: and edits the line otherwise; Shift+Del is the menu's single delete.
        "delete": Delete(by_key=True),
        "shift+delete": DeleteSingle(by_key=True),
        #: Scrolling a name too long for its column; the list mode's panel
        #: takes these first and moves a column instead.
        "left": ScrollNames(-1),
        "right": ScrollNames(1),
    }

    #: How long the tree's cursor has to rest before the panel follows it:
    #: DOS Navigator's thirty ticks of the 18.2 Hz timer (``NeedLocated``).
    LOCATE_DELAY = 30 / 18.2

    #: The panel something else stands in for -- the directory tree (Ctrl+T)
    #: or the quick view (Ctrl+Q) -- and that something, or None for both
    #: while the two panels are showing.  DOS Navigator's ``LType``/``RType``:
    #: one side at a time is ever not a panel.  Reactive, so ``active_panel``
    #: and the follow effects move with them.
    replaced: Any = reactive(None)
    replacement: Any = reactive(None)

    #: The panel that last held the keyboard.  What ``active_panel`` answers
    #: while neither does -- Ctrl+O has given the keyboard to the console, or
    #: a dialog has it -- since the panel the user left active is still the
    #: one a command means.
    _last_panel: Any = reactive(None)

    def __init__(self, left: Path, right: Path, **kwargs):
        """Build the window, then seed where the panels open.

        ``super().__init__()`` is the generated half, so the whole tree exists
        from the next line on -- which is the contract the merge rests on.

        **Where the panels open is seeded rather than bound.**  A markup
        property line compiles to a binding, a bound attribute is read-only
        until something unbinds it, and
        :meth:`~navigator.widgets.panel.Panel.enter` assigns ``path`` every
        time the user descends a directory.  So a property a widget
        *navigates* can be given a starting value by its parent and cannot be
        bound to one.
        """
        super().__init__(**kwargs)
        self.left.path = left
        self.right.path = right
        self.tree.visible = False
        self.quick.visible = False
        #: The pending "panel, follow the tree" -- cancelled by every move.
        self._follow: asyncio.Task[Any] | None = None

    def mounted(self) -> None:
        super().mounted()
        effect(self, Manager._remember_panel)
        effect(self, Manager._tree_follows_panel)
        effect(self, Manager._panel_follows_tree)
        effect(self, Manager._quick_view_follows_panel)

    # -- commands ------------------------------------------------------------
    #
    # The keys are the markup's ``keys:`` block.  Alt+X is not among them: a
    # way out of Navigator cannot live on a window the user can close, so it
    # is the application's.

    async def on_switch_panel(self, event: SwitchPanel) -> bool:
        self.switch_panel()
        return True

    async def on_rescan(self, event: Rescan) -> bool:
        if self.tree.focused:
            self.tree.reload()
        else:
            self.active_panel.reload()
        return True

    async def on_change_directory(self, event: ChangeDirectory) -> bool:
        # Started, not awaited, for the reason ``on_make_directory`` gives.
        self.spawn(self.change_directory())
        return True

    async def change_directory(self) -> None:
        """Alt+T: *Choose Directory*, and the active panel goes where it says.

        The panel that asked, remembered before the dialog takes the keyboard:
        while it is up the focus is in the dialog, and which panel was active
        is no longer something the focus can say.
        """
        from navigator.widgets.change_dir_dialog import ChangeDirDialog

        panel = self.active_panel
        chosen = await ChangeDirDialog(start=panel.path, hidden=panel.show_hidden).execute(self.application)
        if chosen is not None:
            panel.path = Path(chosen)
            panel.focus()

    def enables(self, command: Any) -> bool:
        """Tagging and the quick search are the active panel's, and not while
        the tree or the quick view standing beside it has the keyboard -- those
        are not a listing.  Asked of a menu too, where neither has it and the
        panel is meant."""
        if isinstance(
            command, (ToggleMark, SelectGroup, UnselectGroup, InvertSelection, QuickSearch)
        ):
            if getattr(command, "by_key", False) and self._command_line_has_text():
                # Disabled, so the key falls through and types its character.
                return False
            return not (self.tree.focused or self.quick.focused)
        if isinstance(command, GoParent):
            if command.by_key and self._command_line_has_text():
                # Disabled, so Backspace falls through and edits the line.
                return False
            return not (self.tree.focused or self.quick.focused)
        if isinstance(command, (Delete, DeleteSingle)) and command.by_key:
            if self._command_line_has_text():
                # Disabled, so Del deletes a character and Shift+Del cuts.
                return False
        if isinstance(command, DeleteSingle):
            entry = self.active_panel.selected
            return not (self.tree.focused or self.quick.focused) and (
                entry is not None and entry.name != ".."
            )
        if isinstance(command, (Copy, RenameMove, MakeLink, Delete)):
            # DN's ``GetSelection`` answering nil: nothing tagged and the
            # cursor on ``..``, or a listing that is not a panel's.
            return not (self.tree.focused or self.quick.focused) and bool(
                self.selection(self.active_panel)
            )
        if isinstance(command, ScrollNames):
            panel = self.active_panel
            return (
                not (self.tree.focused or self.quick.focused)
                and not self._command_line_has_text()
                and panel.can_scroll_names(command.step)
            )
        return super().enables(command)

    def checks(self, command: Any) -> bool | None:
        """Ctrl+H is ticked in the menu while the active panel shows its dot-files."""
        if isinstance(command, ToggleHidden):
            return self.active_panel.show_hidden
        return super().checks(command)

    def _command_line_has_text(self) -> bool:
        """Whether the command line of the screen this window is on holds
        anything -- a blank included, as for Space.  ``False`` with none."""
        widget = self.parent
        while widget is not None:
            line = getattr(widget, "command_line", None)
            if line is not None:
                return bool(line.value)
            widget = widget.parent
        return False

    async def on_scroll_names(self, event: ScrollNames) -> bool:
        self.active_panel.scroll_names(event.step)
        return True

    async def on_go_parent(self, event: GoParent) -> bool:
        self.active_panel.go_up()
        return True

    async def on_toggle_mark(self, event: ToggleMark) -> bool:
        """Insert: tag the active panel's entry and step down."""
        self.active_panel.toggle_mark()
        return True

    async def on_invert_selection(self, event: InvertSelection) -> bool:
        self.active_panel.invert_marks(directories=event.directories)
        return True

    async def on_select_group(self, event: SelectGroup) -> bool:
        # Started, not awaited, for the reason ``on_make_directory`` gives.
        self.spawn(self.select_group(select=True, invert=event.invert))
        return True

    async def on_unselect_group(self, event: UnselectGroup) -> bool:
        self.spawn(self.select_group(select=False, invert=event.invert))
        return True

    async def select_group(self, *, select: bool, invert: bool) -> None:
        """Gray ``+``/``-``: ask for a mask, then tag or untag what it matches.

        The panel is taken before the dialog is, for the reason
        :meth:`change_directory` gives.
        """
        from navigator.widgets.select_dialog import SelectDialog

        panel = self.active_panel
        answer = await SelectDialog(select=select, invert=invert).execute(self.application)
        if answer is not None:
            mask, except_mask = answer
            panel.select_group(mask, select=select, invert=except_mask)

    async def on_toggle_show_mode(self, event: ToggleShowMode) -> bool:
        """Ctrl+Y: the active panel's next show mode -- simple, detailed, list."""
        self.active_panel.cycle_view_mode()
        return True

    async def on_toggle_hidden(self, event: ToggleHidden) -> bool:
        """Ctrl+H: the active panel's dot-files, hidden or shown."""
        self.active_panel.toggle_hidden()
        return True

    async def on_quick_search(self, event: QuickSearch) -> bool:
        """Ctrl+S: the active panel starts its quick search."""
        self.active_panel.start_quick_search()
        return True

    async def on_toggle_tree(self, event: ToggleTree) -> bool:
        self.toggle_tree()
        return True

    async def on_quick_view(self, event: QuickView) -> bool:
        self.toggle_quick_view()
        return True

    async def on_tree_chosen(self, event: Any) -> bool:
        """Enter in the tree: the panel goes there now, not after the pause."""
        self.active_panel.path = event.node.data
        return True

    async def on_make_directory(self, event: MakeDirectory) -> bool:
        # **Started, not awaited.**  A handler that waits for a dialog holds
        # the event queue's only consumer, so the dialog is never painted and
        # the key that would dismiss it is never dispatched.  `spawn' lets
        # this handler return, the batch finish and the frame appear -- see
        # `Dialog.execute', which refuses the mistake.
        self.spawn(self.make_directory())
        return True

    async def make_directory(self) -> None:
        """F7: ask for a name, and make it in the active panel.

        The shape every file operation will take: start a dialog, wait for
        its answer in a task, act, and tell the panel to look again.  The
        rescan is a token rather than a call because the panel's listing
        follows its path and its token -- which is what makes "the directory
        changed" and "the user pressed Ctrl+R" the same code path.
        """
        panel = self.active_panel
        name = await MkdirDialog().execute(self.application)
        if not name:
            return
        try:
            (panel.path / name).mkdir()
        except OSError as error:
            await Dialog(
                title="Cannot make directory",
                prompt=error.strerror or str(error),
                buttons="ok",
            ).execute(self.application)
        panel.reload()

    # -- copying and moving ------------------------------------------------------

    def selection(self, panel: Panel) -> list[Any]:
        """DN's ``GetSelection``: the tagged entries, or else the one under the cursor.

        Empty when nothing is tagged and the cursor is on ``..``, which is
        never a thing to copy.
        """
        marked = panel.marked_entries
        if marked:
            return marked
        entry = panel.selected
        if entry is None or entry.name == "..":
            return []
        return [entry]

    async def on_copy(self, event: Copy) -> bool:
        """F5: ``cmCopyFiles``."""
        self.spawn(self.copy_files(move=False))
        return True

    async def on_rename_move(self, event: RenameMove) -> bool:
        """F6: ``cmMoveFiles``, the same dialog with *Remove source* ticked."""
        self.spawn(self.copy_files(move=True))
        return True

    async def copy_files(self, *, move: bool) -> None:
        """Ask where, copy on a thread, and let both panels look again.

        ``make_directory``'s shape with a worker in the middle: the copy runs
        through ``asyncio.to_thread`` so the loop keeps painting, and
        :meth:`_watch_copy` stands between the two -- the progress box once
        the copy has taken a moment, and every question the worker puts, one
        at a time.  What was copied in full is untagged, as DN deselected each
        file as it went; what was skipped keeps its tag.
        """
        from navigator import filecopy
        from navigator.widgets.copy_dialog import CopyDialog

        app = self.application
        panel, other = self.active_panel, self.passive_panel
        entries = self.selection(panel)
        if app is None or not entries:
            return
        here = Path(panel.path)
        request = await CopyDialog(
            entries=entries, here=here, other=Path(other.path),
            hidden=panel.show_hidden, move=move,
        ).execute(app)
        if request is None:
            return
        job = filecopy.CopyJob()
        work = asyncio.ensure_future(asyncio.to_thread(filecopy.run, request, job, here))
        try:
            await self._watch_copy(work, job, move)
            done = await work
        finally:
            if not work.done():
                # Cancelled -- Navigator is going -- so the thread is told to
                # stop rather than left copying, or asking, behind it.
                job.stop()
        names = {path.name for path in done}
        if names:
            panel.marked = panel.marked - names
        panel.reload()
        other.reload()

    async def _watch_copy(self, work: asyncio.Future[Any], job: Any, move: bool) -> None:
        """The copy's progress box, *Stop*, and the worker's questions, until *work* ends."""
        from navigator.widgets.copy_progress import CopyProgress

        def refresh(box: Any) -> None:
            box.source, box.dest = job.source, job.dest
            box.file_done, box.file_bytes = job.file_done, job.file_bytes
            box.done, box.total = job.done_bytes, job.total_bytes

        await self._watch_job(
            work, job, lambda: CopyProgress(move=move), refresh, self._answer_copy_question
        )

    async def _watch_job(
        self,
        work: asyncio.Future[Any],
        job: Any,
        make_box: Callable[[], Any],
        refresh: Callable[[Any], None],
        answer: Callable[[Any], Awaitable[Any]],
    ) -> None:
        """A worker's progress box, its one button, and its questions, until *work* ends.

        The box is *make_box*'s, put up once the work has taken
        ``PROGRESS_DELAY``, and *refresh* copies *job*'s fields into it every
        tick.  Each question the worker puts goes to *answer*, one at a time.
        The box closing -- its button, or Esc -- holds the worker and asks
        ``dlQueryAbort`` before anything stops.
        """
        from navigator.widgets.file_window.file_window import PROGRESS_DELAY, PROGRESS_TICK

        app = self.application
        loop = asyncio.get_running_loop()
        started = loop.time()
        box: Any = None
        shown: asyncio.Future[Any] | None = None

        async def tick() -> None:
            # Through the queue, so each update is painted with its batch.
            if box is not None:
                refresh(box)

        repeat = app.call_every(PROGRESS_TICK, tick)
        try:
            while not work.done():
                waiting = {work} if shown is None else {work, shown}
                await asyncio.wait(waiting, timeout=PROGRESS_TICK, return_when=asyncio.FIRST_COMPLETED)
                pending = job.take_question()
                if pending is not None:
                    question, future = pending
                    result = None
                    try:
                        result = await answer(question)
                    finally:
                        future.set_result(result)
                    continue
                if shown is not None and shown.done():
                    # *Stop*, or Esc: ``dlQueryAbort`` before anything stops.
                    box, shown = None, None
                    job.pause()
                    try:
                        if await self._ask_yes_no("Abort operation?") is True:
                            job.stop()
                    finally:
                        job.resume()
                    continue
                if work.done():
                    break
                if shown is None and not job.stopped and loop.time() - started >= PROGRESS_DELAY:
                    box = make_box()
                    refresh(box)
                    shown = asyncio.ensure_future(box.execute(app))
        finally:
            repeat.cancel()
            if shown is not None and not shown.done():
                # Cancelled rather than closed: a box whose ``execute`` has
                # not started yet has nothing to close, and would mount and
                # wait for ever the moment it did.  ``execute``'s own
                # ``finally`` takes it down.  Waited for, not awaited, so a
                # cancellation of this task is not swallowed with its own.
                shown.cancel()
                await asyncio.wait({shown})

    async def _ask_yes_no(self, prompt: str, title: str = "Confirm") -> Any:
        return await Dialog(title=title, prompt=prompt, buttons="yes-no-cancel").execute(self.application)

    async def _answer_copy_question(self, question: Any) -> Any:
        """Put one of the worker's questions to the user, and answer as it expects."""
        from navml.widgets.dialog.control import escape_caption

        from navigator import filecopy
        from navigator.widgets.overwrite_query import OverwriteQuery

        app = self.application
        if isinstance(question, filecopy.Overwrite):
            return await OverwriteQuery(question=question).execute(app)
        if isinstance(question, filecopy.CreateDirectory):
            # DN's ``dlQueryCreateDir``.
            return await self._ask_yes_no(
                f"Would you like to create directory {escape_caption(str(question.path))}?"
            ) is True
        if isinstance(question, filecopy.NoRoom):
            # DN's ``erNotDiskSpace1``: Yes goes on without this file.
            return await self._ask_yes_no(
                f"There is not enough room to copy file "
                f"{escape_caption(question.dest.name)}. Copy other files?",
                title="Warning",
            ) is True
        if isinstance(question, filecopy.Failure):
            return await self._ask_skip(question.message)
        return None

    async def _ask_skip(self, message: str) -> bool:
        """An error with *Skip* and *Cancel*: True to go on without this file."""
        from navkit.reactive import unbind

        from navml.widgets.dialog.button import Button
        from navml.widgets.dialog.control import escape_caption

        box = Dialog(title="Error", prompt=escape_caption(message), buttons="ok-cancel")
        unbind(box.ok, Button.text)
        box.ok.text = "~S~kip"
        return await box.execute(self.application) is True

    # -- deleting ----------------------------------------------------------------

    async def on_delete(self, event: Delete) -> bool:
        """F8 and Del: ``cmPanelErase``."""
        self.spawn(self.delete_files(single=False))
        return True

    async def on_delete_single(self, event: DeleteSingle) -> bool:
        """Shift+F8 and Shift+Del: ``cmSingleDel``, the cursor's entry whatever is tagged."""
        self.spawn(self.delete_files(single=True))
        return True

    async def delete_files(self, *, single: bool) -> None:
        """Ask, delete on a thread, and let both panels look again.

        ``copy_files``'s shape: the Delete dialog, then ``fileerase.run``
        through ``asyncio.to_thread`` with :meth:`_watch_job` between the two
        -- the *Erase* box, and the worker's *not empty*, *read-only* and
        failure questions.  What went is untagged; what was kept keeps its tag.
        """
        from navigator import fileerase
        from navigator.widgets.delete_dialog import DeleteDialog
        from navigator.widgets.delete_progress import DeleteProgress

        app = self.application
        panel, other = self.active_panel, self.passive_panel
        if single:
            entry = panel.selected
            entries = [] if entry is None or entry.name == ".." else [entry]
        else:
            entries = self.selection(panel)
        if app is None or not entries:
            return
        request = await DeleteDialog(entries=entries, here=Path(panel.path)).execute(app)
        if request is None:
            return
        job = fileerase.EraseJob()
        work = asyncio.ensure_future(asyncio.to_thread(fileerase.run, request, job))

        def refresh(box: Any) -> None:
            box.action, box.path = job.action, job.path
            box.done, box.total = job.done, job.total

        done: list[Path] = []
        try:
            await self._watch_job(work, job, DeleteProgress, refresh, self._answer_erase_question)
            done = await work
        finally:
            if not work.done():
                job.stop()
            names = {path.name for path in done}
            if names:
                panel.marked = panel.marked - names
            panel.reload()
            other.reload()

    async def _answer_erase_question(self, question: Any) -> Any:
        """Put one of the eraser's questions to the user, and answer as it expects."""
        from navigator import fileerase, filecopy
        from navigator.widgets.erase_query import EraseQuery

        if isinstance(question, (fileerase.NotEmpty, fileerase.ReadOnly)):
            return await EraseQuery(question=question).execute(self.application)
        if isinstance(question, filecopy.Failure):
            return await self._ask_skip(question.message)
        return None

    # -- symbolic links ----------------------------------------------------------

    async def on_make_link(self, event: MakeLink) -> bool:
        """Shift+F5: a symbolic link to each selected entry."""
        self.spawn(self.make_links())
        return True

    async def make_links(self) -> None:
        """Ask where, link each entry there, and let both panels look again.

        ``copy_files``'s shape without the worker: the target is read as
        Copy's is, a directory that is not there yet is offered as Copy
        offers it, and a link that cannot be made puts Copy's *Skip* /
        *Cancel*.  What was linked is untagged.
        """
        from navml.widgets.dialog.control import escape_caption

        from navigator import filecopy, filelink
        from navigator.widgets.link_dialog import LinkDialog

        app = self.application
        panel, other = self.active_panel, self.passive_panel
        entries = self.selection(panel)
        if app is None or not entries:
            return
        here = Path(panel.path)
        request = await LinkDialog(
            entries=entries, here=here, other=Path(other.path), hidden=panel.show_hidden,
        ).execute(app)
        if request is None:
            return
        destination = filecopy.resolve_target(request.target, request.sources, here)
        linked: set[str] = set()
        try:
            if destination.create:
                if await self._ask_yes_no(
                    f"Would you like to create directory {escape_caption(str(destination.directory))}?"
                ) is not True:
                    return
                try:
                    destination.directory.mkdir(parents=True)
                except OSError as error:
                    await self._ask_skip(filecopy.error_message(error))
                    return
            for source in request.sources:
                try:
                    filelink.make_link(source, destination.path_for(source), request.relative)
                except OSError as error:
                    if not await self._ask_skip(filecopy.error_message(error)):
                        break
                    continue
                linked.add(source.name)
        finally:
            if linked:
                panel.marked = panel.marked - linked
            panel.reload()
            other.reload()

    async def on_view(self, event: View) -> bool:
        """F3: ``cmFileView``, the selected file in a viewer window."""
        self.spawn(self.view("text"))
        return True

    async def on_view_as_text(self, event: ViewAsText) -> bool:
        self.spawn(self.view("text"))
        return True

    async def on_view_as_hex(self, event: ViewAsHex) -> bool:
        self.spawn(self.view("hex"))
        return True

    async def view(self, mode: str) -> None:
        """Open the selected file in a viewer on this window's desktop.

        A directory is passed over: DN counted its size (``CountLen``), which
        is not written yet, and ``..`` has nothing to show.  A file that will
        not open is said so, as a directory that will not be made is.
        """
        from navigator.widgets.file_window import FileWindow

        panel = self.active_panel
        entry = panel.selected
        desktop = self.desktop
        if entry is None or entry.is_dir or desktop is None:
            return
        path = panel.path / entry.name
        try:
            window = FileWindow(path, mode=mode)
        except OSError as error:
            await Dialog(
                title="Cannot view file",
                prompt=f"{entry.name}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)
            return
        desktop.open(window)

    async def on_edit(self, event: Edit) -> bool:
        """F4: ``cmEditFile``, the selected file in an editor window."""
        self.spawn(self.edit())
        return True

    async def edit(self) -> None:
        """Open the selected file in an editor on this window's desktop.

        A directory and ``..`` are passed over, as DN's ``cmEditFile`` passed
        them; a file that will not open is said so.
        """
        from navigator.widgets.edit_window import EditWindow

        panel = self.active_panel
        entry = panel.selected
        desktop = self.desktop
        if entry is None or entry.is_dir or desktop is None:
            return
        path = panel.path / entry.name
        try:
            window = EditWindow(path)
        except OSError as error:
            await Dialog(
                title="Cannot edit file",
                prompt=f"{entry.name}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)
            return
        desktop.open(window)

    def _remember_panel(self) -> None:
        if self.right.focused:
            self._last_panel = self.right
        elif self.left.focused:
            self._last_panel = self.left

    @computed
    def active_panel(self) -> Panel:
        """Whichever panel has the keyboard, or had it last.

        **Last, not "the left one"**, while the focus is somewhere else --
        the console after Ctrl+O, a dialog.  DOS Navigator's active panel
        stayed active while its user screen was up, and a command typed then
        ran in *its* directory; answering "left" whenever neither panel held
        the keyboard sent the shell back to the left panel's directory the
        moment the console was shown.  While the tree stands in for one
        panel, the other is the active one whether or not it holds the
        keyboard: it is the one the tree steers.
        """
        replaced = self.replaced
        if replaced is not None:
            return self.right if replaced is self.left else self.left
        if self.right.focused:
            return self.right
        if self.left.focused:
            return self.left
        return self._last_panel or self.left

    @computed
    def passive_panel(self) -> Panel:
        """The panel that is not the active one, showing or not.

        While the tree or the quick view stands in for it, it is the panel
        they stand in for: its directory is still where DN's ``cmPushFirstName``
        would have pointed a copy.
        """
        return self.right if self.active_panel is self.left else self.left

    def list_name(self) -> str:
        """The active panel's directory: what the window list shows for this window.

        DOS Navigator's double window passed ``cmGetName`` on to its panel.
        A window in the background has lost the keyboard, so which panel was
        active is read off what it will get back, not off the focus.
        """
        app = self.application
        saved = self._saved_focus
        if (
            self.replaced is None
            and not (app is not None and self._holds(app.focused))
            and saved in (self.left, self.right)
        ):
            return str(saved.path)
        return str(self.active_panel.path)

    def switch_panel(self) -> None:
        """Move the keyboard to the other panel, or between panel and tree."""
        replacement = self.replacement
        if replacement is not None:
            if replacement.focus_within:
                self.active_panel.focus()
            else:
                self._focus_replacement()
            return
        self.passive_panel.focus()

    # -- the directory tree ----------------------------------------------------

    @computed
    def tree_replaces(self) -> Any:
        """The panel the directory tree stands in for, or None while there is none."""
        return self.replaced if self.replacement is self.tree else None

    def toggle_tree(self) -> None:
        """Ctrl+T: ``SwitchView(dtTree)``."""
        self.switch_view(self.tree)

    def toggle_quick_view(self) -> None:
        """Ctrl+Q: ``SwitchView(dtView)``, and the view loads the file under the cursor."""
        self.switch_view(self.quick)

    def switch_view(self, view: Any) -> None:
        """DOS Navigator's ``SwitchView``: *view* in the passive panel's place, or out of it.

        The **passive** panel gives way to *view*, in its place, and the
        keyboard stays with the active one.  Asking again for the view that is
        showing puts the panel back -- and gives it the keyboard if the view
        had it, as the original re-selected the panel it restored.  Asking for
        the *other* view swaps it in where the first one stood, and the
        keyboard goes back to the active panel, as ``SwitchView`` selected it.
        """
        current, replaced = self.replacement, self.replaced
        if current is view:
            had_keys = view.focus_within
            view.visible = False
            replaced.visible = True
            self.replacement = self.replaced = None
            if had_keys:
                replaced.focus()
            self.panels.invalidate()
            return
        active = self.active_panel
        had_keys = False
        if current is not None:
            had_keys = current.focus_within
            current.visible = False
            passive = replaced
        else:
            passive = self.passive_panel
        row = self.panels.children
        row.remove(view)
        row.insert(row.index(passive), view)
        if view is self.tree:
            view.set_show_hidden(active.show_hidden)
            view.show(active.path)
        passive.visible = False
        view.visible = True
        self.replaced, self.replacement = passive, view
        if had_keys:
            active.focus()
        if view is self.quick:
            self._quick_view_follows_panel()
        self.panels.invalidate()

    def _focus_replacement(self) -> None:
        (self.quick.viewer if self.replacement is self.quick else self.tree).focus()

    def _quick_view_follows_panel(self) -> None:
        """The quick view shows whatever the active panel's cursor is on: ``SendLocated``."""
        if self.replacement is not self.quick:
            return
        panel = self.active_panel
        entry, directory = panel.selected, panel.path
        path = None if entry is None or entry.is_dir else directory / entry.name
        with untracked():
            self.quick.show(path)

    def _tree_follows_panel(self) -> None:
        """The tree's cursor goes wherever the active panel goes: ``cmChangeTree``."""
        if self.tree_replaces is None:
            return
        path, hidden = self.active_panel.path, self.active_panel.show_hidden
        with untracked():
            self.tree.set_show_hidden(hidden)
            if self.tree.selected_path != Path(path).resolve():
                self.tree.show(path)

    def _panel_follows_tree(self) -> None:
        """A cursor at rest in a focused tree takes the panel with it.

        DOS Navigator's ``NeedLocated``: every move restarts the wait, and the
        panel moves only once the cursor has stayed put for ``LOCATE_DELAY``.
        """
        path, focused = self.tree.selected_path, self.tree.focused
        with untracked():
            if self._follow is not None:
                self._follow.cancel()
                self._follow = None
            app = self.application
            if (
                self.tree_replaces is None or not focused or path is None
                or app is None or not app.is_running
            ):
                return
            self._follow = self.spawn(self._follow_later(path))

    async def _follow_later(self, path: Path) -> None:
        await asyncio.sleep(self.LOCATE_DELAY)
        if self.tree.focused and self.tree.selected_path == path:
            self.active_panel.path = path
