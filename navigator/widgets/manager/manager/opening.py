"""Attributes (Alt+E), and opening files: F3/F4 internal or external, Open with,
the associations, Edit named, and As root on a refusal.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
import os
import shlex
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.commands import Edit, OpenWith
from navigator.lib.config.file_history import open_editor, open_viewer
from navigator.lib.config.associations import EDITORS, VIEWERS
from navigator.lib.drives import Location, drive_of
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager.helpers import action_caption

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Opening(_Base):
    """Attributes (Alt+E), and opening files: F3/F4 internal or external, Open with,"""

    # -- attributes --------------------------------------------------------------

    async def change_attributes(self, entries: list[Any] | None = None) -> None:
        """Ask what to change, change it on a thread, and let both panels look again.

        *entries* instead of the selection: F4 on a directory, DN's
        ``CM_SetAttributes(..., Single = On, ...)`` -- that one, whatever is
        tagged, and its tag left alone (``if not Single then PF^.Selected :=
        Off``, ``FLTOOLS.PAS:669``).

        ``delete_files``'s shape: the dialog, then ``fileattr.run`` through
        ``asyncio.to_thread`` with :meth:`_watch_job` between the two -- the
        progress box, titled *Attributes*, shows only for a long recursion --
        and each failure put as Copy's *Skip* / *Cancel*.  What was changed
        without a failure is untagged.
        """
        from navigator.lib.file_ops import fileattr
        from navigator.widgets.file_ops.attr_dialog import AttrDialog
        from navigator.widgets.file_ops.delete_progress import DeleteProgress

        app = self.application
        panel, other = self.active_panel, self.passive_panel
        single = entries is not None
        if entries is None:
            entries = self.selection(panel)
        if app is None or not entries:
            return
        from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress
        from navigator.widgets.editor.loading import FileJob, progress_box, refresh_box
        from navigator.widgets.file_ops.attr_dialog.attr_dialog import gather

        here = panel.location
        # What the dialog shows is asked of the system on a thread: a stat per
        # entry, and user and group lists a directory server may be slow with.
        looking = FileJob()
        facts = await run_with_progress(
            app, lambda: gather([shown(panel.entry_location(entry)) for entry in entries]), looking,
            lambda: progress_box(looking, tr("Reading file attributes")), refresh_box(looking),
            delay=SLOW_PROGRESS_DELAY,
        )
        if looking.stopped:
            return
        request = await AttrDialog(entries=entries, here=here, facts=facts).execute(app)
        if request is None:
            return
        job = fileattr.AttrJob()
        work = asyncio.ensure_future(asyncio.to_thread(fileattr.run, request, job))

        def make_box() -> Any:
            # The *Erase* box's lines and gauge fit as they are; only the
            # title is the document's, and so is assigned after it.
            box = DeleteProgress()
            box.title = tr("Attributes")
            return box

        def refresh(box: Any) -> None:
            box.action, box.path = action_caption(job.action), job.path
            box.done, box.total = job.done, job.total

        done: list[Path] = []
        try:
            await self._watch_job(work, job, make_box, refresh, self._answer_erase_question)
            done = await work
        finally:
            if not work.done():
                job.stop()
            if not single:
                panel.untag_paths(done)
            panel.reload()
            other.reload()

    async def on_open_with(self, event: OpenWith) -> bool:
        """File > *Open with*: the file at the cursor in one of the desktop's applications."""
        panel = self.active_panel
        entry = panel.selected
        shell = getattr(self.application, "shell", None)
        if entry is not None and not entry.is_dir and entry.name != ".." and shell is not None:
            self.spawn(shell.open_with(panel.entry_location(entry)))
        return True

    async def view_file(self, intern: bool) -> None:
        """DN's ``ViewFile(Intern, ...)``: F3 is *intern*, Alt+F3 is not.

        A directory, either key, is ``CountLen`` -- Alt+G's count, the tagged
        ones too -- but not in an archive, DN's ``dtArc`` test.  Alt+F3 is
        ``InternalView``: the viewer on the file as text, nothing asked.  F3
        is DN's order: a dBase, SQLite or CSV file its window (``XT =
        '.DBF'``), an archive into the panel (``ArcViewer``, whatever *Enter
        opens an archive* says), then what ``viewers.ini`` says (``DN.VWR``),
        then the viewer.  With *Internal viewer* off, F3 runs ``viewers.ini``
        and without an entry ``$PAGER`` -- a departure: DN fell back to its
        own viewer, there being no pager in DOS.
        """
        panel = self.active_panel
        entry = panel.selected
        if entry is None:
            return
        if entry.is_dir:
            if panel.location.outer is None:
                await self.count_length(panel)
            return
        if not intern:
            await self.view(plain=True)
            return
        if not SETTINGS.system.internal_viewer:
            if not await self._run_associated(VIEWERS):
                self.run_external("PAGER", "less")
            return
        if await asyncio.to_thread(self._has_window_of_its_own, panel, entry):
            await self.view()
            return
        if panel.archive_on_f3(entry):
            from navigator.widgets.drives.archives import enter_archive

            if await enter_archive(panel, panel.entry_location(entry)):
                return
        if await self._run_associated(VIEWERS):
            return
        await self.view()

    @staticmethod
    def _has_window_of_its_own(panel: Any, entry: Any) -> bool:
        """Whether F3 opens *entry* in the sheet or database window rather
        than the viewer: :meth:`view`'s tests, on a thread (an SQLite file on
        the disk is told by its first bytes)."""
        from navigator.lib.viewer.sqlite import is_database, is_sqlite
        from navigator.lib.viewer.table import is_table

        name = entry.name
        if is_table(name):
            return True
        if not panel.location.is_local and entry.directory is None:
            return name.lower().endswith(".dbf") or is_database(name)
        if name.lower().endswith(".dbf"):
            return True
        try:
            return is_database(name) and is_sqlite(entry.path_in(panel.path))
        except OSError:
            return False

    async def _run_associated(self, file_name: str, before: Any = None) -> bool:
        """What *file_name* has for the selected file, run; False if nothing.
        *before* (a local file only) is awaited once an entry is found, and
        a False from it runs nothing."""
        shell = getattr(self.application, "shell", None)
        panel = self.active_panel
        entry = panel.selected
        if shell is None or entry is None or entry.is_dir:
            return False
        if not panel.location.is_local and entry.directory is None:
            # ``UseFile`` first -- only if the file has something to run --
            # and the program run beside the copy.
            from navigator.lib.config import associations
            from navigator.lib.drives import usefile
            from navigator.widgets.drives.use_file import materialize

            try:
                groups = await asyncio.to_thread(associations.read, file_name)
            except (OSError, ValueError):
                return await shell.run_associated(file_name, entry.name)  # says why
            if associations.for_file(groups, entry.name) is None:
                return False
            use = await materialize(self.application, [panel.entry_location(entry)])
            if use is None:
                return True
            if not await shell.run_associated(file_name, entry.name, cwd=use.directory, uses=[use]):
                await asyncio.to_thread(usefile.discard, use)
            return True
        return await shell.run_associated(file_name, entry.name, before=before)

    async def _view_sheet(self, desktop: Any, place: Any) -> bool:
        """F3 on a CSV or TSV, or *As Spreadsheet*: DN's ``XT = '.WKZ'`` --
        the database window, on a copy for a file on another drive.  False
        when it could not be read so, for the text viewer to try (and to say
        why, or offer *As root*)."""
        from navigator.widgets.viewer.db_window.db_window import open_csv

        if isinstance(place, Path):
            try:
                await open_csv(desktop, place)
            except OSError:
                return False
            return True
        from navigator.lib.drives import usefile
        from navigator.widgets.drives.use_file import materialize

        use = await materialize(self.application, [place])
        if use is None:
            return True
        try:
            window = await open_csv(desktop, use.local_for(place))
        except OSError:
            await asyncio.to_thread(usefile.discard, use)
            return False
        window.use_set = use
        window.place = str(place)
        return True

    async def view(self, mode: str | None = None, *, plain: bool = False) -> None:
        """Open the selected file in a viewer on this window's desktop.

        A directory is passed over here: F3 counted it already
        (:meth:`view_file`).  *plain* is Alt+F3's ``InternalView``: the
        viewer, never the sheet or database window nor the structured tree.
        A file that will not open is said so, as a directory that will not be
        made is.
        """
        panel = self.active_panel
        entry = panel.selected
        desktop = self.desktop
        if entry is None or entry.is_dir or desktop is None:
            return
        from navigator.lib.viewer.table import is_table

        if not plain and (mode == "sheet" or (mode is None and is_table(entry.name))):
            local = panel.location.is_local or entry.directory is not None
            place = entry.path_in(panel.path) if local else panel.entry_location(entry)
            if await self._view_sheet(desktop, place):
                return
            mode = None
        if not panel.location.is_local and entry.directory is None:
            from navigator.lib.viewer.dbf import DBFError
            from navigator.widgets.drives.use_file import database_elsewhere, view_elsewhere

            origin = panel.entry_location(entry)
            try:
                from navigator.lib.viewer.sqlite import is_database

                if mode == "database" or (mode is None and not plain and (origin.name.lower().endswith(".dbf")
                                                            or is_database(origin.name))):
                    try:
                        await database_elsewhere(desktop, origin)
                        return
                    except DBFError:
                        if mode == "database":
                            await Dialog(title=tr("Cannot view file"),
                                         prompt=tr("{name}: not a dBase or SQLite file").format(name=entry.name),
                                         buttons="ok").execute(self.application)
                            return
                    mode = None
                await view_elsewhere(desktop, origin, mode)
            except OSError as error:
                await Dialog(title=tr("Cannot view file"), prompt=f"{entry.name}: {error.strerror or error}",
                             buttons="ok").execute(self.application)
            return
        path = entry.path_in(panel.path)
        from navigator.lib.viewer.sqlite import is_database, is_sqlite

        if mode == "database" or (mode is None and not plain and (path.suffix.lower() == ".dbf"
                                                    or (is_database(path.name) and is_sqlite(path)))):
            # ``ViewFile``'s ``XT = '.DBF'``, and *As DataBase*: the dBase
            # viewer -- F3 on a ``.dbf`` that is not one falls back to text.
            from navigator.lib.viewer.dbf import DBFError
            from navigator.widgets.viewer.db_window.db_window import open_database

            try:
                await open_database(desktop, path)
                return
            except DBFError:
                if mode == "database":
                    await Dialog(title=tr("Cannot view file"),
                                 prompt=tr("{name}: not a dBase or SQLite file").format(name=entry.name),
                                 buttons="ok").execute(self.application)
                    return
            except OSError as error:
                message = f"{entry.name}: {error.strerror or error}"
                # Refused permission: *As root*, on a copy fetched through the
                # helper (a departure; :mod:`navigator.lib.system.elevate`).
                if await self._may_as_root(error, message):
                    from navigator.widgets.file_ops.as_root import database_as_root

                    try:
                        await database_as_root(desktop, path)
                    except DBFError:
                        await Dialog(title=tr("Cannot view file"),
                                     prompt=tr("{name}: not a dBase or SQLite file").format(name=entry.name),
                                     buttons="ok").execute(self.application)
                    except OSError as again:
                        await Dialog(title=tr("Cannot view file"),
                                     prompt=f"{entry.name}: {again.strerror or again}",
                                     buttons="ok").execute(self.application)
                    return
                if not self._as_root_declined:
                    await Dialog(title=tr("Cannot view file"), prompt=message,
                                 buttons="ok").execute(self.application)
                return
            mode = None
        try:
            window = await open_viewer(desktop, path, mode)
            if window is not None and mode is None and not plain and SETTINGS.viewer.render_structured \
                    and window.shows_tree():
                # ``[viewer] render_structured``: the data as a tree straight
                # away, as F3 shows a CSV as a spreadsheet (a departure).
                await window.as_tree()
        except OSError as error:
            from navigator.lib.system.elevate import ELEVATION, refused

            message = f"{entry.name}: {error.strerror or error}"
            # Refused permission: *As root* (a departure;
            # :mod:`navigator.lib.system.elevate`), read through the helper.
            if refused(error) and await asyncio.to_thread(ELEVATION.available):
                from navigator.widgets.file_ops.as_root import ask_as_root, view_as_root

                if await ask_as_root(self.application, message):
                    try:
                        await view_as_root(desktop, path, mode)
                    except OSError as again:
                        await Dialog(title=tr("Cannot view file"),
                                     prompt=f"{entry.name}: {again.strerror or again}",
                                     buttons="ok").execute(self.application)
                return
            await Dialog(
                title=tr("Cannot view file"),
                prompt=message,
                buttons="ok",
            ).execute(self.application)

    async def on_edit(self, event: Edit) -> bool:
        """F4: ``cmEditFile``, the selected file in an editor window.

        Or, with *Internal editor* off in System Setup, what ``editors.ini``
        (Options > Editors) says for it, else ``$EDITOR`` on the console
        (:meth:`edit_file`).
        """
        if self.info.focus_within:
            self.spawn(self.edit_info_file())
        else:
            self.spawn(self.edit_file(True))
        return True

    async def edit_info_file(self) -> None:
        """F4 in the information panel: ``TDiskInfo``'s *Edit DirInfo* -- the
        ``DirInfo`` or ``File_ID.DIZ`` it shows, in the editor; the panel reads
        it again once saved (``cmRereadInfo`` from ``FileChanged``)."""
        from navigator.lib.config.file_history import open_editor

        path = self.info.info_path
        if path is None or self.parent is None:
            return
        try:
            await open_editor(self.parent, path)
        except OSError as error:
            await Dialog(title=tr("Cannot edit file"), prompt=f"{path.name}: {error.strerror or error}",
                         buttons="ok").execute(self.application)

    async def edit_file(self, intern: bool) -> None:
        """DN's ``EditFile(Intern, ...)``, as :meth:`view_file` for the viewer:
        ``editors.ini`` (DN's ``DN.EDT``) for the key that disagrees with
        *Internal editor*, falling back to ``$EDITOR`` for F4 and, for Alt+F4,
        the editor window if F4 runs ``$EDITOR`` -- else a box of the console
        editors installed, each run in a window of its own.  A departure:
        DN's Alt+F4 fell back to the editor window there too, which is F4.

        Another: with *Internal editor* off and nothing in ``editors.ini``, F4
        runs ``$EDITOR``, where DN fell back to its own editor -- on POSIX that
        is the external editor, and turning the setting off is how it is asked for.

        A directory under the cursor, F4 or Alt+F4, is Attributes for it alone,
        as ``isSelDir`` sent ``cmEditFile`` to ``CM_SetAttributes`` (``FLPANELX.PAS:1486``);
        ``..`` is passed over (DN's box on the parent, from inside it).
        """
        entry = self.active_panel.selected
        if entry is not None and entry.is_dir:
            if entry.name != "..":
                await self.change_attributes(entries=[entry])
            return
        if intern == SETTINGS.system.internal_editor:
            await self.edit()
        elif await self._run_associated(EDITORS, before=self._save_before_external):
            return
        elif intern:
            if await self._save_before_external():
                self.run_external("EDITOR", "vi")
        elif SETTINGS.system.internal_editor:
            await self.console_editor()
        else:
            await self.edit()

    async def _save_before_external(self) -> bool:
        """The selected file about to be edited outside: a changed editor window
        on it asks to save first (:func:`~navigator.widgets.editor.external.save_before_external`);
        False is Cancel.  A file on another drive is not asked about."""
        from navigator.widgets.editor.external import save_before_external

        panel = self.active_panel
        entry = panel.selected
        if entry is None or entry.is_dir or (not panel.location.is_local and entry.directory is None):
            return True
        return await save_before_external(self.application, [entry.path_in(panel.path)])

    async def console_editor(self) -> None:
        """Alt+F4 with nothing in ``editors.ini``: a box of the console editors
        installed (:mod:`navigator.lib.editor.console_editors`) and *Internal
        editor*, the one chosen run on the file in a window of its own
        (``TerminalWindow``).  A file on another drive is fetched first and
        offered back up once the window is closed.  With none installed it
        is the editor window, as before."""
        from navigator.lib.config.associations import Action
        from navigator.lib.config.usermenu import Commands
        from navigator.lib.editor import console_editors

        shell = getattr(self.application, "shell", None)
        panel = self.active_panel
        entry = panel.selected
        if shell is None or entry is None or entry.is_dir:
            await self.edit()
            return
        found = await asyncio.to_thread(console_editors.installed)
        if not found:
            await self.edit()
            return
        internal = Action(tr("~I~nternal editor"), Commands([]))
        action = await shell.choose_action([*console_editors.actions(found), internal],
                                           title=tr("Choose editor"))
        if action is None:
            return
        if action is internal:
            await self.edit()
            return
        if panel.location.is_local or entry.directory is not None:
            if await self._save_before_external():
                await shell.run_commands(action.commands)
            return
        from navigator.widgets.drives.use_file import materialize

        use = await materialize(self.application, [panel.entry_location(entry)])
        if use is not None:
            await shell.run_commands(action.commands, cwd=use.directory, uses=[use])

    def run_external(self, variable: str, fallback: str, path: Path | None = None) -> None:
        """Run the program ``$variable`` names (or *fallback*) on *path*, else the selected file.

        As though it had been typed on the command line, so it runs on the
        console with the keyboard, and the panels look again when it is done.
        """
        shell = getattr(self.application, "shell", None)
        program = os.environ.get(variable, "").strip() or fallback
        if path is None:
            panel = self.active_panel
            entry = panel.selected
            if entry is None or entry.is_dir:
                return
            if not panel.location.is_local and entry.directory is None:
                if shell is not None:
                    self.spawn(self._run_external_elsewhere(shell, program, panel.entry_location(entry)))
                return
            path = entry.path_in(panel.path)
        if shell is None:
            return
        shell.run_command(f"{program} {shlex.quote(str(path))}")

    async def _run_external_elsewhere(self, shell: Any, program: str, origin: Location) -> None:
        """``$PAGER`` or ``$EDITOR`` on a file on another drive: on its
        fetched copy, offered back once the program is done."""
        from navigator.widgets.drives.use_file import materialize

        use = await materialize(self.application, [origin])
        if use is not None:
            local = use.local_for(origin)
            shell.run_command(f"{program} {shlex.quote(str(local))}", cwd=use.directory, uses=[use])

    async def edit_named(self) -> None:
        """Shift+F4, *Edit...*: DN's ``OpenEditor`` (``MICROED.PAS:1284``) -- the name
        asked in the file dialog *Open a File*, with *~O~pen*, in the history the
        editor's F3 shares (``hsEditOpen``, ``edit_open``), listing the active
        panel's directory; that file edited, which saving creates if it is new.

        The dialog lists a directory typed rather than answering it and refuses
        a name whose directory does not exist; a URL or an archive place is
        taken as typed and reaches its drive (:meth:`_edit_named_elsewhere`).

        Departures: with *Internal editor* off the name goes to ``$EDITOR``, as
        F4's file does, where ``OpenEditor`` always used its own editor; and the
        file's edit record is brought back, where DN opened on the whole desktop
        at the top.  With the active panel on another drive the box lists
        nothing (``unlisted``) and a name typed is that panel's.
        """
        from navml.widgets.dialog.file_dialog import FileDialog

        from navigator.lib.drives.root import on_disk

        panel = self.active_panel
        here = on_disk(panel.location)
        remote = here is None or not here.is_local
        dialog = FileDialog(title=tr("Open a File"), label=tr("~N~ame"), ok_text=tr("~O~pen"),
                            history_id="edit_open", directory=self._disk_directory(),
                            hidden=SETTINGS.system.show_hidden,
                            unlisted=str(panel.location) if remote else None)
        if not remote:
            # A URL, or a place in an archive, goes as typed: to that drive.
            # (Unlisted, every name already does.)
            dialog.raw = lambda text: "://" in text or "#/" in text
        name = await dialog.execute(self.application)
        if not name:
            return
        from navigator.lib.file_ops.filecopy import target_location

        place = target_location(name, panel.location)
        if not place.is_local:
            await self._edit_named_elsewhere(name, place)
            return
        path = place.local
        problem = None
        if path.is_dir():
            problem = tr("Is a directory")
        elif not path.parent.is_dir():
            problem = tr("No such directory")
        if problem is None and not SETTINGS.system.internal_editor:
            from navigator.widgets.editor.external import save_before_external

            if await save_before_external(self.application, [path]):
                self.run_external("EDITOR", "vi", path)
            return
        desktop = self.desktop
        if problem is None and desktop is not None:
            try:
                await open_editor(desktop, path, new=True)
                return
            except OSError as error:
                problem = error.strerror or str(error)
        if problem is not None:
            await Dialog(
                title=tr("Cannot edit file"),
                prompt=f"{name}: {problem}",
                buttons="ok",
            ).execute(self.application)

    def _disk_directory(self) -> Path:
        """Where a file dialog opened from the panels starts: the active panel's
        directory if it is on the disk, else the passive one's, else home --
        the box browses the disk alone (``EditWindow._start_directory``'s rule)."""
        from navigator.lib.drives.root import on_disk

        for side in (self.active_panel, self.passive_panel):
            place = on_disk(side.location) if side is not None else None
            if place is not None and place.is_local:
                return place.local
        return Path.home()

    async def _edit_named_elsewhere(self, name: str, place: Location) -> None:
        """Shift+F4 on a name on another drive: connected to (or the archive
        opened) first, then fetched and edited -- or, not there yet, an empty
        file F2 makes there.  ``$EDITOR`` gets the fetched copy."""
        from navigator.widgets.drives.use_file import edit_elsewhere

        app = self.application
        reach = getattr(getattr(app, "shell", None), "reach", None)
        if reach is None or not await reach(place):
            return

        def look() -> tuple[str | None, bool]:
            drive = drive_of(place)
            if drive.is_dir(place):
                return tr("Is a directory"), False
            if not drive.is_dir(place.parent):
                return tr("No such directory"), False
            return None, drive.lexists(place)

        try:
            problem, there = await asyncio.to_thread(look)
        except OSError as error:
            problem, there = error.strerror or str(error), False
        if problem is None and not SETTINGS.system.internal_editor:
            shell = getattr(app, "shell", None)
            if shell is not None:
                if there:
                    program = os.environ.get("EDITOR", "").strip() or "vi"
                    await self._run_external_elsewhere(shell, program, place)
                    return
                problem = tr("$EDITOR edits a file on another drive only once it is there")
        if problem is None and self.desktop is not None:
            try:
                await edit_elsewhere(self.desktop, place, new=not there)
                return
            except OSError as error:
                problem = error.strerror or str(error)
        if problem is not None:
            await Dialog(title=tr("Cannot edit file"), prompt=f"{name}: {problem}", buttons="ok").execute(app)

    async def edit(self) -> None:
        """Open the selected file in an editor on this window's desktop.

        A directory is :meth:`edit_file`'s; one that will not open is said so --
        but one gone since the panel listed it is an empty text under its name,
        which saving creates, as DN's ``ReadBlock`` took DOS errors 2 and 3
        (``MICROED.PAS:3436``).
        """
        panel = self.active_panel
        entry = panel.selected
        desktop = self.desktop
        if entry is None or entry.is_dir or desktop is None:
            return
        if not panel.location.is_local and entry.directory is None:
            from navigator.widgets.drives.use_file import edit_elsewhere

            try:
                await edit_elsewhere(desktop, panel.entry_location(entry))
            except OSError as error:
                await Dialog(title=tr("Cannot edit file"), prompt=f"{entry.name}: {error.strerror or error}",
                             buttons="ok").execute(self.application)
            return
        path = entry.path_in(panel.path)
        try:
            try:
                await open_editor(desktop, path)
            except FileNotFoundError:
                if not path.parent.is_dir():
                    raise
                await open_editor(desktop, path, new=True)
        except OSError as error:
            message = f"{entry.name}: {error.strerror or error}"
            # Refused permission: *As root* (a departure;
            # :mod:`navigator.lib.system.elevate`) -- read through the helper.
            if await self._may_as_root(error, message):
                try:
                    await open_editor(desktop, path, as_root=True)
                except OSError as again:
                    await Dialog(title=tr("Cannot edit file"), prompt=f"{entry.name}: {again.strerror or again}",
                                 buttons="ok").execute(self.application)
                return
            if self._as_root_declined:
                return
            await Dialog(
                title=tr("Cannot edit file"),
                prompt=message,
                buttons="ok",
            ).execute(self.application)

    @staticmethod
    async def _release_if(used: bool) -> None:
        """Root's helper let go as ``root_timeout`` says, if *used* -- the end
        of an operation that answered *As root* part way."""
        if used:
            from navigator.lib.system.elevate import ELEVATION

            await asyncio.to_thread(ELEVATION.release)

    async def _may_as_root(self, error: OSError, message: str) -> bool:
        """For a local step refused permission: *As root* asked, True once the
        helper runs.  False -- and :attr:`_as_root_declined` set if the user
        said Cancel to it -- where it may not be offered or was not wanted."""
        from navigator.lib.system.elevate import ELEVATION, refused

        self._as_root_declined = False
        if not refused(error) or not await asyncio.to_thread(ELEVATION.available):
            return False
        from navigator.widgets.file_ops.as_root import ask_as_root

        if await ask_as_root(self.application, message):
            return True
        self._as_root_declined = True
        return False
