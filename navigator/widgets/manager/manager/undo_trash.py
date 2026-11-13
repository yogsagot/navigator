"""File > Undo (navigator.lib.file_ops.undo) and the Trash (navigator.lib.drives.trash);
neither is DN's.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
import errno
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.commands import Undo
from navigator.widgets.manager.panel import Panel
from navigator.lib.drives import Location, drive_of
from navigator.lib.drives import trash as trash_drive
from navigator.lib.file_ops import undo as undo_history
from navigator.lib.file_ops.undo import UNDO
from navigator.lib.drives.location import shown

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class UndoTrash(_Base):
    """File > Undo (navigator.lib.file_ops.undo) and the Trash (navigator.lib.drives.trash);"""

    # -- File > Undo (not DN's: navigator.lib.file_ops.undo) ---------------------

    async def undo(self, panel: Panel) -> None:
        """File > Undo (Ctrl+Z): the newest operation in the session's history
        taken back, after a Yes, through the worker that did it.  What could
        not be taken back (skipped, stopped) goes back on the history, so
        Ctrl+Z can try it again."""
        app = self.application
        entry = UNDO.peek()
        if app is None or entry is None:
            return
        if not await Dialog(title=tr("Undo"), prompt=entry.question(), buttons="yes-no").execute(app):
            return
        if UNDO.peek() is not entry:
            return  # something else went on the history meanwhile
        UNDO.pop()
        left: Any = None
        # Where the first thing put back now is, set by the step that put it
        # back: the panel showing its directory lands on it, as F5/F6's do on
        # what they made.  Undoing a copy or a directory puts nothing back.
        self._undo_landing = None
        try:
            if isinstance(entry, undo_history.Renamed):
                left = await self._undo_renames(panel, entry)
            elif isinstance(entry, undo_history.Moved):
                left = await self._undo_move(panel, entry)
            elif isinstance(entry, undo_history.Copied):
                left = await self._undo_copy(entry)
            elif isinstance(entry, undo_history.Trashed):
                left = await self._undo_trash(panel, entry)
            elif isinstance(entry, undo_history.MadeDirectory):
                left = await self._undo_mkdir(panel, entry)
        finally:
            landing = self._undo_landing
            for side in (self.left, self.right):
                if side.application is not None:
                    there = (landing is not None and side.found is None
                             and Location.of(side.location) == landing.parent)
                    side.reload(key=landing.name if there else None)
        if left is not None:
            UNDO.push(left)
            return
        toast = getattr(getattr(app, "root", None), "toast", None)
        if toast is not None and app.is_running:
            toast(entry.undone(), title=tr("Undo"))

    async def _undo_renames(self, panel: Panel, entry: Any) -> Any:
        """The names put back (:meth:`_run_renames`); what was not, as an entry."""
        done = await self._run_renames(entry.undo_pairs())
        if done:
            place, _now, back_to = done[0]
            self._undo_landing = Location.of(place) / back_to
            await self._after_renames(panel, done)
        back = {(place, new) for place, new, _old in done}
        rest = tuple(pair for pair in entry.pairs if (pair[0], pair[2]) not in back)
        return undo_history.Renamed(rest) if rest else None

    async def _undo_move(self, panel: Panel, entry: Any) -> Any:
        """Each destination moved back to its source through the copier
        (:meth:`_run_copy`, its questions and box), a source's directory
        made again if the move emptied it away."""
        from navigator.lib.file_ops import filecopy

        pairs = entry.undo_pairs()
        parents = list(dict.fromkeys(source.parent for _dest, source in pairs))

        def missing() -> list[Any]:
            return [parent for parent in parents if not drive_of(parent).is_dir(parent)]

        request = filecopy.CopyRequest(
            sources=[shown(dest) for dest, _ in pairs],
            target=str(shown(parents[0])) if len(parents) == 1 else "",
            mode=filecopy.ASK, options=filecopy.PRESERVE | filecopy.MOVE,
            pairs=[(shown(dest), shown(source)) for dest, source in pairs],
            directories=[shown(parent) for parent in await asyncio.to_thread(missing)],
        )
        job_done: list[Any] = []
        await self._run_copy(panel, request, panel.location, move=True,
                             others=(self.passive_panel,), record=False, done_into=job_done)
        back = {Location.of(dest) for dest in job_done}
        self._undo_landing = next((Location.of(source) for dest, source in pairs if Location.of(dest) in back), None)
        rest = tuple(pair for pair in entry.pairs if pair[1] not in back)
        return undo_history.Moved(rest, entry.replaced) if rest else None

    async def _undo_copy(self, entry: Any) -> Any:
        """What the copy made removed -- only what is still as it left it
        (:func:`navigator.lib.file_ops.uncopy.check`, on a thread), the rest
        kept and said in one box -- through the eraser: to the Trash on the
        disk (its *erase instead?* question where there is none), for good
        elsewhere.  The Trash it goes to is not Undo's history again."""
        from navigator.lib.file_ops import fileerase, uncopy

        app = self.application
        same, changed = await asyncio.to_thread(uncopy.check, list(entry.pairs), drive_of)
        if changed:
            lines = [str(shown(location)) for location in changed[:8]]
            if len(changed) > 8:
                lines.append(tr_n("and {n} more", "and {n} more", len(changed) - 8))
            heading = tr_n("{n} entry changed since the copy, kept:",
                           "{n} entries changed since the copy, kept:", len(changed))
            await Dialog(title=tr("Undo"), prompt="\n".join([heading, *lines]), buttons="ok").execute(app)
        if not same:
            return None
        request = fileerase.EraseRequest(sources=[shown(location) for location in same], recursive=True,
                                         trash=entry.to_trash)
        gone = {Location.of(source) for source in await self._run_erase(request, record=False)}
        rest = tuple(pair for pair in entry.pairs if pair[0] in same and pair[0] not in gone)
        return undo_history.Copied(rest, entry.overwritten) if rest else None

    async def _undo_trash(self, panel: Panel, entry: Any) -> Any:
        """The items restored where each came from (``trash.restore_all``:
        never over anything, *Skip* or *Cancel* when the name is taken)."""
        from navigator.lib.file_ops import filecopy, trash
        from navigator.widgets.manager.find_progress import FindProgress

        job = trash.RestoreJob()

        def make_box() -> Any:
            box = FindProgress()
            box.title = tr("Restore")
            box.count_row.visible = False
            return box

        def refresh(box: Any) -> None:
            box.directory = f"{job.count}/{job.total}  {job.current}"

        async def answer(question: Any) -> Any:
            if isinstance(question, filecopy.Failure):
                return await self._ask_skip(question.message, elevate=question.elevate)
            return None

        running = asyncio.ensure_future(asyncio.to_thread(trash.restore_all, list(entry.items), job))
        try:
            await self._watch_job(running, job, make_box, refresh, answer)
            await running
        finally:
            if not running.done():
                job.stop()
            await self._release_if(job.as_root)
        back = {id(item) for item in job.done}
        first = next((item.original for item in job.done if item.original is not None), None)
        if first is not None:
            self._undo_landing = Location.of(first)
        rest = tuple(item for item in entry.items if id(item) not in back)
        return undo_history.Trashed(rest) if rest else None

    async def _undo_mkdir(self, panel: Panel, entry: Any) -> Any:
        """F7's directory removed -- only while it is empty: Undo erases
        nothing.  Refused permission on the disk, *As root* as F7 offers it."""
        from navigator.lib.system.elevate import ELEVATION, refused

        place = entry.location
        as_root = False

        def remove() -> None:
            if as_root:
                from navigator.lib.drives.root import ROOT_DRIVE

                drive = ROOT_DRIVE
            else:
                drive = drive_of(place)
            try:
                drive.rmdir(place)
                # The new ones above it, while each is empty still: one with
                # something in it now is left, and so is all above it.
                for each in entry.above:
                    try:
                        drive.rmdir(each)
                    except OSError:
                        break
                drive.finish()
            finally:
                if as_root:
                    ELEVATION.release()

        while True:
            try:
                await asyncio.to_thread(remove)
            except FileNotFoundError:
                return None  # gone already: nothing left to undo
            except OSError as error:
                if error.errno in (errno.ENOTEMPTY, errno.EEXIST):
                    message = tr("{name} is not empty any more").format(name=place.name)
                else:
                    message = tr("Cannot remove directory {name}: {error}").format(
                        name=place.name, error=error.strerror or error)
                    if (not as_root and place.is_local and refused(error)
                            and await asyncio.to_thread(ELEVATION.available)):
                        from navigator.widgets.file_ops.as_root import ask_as_root

                        if await ask_as_root(self.application, message):
                            as_root = True
                            continue
                        return entry
                await Dialog(title=tr("Error"), prompt=message, buttons="ok").execute(self.application)
                return None if error.errno in (errno.ENOTEMPTY, errno.EEXIST) else entry
            return None

    # -- the Trash (not DN's: navigator.lib.drives.trash) ------------------------

    async def open_trash(self, panel: Panel | None = None, *, focus: bool = True) -> None:
        """*panel* (the active one) on the Trash, and the keyboard with it unless not *focus*."""
        await self._go_to(panel or self.active_panel, str(trash_drive.location()), focus=focus)

    async def restore_trash(self, panel: Panel) -> None:
        """File > Restore from Trash: the selection put back where each came from.

        On a thread (:func:`navigator.lib.file_ops.trash.restore_all`), a box
        once it takes a moment; a name taken where one goes back asks *Skip*
        or *Cancel*.  What went back is untagged, and both panels look again:
        one showing where the first went back lands on it, as F5/F6's on what
        they made.
        """
        from navigator.lib.file_ops import filecopy, trash
        from navigator.widgets.manager.find_progress import FindProgress

        entries = self.selection(panel)
        names = [entry.name for entry in entries]
        found = await asyncio.to_thread(lambda: [trash_drive.TRASH.item(name) for name in names])
        chosen = [item for item in found if item is not None]
        if not chosen:
            return
        by_item = {id(item): trash_drive.location(name) for name, item in zip(names, found) if item is not None}
        job = trash.RestoreJob()

        def make_box() -> Any:
            box = FindProgress()
            box.title = tr("Restore")
            box.count_row.visible = False
            return box

        def refresh(box: Any) -> None:
            box.directory = f"{job.count}/{job.total}  {job.current}"

        async def answer(question: Any) -> Any:
            if isinstance(question, filecopy.Failure):
                return await self._ask_skip(question.message, elevate=question.elevate)
            return None

        running = asyncio.ensure_future(asyncio.to_thread(trash.restore_all, chosen, job))
        try:
            await self._watch_job(running, job, make_box, refresh, answer)
            await running
        finally:
            if not running.done():
                job.stop()
            await self._release_if(job.as_root)
            panel.untag_paths([by_item[id(item)] for item in job.done])
            first = next((Location.of(item.original) for item in job.done if item.original is not None), None)
            for side in (panel, self.right if panel is self.left else self.left):
                there = first is not None and side.found is None and Location.of(side.location) == first.parent
                side.reload(key=first.name if there else None)

    async def empty_trash(self) -> None:
        """Disk > Empty Trash: asked, then everything in it erased through the
        one eraser (:meth:`_run_erase`), its box and its questions."""
        from navigator.lib.file_ops import fileerase

        app = self.application
        if app is None:
            return
        names = await asyncio.to_thread(lambda: list(trash_drive.TRASH.items()))
        if not names:
            await Dialog(title=tr("Empty Trash"), prompt=tr("The Trash is empty"), buttons="ok").execute(app)
            return
        prompt = tr_n("Do you wish to empty the Trash?\n{n} item will be erased for good.",
                      "Do you wish to empty the Trash?\n{n} items will be erased for good.", len(names))
        if await Dialog(title=tr("Empty Trash"), prompt=prompt, buttons="yes-no").execute(app) is not True:
            return
        try:
            await self._run_erase(fileerase.EraseRequest(
                [trash_drive.location(name) for name in names], recursive=True))
        finally:
            self.left.reload()
            self.right.reload()
