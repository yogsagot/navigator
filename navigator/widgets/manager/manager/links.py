"""Symbolic and hard links (Shift+F5), and changing them: Show hard links, broken links,
bad names, Edit link target, relative/absolute.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.panel import Panel
from navigator.lib.drives import DriveGone, Location, drive_of
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Links(_Base):
    """Symbolic and hard links (Shift+F5), and changing them: Show hard links, broken links,"""

    # -- symbolic links ----------------------------------------------------------

    async def make_links(self) -> None:
        """Ask where, link each entry there, and let both panels look again.

        ``copy_files``'s shape without the worker: the target is read as
        Copy's is, a directory that is not there yet is offered as Copy
        offers it, and a link that cannot be made puts Copy's *Skip* /
        *Cancel*.  What was linked is untagged.
        """
        panel, other = self.active_panel, self.passive_panel
        entries = self.selection(panel)
        if entries:
            await self.link_entries(panel, entries, self._push_first_name(other), others=(other,))

    async def link_entries(self, panel: Panel, entries: list[Any], target: Path | None, *,
                           relative: bool | None = None, others: tuple[Any, ...] = (),
                           ask: bool = True) -> None:
        """Links to *entries* of *panel* made in *target*: the Create symlink
        dialog first when *ask* (its *Relative link* box ticked as *relative*
        says, or as the session left it for None), else at once; then *panel*
        and *others* look again, one showing where the links went with its
        cursor on the first made, as F7's is on its directory."""
        from navml.widgets.dialog.control import escape_caption

        from navigator.lib.file_ops import filecopy, filelink
        from navigator.widgets.file_ops.link_dialog import LinkDialog

        app = self.application
        if app is None or not entries:
            return
        here = panel.location
        if ask:
            try:
                can_hard = drive_of(here).can("hardlink")
            except DriveGone:
                can_hard = False
            request = await LinkDialog(
                entries=entries, here=here, other=target, hidden=panel.show_hidden, relative=relative,
                can_hard=can_hard,
            ).execute(app)
        else:
            request = filelink.LinkRequest(
                sources=[shown(panel.entry_location(entry)) for entry in entries],
                target=str(target).rstrip("/") + "/",
                relative=bool(relative),
            )
        if request is None:
            return
        from navigator.lib.system.elevate import ELEVATION, refused

        # On another drive every step is a round trip: on a thread.  So is
        # every step once *As root* was answered: each is the helper's.
        elsewhere = not here.is_local or "://" in request.target or "#/" in request.target
        as_root = False

        async def step(function: Any, *args: Any) -> Any:
            if elsewhere or as_root:
                return await asyncio.to_thread(function, *args)
            return function(*args)

        def drive_or_root(place: Location) -> Any:
            if as_root and place.is_local:
                from navigator.lib.drives.root import ROOT_DRIVE

                return ROOT_DRIVE
            return drive_of(place)

        async def failed(error: OSError) -> Any:
            """Skip / Cancel, and *As root* for a local refusal not yet root's."""
            nonlocal as_root
            answer = await self._ask_skip(filecopy.error_message(error),
                                          elevate=not elsewhere and not as_root and refused(error))
            if answer == filecopy.AS_ROOT:
                as_root = True
            return answer

        destination = await step(filecopy.resolve_target, request.target, request.sources, shown(here))
        linked: set[Any] = set()
        first: Location | None = None  # the first link made
        try:
            if destination.create:
                if SETTINGS.confirmations.create_dir and await self._ask_yes_no(
                    tr("Would you like to create directory {path}?").format(
                        path=escape_caption(str(destination.directory)))
                ) is not True:
                    return
                place = Location.of(destination.directory)
                while True:
                    try:
                        await step(lambda: drive_or_root(place).makedirs(place))
                        break
                    except OSError as error:
                        if await failed(error) != filecopy.AS_ROOT:
                            return
            for source in request.sources:
                while True:
                    try:
                        await step(filelink.make_link, source, destination.path_for(source),
                                   request.relative, as_root, request.hard)
                    except OSError as error:
                        answer = await failed(error)
                        if answer == filecopy.AS_ROOT:
                            continue
                        if not answer:
                            return
                        break
                    linked.add(source)
                    if first is None:
                        first = Location.of(destination.path_for(source))
                    break
        finally:
            if as_root:
                await asyncio.to_thread(ELEVATION.release)
            panel.untag_paths(linked)
            for each in (panel, *others):
                there = first is not None and each.found is None and Location.of(each.location) == first.parent
                each.reload(key=first.name if there else None)

    # -- changing links ----------------------------------------------------------

    def selected_links(self, panel: Panel) -> list[Any]:
        """The symbolic links in :meth:`selection`: what File > Symlink's
        *Edit link target*, *Make relative* and *Make absolute* change."""
        return [entry for entry in self.selection(panel) if entry.is_link]

    async def show_hard_links(self, panel: Panel) -> None:
        """Every name of the file at *panel*'s cursor, found on its file
        system on a thread (:func:`navigator.lib.file_ops.hardlinks.find_names`)
        and shown in *panel* as a *Links:* listing, the file's own name first
        and the cursor on it.  Fewer found than the file has (an unreadable
        directory, another mount) is said in a toast.  A departure, asked for."""
        from navml.widgets.dialog.control import escape_caption

        from navigator.lib.file_ops import filecopy
        from navigator.lib.file_ops.filefind import FindListing
        from navigator.lib.file_ops.hardlinks import HardLinksJob, find_names
        from navigator.lib.system.job import Stopped
        from navigator.widgets.manager.find_progress import FindProgress
        from navigator.widgets.manager.panel.panel import entry_at

        app = self.application
        entry = panel.selected
        if app is None or entry is None or entry.name == ".." or panel.found is not None \
                or not panel.location.is_local:
            return
        here = Path(panel.path)
        path = Path(entry.path_in(here))
        job = HardLinksJob()

        def work() -> tuple[list[Any], int]:
            names = find_names(path, job)
            entries = [found for found in (entry_at(name, name.parent) for name in names.paths)
                       if found is not None]
            return entries, names.count

        def make_box() -> Any:
            box = FindProgress()
            box.title = tr("Find hard links")
            return box

        def refresh(box: Any) -> None:
            box.directory = job.directory
            box.count = len(job.found)

        async def no_questions(question: Any) -> None:
            return None

        running = asyncio.ensure_future(asyncio.to_thread(work))
        try:
            await self._watch_job(running, job, make_box, refresh, no_questions,
                                  abort=tr("Cancel search?"))
            entries, count = await running
        except Stopped:
            return
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=escape_caption(filecopy.error_message(error)),
                         buttons="ok").execute(app)
            return
        finally:
            if not running.done():
                job.stop()
        if job.stopped or panel.location != Location.of(here) or panel.found is not None:
            return  # stopped, or the panel went elsewhere meanwhile
        panel.show_found(FindListing(tr("Links: {name}").format(name=entry.name), here, entries,
                                     return_to=entry.name, keep_order=True), at=entry.name)
        panel.focus()
        toast = getattr(getattr(app, "root", None), "toast", None)
        if len(entries) < count and toast is not None and app.is_running:
            toast(tr("{found} of {count} names found").format(found=len(entries), count=count),
                  title=tr("Links: {name}").format(name=entry.name))

    def select_broken_links(self, panel: Panel) -> None:
        """Tag every link in *panel* that points nowhere, beside the tags there."""
        keys = {entry.key for entry in panel.items if entry.is_stale_link}
        if keys - panel.marked:
            panel.marked = panel.marked | keys

    @staticmethod
    def bad_names(panel: Panel) -> set[Any]:
        """The keys of *panel*'s entries Multi-rename's *Clean up names* would
        change: a name wrong on its own, or one differing from another in its
        directory only by case (a listing's entries each in their own)."""
        from navigator.lib.file_ops import multirename

        entries = [entry for entry in panel.items if entry.name != ".."]
        keys = {entry.key for entry in entries if multirename.faults(entry.name)}
        groups: dict[Any, list[Any]] = {}
        for entry in entries:
            groups.setdefault(entry.directory, []).append(entry)
        for group in groups.values():
            clashing = multirename.case_clashes(entry.name for entry in group)
            keys |= {entry.key for entry in group if entry.name in clashing}
        return keys

    def select_bad_names(self, panel: Panel) -> None:
        """Tag every bad name in *panel* (:meth:`bad_names`), beside the tags there."""
        keys = self.bad_names(panel)
        if keys - panel.marked:
            panel.marked = panel.marked | keys

    async def edit_link_targets(self) -> None:
        """One link: its target in a line (``LinkTargetDialog``).  Several:
        one replacement in all their targets, seen first (``RelinkDialog``).
        Then each is changed by :func:`filelink.retarget`."""
        from navigator.lib.file_ops import filelink
        from navigator.widgets.file_ops.link_target_dialog import LinkTargetDialog
        from navigator.widgets.file_ops.relink_dialog import RelinkDialog

        app = self.application
        panel = self.active_panel
        entries = self.selected_links(panel)
        if app is None or not entries:
            return
        links = [(panel.entry_location(entry), entry.link_target or "") for entry in entries]
        if len(links) == 1:
            link, target = links[0]
            try:
                base = await asyncio.to_thread(filelink.link_base, panel.drive, link)
            except (OSError, DriveGone):
                base = str(link.parent.path)
            answer = await LinkTargetDialog(name=link.name, target=target, base=base).execute(app)
            if answer is None or answer == target:
                return
            changes = [(link, answer)]
        else:
            rows = await RelinkDialog(links=links).execute(app)
            if not rows:
                return
            changes = [(row.link, row.new) for row in rows if not row.problem]
        await self._retarget(panel, changes)

    async def switch_links(self, *, relative: bool) -> None:
        """*Make relative* / *Make absolute*: each selected link rewritten to
        reach the same file (:func:`filelink.switched`), no question asked.
        One already so is left alone; one whose rewritten target would reach
        another file is skipped, and the skipped are said in one box."""
        from navml.widgets.dialog.control import escape_caption

        from navigator.lib.file_ops import filecopy, filelink

        panel = self.active_panel
        entries = self.selected_links(panel)
        if self.application is None or not entries:
            return
        try:
            drive = panel.drive
        except DriveGone:
            return
        changes, already, skipped = [], [], []
        for entry in entries:
            link = panel.entry_location(entry)
            try:
                target = await asyncio.to_thread(filelink.switched, drive, link, relative)
            except filelink.NotTheSame:
                skipped.append((link.name, tr("a link on the way would lead elsewhere")))
                continue
            except OSError as error:
                skipped.append((link.name, filecopy.error_message(error)))
                continue
            if target is None:
                already.append(link)
            else:
                changes.append((link, target))
        await self._retarget(panel, changes, already=already)
        if skipped:
            lines = [escape_caption(f"{name}: {reason}") for name, reason in skipped[:8]]
            if len(skipped) > 8:
                lines.append(tr_n("and {n} more", "and {n} more", len(skipped) - 8))
            prompt = tr_n("{n} link was left as it was:", "{n} links were left as they were:", len(skipped))
            await Dialog(title=tr("Error"), prompt=prompt + "\n" + "\n".join(lines),
                         buttons="ok").execute(self.application)

    async def _retarget(self, panel: Panel, changes: list[tuple[Location, str]], *,
                        already: Sequence[Location] = ()) -> None:
        """Each ``(link, target)`` of *changes* made so, on a thread, a
        failure put as Copy's *Skip* / *Cancel* (and *As root* for a local
        refusal); then the changed and the *already* right untagged, and
        both panels re-read."""
        from navigator.lib.file_ops import filecopy, filelink
        from navigator.lib.system.elevate import ELEVATION, refused

        as_root = False
        changed: list[Location] = list(already)
        try:
            for link, target in changes:
                while True:
                    if as_root and link.is_local:
                        from navigator.lib.drives.root import ROOT_DRIVE

                        drive = ROOT_DRIVE
                    else:
                        drive = drive_of(link)
                    try:
                        await asyncio.to_thread(filelink.retarget, drive, link, target)
                    except OSError as error:
                        answer = await self._ask_skip(filecopy.error_message(error),
                                                      elevate=link.is_local and not as_root and refused(error))
                        if answer == filecopy.AS_ROOT:
                            as_root = True
                            continue
                        if not answer:
                            return
                        break
                    changed.append(link)
                    break
        finally:
            if as_root:
                await asyncio.to_thread(ELEVATION.release)
            finished = set(changed)
            panel.untag(entry for entry in panel.items if panel.entry_location(entry) in finished)
            panel.reload()
            self.passive_panel.reload()
