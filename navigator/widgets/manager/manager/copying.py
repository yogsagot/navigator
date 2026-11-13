"""Copying and moving: F5/F6, the clipboard, dragging and dropping, Print, and watching a job.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from navkit import glyphs as glyphs_module
from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.commands import Copy, Delete
from navigator.widgets.manager.panel import Panel
from navigator.widgets.manager.panel.drag import Dropped, label_for
from navigator.widgets.tree.directory_tree.directory_tree import reread_trees
from navigator.lib.drives import DriveGone, Location
from navigator.lib.file_ops.clip import CLIP
from navigator.lib.file_ops import undo as undo_history
from navigator.lib.file_ops.undo import UNDO
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager.helpers import (
    _entry_location,
    _into_itself,
    _real_place,
    _rename_found,
    job_subject,
    relative_to,
    source_base,
)

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Copying(_Base):
    """Copying and moving: F5/F6, the clipboard, dragging and dropping, Print, and watching a job."""

    async def print_files(self) -> None:
        """The selection's files to the printer, untagged as each is queued.

        Directories are passed over, and a selection of nothing else prints
        nothing.  The question is DN's *Print file NAME?* or *Print N files?*,
        N counting what was selected, directories included, as DN's did.  The
        spooler (:mod:`navigator.lib.system.printing`) stands for DN's print manager; one
        that refuses stops the run and says why.
        """
        from navigator.lib.system.printing import spool_file

        panel = self.active_panel
        entries = self.selection(panel)
        files = [entry for entry in entries if not entry.is_dir]
        if not files:
            return
        if len(entries) == 1:
            prompt = tr("Print file {name}?").format(name=entries[0].name)
        else:
            prompt = tr_n("Print {n} file?", "Print {n} files?", len(entries))
        answer = await Dialog(
            title=tr("Confirm"), prompt=prompt, buttons="yes-no",
        ).execute(self.application)
        if answer is not True:
            return
        loop = asyncio.get_running_loop()
        elsewhere = not panel.location.is_local and panel.found is None
        for entry in files:
            if elsewhere:
                # A file on another drive is printed from a copy: ``lp`` spools
                # what it is given at once, so the copy goes after.
                from navigator.lib.drives import usefile
                from navigator.widgets.drives.use_file import materialize

                origin = panel.entry_location(entry)
                use = await materialize(self.application, [origin])
                if use is None:
                    return
                try:
                    problem = await loop.run_in_executor(None, spool_file, use.local_for(origin))
                finally:
                    await asyncio.to_thread(usefile.discard, use)
            else:
                problem = await loop.run_in_executor(None, spool_file, entry.path_in(panel.path))
            if problem is not None:
                await Dialog(
                    title=tr("Error"), prompt=tr("Cannot print {name}: {reason}").format(name=entry.name, reason=problem),
                    buttons="ok",
                ).execute(self.application)
                return
            # ``cmCopyUnselect``: what has gone to the printer is untagged.
            panel.untag([entry])

    async def tree_copy(self, *, move: bool) -> None:
        """F5/F6 in the Ctrl+T tree: ``TTreePanel.CopyDir``, the directory under
        its cursor copied (or moved), the Copy box offering the active panel's
        directory -- the other side; then the tree and the panels look again."""
        found = await asyncio.to_thread(self._tree_entry)
        if found is None:
            return
        here, entry = found
        panel = self.active_panel
        try:
            target = shown(panel.location) if panel.drive.can("write") else None
        except DriveGone:
            target = None
        others = tuple(other for other in self.all_panels if other is not panel)
        await self.copy_entries(panel, [entry], target, move=move, others=others, here=here)
        self.reread_info()  # the trees re-read in ``_run_copy``

    async def copy_files(self, *, move: bool) -> None:
        """Ask where, copy on a thread, and let both panels look again.

        ``make_directory``'s shape with a worker in the middle: the copy runs
        through ``asyncio.to_thread`` so the loop keeps painting, and
        :meth:`_watch_copy` stands between the two -- the progress box once
        the copy has taken a moment, and every question the worker puts, one
        at a time.  What was copied in full is untagged once the copy ends --
        after Stop too -- where DN deselected each as it finished (a departure,
        ``filecopy.run``); what was skipped keeps its tag.
        """
        panel, other = self.active_panel, self.passive_panel
        entries = self.selection(panel)
        if entries:
            # ``cmPushFirstName``: the other panel's place -- unless nothing can
            # be written there, or it is a *Find:* listing, when the line is empty.
            target = self._push_first_name(other)
            await self.copy_entries(panel, entries, target, move=move, others=(other,))

    def clip_files(self, *, move: bool) -> None:
        """The selection's paths on the clipboard, one a line, and the entries
        in :data:`~navigator.lib.file_ops.clip.CLIP`.  Tags stay: the clip is
        marked beside them, and a paste is not an operation on this panel."""
        panel = self.active_panel
        entries = self.selection(panel)
        if not entries:
            return
        locations = [panel.entry_location(entry) for entry in entries]
        text = CLIP.set(panel.location, entries, locations, move=move)
        if self.application is not None:
            self.application.copy_to_clipboard(text)

    async def paste_files(self) -> None:
        """F5's or F6's dialog on the clipped entries, into the active panel.

        The dialog's sources are where the entries were clipped, wherever the
        panel that listed them has gone since.  A directory is never pasted
        into itself; a move pasted is done, and forgotten, while a copy can be
        pasted again.  Never into a *Find:* listing (refused: DN's
        ``CopyFilesInto`` did nothing).
        """
        if not CLIP:
            return
        target = await asyncio.to_thread(_real_place, self.active_panel.location)
        entries, here, move = list(CLIP.entries), CLIP.here, CLIP.move
        if (itself := _into_itself(target, entries, here)) is not None:
            await self._say_into_itself(itself)
            return
        if move and target == here:
            return
        source = next(
            (panel for panel in self.all_panels if panel.location == here), self.active_panel
        )
        others = tuple(panel for panel in self.all_panels if panel is not source)
        done = await self.copy_entries(source, entries, shown(target), move=move, others=others, here=here)
        if done and move:
            CLIP.clear()

    async def on_dropped(self, event: Dropped) -> bool:
        """Files dropped from one of this window's panels: ``CM_Dropped`` -- or
        on the trash can, which erases them.

        What to do with them is asked in a menu at the drop
        (:meth:`_drop_menu`); a directory is never dropped into itself.
        """
        source = event.source
        if source not in self.all_panels:
            return False
        if event.trash:
            self.spawn(self._drop_on_trash(source, list(event.entries)))
            return True
        self.spawn(self._dropped(event, source))
        return True

    async def _dropped(self, event: Dropped, source: Panel) -> None:
        """The rest of :meth:`on_dropped`, in a task: where it was dropped is
        resolved on a thread (a hung mount waits there, not on the loop)."""
        target = await asyncio.to_thread(_real_place, Location.of(event.target))
        if (itself := _into_itself(target, event.entries, source.location)) is not None:
            await self._say_into_itself(itself)
            return
        target = shown(target)
        others = (event.panel,) if event.panel is not None and event.panel is not source else ()
        await self._drop_menu(event, target, others)

    async def _say_into_itself(self, entry: Any) -> None:
        """DN's ``erIntoItself``: a directory pasted or dropped into itself, said
        in an error box, and nothing copied."""
        from navml.widgets.dialog.control import escape_caption

        if self.application is not None:
            await Dialog(title=tr("Error"), buttons="ok", prompt=tr("Cannot copy directory {name} into itself").format(
                name=escape_caption(entry.name))).execute(self.application)

    async def _drop_on_trash(self, source: Panel, entries: list[Any]) -> None:
        """``TTrashCan``: ``cmEraseGroup`` once a Yes/No box agrees.

        A departure: DN erased at once with every confirmation off.  The box
        stands in for F8's Delete dialog; past it the non-empty and read-only
        questions are answered Yes, as ``Confirms := 0`` did, unless
        Confirmations' *Drag and drop* is ticked.
        """
        from navml.widgets.dialog.control import escape_caption

        if self._trashes(source, entries):
            if len(entries) == 1:
                prompt = tr("Do you wish to move {name} to the Trash?").format(name=escape_caption(entries[0].name))
            else:
                prompt = tr_n("Do you wish to move {n} file to the Trash?",
                              "Do you wish to move {n} files to the Trash?", len(entries))
        elif len(entries) == 1:
            prompt = tr("Do you wish to delete {name}?").format(name=escape_caption(entries[0].name))
        else:
            prompt = tr_n("Do you wish to delete {n} file?", "Do you wish to delete {n} files?", len(entries))
        if await self._ask_yes_no(prompt, tr("Delete")) is not True:
            return
        await self.erase_entries(source, entries, quiet=not SETTINGS.confirmations.drag_and_drop, dialog=False)

    async def _drop_menu(self, event: Dropped, target: Any, others: tuple[Any, ...]) -> None:
        """Copy, move or link what was dropped, as chosen from a menu at the drop.

        A departure: ``CM_Dropped`` copied at once, or moved with Shift held;
        here Shift opens the menu on *Move*.  Then into *target* at once,
        unless Confirmations' *Drag and drop* asks first (``cfMouseConfirm``),
        when the Copy or Create symlink dialog comes up with it filled in.
        """
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        app = self.application
        if app is None:
            return
        menu = SubMenu()
        copy = menu.add_item(tr("~C~opy here"))
        move = menu.add_item(tr("~M~ove here"))
        link = menu.add_item(tr("~S~ymlink here"))
        relative = menu.add_item(tr("~R~elative symlink here"))
        menu.add_line()
        menu.add_item(tr("Cancel"), key="Esc")
        title = label_for(list(event.entries))
        from navigator.lib.system.title import tilde

        # Where they go, in the bottom frame, home as ``~``: the path's start
        # gives way to keep the box on the screen.
        where = tr("To {path}")
        room = max(8, (app.root.width if app.root is not None else 80) - 10 - len(where.format(path="")))
        path = tilde(target) if isinstance(target, Path) else str(target)
        if len(path) > room:
            marker = glyphs_module.ellipsis(self.glyphs)
            path = marker + path[-(room - len(marker)):]
        chosen = await PopupMenu(menu, event.x, event.y, current=1 if event.move else 0, behind=self,
                                 title=title, footer=where.format(path=path)).execute(app)
        source, entries = event.source, list(event.entries)
        ask = SETTINGS.confirmations.drag_and_drop
        if chosen is copy or chosen is move:
            await self.copy_entries(source, entries, target, move=chosen is move, others=others, ask=ask)
        elif chosen is link or chosen is relative:
            await self.link_entries(source, entries, target, relative=chosen is relative,
                                    others=others, ask=ask)

    async def copy_entries(self, panel: Panel, entries: list[Any], target: Any, *, move: bool,
                           others: tuple[Any, ...] = (), ask: bool = True, here: Any = None) -> bool:
        """*entries* of *panel* copied (or moved) to *target*: the Copy dialog
        first when *ask*, else at once in the dialog's session mode and
        options; then *panel* and *others* look again.  *here* is where the
        entries are listed, *panel*'s directory unless said.  Whether the
        copy ran, and was not stopped."""
        from navigator.lib.file_ops import filecopy
        from navigator.widgets.file_ops.copy_dialog import CopyDialog
        from navigator.widgets.file_ops.copy_dialog import copy_dialog

        app = self.application
        if app is None or not entries:
            return False
        if here is None:
            here = panel.location
        if ask:
            request = await CopyDialog(
                entries=entries, here=here, other=target,
                hidden=panel.show_hidden, move=move,
            ).execute(app)
        else:
            session = copy_dialog._session
            options = session["options"] & ~filecopy.MOVE
            request = filecopy.CopyRequest(
                sources=[shown(_entry_location(here, entry)) for entry in entries],
                target=str(target).rstrip("/") + "/",
                mode=session["mode"],
                options=options | filecopy.MOVE if move else options,
                flush=SETTINGS.system.flush_buffers,
            )
        if request is None:
            return False
        # DN's ``cpoFromTemp``: a move to a bare mask renames each found file
        # where it is (``filecopy.in_place_name``).
        request.from_listing = panel.found is not None and here == panel.location
        return await self._run_copy(panel, request, here, move=move, others=others)

    async def _run_copy(self, panel: Panel, request: Any, here: Any, *, move: bool,
                        others: tuple[Any, ...] = (), record: bool = True,
                        done_into: list[Any] | None = None) -> bool:
        """*request* run on a thread under the copy's box and questions; then
        what went is untagged in *panel*, and it and *others* look again.

        A copy or a move off and onto anything but an archive goes on File >
        Undo's history, unless *record* is false (Undo's own); *done_into* is
        given the sources done in full."""
        from navigator.lib.file_ops import filecopy

        app = self.application
        job = filecopy.CopyJob()
        work = asyncio.ensure_future(asyncio.to_thread(filecopy.run, request, job, here))
        try:
            await self._watch_copy(work, job, move, subject=job_subject(
                "move" if move else "copy", request.sources, request.target),
                base=source_base(request.sources))
            done = await work
        finally:
            if not work.done():
                # Cancelled -- Navigator is going -- so the thread is told to
                # stop rather than left copying, or asking, behind it.
                job.stop()
            elif record and request.archive is None and request.pairs is None and all(
                    Location.of(source).outer is None for source in request.sources):
                if move and job.moved and all(dest.outer is None for _source, dest in job.moved):
                    UNDO.push(undo_history.Moved(tuple(job.moved), job.replaced))
                elif not move and job.copied and all(dest.outer is None for dest, _fp in job.copied):
                    UNDO.push(undo_history.Copied(tuple(job.copied), job.overwritten))
        if done_into is not None:
            done_into.extend(done)
        # The window may have closed while the copy was in the background.
        # A panel showing where the first source went lands on it there --
        # or, packed into an archive (Shift+F1), on the archive.
        first = job.first_target

        def key_in(each: Panel) -> str | None:
            if each.found is not None:
                return None
            shows = Location.of(each.location)
            landed = first
            while landed is not None:
                if landed.parent == shows:
                    return landed.name
                landed = landed.outer
            return None

        if panel.application is not None:
            panel.untag_paths(done)
            if move and panel.found is not None and job.moved:
                _rename_found(panel.found, job.moved)
            panel.reload(key=key_in(panel))
        for other in others:
            if other.application is not None:
                other.reload(key=key_in(other))
        # DN's ``cmRereadTree`` for the drives the copy touched (``FILECOPY.PAS:2416``).
        reread_trees(app)
        if job.attributes_lost_count:
            # *Preserve attributes* kept what it could: the rest said once, as
            # ``cp -p`` warns -- a FAT stick or a server keeps no owner or mode.
            from navml.widgets.dialog.control import escape_caption

            toast = getattr(getattr(app, "root", None), "toast", None)
            if toast is not None and app.is_running:
                path, reason = job.attributes_lost[0]
                toast(tr_n("Times, permissions or owner were not kept on {n} file: {path}: {reason}",
                           "Times, permissions or owner were not kept on {n} files, first {path}: {reason}",
                           job.attributes_lost_count, path=escape_caption(path), reason=escape_caption(reason)),
                      title=tr("Move") if move else tr("Copy"))
        if SETTINGS.file_manager.beep_after_copy and not job.stopped and app is not None:
            # ``BeepAfterCopy``, after a copy that was not aborted.
            app.bell()
        return not job.stopped

    async def _watch_copy(self, work: asyncio.Future[Any], job: Any, move: bool, *,
                          subject: str = "", base: str = "") -> None:
        """The copy's progress box, *Stop*, and the worker's questions, until *work* ends."""
        from navigator.lib.system.progress import Rate
        from navigator.widgets.file_ops.copy_progress import CopyProgress

        rate = Rate()
        loop = asyncio.get_running_loop()
        packing = False

        def refresh(box: Any) -> None:
            nonlocal rate, packing
            if job.packing != packing:
                # The packing counts again from nought: the speed with it.
                packing, rate = job.packing, Rate()
            box.packing = job.packing
            box.measuring, box.note = job.measuring, job.note
            box.source, box.dest = job.source, job.dest
            box.file_done, box.file_bytes = job.file_done, job.file_bytes
            box.done, box.total = job.done_bytes, job.total_bytes
            rate.add(loop.time(), job.done_bytes)
            speed = rate.speed()
            left = rate.left(job.total_bytes) if job.total_bytes else None
            box.speed = -1.0 if speed is None else speed
            box.left = -1.0 if left is None else left

        def far() -> tuple[int, int, str]:
            return job.done_bytes, job.total_bytes, relative_to(job.source, base)

        await self._watch_job(
            work, job, lambda: CopyProgress(move=move), refresh, self._answer_copy_question,
            background=far, title=tr("Rename/move") if move else tr("Copy"), subject=subject,
        )

    async def _watch_job(
        self,
        work: asyncio.Future[Any],
        job: Any,
        make_box: Callable[[], Any],
        refresh: Callable[[Any], None],
        answer: Callable[[Any], Awaitable[Any]],
        abort: str | None = None,
        *,
        background: Callable[[], tuple[int, int, str]] | None = None,
        title: str = "",
        subject: str = "",
    ) -> None:
        """A worker's progress box, its one button, and its questions, until *work* ends.

        The box is *make_box*'s, put up once the work has taken
        ``PROGRESS_DELAY``, and *refresh* copies *job*'s fields into it every
        tick.  Each question the worker puts goes to *answer*, one at a time.
        The box closing -- its button, or Esc -- holds the worker and asks
        ``dlQueryAbort`` before anything stops.

        With *background* -- the job's done, total and current file, for the
        menu bar's mark and its tooltip, which names the work by *subject* -- the box has *Background* too (a departure; DN's boxes held
        the screen).  Pressed, the box comes down and the work goes on,
        registered in ``BACKGROUND`` under *title*: a question then waits,
        the mark showing it, until the box is called back
        (``BACKGROUND.recall``), which puts it up again.  An end while away --
        not one in the box, called back or never sent -- is said in a toast,
        *title* over *Finished* or *Stopped*.

        A departure too: once the box has been up, the end -- and a question
        the worker waits on -- is also said in a desktop notification, but
        only while the terminal has reported it is in the background
        (``Shell.notify_away``, ``[system] notifications``).
        """
        from navigator.lib.system.background import BACKGROUND, Running
        from navigator.lib.system.progress import PROGRESS_DELAY, PROGRESS_TICK
        from navigator.widgets.file_ops.background_button import BACKGROUND as AWAY

        app = self.application
        loop = asyncio.get_running_loop()
        started = loop.time()
        box: Any = None
        shown: asyncio.Future[Any] | None = None
        #: Registered while in the background, and the wait for its recall.
        away: Running | None = None
        recall: asyncio.Future[Any] | None = None
        #: A question taken from the worker while away, put once the box is back.
        held: Any = None
        seen = False
        #: What the notifications name it by: *title*, else its box's title.
        named = title
        #: The question last notified, so one is told of once.
        told: Any = None

        def notify(text: str) -> None:
            # The application's root is the shell, which knows the focus.
            notify_away = getattr(getattr(app, "root", None), "notify_away", None)
            if notify_away is not None and app.is_running:
                notify_away(named or tr("Navigator"), text)

        async def tick() -> None:
            # Through the queue, so each update is painted with its batch.
            if box is not None:
                refresh(box)
            elif away is not None and background is not None:
                away.done, away.total, away.current = background()

        def show() -> None:
            nonlocal box, shown, seen, named
            box = make_box()
            named = named or getattr(box, "title", "") or ""
            if background is not None:
                box.background = True
            refresh(box)
            shown = asyncio.ensure_future(box.execute(app))
            seen = True

        repeat = app.call_every(PROGRESS_TICK, tick)
        try:
            while not work.done():
                waiting: set[asyncio.Future[Any]] = {work}
                if shown is not None:
                    waiting.add(shown)
                if recall is not None:
                    waiting.add(recall)
                await asyncio.wait(waiting, timeout=PROGRESS_TICK, return_when=asyncio.FIRST_COMPLETED)
                pending = held if held is not None else job.take_question()
                if pending is not None and pending is not told and seen:
                    told = pending
                    what = subject or named
                    notify(tr("Waiting for an answer: {what}").format(what=what) if what
                           else tr("Waiting for an answer"))
                if pending is not None and away is not None:
                    # Away, a question waits for the box to come back.
                    held = pending
                    away.asking = True
                elif pending is not None:
                    held = None
                    question, future = pending
                    result = None
                    try:
                        if self.application is not None:
                            # A window closed while its work was away has
                            # no one to ask: the question is Esc'd.
                            result = await answer(question)
                    finally:
                        future.set_result(result)
                    continue
                if away is not None:
                    if recall is not None and recall.done():
                        BACKGROUND.remove(away)
                        away, recall = None, None
                        show()
                    continue
                if shown is not None and shown.done():
                    if not shown.cancelled() and shown.result() is AWAY:
                        box, shown = None, None
                        away = BACKGROUND.add(job, title, subject)
                        if background is not None:
                            away.done, away.total, away.current = background()
                        recall = asyncio.ensure_future(away.recalled.wait())
                        continue
                    # *Stop*, or Esc: ``dlQueryAbort`` before anything stops.
                    box, shown = None, None
                    job.pause()
                    try:
                        if await self._ask_yes_no(abort or tr("Abort operation?")) is True:
                            job.stop()
                    finally:
                        job.resume()
                    continue
                if work.done():
                    break
                if shown is None and not job.stopped and loop.time() - started >= PROGRESS_DELAY:
                    show()
        finally:
            repeat.cancel()
            if away is not None:
                BACKGROUND.remove(away)
            if recall is not None and not recall.done():
                recall.cancel()
            if held is not None and not held[1].done():
                # The work ended -- or this watcher was cancelled -- with a
                # question unasked: answered as Esc would, so no worker waits.
                held[1].set_result(None)
            if shown is not None and not shown.done():
                # Cancelled rather than closed: a box whose ``execute`` has
                # not started yet has nothing to close, and would mount and
                # wait for ever the moment it did.  ``execute``'s own
                # ``finally`` takes it down.  Waited for, not awaited, so a
                # cancellation of this task is not swallowed with its own.
                shown.cancel()
                await asyncio.wait({shown})
        if seen and work.done() and not work.cancelled():
            from navigator.lib.system.job import Stopped

            error = work.exception()
            what = subject or named
            if error is None and not job.stopped:
                notify(tr("Finished: {what}").format(what=what) if what else tr("Finished"))
            elif error is None or isinstance(error, Stopped):
                notify(tr("Stopped: {what}").format(what=what) if what else tr("Stopped"))
            else:
                notify(tr("Failed: {what}").format(what=what) if what else tr("Failed"))
        if away is not None and work.done() and not work.cancelled() and work.exception() is None:
            # Only an end that happened in the background: one in its box was
            # seen there.  The application's root is the shell, which places toasts.
            toast = getattr(getattr(app, "root", None), "toast", None)
            if toast is not None and app.is_running:
                toast(tr("Stopped") if job.stopped else tr("Finished"), title=title)

    async def _ask_yes_no(self, prompt: str, title: str | None = None) -> Any:
        return await Dialog(title=title or tr("Confirm"), prompt=prompt, buttons="yes-no").execute(self.application)

    async def _answer_copy_question(self, question: Any) -> Any:
        """Put one of the worker's questions to the user, and answer as it expects."""
        from navml.widgets.dialog.control import escape_caption

        from navigator.lib.file_ops import filecopy
        from navigator.widgets.file_ops.overwrite_query import OverwriteQuery

        app = self.application
        if isinstance(question, filecopy.Overwrite):
            return await OverwriteQuery(question=question).execute(app)
        if isinstance(question, filecopy.CreateDirectory):
            # DN's ``dlQueryCreateDir``, asked only with *Create non-existing
            # dir* ticked in Confirmations (``cfCreateSubdir``).
            if not SETTINGS.confirmations.create_dir:
                return True
            return await self._ask_yes_no(
                tr("Would you like to create directory {path}?").format(path=escape_caption(str(question.path)))
            ) is True
        if isinstance(question, filecopy.NoRoom):
            # DN's ``erNotDiskSpace1`` (``mfError``), the mount point for its
            # drive letter: Yes goes on without this file.
            return await self._ask_yes_no(
                tr("There is not enough room\non {drive} to copy\nfile {name}. Copy other files?").format(
                    drive=escape_caption(question.drive), name=escape_caption(question.dest.name)),
                title=tr("Error"),
            ) is True
        if isinstance(question, filecopy.Failure):
            return await self._ask_skip(question.message, elevate=question.elevate)
        return None

    async def _ask_skip(self, message: str, *, elevate: bool = False) -> Any:
        """An error with *Skip* and *Cancel*: True to go on without this file.
        With *elevate*, *As root* too (:func:`navigator.widgets.file_ops.as_root.ask_skip`)."""
        from navigator.widgets.file_ops.as_root import ask_skip

        return await ask_skip(self.application, message, elevate=elevate)
