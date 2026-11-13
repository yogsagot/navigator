"""Renaming in place: Fast rename, Quick rename, Multi-rename.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
import errno
import os
from typing import TYPE_CHECKING, Any, Sequence

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.panel import Panel
from navigator.lib.drives import Location, drive_of
from navigator.lib.file_ops import undo as undo_history
from navigator.lib.file_ops.undo import UNDO

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Renaming(_Base):
    """Renaming in place: Fast rename, Quick rename, Multi-rename."""

    async def fast_rename(self, panel: Panel) -> None:
        """Alt+F6: ``cmFastRename`` -> ``CM_RenameSingle``, the name edited in place.

        :class:`~navigator.widgets.manager.fast_rename.FastRenameLine` over the
        name at the cursor -- never ``..`` -- and the file renamed when it ends
        with another name; a name already taken is refused, as DOS's rename
        refused it where POSIX's would replace it.  The cursor stays on the
        file under its new name, a tag goes with it, and Up or Down ending
        the line is then the panel's (``PutEvent``) -- when the name changed:
        an unchanged one is DN's ``cmCancel``, its key dropped.
        """
        from navigator.widgets.manager.fast_rename import FastRenameLine

        app = self.application
        entry, cell = panel.selected, panel.name_cell()
        if app is None or entry is None or entry.name == ".." or cell is None:
            return
        ox, oy = panel.offset()
        x, y, width = cell
        old = entry.name
        new, key = await FastRenameLine(old, ox + panel.x + x, oy + panel.y + y, width).execute(app)
        if not new or new == old:
            # DN's ``cmCancel`` (Esc, or the name as it was): nothing renamed,
            # and the key that ended the line is not the panel's.
            return
        await self._rename_entry(panel, entry, new)
        if key is not None:
            # Posted after the rename was tried, gone or not, as DN's ``PutEvent``.
            app.post_event(key)

    def _rename_candidate(self, panel: Panel) -> Any:
        """The one entry Quick rename would rename: the one tagged, else the
        one at the cursor -- None for ``..``, nothing, or more than one."""
        if panel.marked:
            marked = panel.marked_entries
            return marked[0] if len(marked) == 1 else None
        entry = panel.selected
        return None if entry is None or entry.name == ".." else entry

    async def quick_rename(self, panel: Panel) -> None:
        """File > Quick rename: Alt+F6's rename, the new name asked in a box."""
        from navigator.widgets.file_ops.rename_dialog import RenameDialog

        app = self.application
        entry = self._rename_candidate(panel)
        if app is None or entry is None:
            return
        new = await RenameDialog(name=entry.name, is_dir=entry.is_dir).execute(app)
        if new and new != entry.name:
            await self._rename_entry(panel, entry, new)

    async def _rename_entry(self, panel: Panel, entry: Any, new: str) -> None:
        """*entry* renamed to *new* beside itself, on a thread.

        A name already taken is refused, as DOS's rename refused it where
        POSIX's would replace it; a ``/`` is no name.  The cursor goes to the
        file under its new name, and a tag goes with it.  A local rename
        refused permission offers *As root* (a departure;
        :mod:`navigator.lib.system.elevate`).
        """
        from navigator.lib.system.elevate import ELEVATION, refused

        app = self.application
        old = entry.name
        here = Location.of(entry.directory) if entry.directory is not None else panel.location
        if "/" in new:
            await Dialog(title=tr("Error"),
                         prompt=tr("Could not rename {old}\nto {new}: {reason}").format(
                             old=old, new=new, reason=tr("a name cannot hold a /")),
                         buttons="ok").execute(app)
            return
        taken = "a file of that name is already there"
        as_root = False

        def rename() -> None:
            target = here / new
            if as_root:
                from navigator.lib.drives.root import ROOT_DRIVE

                drive = ROOT_DRIVE
            else:
                drive = drive_of(here)
            try:
                if drive.lexists(target) and not drive.same_file(here / old, target):
                    raise FileExistsError(errno.EEXIST, taken)
                drive.rename(here / old, target)
                drive.finish()
            finally:
                if as_root:
                    ELEVATION.release()

        while True:
            try:
                await asyncio.to_thread(rename)
            except OSError as error:
                reason = (tr("a file of that name is already there") if error.strerror == taken
                          else error.strerror or error)
                message = tr("Could not rename {old}\nto {new}: {reason}").format(old=old, new=new, reason=reason)
                if (not as_root and here.is_local and refused(error)
                        and await asyncio.to_thread(ELEVATION.available)):
                    from navigator.widgets.file_ops.as_root import ask_as_root

                    if await ask_as_root(app, message):
                        as_root = True
                        continue
                    return
                await Dialog(title=tr("Error"), prompt=message, buttons="ok").execute(app)
                return
            UNDO.push(undo_history.Renamed(((here, old, new),)))
            await self._after_renames(panel, [(here, old, new)], at=(here, new))
            return

    async def _after_renames(self, panel: Panel, renamed: Sequence[tuple[Location, str, str]],
                             at: tuple[Location, str] | None = None) -> None:
        """What *panel* knows of files renamed, ``(place, old, new)`` each: a
        listing's entries and the tags take the new names, an editor holding
        one hears of it, and the panel -- the cursor on *at* if given -- and
        the other one showing the same place are read again, the other's
        cursor on *at* too when it shows *at*'s directory (as F5/F6's)."""
        from navigator.widgets.editor.edit_window.edit_window import FileSaved

        names = {(place, old): new for place, old, new in renamed}
        here = panel.location

        def key(directory: Any, name: str) -> str:
            return name if directory is None else os.path.join(str(directory), name)

        marked = set(panel.marked)
        cursor_key = None
        if panel.found is not None:
            # The listing knows its files by name: tell it the new ones.
            for found in panel.found.entries:
                place = Location.of(found.directory) if found.directory is not None else here
                new = names.get((place, found.name))
                if new is None:
                    continue
                old_key = found.key
                found.name = new
                if old_key in marked:
                    marked = (marked - {old_key}) | {found.key}
                if at == (place, new):
                    cursor_key = found.key
        else:
            for (place, old), new in names.items():
                if place == here and old in marked:
                    marked = (marked - {old}) | {new}
            if at is not None and at[0] == here:
                cursor_key = key(None, at[1])
        if marked != panel.marked:
            panel.marked = frozenset(marked)
        for place, _old, new in renamed:
            if place.is_local:
                await self.emit(FileSaved(place.local / new))
        panel.reload(key=cursor_key)
        other = self.passive_panel
        if other is not panel and other.found is None and other.location in {place for place, _, _ in renamed}:
            other.reload(key=at[1] if at is not None and at[0] == other.location else None)

    async def multi_rename(self, panel: Panel) -> None:
        """Alt+A: the tagged files -- or the one at the cursor -- renamed by
        a pattern, every new name previewed first
        (:mod:`navigator.lib.file_ops.multirename`), then renamed on a thread.
        A departure: Total Commander's *Multi-Rename Tool*."""
        from navigator.lib.file_ops import multirename
        from navigator.widgets.file_ops.multi_rename_dialog import MultiRenameDialog

        app = self.application
        entries = self.selection(panel)
        if app is None or not entries:
            return
        here = panel.location
        items = []
        for entry in entries:
            place = Location.of(entry.directory) if entry.directory is not None else here
            items.append(multirename.Item(entry.name, place, entry.is_dir, entry.mtime,
                                          place.name if not place.is_root else ""))
        places = {item.place for item in items}

        def taken() -> dict[Any, set[str]]:
            names: dict[Any, set[str]] = {}
            for place in places:
                try:
                    names[place] = {name for name, _ in drive_of(place).children(place)}
                except OSError:
                    pass
            return names

        known = await asyncio.to_thread(taken)
        rows = await MultiRenameDialog(items, known).execute(app)
        if not rows:
            return
        pairs = [(row.item.place, row.item.name, row.new) for row in rows]
        done = await self._run_renames(pairs)
        if done:
            UNDO.push(undo_history.Renamed(tuple(done)))
            # The cursor follows its own file if that was renamed, else goes
            # to the first renamed, as F5/F6 land on what they made.
            at = (done[0][0], done[0][2])
            selected = panel.selected
            if selected is not None:
                where = Location.of(selected.directory) if selected.directory is not None else here
                at = next(((place, new) for place, old, new in done
                           if place == where and old == selected.name), at)
            await self._after_renames(panel, done, at=at)

    async def _run_renames(self, pairs: Sequence[tuple[Location, str, str]]) -> list[tuple[Location, str, str]]:
        """*pairs* renamed on a thread (:func:`navigator.lib.file_ops.multirename.run`),
        a box showing how far it is once it takes a moment; what was done."""
        from navigator.lib.file_ops import filecopy, multirename
        from navigator.lib.system.job import Stopped
        from navigator.widgets.manager.find_progress import FindProgress

        job = multirename.RenameJob()

        def make_box() -> Any:
            box = FindProgress()
            box.title = tr("Rename")
            box.count_row.visible = False
            return box

        def refresh(box: Any) -> None:
            box.directory = f"{job.count}/{job.total}  {job.current}"

        async def answer(question: Any) -> Any:
            if isinstance(question, filecopy.Failure):
                return await self._ask_skip(question.message, elevate=question.elevate)
            return None

        running = asyncio.ensure_future(asyncio.to_thread(multirename.run, list(pairs), job, drive_of))
        try:
            await self._watch_job(running, job, make_box, refresh, answer)
            await running
        except Stopped:
            pass
        finally:
            if not running.done():
                job.stop()
        return list(job.done)
