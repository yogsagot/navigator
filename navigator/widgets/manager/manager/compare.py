"""Compare directories, the recursive Synchronize window and Compare files.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.commands import Copy, Delete
from navigator.lib.drives import Location
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Compare(_Base):
    """Compare directories, the recursive Synchronize window and Compare files."""

    async def compare_directories(self) -> None:
        """Panel > Compare directories: ``CM_CompareDirs``, each panel against the other.

        *Compare directories* asks what to compare and whether to select or
        unselect; then each panel's files are compared with the other's
        (:mod:`navigator.lib.file_ops.dircompare`) and its tags set from what differs.
        Reading the files' contents goes on a thread, under *Comparing
        files* if it takes a while (DN's ``dlComparing``), and Esc there
        leaves the tags as they were; the rest is the listings alone.  A
        panel that has moved on by the time it is done is left alone.
        """
        from navigator.lib.file_ops.dircompare import differing, tagged
        from navigator.widgets.manager.compare_dialog import CompareDialog

        app = self.application
        if app is None:
            return
        panel, other = self.active_panel, self.passive_panel
        request = await CompareDialog().execute(app)
        if request is None:
            return
        if request.window:
            await self.sync_directories(request)
            return
        here, there = shown(panel.location), shown(other.location)
        mine, theirs = list(panel.items), list(other.items)

        def compare(job: Any = None) -> tuple[set[str], set[str]] | None:
            first = differing(mine, theirs, request, here, there, job)
            second = differing(theirs, mine, request, there, here, job) if first is not None else None
            return None if second is None else (first, second)

        if request.contents:
            from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress
            from navigator.widgets.editor.loading import FileJob, progress_box, refresh_box

            job = FileJob()
            found = await run_with_progress(
                app, lambda: compare(job), job, lambda: progress_box(job, tr("Comparing files")),
                refresh_box(job), delay=SLOW_PROGRESS_DELAY,
            )
        else:
            found = compare()
        if found is None:
            return
        for side, place, names in ((panel, here, found[0]), (other, there, found[1])):
            if side.location == Location.of(place):
                side.marked = tagged(side.marked, names, request)

    async def sync_directories(self, request: Any) -> None:
        """*Compare directories*' *Window, recursive*: the two panels' trees
        walked (:func:`~navigator.widgets.manager.sync_window.sync_window.walk_trees`)
        and what differs listed in the *Synchronize* window -- the left
        panel's tree on the left, whichever is active."""
        from navigator.widgets.manager.sync_window import SyncWindow
        from navigator.widgets.manager.sync_window.sync_window import sync_options, walk_trees

        app, desktop = self.application, self.desktop
        if app is None or desktop is None:
            return
        left, right = shown(self.left.location), shown(self.right.location)
        if self.left.location == self.right.location:
            await Dialog(title=tr("Compare directories"), prompt=tr("Both panels show the same directory."),
                         buttons="ok").execute(app)
            return
        show_hidden = self.left.show_hidden and self.right.show_hidden
        options = sync_options()
        rows = await walk_trees(app, left, right, request, show_hidden, options)
        if rows is None:
            return
        desktop.open(SyncWindow(manager=self, left=left, right=right, request=request, rows=rows,
                                show_hidden=show_hidden, options=options))

    async def synchronize(self, plan: Any) -> bool:
        """The *Synchronize* window's F5: *plan*'s copies, then its deletes,
        once confirmed.  The copies are one F5 copy, overwriting without
        asking -- the window said which way each goes -- and keeping each
        file's time, or the next compare would find every one different
        again; the deletes are one F8 with *Recursive delete*.  True when
        nothing was stopped."""
        from navigator.lib.file_ops import filecopy, fileerase

        copies, deletes = len(plan.pairs), len(plan.deletes)
        if not copies and not deletes:
            return False
        if copies and deletes:
            prompt = tr("Copy {copies} and delete {deletes}?").format(
                copies=tr_n("{n} file", "{n} files", copies), deletes=tr_n("{n} file", "{n} files", deletes))
        elif copies:
            prompt = tr_n("Copy {n} file?", "Copy {n} files?", copies)
        else:
            prompt = tr_n("Delete {n} file?", "Delete {n} files?", deletes)
        if await self._ask_yes_no(prompt, title=tr("Synchronize")) is not True:
            return False
        ok = True
        try:
            if copies:
                request = filecopy.CopyRequest(
                    sources=[], target="", mode=filecopy.OVERWRITE, options=filecopy.PRESERVE,
                    flush=SETTINGS.system.flush_buffers, pairs=list(plan.pairs),
                    directories=list(plan.directories),
                )
                ok = await self._run_copy(self.left, request, self.left.location, move=False, others=(self.right,))
            if ok and deletes:
                await self._run_erase(fileerase.EraseRequest(list(plan.deletes), recursive=True))
        finally:
            self.left.reload()
            self.right.reload()
        return ok

    def _diff_pair(self) -> tuple[Any, Any] | None:
        """The two files File > Compare files compares: two tagged in the
        active panel; else the one at its cursor and its namesake in the
        other panel -- or, without one, the file at the other's cursor.  None
        when there are not two files to compare."""
        panel, other = self.active_panel, self.passive_panel

        def is_file(entry: Any) -> bool:
            return entry is not None and not entry.is_dir and entry.name != ".."

        marked = [entry for entry in panel.marked_entries if is_file(entry)]
        if len(marked) == 2:
            return panel.entry_location(marked[0]), panel.entry_location(marked[1])
        entry = panel.selected
        if not is_file(entry) or self.miller_mode or self.hidden_side is not None:
            return None
        namesake = next((item for item in other.items if item.name == entry.name and is_file(item)), None)
        match = namesake if namesake is not None else other.selected
        if not is_file(match):
            return None
        pair = panel.entry_location(entry), other.entry_location(match)
        if panel is self.right:
            pair = pair[1], pair[0]  # the left panel's file on the left
        return pair

    async def diff_files(self) -> None:
        """File > Compare files: :func:`~navigator.widgets.viewer.diff_window.open_diff`
        on :meth:`_diff_pair`'s two files."""
        from navigator.widgets.viewer.diff_window import open_diff

        pair = self._diff_pair()
        desktop = self.desktop
        if pair is None or desktop is None:
            return
        await open_diff(desktop, *pair)
