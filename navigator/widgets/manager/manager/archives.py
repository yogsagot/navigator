"""Archives and disk images: Extract to, Test, Extract archive (ARCVIEW.PAS), Unmount image.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.commands import ExtractArchive, MountImage, ChangeInactive, EnterWithoutArchive
from navigator.widgets.manager.panel import Panel
from navigator.lib.drives import DriveGone, Location
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager.helpers import _is_archive

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Archives(_Base):
    """Archives and disk images: Extract to, Test, Extract archive (ARCVIEW.PAS), Unmount image."""

    # -- archives: Extract to, Test, Extract archive (ARCVIEW.PAS) ---------------------------------

    # -- disk images: Unmount image (a departure: DOS had no loop devices) ---------------------------

    async def on_mount_image(self, event: MountImage) -> bool:
        """Disk > *Mount image*: Enter's mounting (``enter_image``), asked for
        by name -- the image at the cursor, whatever *ENTER mounts disc
        images* says."""
        from navigator.widgets.drives.disk_image import enter_image

        panel = self.active_panel
        path = panel.image_file()
        if path is not None:
            self.spawn(enter_image(panel, path))
        return True

    async def unmount_image(self, panel: Any) -> None:
        """The disk image *panel* is in -- or at its cursor -- unmounted and
        detached (:func:`navigator.widgets.drives.disk_image.unmount_image`)."""
        from navigator.widgets.drives.disk_image import unmount_image

        await unmount_image(self.application, panel.image_here())

    async def on_extract_archive(self, event: ExtractArchive) -> bool:
        """Shift+F2: the archives at the cursor or tagged extracted -- or, in
        an archive, what is tagged there (*Extract to...*), so the one key
        extracts wherever the panel is.  A departure, asked for: DN's
        ``cmExtractArchive`` did nothing inside an archive."""
        panel = self.active_panel
        if panel.location.outer is not None:
            self.spawn(self.extract_files(panel))
        else:
            self.spawn(self.extract_archives(panel))
        return True

    async def archive_files(self, panel: Panel) -> None:
        from navigator.widgets.file_ops.archive_dialog import ArchiveDialog

        app = self.application
        entries = self.selection(panel)
        place = self._archive_place(panel, entries)
        if app is None or place is None:
            return
        directory, stem = place
        request = await ArchiveDialog(entries=entries, here=panel.location, directory=directory, stem=stem,
                                      hidden=panel.show_hidden).execute(app)
        if request is None:
            return
        await self._run_copy(panel, request, panel.location, move=request.move, others=(self.passive_panel,))

    def _archive_place(self, panel: Panel, entries: list[Any]) -> tuple[str, str] | None:
        """Where the new archive goes and its name without an ending: named
        after the one entry, or after the panel's directory for several, in
        the other panel's place when it can be written, else this one's --
        never inside an archive.  None where neither can be written."""
        from navigator.widgets.file_ops.archive_dialog.archive_dialog import suffix_of

        if not entries:
            return None
        if len(entries) == 1 and entries[0].name != "..":
            name = entries[0].name
            ending = suffix_of(name)
            stem = name if entries[0].is_dir else name[: len(name) - len(ending)] if ending else Path(name).stem
        else:
            stem = panel.location.path.name or "archive"
        for side in (self.passive_panel, panel):
            place = self._push_first_name(side)
            if place is not None and side.location.outer is None:
                return str(place), stem or "archive"
        return None

    def _extract_target(self, panel: Panel) -> str | None:
        """``cmPushFirstName``: the other panel's place, where it can be written."""
        place = self._push_first_name(self.right if panel is self.left else self.left)
        return str(place) if place is not None else None

    @staticmethod
    def _push_first_name(other: Panel) -> Any:
        """DN's ``cmPushFirstName``, what a target line opens on: *other*'s
        place -- none where it cannot be written, or where it is a *Find:*
        listing, which has no one place (``TFindDrive.GetRealName`` was
        empty, so DN's line opened empty)."""
        if other.found is not None:
            return None
        try:
            return shown(other.location) if other.drive.can("write") else None
        except DriveGone:
            return None

    async def _ask_extract(self, panel: Panel, outer: Location) -> dict[str, Any] | None:
        from navigator.widgets.file_ops.extract_dialog import ExtractDialog

        app = self.application
        if app is None:
            return None
        return await ExtractDialog(here=outer.parent, other=self._extract_target(panel),
                                   hidden=panel.show_hidden).execute(app)

    async def extract_files(self, panel: Panel) -> None:
        """``cmExtractTo``, ``TArcDrive.CopyFiles``' *Extract files*: what is
        tagged in the archive, or at the cursor, copied out where the box
        says -- with its path inside, or (*Extract with path names* off)
        straight into the target -- or, with *Test only*, tested instead."""
        outer = panel.location.outer
        entries = self.selection(panel)
        if outer is None or not entries:
            return
        answer = await self._ask_extract(panel, outer)
        if answer is None:
            return
        sources = [panel.entry_location(entry) for entry in entries]
        if answer["test"]:
            await self.test_archive(panel, sources)
            return
        await self._extract(panel, sources, outer, answer)

    async def _extract(self, panel: Panel, sources: list[Location], outer: Location,
                       answer: dict[str, Any]) -> None:
        """*sources* in the archive at *outer* copied out as *answer* says:
        an empty target is the archive's own directory, as DN's empty
        ``ExtrDir`` was."""
        from navigator.lib.file_ops import filecopy
        from navigator.widgets.file_ops.copy_dialog import copy_dialog

        here = outer.parent
        target = answer["target"] or str(shown(here))
        session = copy_dialog._session
        request = filecopy.CopyRequest(
            sources=list(sources), target=target.rstrip("/") + "/", mode=session["mode"],
            options=session["options"] & ~filecopy.MOVE, flush=SETTINGS.system.flush_buffers,
            flatten=not answer["paths"],
        )
        other = self.right if panel is self.left else self.left
        await self._run_copy(panel, request, here, move=False, others=(other,))

    async def extract_archives(self, panel: Panel) -> None:
        """Shift+F2, ``cmExtractArchive``: each archive tagged, or the one at
        the cursor, opened on a thread and all that is in it extracted where
        the one *Extract files* box says -- or tested."""
        from navigator.lib.drives import archive
        from navigator.lib.system.job import Stopped
        from navigator.widgets.editor.loading import FileJob
        from navml.widgets.dialog.control import escape_caption

        app = self.application
        archives = [panel.entry_location(entry) for entry in self.selection(panel) if _is_archive(entry)]
        if app is None or not archives or panel.location.outer is not None:
            return
        answer = await self._ask_extract(panel, archives[0])
        if answer is None:
            return
        for outer in archives:
            job = FileJob()

            from navigator.widgets.drives.archives import open_archive_or_root

            try:
                # An archive the user may not read offers *As root* here.
                drive = await open_archive_or_root(app, outer, job)
                root = drive.at("/")
                sources = await asyncio.to_thread(lambda: [root / name for name in drive.names(root)])
            except Stopped:
                return
            except (OSError, archive.NotAnArchive) as error:
                await Dialog(title=tr("Error"), prompt=tr("Cannot read {path}: {error}").format(
                    path=escape_caption(str(outer)), error=escape_caption(
                        getattr(error, "strerror", None) or str(error))), buttons="ok").execute(app)
                continue
            try:
                if answer["test"]:
                    await self._test(drive, outer, None)
                elif sources:
                    await self._extract(panel, sources, outer, answer)
            finally:
                # Closed, on a thread, unless a panel went into it meanwhile.
                await asyncio.to_thread(archive.release_unheld, outer)

    async def test_archive(self, panel: Panel, sources: list[Location] | None = None) -> None:
        """``cmArcTest``: what is tagged in the archive -- the whole of it at
        ``..`` with nothing tagged -- read through on a thread, and what
        failed its check said."""
        outer = panel.location.outer
        if outer is None:
            return
        if sources is None:
            entries = self.selection(panel)
            sources = [panel.entry_location(entry) for entry in entries] or None
        try:
            drive = panel.drive
        except DriveGone:
            return
        await self._test(drive, outer, sources)

    async def _test(self, drive: Any, outer: Location, sources: list[Location] | None) -> None:
        from navigator.lib.system.job import Stopped
        from navigator.widgets.editor.loading import FileJob, progress_box, refresh_box
        from navml.widgets.dialog.control import escape_caption

        app = self.application
        job = FileJob()
        notice = tr("Testing {name}").format(name=outer.name)
        work = asyncio.ensure_future(asyncio.to_thread(drive.test, job, sources))
        try:
            await self._watch_job(work, job, lambda: progress_box(job, notice), refresh_box(job),
                                  self._no_question)
            failures = await work
        except Stopped:
            return
        except OSError as error:
            failures = [("", error.strerror or str(error))]
        finally:
            if not work.done():
                job.stop()
        if app is None:
            return
        name = escape_caption(outer.name)
        if not failures:
            prompt = tr("No errors found in {name}").format(name=name)
        else:
            shown_lines = [escape_caption(f"{path}: {why}" if path else why) for path, why in failures[:8]]
            if len(failures) > 8:
                shown_lines.append(tr_n("and {n} more", "and {n} more", len(failures) - 8))
            prompt = (tr_n("{n} error found in {name}:", "{n} errors found in {name}:", len(failures), name=name)
                      + "\n" + "\n".join(shown_lines))
        await Dialog(title=tr("Test archive"), prompt=prompt, buttons="ok").execute(app)

    @staticmethod
    async def _no_question(question: Any) -> Any:
        return None

    async def on_enter_without_archive(self, event: EnterWithoutArchive) -> bool:
        """Shift+Enter: in a *Find:* listing ``cmChangeInactive``; elsewhere
        Enter without the archive (and disk image) test."""
        if self.active_panel.found is not None:
            return await self.on_change_inactive(ChangeInactive())
        await self.active_panel.choose(archives=False)
        return True

    async def on_change_inactive(self, event: ChangeInactive) -> bool:
        """Shift+Enter in a *Find:* listing: ``cmChangeInactive``, the passive
        panel on the found file's directory, its cursor on the file -- shown,
        if it was hidden or stood behind the tree or the quick view.

        That panel's ``cmFindGotoFile``: its file mask back to all files
        (``FileMask := x_x``), so the file is listed whatever it showed, and
        the keyboard there (``Owner^.Select; Select``); the listing stays in
        its own panel, Tab away.

        On ``..`` it leaves the listing, as Enter does there: DN's
        ``_CtrlPgDn`` tested ``..`` before Shift (``_CtrlPgUp``)."""
        from navigator.lib.appearance import filetypes

        entry = self.active_panel.selected
        if entry is not None and entry.name == ".." and self.active_panel.found is not None:
            self.active_panel.leave_found()
            return True
        if entry is None or entry.directory is None:
            return True
        side = "right" if self.active_panel is self.left else "left"
        panel = self.bring_side(side)
        panel.file_mask = filetypes.ALL_FILES
        panel.go_to_entry(entry)
        panel.focus()
        return True

    @staticmethod
    def _way_back(panel: Panel, current: Any) -> str | None:
        """Where the cursor goes in the directory when a new listing is left
        for good: the entry it is on -- or, made from a listing, that
        listing's own way back, its entries being from other directories."""
        if panel.found is not None:
            return panel.found.return_to
        return current.name if current is not None else None
