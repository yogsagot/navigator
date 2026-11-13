"""Listings that are no directory: File Find, Panelize, Read file list, Find duplicates,
Replace in files, and Make list.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.commands import Panelize
from navigator.widgets.manager.panel import Panel
from navigator.widgets.tree.directory_tree.directory_tree import reread_trees
from navigator.lib.drives import Location, drive_of
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Listings(_Base):
    """Listings that are no directory: File Find, Panelize, Read file list, Find duplicates,"""

    async def read_file_list(self, panel: Panel) -> None:
        """Alt+V: ``cmPanelMakeList`` -- the list file at the cursor read on a
        thread (:func:`navigator.lib.file_ops.filefind.read_list`) into a listing titled
        with its name (``TFindDrive.InitList``), ``..`` leading back.  None of
        its files there: *No files found*, as ``ReadList`` said."""
        from navigator.lib.file_ops.filefind import FindListing, read_list
        from navigator.widgets.manager.panel.panel import entry_at

        app = self.application
        entry = panel.selected
        if app is None or entry is None or entry.is_dir:
            return
        if not panel.location.is_local and entry.directory is None:
            from navigator.lib.file_ops.filefind import read_list_on_drive

            here_place = panel.location
            source = panel.entry_location(entry)
            try:
                entries = await asyncio.to_thread(read_list_on_drive, source, here_place)
            except OSError as error:
                await Dialog(title=tr("Error"),
                             prompt=tr("Cannot read {path}: {reason}").format(path=source, reason=error.strerror or error),
                             buttons="ok").execute(app)
                return
            if not entries:
                await Dialog(title=tr("Error"), prompt=tr("No files found"), buttons="ok").execute(app)
                return
            panel.show_found(FindListing(str(source), here_place, entries, return_to=self._way_back(panel, entry)))
            return
        here = Path(panel.path)
        source = entry.path_in(here)
        try:
            entries = await asyncio.to_thread(
                read_list, source, here, lambda path: entry_at(path, path.parent))
        except OSError as error:
            await Dialog(title=tr("Error"),
                         prompt=tr("Cannot read {path}: {reason}").format(path=source, reason=error.strerror or error),
                         buttons="ok").execute(app)
            return
        if not entries:
            await Dialog(title=tr("Error"), prompt=tr("No files found"), buttons="ok").execute(app)
            return
        panel.show_found(FindListing(str(source), here, entries, return_to=self._way_back(panel, entry)))

    async def panelize(self, panel: Panel, command: str | None = None) -> None:
        """Alt+O: what *command* prints, run in *panel*'s directory on a
        thread, as a listing titled with it (:mod:`navigator.lib.file_ops.panelize`);
        asked for first when not given.  Its box shows once the command has
        taken a moment, and *Cancel* ends it.  A departure: MC's *External
        panelize*."""
        from navigator.lib.file_ops.filefind import FindListing, list_from_lines
        from navigator.lib.file_ops.panelize import PanelizeJob, capture, lines_of
        from navigator.lib.system.job import Stopped
        from navigator.widgets.manager.find_progress import FindProgress
        from navigator.widgets.manager.panel.panel import entry_at
        from navigator.widgets.manager.panelize_dialog import PanelizeDialog

        app = self.application
        if app is None:
            return
        if command is None:
            command = await PanelizeDialog(type(self).last_panelized).execute(app)
            if not command:
                return
        if not panel.location.is_local:
            await Dialog(title=tr("Error"), prompt=tr("A command's output can be panelized on this machine's disk only"),
                         buttons="ok").execute(app)
            return
        type(self).last_panelized = command
        here = Path(panel.path)
        current = panel.selected
        job = PanelizeJob()

        def work() -> list[Any]:
            capture(command, here, job)
            return list_from_lines(lines_of(job.output), here, lambda path: entry_at(path, path.parent))

        def make_box() -> Any:
            box = FindProgress()
            box.title = tr("Panelize")
            box.count_row.visible = False
            return box

        def refresh(box: Any) -> None:
            box.directory = command

        async def no_questions(question: Any) -> None:
            return None

        running = asyncio.ensure_future(asyncio.to_thread(work))
        try:
            await self._watch_job(running, job, make_box, refresh, no_questions,
                                  abort=tr("Stop the command?"))
            entries = await running
        except Stopped:
            return
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot run {command}: {reason}").format(
                command=command, reason=error.strerror or error), buttons="ok").execute(app)
            return
        finally:
            if not running.done():
                job.stop()
        if panel.location != Location.of(here):
            return  # the panel went elsewhere meanwhile
        if not entries:
            reason = job.errors.strip().splitlines()[0] if job.status and job.errors.strip() else ""
            prompt = tr("No files found") if not reason else tr("No files found\n{reason}").format(reason=reason)
            await Dialog(title=tr("Error"), prompt=prompt, buttons="ok").execute(app)
            return
        again = panel.found is not None and panel.found.command == command
        if again:
            # Ctrl+R: the same listing read anew, its columns and cursor kept.
            columns, back = panel.find_columns, panel.found.return_to
        else:
            back = self._way_back(panel, current)
        panel.show_found(FindListing(tr("Panel: {command}").format(command=command), here, entries,
                                     return_to=back, command=command), stack=not again)
        if again:
            panel.find_columns = columns
            if current is not None:
                panel.reload(key=current.key)
        panel.focus()

    async def find_file(self, panel: Panel) -> None:
        """Alt+F7: ``FindFile``, what *Find File* asks for found into *panel*.

        The search runs on a thread (:func:`navigator.lib.file_ops.filefind.search`) under
        *Search* -- the directory it is in and the count -- whose *Stop* asks
        DN's *Cancel search?*.  The panel becomes a *Find:* listing with the
        first file found and fills as the rest are (``cmInsertFile``); nothing
        found leaves it as it was and says *No files found*.
        """
        from navigator.widgets.manager.find_file_dialog import FindFileDialog

        app = self.application
        if app is None:
            return
        request = await FindFileDialog().execute(app)
        if request is None:
            return
        from navigator.lib.file_ops.filefind import hand_on

        hand_on(request)
        await self._search_into(panel, request, tr("Find: {mask}").format(mask=request.mask))

    async def replace_in_files(self, panel: Panel) -> None:
        """File > Replace in files (a departure, asked for): Find File's
        search from *panel*, the text replaced in each file holding it once
        :class:`~navigator.widgets.file_ops.replace_query.ReplaceQuery` says
        so (:func:`navigator.lib.file_ops.filereplace.replace`, on a thread).

        The files changed fill a *Replaced:* listing as Find's fill its own,
        and a toast says how many replacements in how many files; none
        changed leaves the panel as it was and says why.
        """
        from navigator.lib.file_ops.filereplace import ReplaceJob, ReplaceQuestion, replace
        from navigator.widgets.manager.find_file_dialog import FindFileDialog

        app = self.application
        if app is None:
            return
        request = await FindFileDialog(replacing=True).execute(app)
        if request is None:
            return
        job = ReplaceJob()

        def work(start: Any, make: Any, hidden: bool, mounts: Any) -> list[Any]:
            return replace(request, start, make, job, show_hidden=hidden, mounts=mounts)

        async def answer(question: Any) -> Any:
            from navigator.widgets.file_ops.replace_query import ReplaceQuery

            if isinstance(question, ReplaceQuestion):
                return await ReplaceQuery(question=question).execute(app)
            return await self._answer_copy_question(question)

        def nothing() -> str:
            if not job.matched:
                return tr("No files found")
            return tr("No files changed")

        try:
            await self._search_into(panel, request.find, tr("Replaced: {text}").format(text=request.find.text),
                                    job=job, work=work, answer=answer, nothing=nothing)
        finally:
            if job.as_root:
                # *As root* was answered: the helper let go as ``root_timeout`` says.
                from navigator.lib.system.elevate import ELEVATION

                await asyncio.to_thread(ELEVATION.release)
        if job.found:
            toast = getattr(getattr(app, "root", None), "toast", None)
            if toast is not None and app.is_running:
                # A toast is one line: the files under the replacements' count.
                toast(tr_n("{count} file changed", "{count} files changed", len(job.found), count=len(job.found)),
                      title=tr_n("{count} replacement", "{count} replacements", job.replacements,
                                 count=job.replacements))

    async def find_duplicates(self, panel: Panel, request: Any = None) -> None:
        """Panel > Find duplicates: the identical files below *panel*'s
        directory, asked for first when *request* is not given, compared on
        a thread (:func:`navigator.lib.file_ops.duplicates.find_duplicates`) into a
        listing that keeps its groups together.  A departure, asked for."""
        from navigator.lib.file_ops.duplicates import DuplicatesJob, find_duplicates
        from navigator.lib.file_ops.filefind import FindListing
        from navigator.lib.system.job import Stopped
        from navigator.widgets.manager.duplicates_dialog import DuplicatesDialog
        from navigator.widgets.manager.find_progress import FindProgress
        from navigator.widgets.manager.panel.panel import entry_at

        app = self.application
        if app is None or panel.found is not None:
            return
        if request is None:
            request = await DuplicatesDialog().execute(app)
            if request is None:
                return
        # Any drive: the disk's path, or the place itself -- a server, an
        # archive, ``root:`` through the root helper.
        place, hidden = panel.location, panel.show_hidden
        here = place.local if place.is_local else place
        current = panel.selected
        job = DuplicatesJob()

        def work() -> list[Any]:
            groups = find_duplicates(request, here, job, show_hidden=hidden)
            entries = []
            for group in groups:
                for path in group:
                    if place.is_local:
                        entry = entry_at(path, path.parent)
                    else:
                        entry = job.listed.get(path)  # as the drive's walk listed it
                    if entry is not None:
                        entries.append(entry)
            return entries

        def make_box() -> Any:
            box = FindProgress()
            box.title = tr("Find duplicates")
            return box

        def refresh(box: Any) -> None:
            box.directory = job.directory
            box.count = len(job.found) if job.phase == "scan" else job.candidates

        async def no_questions(question: Any) -> None:
            return None

        running = asyncio.ensure_future(asyncio.to_thread(work))
        try:
            await self._watch_job(running, job, make_box, refresh, no_questions,
                                  abort=tr("Cancel search?"))
            entries = await running
        except Stopped:
            return
        finally:
            if not running.done():
                job.stop()
        if panel.location != place or panel.found is not None:
            return  # the panel went elsewhere meanwhile
        if not entries:
            await Dialog(title=tr("Error"), prompt=tr("No duplicate files found"), buttons="ok").execute(app)
            return
        panel.show_found(FindListing(tr("Duplicates: {path}").format(path=panel.title_location), here, entries,
                                     return_to=current.name if current is not None else None, keep_order=True))
        panel.focus()

    async def _search_into(self, panel: Panel, request: Any, title: str, *, job: Any = None,
                           work: Callable[..., list[Any]] | None = None,
                           answer: Callable[[Any], Awaitable[Any]] | None = None,
                           nothing: Callable[[], str] | None = None) -> None:
        """*request* searched from *panel*'s directory into a listing titled
        *title*, filling as it is found; nothing found says so.

        Replace in files passes its own *job*, the *work* that walks --
        given the start, the entry maker, whether hidden files count and the
        mounts -- the *answer* to its questions, and what *nothing* found
        says."""
        from navigator.lib.file_ops.filefind import FindJob, FindListing, search, searchable_mounts
        from navigator.widgets.manager.find_progress import FindProgress
        from navigator.widgets.manager.panel.panel import make_entry

        app = self.application
        if app is None:
            return
        start, hidden = shown(panel.location), panel.show_hidden
        current = panel.selected
        listing = FindListing(title, start, live=True, return_to=self._way_back(panel, current))
        if job is None:
            job = FindJob()
        walk = work

        def work() -> list[Any]:
            mounts = searchable_mounts() if request.scope == "drives" and isinstance(start, Path) else ()
            make = lambda directory, item, info: make_entry(item, directory)  # noqa: E731
            if walk is not None:
                return walk(start, make, hidden, mounts)
            return search(request, start, make, job, show_hidden=hidden, mounts=mounts)

        def refresh(box: Any = None) -> None:
            if box is not None:
                box.directory, box.count = job.directory, len(job.found)
            if len(job.found) != len(listing.entries) and panel.location == Location.of(start):
                listing.entries = list(job.found)
                if panel.found is not listing:
                    panel.show_found(listing)
                else:
                    panel.reload()

        async def no_questions(question: Any) -> None:
            return None

        running = asyncio.ensure_future(asyncio.to_thread(work))
        try:
            await self._watch_job(running, job, FindProgress, refresh, answer or no_questions,
                                  abort=tr("Cancel search?"))
            await running
        finally:
            if not running.done():
                job.stop()
        refresh()
        listing.live = False
        if not listing.entries:
            prompt = nothing() if nothing is not None else tr("No files found")
            await Dialog(title=tr("Error"), prompt=prompt, buttons="ok").execute(app)
            return
        if panel.found is listing:
            panel.reload()
            panel.focus()

    #: *Make List File*'s boxes as last left, for the session (DN kept
    #: ``MakeListFileOptions`` in its configuration).

    async def make_list(self, panel: Panel) -> None:
        """Alt+L: ``CM_MakeList`` -> ``MakeListFile``, the tagged files in a list file.

        Nothing tagged, *Select* comes first, and nothing tagged after it is
        nothing to do.  Then *Make List File*; a file already there is asked
        about -- *Yes* replaces it, *Append* adds to it -- and what is written
        is untagged, file by file as DN's ``cmCopyUnselect`` did, and every
        panel showing the list's directory re-reads (``RereadDirectory``).
        The relative name is the active panel's directory's, DN's current one.

        The boxes are ``[make_list]``'s, DN's ``MakeListFileOptions``; a
        *Store path names* left ticked stays so only for files from more than
        one directory (a *Find:* listing), as ``MakeListFile`` unticked it.
        """
        from navigator.lib.file_ops.makelist import AUTO_PATHS, STORE_PATHS, make_lines
        from navigator.widgets.editor.edit_window.edit_window import FileSaved
        from navigator.widgets.manager.make_list_dialog import MakeListDialog
        from navigator.widgets.manager.select_dialog import SelectDialog

        app = self.application
        if app is None or not panel.items:
            return
        if not panel.marked_entries:
            answer = await SelectDialog(select=True, invert=False).execute(app)
            if answer is None:
                return
            mask, except_mask = answer
            panel.select_group(mask, select=True, invert=except_mask)
        entries = panel.marked_entries
        if not entries:
            return
        kept = SETTINGS.make_list
        options = (STORE_PATHS if kept.store_paths else 0) | (AUTO_PATHS if kept.auto_paths else 0)
        if options & STORE_PATHS and len({panel.entry_location(entry).parent for entry in entries}) < 2:
            options &= ~STORE_PATHS  # ``cmlPathNames`` dropped: one directory needs no paths
        answer = await MakeListDialog(options).execute(app)
        if answer is None:
            return
        name, action, options = answer
        self._keep_section("make_list", {"store_paths": bool(options & STORE_PATHS),
                                         "auto_paths": bool(options & AUTO_PATHS)}, app)
        if not panel.location.is_local:
            await self._make_list_elsewhere(panel, entries, name, action, options)
            return
        here = Path(panel.path)
        target = (here / Path(name).expanduser()).absolute()
        appending = False
        if await asyncio.to_thread(target.exists):
            query = Dialog(title=tr("Warning"),
                           prompt=tr("File {name}\nalready exists.\nOK to overwrite it?").format(name=target.name),
                           buttons="yes-no-cancel")
            query.no.text = tr("A~p~pend")
            reply = await query.execute(app)
            if reply is None:
                return
            appending = reply is False
        lines = make_lines([entry.path_in(here) for entry in entries], action, target.parent, options)

        def write() -> None:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "a" if appending else "w", encoding="utf-8",
                      errors="surrogateescape") as file:
                file.writelines(f"{text}\n" for text in lines)

        if not await self._write_list(write, Location.of(target), lines, appending):
            return
        panel.untag(entries)
        await self.emit(FileSaved(target))
        reread_trees(self.application)  # DN's ``cmRereadTree`` (``FILECOPY.PAS:574``)

    async def _make_list_elsewhere(self, panel: Panel, entries: list[Any], name: str, action: str,
                                   options: int) -> None:
        """Alt+L on another drive: the list written there, on its drive,
        naming its files by that drive's own paths -- a list made on a server
        is for use there."""
        from navigator.lib.file_ops.filecopy import target_location
        from navigator.lib.file_ops.makelist import make_lines
        from navigator.widgets.editor.edit_window.edit_window import FileSaved

        app = self.application
        target = target_location(name, panel.location)
        if target.is_local:
            # A list named on the disk from a panel elsewhere: the panel's paths.
            local, list_dir = target.local.absolute(), target.local.absolute().parent
        else:
            local, list_dir = None, target.parent.path
        files = [panel.entry_location(entry).path for entry in entries]

        def there() -> bool:
            try:
                return drive_of(target).lexists(target)
            except OSError:
                return False

        appending = False
        if await asyncio.to_thread(there):
            query = Dialog(title=tr("Warning"),
                           prompt=tr("File {name}\nalready exists.\nOK to overwrite it?").format(name=target.name),
                           buttons="yes-no-cancel")
            query.no.text = tr("A~p~pend")
            reply = await query.execute(app)
            if reply is None:
                return
            appending = reply is False
        lines = make_lines(files, action, list_dir, options)

        def write() -> None:
            drive = drive_of(target)
            with drive.open_write(target, append=appending) as file:
                file.write("".join(f"{text}\n" for text in lines).encode("utf-8", "surrogateescape"))
            drive.finish()

        if not await self._write_list(write, target, lines, appending):
            return
        panel.untag(entries)
        await self.emit(FileSaved(local if local is not None else target))
        reread_trees(self.application)

    async def _write_list(self, write: Callable[[], None], target: Location, lines: list[str],
                          appending: bool) -> bool:
        """Alt+L's *write* on a thread, its failure said; True once written.
        A list on the disk refused permission offers *As root* and is written
        through the helper (a departure; :mod:`navigator.lib.system.elevate`)."""
        def as_root() -> None:
            from navigator.lib.drives.root import ROOT_DRIVE

            try:
                ROOT_DRIVE.makedirs(target.parent)
                with ROOT_DRIVE.open_write(target, append=appending) as file:
                    file.write("".join(f"{text}\n" for text in lines).encode("utf-8", "surrogateescape"))
            finally:
                ROOT_DRIVE.release()

        try:
            await asyncio.to_thread(write)
            return True
        except OSError as error:
            message = tr("Cannot open {path}: {reason}").format(path=target, reason=error.strerror or error)
            if target.is_local and await self._may_as_root(error, message):
                try:
                    await asyncio.to_thread(as_root)
                    return True
                except OSError as again:
                    message = tr("Cannot open {path}: {reason}").format(path=target, reason=again.strerror or again)
            elif target.is_local and self._as_root_declined:
                return False
            await Dialog(title=tr("Error"), prompt=message, buttons="ok").execute(self.application)
            return False
