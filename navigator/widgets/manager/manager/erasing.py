"""Deleting (F8/Del), into the Trash or for good.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr, tr_n

from navigator.widgets.manager.commands import Delete
from navigator.widgets.manager.panel import Panel
from navigator.widgets.tree.directory_tree.directory_tree import reread_trees
from navigator.lib.drives import Location
from navigator.lib.file_ops import undo as undo_history
from navigator.lib.file_ops.undo import UNDO
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager.helpers import action_caption, job_subject, relative_to, source_base

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Erasing(_Base):
    """Deleting (F8/Del), into the Trash or for good."""

    # -- deleting ----------------------------------------------------------------

    async def tree_erase(self) -> None:
        """F8/Del in the Ctrl+T tree: ``EraseDir``, the directory under its
        cursor erased as F8 erases (the Delete box, the Trash, the questions);
        then the tree and the panels look again."""
        found = await asyncio.to_thread(self._tree_entry)
        if found is None:
            return
        here, entry = found
        await self.erase_located(here, [entry])  # every tree re-read there
        for panel in self.all_panels:
            panel.reload()
        self.reread_info()

    async def delete_files(self, *, single: bool) -> None:
        """Ask, delete on a thread, and let both panels look again.

        ``copy_files``'s shape: the Delete dialog, then ``fileerase.run``
        through ``asyncio.to_thread`` with :meth:`_watch_job` between the two
        -- the *Erase* box, and the worker's *not empty*, *read-only* and
        failure questions.  What went is untagged; what was kept keeps its tag.
        """
        panel = self.active_panel
        if single:
            entry = panel.selected
            entries = [] if entry is None or entry.name == ".." else [entry]
        else:
            entries = self.selection(panel)
        await self.erase_entries(panel, entries)

    async def erase_entries(self, panel: Panel, entries: list[Any], *, quiet: bool = False,
                            dialog: bool = True) -> None:
        """*entries* of *panel* erased, as F8 erases them -- or, *quiet*, as
        the trash can did with ``Confirms := 0``: no dialog, and Yes to the
        questions on the way.  Without *dialog* the Delete dialog is left
        out, the caller having asked already."""
        other = self.right if panel is self.left else self.left
        if self.application is None or not entries:
            return
        done: list[Path] = []
        try:
            done = await self.erase_located(panel.location, entries, quiet=quiet, dialog=dialog)
        finally:
            # The window may have closed while the erase was in the background.
            if panel.application is not None:
                panel.untag_paths(done)
                panel.reload()
            if other.application is not None:
                other.reload()

    async def erase_located(self, here: Location, entries: list[Any], *, quiet: bool = False,
                            dialog: bool = True) -> list[Any]:
        """*entries*, named in the directory *here*, erased as F8 erases them
        -- the dialog, the Trash, the questions; what went in full.  What
        :meth:`erase_entries` does for a panel, for a window that lists files
        without being one (Disk > Directory sizes), which reads the panels
        again itself."""
        from navigator.lib.file_ops import fileerase
        from navigator.widgets.file_ops.delete_dialog import DeleteDialog

        app = self.application
        if app is None or not entries:
            return []
        # DN's ``ValidErase``: *Erase single file* (``cfSingleErase``)
        # unticked, one entry goes with no dialog, and so no *Recursive
        # delete* either -- a non-empty directory is then asked about below,
        # if that is ticked.  Several are always asked about; *Erase multiple
        # files* (``cfMultiErase``) adds DN's second box, ``OK to delete N
        # files ?``, after the dialog's Yes.
        confirms = SETTINGS.confirmations
        trash = SETTINGS.file_manager.use_trash and all(
            Location.of(entry.path_in(here)).is_local for entry in entries)
        several = len(entries) > 1
        if dialog and not quiet and (several or confirms.erase_single):
            request = await DeleteDialog(entries=entries, here=here, trash=trash).execute(app)
            if request is not None and several and confirms.erase_multiple:
                n = len(entries)
                if getattr(request, "trash", False):
                    prompt = tr_n("OK to move {n} file to the Trash?", "OK to move {n} files to the Trash?", n)
                else:
                    prompt = tr_n("OK to delete {n} file?", "OK to delete {n} files?", n)
                if await self._ask_yes_no(prompt, tr("Delete")) is not True:
                    return []
        else:
            request = fileerase.EraseRequest(
                sources=[shown(entry.path_in(here)) for entry in entries], trash=trash,
            )
        if request is None:
            return []
        try:
            return await self._run_erase(request, quiet=quiet)
        finally:
            reread_trees(app)  # DN's ``cmRereadTree`` (``ERASER.PAS:485``)

    @staticmethod
    def _trashes(panel: Panel, entries: list[Any]) -> bool:
        """Whether erasing *entries* moves them to the Trash: File Manager
        Setup's *F8 moves to Trash* (not DN's), and only what is on the disk."""
        return SETTINGS.file_manager.use_trash and all(panel.entry_location(entry).is_local for entry in entries)

    async def _run_erase(self, request: Any, *, quiet: bool = False, record: bool = True) -> list[Any]:
        """*request* run on a thread under *Deleting* and the eraser's
        questions; what went in full.  Cancelled, the worker is told to stop."""
        from navigator.lib.file_ops import fileerase
        from navigator.lib.system.progress import Rate
        from navigator.widgets.file_ops.delete_progress import DeleteProgress

        job = fileerase.EraseJob()
        base = source_base(request.sources)
        work = asyncio.ensure_future(asyncio.to_thread(fileerase.run, request, job))
        rate = Rate()
        loop = asyncio.get_running_loop()

        def refresh(box: Any) -> None:
            box.action, box.path = action_caption(job.action), job.path
            box.done, box.total = job.done, job.total
            rate.add(loop.time(), job.done)
            speed = rate.speed()
            left = None if job.measuring or not job.total else rate.left(job.total)
            box.speed = -1.0 if speed is None else speed
            box.left = -1.0 if left is None else left

        try:
            await self._watch_job(work, job, DeleteProgress, refresh,
                                  lambda question: self._answer_erase_question(question, quiet=quiet),
                                  background=lambda: (job.done, max(1, job.total), relative_to(job.path, base)),
                                  title=tr("Erase"), subject=job_subject("erase", request.sources))
            return await work
        finally:
            if not work.done():
                job.stop()
            elif record and getattr(request, "trash", False) and job.trashed:
                UNDO.push(undo_history.Trashed(tuple(job.trashed)))

    async def _answer_erase_question(self, question: Any, *, quiet: bool = False) -> Any:
        """Put one of the eraser's questions to the user, and answer as it expects."""
        from navigator.lib.file_ops import fileerase, filecopy
        from navigator.widgets.file_ops.erase_query import EraseQuery

        if quiet and isinstance(question, (fileerase.NotEmpty, fileerase.ReadOnly)):
            return fileerase.YES
        if isinstance(question, fileerase.NoTrash):
            # Asked even when quiet: Yes loses what was meant for the Trash.
            return await EraseQuery(question=question).execute(self.application)

        # *Erase non-empty sub-dir* and *Erase read-only files* in
        # Confirmations (``cfEraseSubdir``, ``cfEraseReadonly``): unticked,
        # the answer is Yes without asking.
        confirms = SETTINGS.confirmations
        if isinstance(question, fileerase.NotEmpty) and not confirms.erase_non_empty_dir:
            return fileerase.YES
        if isinstance(question, fileerase.ReadOnly) and not confirms.erase_read_only:
            return fileerase.YES
        if isinstance(question, (fileerase.NotEmpty, fileerase.ReadOnly)):
            return await EraseQuery(question=question).execute(self.application)
        if isinstance(question, filecopy.Failure):
            return await self._ask_skip(question.message, elevate=question.elevate)
        return None
