"""File > Encoding: UU encode and decode, split/combine, checksums, encryption, convert text.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from navkit.i18n import tr, tr_n

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.panel import Panel
from navigator.widgets.tree.directory_tree.directory_tree import reread_trees
from navigator.lib.drives import Location, drive_of
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Encoding(_Base):
    """File > Encoding: UU encode and decode, split/combine, checksums, encryption, convert text."""

    # -- UU Encode and UU Decode (navigator.lib.file_ops.uucode) ---------------------------------

    async def uu_encode(self, panel: Panel) -> None:
        """Ctrl+F7: ``UuEncode`` -- *UU Encode* asks where and how, and the
        file at the cursor is encoded on a thread, into one file a section."""
        from navigator.lib.file_ops import uucode
        from navigator.widgets.file_ops.uu_encode_dialog import UUEncodeDialog

        app = self.application
        place = self._uu_place(panel)
        if app is None or place is None:
            return
        source = place.local if place.is_local else Path(place.name)
        answer = await UUEncodeDialog(source=source, other=self._uu_other(panel),
                                      hidden=panel.show_hidden).execute(app)
        if answer is None:
            return
        self._keep_uucode(answer["uucode"])
        section = SETTINGS.uucode

        def request_for(local: Path, target: str) -> Any:
            return uucode.EncodeRequest(
                local, target, file_time=section.file_time, map_table=section.map_table,
                statistics=section.statistics, checksum=section.checksum,
                lines=section.lines_per_section, crlf=section.line_ends == "crlf",
            )

        notice = tr("Encoding {name}").format(name=place.name)
        target = answer["target"]

        def as_root(job: Any, local: Path, staging: Path) -> Any:
            """Encoded from a copy read as root into the staging directory,
            then put where it was asked through the helper."""
            from navigator.lib.file_ops.filecopy import target_location

            dest = target_location(target, place.parent)
            if dest.is_local and (target.endswith("/") or dest.local.is_dir()):
                return uucode.encode(request_for(local, str(staging) + "/"), job, staging), dest
            return uucode.encode(request_for(local, str(staging / dest.name)), job, staging), dest.parent

        rooted = self._staged(place, as_root, uucode.ask_over_encoded, as_root=True)
        if place.is_local and "://" not in target and "#/" not in target:
            request = request_for(source, target)
            await self._run_uucode(panel, lambda job: uucode.encode(request, job, source.parent),
                                   notice, beep_after=20, as_root=rooted)
            return

        def elsewhere(job: Any, local: Path, staging: Path) -> Any:
            from navigator.lib.file_ops.filecopy import target_location

            dest = target_location(target, place.parent)
            if dest.is_local:
                return uucode.encode(request_for(local, str(dest.local)), job, dest.local.parent)
            return uucode.encode(request_for(local, str(staging / dest.name)), job, staging), dest.parent

        await self._run_uucode(panel, self._staged(place, elsewhere, uucode.ask_over_encoded),
                               notice, beep_after=20, as_root=rooted if place.is_local else None)

    async def uu_decode(self, panel: Panel) -> None:
        """Ctrl+F8: ``UuDecode`` -- *UU Decode* asks into which directory,
        and every file the one at the cursor holds is decoded on a thread."""
        from navigator.lib.file_ops import uucode
        from navigator.widgets.file_ops.uu_decode_dialog import UUDecodeDialog

        app = self.application
        place = self._uu_place(panel)
        if app is None or place is None:
            return
        answer = await UUDecodeDialog(here=place.parent.local if place.is_local else None,
                                      other=self._uu_other(panel), hidden=panel.show_hidden).execute(app)
        if answer is None:
            return
        self._keep_uucode(answer["uucode"])
        section = SETTINGS.uucode
        text = answer["target"].strip()

        def decode(local: Path, out: Path, job: Any) -> Any:
            return uucode.decode(local, out, job, check_existing=section.check_existing,
                                 display_errors=section.display_errors, save_broken=section.save_broken)

        notice = tr("Decoding {name}").format(name=place.name)

        def ask(existing: list[Location], job: Any) -> set[Location]:
            return uucode.ask_over_decoded(existing, job, section.check_existing)

        def as_root(job: Any, local: Path, staging: Path) -> Any:
            """Decoded from a copy read as root into the staging directory,
            the files then put there through the helper."""
            from navigator.lib.file_ops.filecopy import target_location

            out = target_location(text, place.parent) if text else place.parent
            result = uucode.decode(local, staging, job, check_existing=False,
                                   display_errors=section.display_errors, save_broken=section.save_broken)
            return result, out

        rooted = self._staged(place, as_root, ask, as_root=True)
        if place.is_local and "://" not in text and "#/" not in text:
            source = place.local
            expanded = os.path.expanduser(text)
            out = source.parent / expanded if expanded else source.parent
            await self._run_uucode(panel, lambda job: decode(source, out, job), notice, beep_after=5,
                                   as_root=rooted)
            return

        def elsewhere(job: Any, local: Path, staging: Path) -> Any:
            from navigator.lib.file_ops.filecopy import target_location

            out = target_location(text, place.parent) if text else place.parent
            if out.is_local:
                return decode(local, out.local, job)
            # Asked on the target's drive as the files go up, the staging
            # directory being empty.
            result = uucode.decode(local, staging, job, check_existing=False,
                                   display_errors=section.display_errors, save_broken=section.save_broken)
            return result, out

        await self._run_uucode(panel, self._staged(place, elsewhere, ask), notice, beep_after=5,
                               as_root=rooted if place.is_local else None)

    @staticmethod
    def _uu_place(panel: Panel) -> Location | None:
        entry = panel.selected
        if entry is None or entry.is_dir:
            return None
        return panel.entry_location(entry)

    @staticmethod
    def _staged(place: Location, work: Callable[[Any, Path, Path], Any],
                ask: Callable[[list[Location], Any], set[Location]] | None = None, *,
                as_root: bool = False) -> Callable[[Any], Any]:
        """UU on another drive -- or into one: *place* fetched, *work* run on
        the copy with a staging directory for what it makes; when it answers
        ``(result, directory)`` the staged files go up into that directory on
        its drive, *ask(existing, job)* asked first of those there already
        (``usefile.put_files``).  The copy and the staging go after.

        *as_root* (a departure; :mod:`navigator.lib.system.elevate`): a local
        *place* is fetched, and the staged files put on the disk, through the
        root helper, which is let go of after."""
        def run(job: Any) -> Any:
            drive = None
            if as_root:
                from navigator.lib.drives.root import ROOT_DRIVE

                drive = ROOT_DRIVE
            try:
                return staged(job, drive)
            finally:
                if drive is not None:
                    drive.release()

        def staged(job: Any, drive: Any) -> Any:
            import tempfile

            from navigator.lib.drives import usefile

            if place.is_local and drive is None:
                use, local = None, place.local
            else:
                use = usefile.fetch([place], job, drive=drive if place.is_local else None)
                local = use.local_for(place)
            from navigator.lib.system.tempdir import private_dir

            staging = Path(tempfile.mkdtemp(dir=private_dir()))
            try:
                answer = work(job, local, staging)
                if isinstance(answer, tuple) and len(answer) == 2 and isinstance(answer[1], Location):
                    result, directory = answer
                    files = sorted(path for path in staging.iterdir() if path.is_file())
                    usefile.put_files(files, directory, job,
                                      None if ask is None else lambda existing: ask(existing, job),
                                      drive=drive if directory.is_local else None)
                    # What was written is where it went up, not the staging.
                    if isinstance(result, list):
                        return [directory / Path(path).name for path in result]
                    if isinstance(getattr(result, "written", None), list):
                        result.written = [directory / Path(path).name for path in result.written]
                    return result
                return answer
            finally:
                import shutil

                shutil.rmtree(staging, ignore_errors=True)
                if use is not None:
                    usefile.discard(use)
        return run

    def _uu_other(self, panel: Panel) -> Path | None:
        """``cmPushFirstName``: the other panel's directory, while it shows."""
        other = self.right if panel is self.left else self.left
        if not other.location.is_local:
            return None
        return Path(other.path) if other.visible and other.found is None else None

    def _keep_uucode(self, values: dict[str, Any]) -> None:
        """What the dialog was accepted with, kept for the next time and
        saved, as DN set ``ConfigModified`` when it changed."""
        self._keep_section("uucode", values, self.application)

    @staticmethod
    def _keep_section(name: str, values: dict[str, Any], app: Any = None) -> None:
        """*values* kept in the settings section *name* and saved, when they
        changed it -- a file that cannot be written said once, in a toast
        (``settings.save_or_say``), the values kept for the session."""
        from navigator.settings import save_or_say

        section = getattr(SETTINGS, name)
        changed = {key: value for key, value in values.items() if getattr(section, key) != value}
        if changed:
            section.update(changed)
            save_or_say(name, app)

    async def _run_uucode(self, panel: Panel, work_on: Callable[[Any], Any], notice: str,
                          beep_after: float, as_root: Callable[[Any], Any] | None = None) -> None:
        """*work_on(job)* on a thread under a box saying *notice*, its
        questions answered, its failure said, and the panels read again.
        *Beep after copy* rings for one that took longer than *beep_after*
        seconds, as DN's timer did.  A failure refused permission offers
        *As root*, and *as_root(job)* -- the same work through the helper --
        is run instead (a departure; :mod:`navigator.lib.system.elevate`).
        What was written -- a result that is a list of files (UU encode's)
        or has ``written`` (UU decode's, Split/combine's) -- puts the cursor
        of a panel showing the first one on it, as F5's on what it made."""
        from navigator.lib.file_ops import uucode
        from navigator.lib.system.job import Stopped
        from navigator.widgets.editor.loading import FileJob, progress_box, refresh_box

        app = self.application
        job = FileJob()
        job.cancellable = True
        started = asyncio.get_running_loop().time()
        work = asyncio.ensure_future(asyncio.to_thread(work_on, job))
        problem = None
        first: Location | None = None
        try:
            await self._watch_job(work, job, lambda: progress_box(job, notice), refresh_box(job),
                                  self._answer_uu_question)
            result = await work
            written = result if isinstance(result, list) else getattr(result, "written", None)
            if written:
                first = Location.of(written[0])
        except Stopped:
            pass
        except ValueError as error:
            problem = str(error)
            if problem == uucode.TOO_SMALL:
                problem = tr("The input file is too small to UU-Encode.")
        except OSError as error:
            where = f"{error.filename}: " if error.filename else ""
            problem = f"{where}{error.strerror or error}"
            if as_root is not None and await self._may_as_root(error, problem):
                await self._run_uucode(panel, as_root, notice, beep_after)
                return
            if as_root is not None and self._as_root_declined:
                problem = None
        finally:
            if not work.done():
                job.stop()
        for each in self.all_panels:
            there = first is not None and each.found is None and Location.of(each.location) == first.parent
            each.reload(key=first.name if there else None)
        if problem is not None:
            await Dialog(title=tr("Error"), prompt=problem, buttons="ok").execute(app)
        elif (not job.stopped and SETTINGS.file_manager.beep_after_copy
              and asyncio.get_running_loop().time() - started > beep_after):
            app.bell()

    async def _answer_uu_question(self, question: Any) -> Any:
        from navigator.lib.file_ops import uucode
        from navigator.widgets.file_ops.exists_query import ExistsQuery

        app = self.application
        if isinstance(question, uucode.FileExists):
            return await ExistsQuery(path=question.path).execute(app)
        if isinstance(question, uucode.DecodeError):
            await Dialog(title=tr("Error"), prompt=question.text, buttons="ok").execute(app)
        return None

    # -- Split/combine (navigator.lib.file_ops.splitfile): DN's cmPanelLongCopy --------------------

    async def split_combine(self, panel: Panel) -> None:
        """File > Split/combine: ``LongCopy`` -- the file at the cursor split
        into parts of the size asked, or, when it is a part or the set's
        ``.crc`` (DN's ``Tuda``), the set combined; on a thread either way."""
        from navigator.lib.file_ops import splitfile

        app = self.application
        place = self._uu_place(panel)
        if app is None or place is None:
            return
        siblings = {entry.name for entry in panel.items}
        other = self._uu_other(panel)
        here = place.parent.local if place.is_local else place.parent
        cwd = place.parent
        if splitfile.mode_for(place.name, siblings) == "combine":
            from navigator.widgets.file_ops.combine_dialog import CombineDialog

            answer = await CombineDialog(name=place.name, here=here, other=other,
                                         hidden=panel.show_hidden).execute(app)
            if answer is None:
                return
            combine = splitfile.CombineRequest(place, answer["target"], cwd)
            # A refusal on the disk offers *As root*, as UU's does.
            await self._run_uucode(panel, lambda job: splitfile.combine(combine, job),
                                   tr("Combining {name}").format(name=place.name), beep_after=20,
                                   as_root=(lambda job: splitfile.combine(combine, job, as_root=True))
                                   if place.is_local else None)
            reread_trees(app)  # DN's ``cmRereadTree`` (``FBB.PAS:553``)
            return
        from navigator.widgets.file_ops.split_dialog import SplitDialog

        answer = await SplitDialog(name=place.name, here=here, other=other,
                                   hidden=panel.show_hidden).execute(app)
        if answer is None:
            return
        self._keep_section("split", answer["split"], self.application)
        split = splitfile.SplitRequest(place, answer["target"], cwd, answer["size"],
                                       checksum=SETTINGS.split.checksum)
        await self._run_uucode(panel, lambda job: splitfile.split(split, job),
                               tr("Splitting {name}").format(name=place.name), beep_after=20,
                               as_root=(lambda job: splitfile.split(split, job, as_root=True))
                               if place.is_local else None)
        reread_trees(app)

    # -- Checksums (navigator.lib.file_ops.checksum): not DN's, a departure -------------------------

    async def calculate_checksums(self, panel: Panel) -> None:
        """File > Encoding > Checksums > Calculate: the tagged files' -- or the cursor's
        -- digests, a tagged directory's files to the bottom, written as
        ``sha256sum`` writes them: in one list, its names from the list's
        directory, or in ``name.<ext>`` beside each file.

        The files are read on a thread through their drives, under a box if
        it takes a while; Esc there stops it, keeping the lists of *Each
        file* already written.  A list already there is asked about first --
        *Append* adds to the one list -- and the entries done are untagged.
        """
        from navigator.lib.file_ops import checksum
        from navigator.lib.file_ops.filecopy import target_location
        from navigator.lib.system.job import Stopped
        from navigator.widgets.editor.edit_window.edit_window import FileSaved
        from navigator.widgets.file_ops.calculate_checksums_dialog import CalculateChecksumsDialog

        app = self.application
        entries = self.selection(panel)
        if app is None or not entries:
            return
        answer = await CalculateChecksumsDialog(directory_name=panel.location.name).execute(app)
        if answer is None:
            return
        self._keep_section("checksum", {"algorithm": answer["algorithm"], "mode": answer["mode"]},
                           self.application)
        algorithm = answer["algorithm"]
        sources = [panel.entry_location(entry) for entry in entries]
        job = checksum.ChecksumJob()
        title = tr("Calculating checksums")
        written: list[Location] = []
        try:
            if answer["mode"] == "combined":
                target = target_location(answer["name"], panel.location)
                appending = await self._ask_over_list(target)
                if appending is None:
                    return
                skip = target.normalized()

                def calculate() -> list[tuple[Location, str]]:
                    files = checksum.walk(sources, job, lambda location: location.normalized() == skip)
                    return checksum.calculate(files, algorithm, job)

                done = await self._run_checksums(calculate, job, title)
                if done:
                    lines = checksum.list_text(done, target.parent)

                    def write() -> None:
                        drive = drive_of(target)
                        with drive.open_write(target, append=appending) as file:
                            file.write("".join(f"{text}\n" for text in lines).encode("utf-8", "surrogateescape"))
                        drive.finish()

                    if not await self._write_list(write, target, lines, appending):
                        return
                    written.append(target)
            else:
                extension = checksum.EXTENSIONS[algorithm]

                def gather() -> tuple[list[tuple[Location, int]], int]:
                    files = checksum.walk(sources, job, lambda location: checksum.is_list_name(location.name))
                    there = 0
                    for location, _ in files:
                        listing = location.parent / (location.name + extension)
                        try:
                            there += drive_of(listing).lexists(listing)
                        except OSError:
                            pass
                    return files, there

                files, there = await self._run_checksums(gather, job, title)
                if there:
                    prompt = tr_n("{n} checksum file already exists.\nOK to overwrite it?",
                                  "{n} checksum files already exist.\nOK to overwrite them?", there)
                    if not await Dialog(title=tr("Warning"), prompt=prompt, buttons="yes-no").execute(app):
                        return
                written = await self._run_checksums(lambda: checksum.write_each(files, algorithm, job), job, title)

                async def as_root(refused: list[Any]) -> None:
                    again = [(location, size) for location, size, _ in refused]
                    written.extend(await self._run_checksums(
                        lambda: checksum.write_each(again, algorithm, job, as_root=True), job, title))

                await self._again_as_root(job, tr("Write their checksum files as root?"), as_root,
                                          errors=job.write_errors)
        except Stopped:
            return
        finally:
            # One per directory: each re-reads every panel showing it, the
            # cursor on the first list written there, as F5's on what it made.
            first: dict[Any, Location] = {}
            for location in written:
                first.setdefault(location.parent, location)
            for location in first.values():
                await self.emit(FileSaved(shown(location), land=True))
        self._untag_done(panel, entries, sources, job.errors + job.write_errors)
        if job.errors:
            await self._say_checksum_errors(job.errors)
        if job.write_errors:
            await self._say_checksum_errors(job.write_errors, tr_n(
                "{n} checksum file could not be written:", "{n} checksum files could not be written:",
                len(job.write_errors)))

    async def verify_checksums(self, panel: Panel) -> None:
        """File > Encoding > Checksums > Verify: every file the tagged lists name hashed
        again and checked, on a thread through its drive.

        The lists are the tagged files whose names say they are lists --
        ``.sha256sum``, ``SHA256SUMS``... -- else the tagged files or the
        cursor's, told by their digests' length.  The lists are untagged, the
        files that did not match tagged wherever a panel lists them, and the
        counts and those files shown (``ChecksumReport``).
        """
        from navigator.lib.file_ops import checksum
        from navigator.lib.system.job import Stopped
        from navigator.widgets.file_ops.checksum_report import ChecksumReport

        app = self.application
        files = [entry for entry in self.selection(panel) if not entry.is_dir]
        if app is None or not files:
            return
        named = [entry for entry in files if checksum.is_list_name(entry.name)]
        entries = named or files
        lists = [panel.entry_location(entry) for entry in entries]
        job = checksum.ChecksumJob()
        try:
            result = await self._run_checksums(lambda: checksum.verify(lists, job), job,
                                               tr("Verifying checksums"))
        except Stopped:
            return
        panel.untag(entries)
        bad = result.failed + [location for location, _ in result.unreadable]
        for each in self.all_panels:
            each.tag_paths(bad)
        await ChecksumReport(result=result).execute(app)

    async def _run_checksums(self, work: Callable[[], Any], job: Any, title: str) -> Any:
        """*work* on a thread, under the checksums box once it takes a while."""
        from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress
        from navigator.widgets.file_ops.checksum_progress import ChecksumProgress

        def refresh(box: Any) -> None:
            box.current = job.current
            box.position = job.position
            box.total = job.total
            box.files_done = job.files_done
            box.files_total = job.files_total

        return await run_with_progress(self.application, work, job, lambda: ChecksumProgress(title=title),
                                       refresh, delay=SLOW_PROGRESS_DELAY)

    async def _ask_over_list(self, target: Location) -> bool | None:
        """Whether a list file is appended to: False for a new one or *Yes*,
        True for *Append*, None for Cancel -- Alt+L's question."""
        def there() -> bool:
            try:
                return drive_of(target).lexists(target)
            except OSError:
                return False

        if not await asyncio.to_thread(there):
            return False
        query = Dialog(title=tr("Warning"),
                       prompt=tr("File {name}\nalready exists.\nOK to overwrite it?").format(name=target.name),
                       buttons="yes-no-cancel")
        query.no.text = tr("A~p~pend")
        reply = await query.execute(self.application)
        return None if reply is None else reply is False

    async def _say_checksum_errors(self, errors: list[tuple[str, str]], heading: str | None = None) -> None:
        """What could not be read, the first eight of it, as the archive test
        says its failures; *heading* in place of *N files could not be read:*."""
        from navml.widgets.dialog.control import escape_caption

        lines = [escape_caption(f"{name}: {reason}") for name, reason in errors[:8]]
        if len(errors) > 8:
            lines.append(tr_n("and {n} more", "and {n} more", len(errors) - 8))
        if heading is None:
            heading = tr_n("{n} file could not be read:", "{n} files could not be read:", len(errors))
        prompt = heading + "\n" + "\n".join(lines)
        await Dialog(title=tr("Error"), prompt=prompt, buttons="ok").execute(self.application)

    # -- Encryption (navigator.lib.file_ops.encrypt): not DN's, a departure ------------------------

    async def encrypt_files(self, panel: Panel) -> None:
        """File > Encoding > Encryption > Encrypt: the tagged files -- or the cursor's --
        a tagged directory's to the bottom, each encrypted beside itself by gpg
        or age, streamed through their drives on a thread.

        Targets already there are asked about first, in one question.  *Delete
        originals* removes each source whose encrypted copy was written in full;
        Esc in the box stops it, leaving no half-written file.  The entries done
        are untagged and the panels read again.
        """
        from navigator.lib.file_ops import encrypt
        from navigator.lib.system.job import Stopped
        from navigator.widgets.file_ops.encrypt_dialog import EncryptDialog

        app = self.application
        entries = self.selection(panel)
        if app is None or not entries:
            return
        answer = await EncryptDialog().execute(app)
        if answer is None:
            return
        kept = {key: answer[key] for key in ("tool", "method", "armor", "delete_originals")}
        if answer["method"] == "recipients":
            kept["recipients"] = " ".join(answer["recipients"])
        self._keep_section("encryption", kept, self.application)
        options = encrypt.Options(tool=answer["tool"], method=answer["method"], passphrase=answer["passphrase"],
                                  recipients=answer["recipients"], armor=answer["armor"])
        sources = [panel.entry_location(entry) for entry in entries]
        job = encrypt.EncryptJob()
        title = tr("Encrypting")
        try:
            def gather() -> tuple[list[Any], int]:
                plans = encrypt.plan_encrypt(sources, options, job)
                return plans, encrypt.existing_targets(plans)

            plans, there = await self._run_checksums(gather, job, title)
            if there and not await self._ask_over_targets(there):
                return
            done = await self._run_checksums(lambda: encrypt.encrypt(plans, options, job), job, title)

            async def as_root(refused: list[Any]) -> None:
                # The files the disk refused, encrypted again through the root helper.
                job.as_root = True
                again = [job.refused_plans[location] for location, _, _ in refused]
                done.extend(await self._run_checksums(lambda: encrypt.encrypt(again, options, job), job, title))

            await self._again_as_root(job, tr("Encrypt them as root?"), as_root)
            if answer["delete_originals"] and done:
                await self._run_checksums(lambda: encrypt.remove_originals(done, job), job, title)
        except Stopped:
            return
        finally:
            self._reload_landing(job.written[0] if job.written else None)
        self._untag_done(panel, entries, sources, job.errors)
        if job.errors:
            await self._say_checksum_errors(
                self._encryption_reasons(job.errors),
                tr_n("{n} file could not be encrypted:", "{n} files could not be encrypted:", len(job.errors)))

    def _reload_landing(self, landed: Location | None) -> None:
        """Every panel read again, one showing *landed*'s directory with its
        cursor on it -- what an operation made, as F5's on its copy."""
        for each in self.all_panels:
            there = landed is not None and each.found is None and Location.of(each.location) == landed.parent
            each.reload(key=landed.name if there else None)

    async def decrypt_files(self, panel: Panel) -> None:
        """File > Encoding > Encryption > Decrypt: the tagged encrypted files -- or the
        cursor's, a tagged directory's ``.gpg``/``.asc``/``.age`` files -- each
        decrypted beside itself, without its ending.

        Each file is tried without a passphrase first (a public-key file's key
        may be unlocked in gpg's agent already, an age file's identity is a
        file); those that wanted one are tried again with the one asked then,
        three times at most.  The encrypted files are kept.
        """
        from navigator.lib.file_ops import encrypt
        from navigator.lib.system.job import Stopped
        from navigator.widgets.drives.password_dialog import PasswordDialog

        app = self.application
        entries = self.selection(panel)
        if app is None or not entries:
            return
        identities = SETTINGS.encryption.age_identities.split() or encrypt.default_identities()
        options = encrypt.Options(identities=identities)
        sources = [panel.entry_location(entry) for entry in entries]
        job = encrypt.EncryptJob()
        title = tr("Decrypting")
        try:
            def gather() -> tuple[list[Any], int]:
                plans = encrypt.plan_decrypt(sources, job)
                return plans, encrypt.existing_targets(plans)

            plans, there = await self._run_checksums(gather, job, title)
            if not plans and not job.errors:
                await Dialog(title=tr("Error"), prompt=tr("No encrypted file is tagged or at the cursor"),
                             buttons="ok").execute(app)
                return
            if there and not await self._ask_over_targets(there):
                return
            await self._run_checksums(lambda: encrypt.decrypt(plans, options, job), job, title)
            pending = list(job.needs_passphrase)

            async def as_root(refused: list[Any]) -> None:
                # Refused on the disk -- the head unread, or the write -- planned
                # and decrypted again through the root helper; what then wants a
                # passphrase joins those that did already.
                job.as_root = True
                unread = [location for location, _, _ in refused if job.refused_plans[location] is None]
                again = [job.refused_plans[location] for location, _, _ in refused
                         if job.refused_plans[location] is not None]
                if unread:
                    again += await self._run_checksums(lambda: encrypt.plan_decrypt(unread, job), job, title)
                await self._run_checksums(lambda: encrypt.decrypt(again, options, job), job, title)
                pending.extend(job.needs_passphrase)

            await self._again_as_root(job, tr("Decrypt them as root?"), as_root, keep=True)
            tries = 0
            while pending and tries < 3:
                if tries:
                    prompt = tr("The passphrase is wrong. Type it again:")
                else:
                    prompt = tr_n("{n} file needs a passphrase:", "{n} files need a passphrase:", len(pending))
                box = PasswordDialog(prompt=prompt, title=tr("Passphrase"))
                # After construction: the markup's label gives way to an assignment, not to a keyword.
                box.entry.label_text = tr("~P~assphrase")
                reply = await box.execute(app)
                if reply is None:
                    pending = []
                    break
                options.passphrase = reply[0]
                again = pending
                await self._run_checksums(lambda: encrypt.decrypt(again, options, job), job, title)
                pending = job.bad_passphrase
                tries += 1
            job.errors.extend((str(plan.source), encrypt.BAD_PASSPHRASE) for plan in pending)
        except Stopped:
            return
        finally:
            options.passphrase = None
            if job.as_root:
                from navigator.lib.system.elevate import ELEVATION

                await asyncio.to_thread(ELEVATION.release)
            self._reload_landing(job.written[0] if job.written else None)
        self._untag_done(panel, entries, sources, job.errors)
        if job.errors:
            await self._say_checksum_errors(
                self._encryption_reasons(job.errors),
                tr_n("{n} file could not be decrypted:", "{n} files could not be decrypted:", len(job.errors)))

    # -- Convert text (navigator.lib.file_ops.textconv): not DN's, a departure ------------------------

    async def convert_text(self, panel: Panel) -> None:
        """File > Encoding > Convert text: the tagged files -- or the cursor's --
        a tagged directory's to the bottom, each rewritten in place in the
        encoding and with the line endings the box asks for, on a thread.

        Esc in the box stops between two files.  The entries done are
        untagged, the panels read again, and the outcome said: how many were
        converted and how many were already so, then the files left alone
        and why, and those that could not be read or written.
        """
        from navigator.lib.file_ops import textconv
        from navigator.lib.system.job import Stopped
        from navigator.widgets.file_ops.convert_text_dialog import ConvertTextDialog

        app = self.application
        entries = self.selection(panel)
        if app is None or not entries:
            return
        answer = await ConvertTextDialog().execute(app)
        if answer is None:
            return
        self._keep_section("text_conversion", answer, self.application)
        options = textconv.Options(
            encoding="" if answer["encoding"] == "keep" else answer["encoding"],
            ending="" if answer["ending"] == "keep" else answer["ending"],
            fallback=answer["fallback"], keep_times=answer["keep_times"])
        sources = [panel.entry_location(entry) for entry in entries]
        job = textconv.TextJob()
        title = tr("Converting")
        try:
            files = await self._run_checksums(lambda: textconv.plan(sources, job), job, title)
            job.position = 0
            await self._run_checksums(lambda: textconv.convert(files, options, job), job, title)
            await self._convert_as_root(job, options, title)
        except Stopped:
            return
        finally:
            self._reload_landing(self._converted_landing(panel, job.converted))
        self._untag_done(panel, entries, sources, job.errors)
        await self._say_conversion(job)

    @staticmethod
    def _converted_landing(panel: Panel, converted: list[Location]) -> Location | None:
        """Where the cursor goes after Convert text, which makes nothing new:
        on its own file if that was converted, else on the first converted
        in *panel*'s directory, else the first of all -- Alt+A's rule."""
        if not converted:
            return None
        entry = panel.selected
        if entry is not None and entry.name != "..":
            own = panel.entry_location(entry)
            if own in converted:
                return own
        here = Location.of(panel.location)
        return next((location for location in converted if location.parent == here), converted[0])

    async def _convert_as_root(self, job: Any, options: Any, title: str) -> None:
        """The files the disk refused permission, converted again through the
        root helper once asked (:meth:`_again_as_root`)."""
        from navigator.lib.file_ops import textconv

        async def rerun(refused: list[Any]) -> None:
            files = [(location, size) for location, size, _ in refused]
            job.files_done, job.files_total = 0, len(files)
            job.position, job.total = 0, sum(size for _, size in files)
            await self._run_checksums(lambda: textconv.convert(files, options, job, as_root=True), job, title)

        await self._again_as_root(job, tr("Convert them as root?"), rerun)

    async def _again_as_root(self, job: Any, question: str, rerun: Callable[[list[Any]], Awaitable[Any]],
                             *, keep: bool = False, errors: list[Any] | None = None) -> None:
        """A batch's files the disk refused permission (``job.refused``:
        ``(location, size, reason)``), offered *As root* in **one** question
        -- the names, then *question* -- and done again by *rerun(refused)*
        through the root helper, which is let go of after.  Declined, or with
        no way to root, they are ``job.errors`` like any other failure.  A
        departure, as everywhere (``navigator-elevation``): Convert text's,
        Encryption's, Checksums'.  *keep*: the caller goes on as root (Decrypt's
        passphrase questions) and lets the helper go itself; *errors*, where
        the declined go if not ``job.errors``."""
        from navigator.lib.system.elevate import ELEVATION
        from navigator.widgets.file_ops.as_root import ask_as_root

        refused, job.refused = list(job.refused), []
        if not refused:
            return
        failed = job.errors if errors is None else errors
        names = "\n".join(f"{location}: {reason}" for location, _, reason in refused[:8])
        if len(refused) > 8:
            names += "\n" + tr_n("and {n} more", "and {n} more", len(refused) - 8)
        message = tr_n("{n} file was refused permission:", "{n} files were refused permission:",
                       len(refused)) + "\n" + names
        if (not await asyncio.to_thread(ELEVATION.available)
                or not await ask_as_root(self.application, message + "\n" + question)):
            failed.extend((str(location), reason) for location, _, reason in refused)
            return
        try:
            await rerun(refused)
        finally:
            if not keep:
                await asyncio.to_thread(ELEVATION.release)

    async def _say_conversion(self, job: Any) -> None:
        """How the conversion went, in one box."""
        from navml.widgets.dialog.control import escape_caption

        from navigator.lib.file_ops import textconv

        reasons = {
            textconv.BINARY: lambda detail: tr("looks binary"),
            textconv.UNDECODABLE: lambda detail: tr("not UTF-8, and no encoding was chosen to read it as"),
            textconv.UNENCODABLE: lambda detail: tr("the encoding cannot write a character at {place}").format(
                place=detail),
            textconv.TOO_LARGE: lambda detail: tr("too large"),
        }
        lines = [tr_n("{n} file converted", "{n} files converted", len(job.converted)),
                 tr_n("{n} file already so", "{n} files already so", len(job.unchanged))]
        left = [(name, reasons[kind](detail)) for name, kind, detail in job.skipped]
        for heading, failures in (
                (tr_n("{n} file left alone:", "{n} files left alone:", len(left)), left),
                (tr_n("{n} file could not be converted:", "{n} files could not be converted:",
                      len(job.errors)), job.errors)):
            if not failures:
                continue
            lines.append(heading)
            lines += [escape_caption(f"{name}: {reason}") for name, reason in failures[:8]]
            if len(failures) > 8:
                lines.append(tr_n("and {n} more", "and {n} more", len(failures) - 8))
        title = tr("Error") if job.errors else tr("Convert text")
        await Dialog(title=title, prompt="\n".join(lines), buttons="ok").execute(self.application)

    async def _ask_over_targets(self, there: int) -> bool:
        """Whether *there* files already where the results go are written over."""
        prompt = tr_n("{n} file already exists.\nOK to overwrite it?",
                      "{n} files already exist.\nOK to overwrite them?", there)
        return bool(await Dialog(title=tr("Warning"), prompt=prompt, buttons="yes-no").execute(self.application))

    @staticmethod
    def _untag_done(panel: Panel, entries: list[Any], sources: list[Location],
                    errors: list[tuple[str, str]]) -> None:
        """The entries untagged whose files -- a directory's every one -- were done."""
        failed = {name for name, _ in errors}
        panel.untag(entry for entry, source in zip(entries, sources)
                    if not any(name == str(source) or name.startswith(f"{source}/") for name in failed))

    @staticmethod
    def _encryption_reasons(errors: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """*errors* with the model's own reasons translated."""
        from navigator.lib.file_ops import encrypt

        reasons = {
            encrypt.BAD_PASSPHRASE: tr("wrong passphrase"),
            encrypt.NO_IDENTITY: tr("no age identity file: set one in Options > Settings > Tools"),
            encrypt.NO_SECRET_KEY: tr("no secret key for it"),
        }
        return [(name, reasons.get(reason, reason)) for name, reason in errors]
