"""Copying and moving files: DOS Navigator's ``FILECOPY.PAS``.

The model half of F5 and F6, with no widget in it.  :func:`run` is the worker
the file manager starts on a thread; everything it needs to tell the user or
ask of them goes through a :class:`CopyJob`, which is the only thing the
thread and the loop share -- :class:`navigator.lib.system.job.Job`'s *Stop*, pause and
one question at a time, and the progress fields the worker writes and the
loop reads.  Nothing reactive crosses, which is the loop's alone
(``viewer.SearchJob`` is the same shape, smaller).

What is DN's and what is not:

* **The five copy modes are DN's** (``cpmOverwrite`` ... ``cpmRefresh``), in
  its order, so a mode is the radio button's index.  *Ask* puts DN's
  *Confirm* query, whose Overwrite, Append and Skip can be made to stand for
  every file after it, and whose Rename never can.
* **The option bits keep DN's positions**, so *Remove source* is still
  ``$08``; the two DOS-isms beside it are Linux's own options instead --
  *Preserve attributes* where *Verify disk writes* was, *Follow symlinks*
  where *Copy descriptions* was.
* **A move renames first**, as DN's ``DoRename`` did on one drive, and falls
  back to copying and deleting when the kernel says ``EXDEV``.
* **The target is read as DN read it**: an existing directory, or a name
  ending in ``/``, is where the files go; a name with ``*`` or ``?`` in it is
  a mask each name is renamed by (DN's ``MkName``); anything else is the new
  name of a single file, or a directory to create for several.  ``TEMP:``,
  ``LINK:``, archives and DOS devices are not ported.
"""

from __future__ import annotations

import errno
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any, Callable

from navkit.i18n import tr

from navigator.lib.drives import Location, drive_of
from navigator.lib.system.job import POLL, Job, Stopped

#: The copy modes, which are the dialog's radio buttons in order.
OVERWRITE, APPEND, ASK, SKIP, REFRESH = range(5)

#: The option bits, which are the dialog's check boxes in order.
CHECK_FREE = 0x01
PRESERVE = 0x02
FOLLOW_LINKS = 0x04
MOVE = 0x08

#: How much is read and written at a time.
CHUNK = 1 << 20

@dataclass
class CopyRequest:
    """What the Copy dialog answered."""

    sources: list[Path | Location]
    target: str
    mode: int = ASK
    options: int = PRESERVE
    #: System Setup's *Flush buffers*: each file written is synced to disk
    #: before it counts as copied -- and before a move deletes its source.
    flush: bool = False

    @property
    def move(self) -> bool:
        return bool(self.options & MOVE)


# -- the questions -------------------------------------------------------------


@dataclass
class Overwrite:
    """DN's ``dlgOverwriteQuery``: *dest* is there already.

    Answered with an :class:`OverwriteAnswer`, or ``None`` for Cancel.
    """

    source: Path | Location
    dest: Path | Location
    source_size: int
    source_mtime: float
    dest_size: int
    dest_mtime: float


@dataclass
class OverwriteAnswer:
    #: ``"overwrite"``, ``"append"``, ``"rename"`` or ``"skip"``.
    action: str
    #: *Accept choice for all files*; ignored for a rename, as DN ignored it.
    all: bool = False
    #: The new name, for a rename.
    name: str = ""


@dataclass
class NoRoom:
    """``erNotDiskSpace1``: *Copy other files?*  True skips this one, False stops."""

    dest: Path | Location
    size: int
    free: int


@dataclass
class Failure:
    """Something went wrong with *path*.  True skips it, False stops.

    *reason* may be a callable giving a template for *values*, so that a
    worker thread names a message that is put into words on the loop, where
    the language is read.
    """

    path: Path | Location
    reason: str | Callable[[], str]
    values: dict[str, Any] = field(default_factory=dict)

    @property
    def message(self) -> str:
        if callable(self.reason):
            text = self.reason()
            return text.format(**self.values) if self.values else text
        return self.reason


@dataclass
class CreateDirectory:
    """``dlQueryCreateDir``: the target directory does not exist.  True makes it."""

    path: Path | Location


# -- the shared state ------------------------------------------------------------


class CopyJob(Job):
    """A running copy, as the thread doing it and the loop watching it see it."""

    def __init__(self, asker: Callable[[Any], Any] | None = None) -> None:
        super().__init__(asker)
        #: Bytes in everything to be copied, once :func:`run` has measured.
        self.total_bytes = 0
        self.done_bytes = 0
        #: The file in hand, and how far into it.
        self.source = ""
        self.dest = ""
        self.file_bytes = 0
        self.file_done = 0
        #: True while the sources are being measured.
        self.measuring = True


# -- the target ----------------------------------------------------------------


def has_wildcards(text: str) -> bool:
    return "*" in text or "?" in text


def _split_ext(name: str) -> tuple[str, str | None]:
    """``"a.tar.gz"`` -> ``("a.tar", "gz")``; a dot-file's leading dot is not one."""
    dot = name.rfind(".")
    if dot <= 0:
        return name, None
    return name[:dot], name[dot + 1 :]


def _apply_part(source: str, pattern: str) -> str:
    out: list[str] = []
    for index, char in enumerate(pattern):
        if char == "*":
            out.append(source[index:])
            break
        if char == "?":
            out.append(source[index : index + 1])
        else:
            out.append(char)
    return "".join(out)


def apply_mask(name: str, mask: str) -> str:
    """DN's ``MkName``: *name* renamed by *mask*, part by part.

    ``*`` takes the rest of the source's part from where it stands, ``?`` the
    source's character in its place, and anything else is itself; the name
    and the extension are masked separately, as DOS did.  A mask with no dot
    masks the whole name, which ``*`` alone therefore keeps.
    """
    mask_stem, mask_ext = _split_ext(mask)
    if mask_ext is None:
        return _apply_part(name, mask)
    stem, ext = _split_ext(name)
    new_stem = _apply_part(stem, mask_stem)
    new_ext = _apply_part(ext or "", mask_ext)
    return f"{new_stem}.{new_ext}" if new_ext else new_stem


@dataclass
class Destination:
    """Where each source goes: into *directory*, named as :meth:`name_for` says.

    *directory* is a :class:`~pathlib.Path` on the disk and a
    :class:`~navigator.lib.drives.Location` anywhere else.
    """

    directory: Path | Location
    #: The new name of a single source, or ``""`` to keep each source's own.
    name: str = ""
    #: A rename mask, or ``""``.
    mask: str = ""
    #: True when *directory* does not exist yet and has to be made.
    create: bool = False

    def name_for(self, source: Path | Location) -> str:
        if self.name:
            return self.name
        if self.mask:
            return apply_mask(source.name, self.mask) or source.name
        return source.name

    def path_for(self, source: Path | Location) -> Path | Location:
        return self.directory / self.name_for(source)


def shown(location: Path | Location) -> Path | Location:
    """*location* as a question or an answer names it: the plain
    :class:`~pathlib.Path` on the disk, so what reads one there reads what
    it always did, and the location itself elsewhere.  A path is a path."""
    if not isinstance(location, Location):
        return location
    return location.local if location.is_local else location


def target_location(target: str, cwd: Path | Location) -> Location:
    """The dialog's target line as a location: a URL is where it says, a
    plain absolute path the disk -- as in DN only a prefix (``LINK:``) took
    a copy off it -- and anything else is relative to *cwd*, on its drive.
    ``~`` is the local home."""
    text = target.strip()
    archived = Location.parse(text)
    if "://" in text or archived.outer is not None:
        # A URL, or a place in an archive (``/dir/a.zip#/inside``).
        return archived
    if text.startswith("~"):
        text = os.path.expanduser(text)
    if os.path.isabs(text):
        return Location.of(Path(text))
    return Location.of(cwd) / text


def resolve_target(target: str, sources: list[Path | Location], cwd: Path | Location) -> Destination:
    """Read the dialog's target line as DN's ``CopyDialog`` read it.

    Asks the drive whether directories are there, so a thread runs it once
    the target may be remote.
    """
    location = target_location(target, cwd)
    drive = drive_of(location)
    if target.strip().endswith("/") or drive.is_dir(location):
        return Destination(shown(location), create=not drive.is_dir(location))
    parent = location.parent
    if has_wildcards(location.name):
        return Destination(shown(parent), mask=location.name, create=not drive.is_dir(parent))
    if len(sources) == 1:
        return Destination(shown(parent), name=location.name, create=not drive.is_dir(parent))
    return Destination(shown(location), create=True)


# -- the work --------------------------------------------------------------------


def run(request: CopyRequest, job: CopyJob, cwd: Path | Location) -> list[Path | Location]:
    """Copy (or move) what *request* says; answer the sources done in full.

    A source skipped, or one that failed in part, is not in the answer -- the
    file manager untags only what went, as DN deselected a file as it copied.
    The sources and the target may be on any drives
    (:mod:`navigator.lib.drives`): the work is the same steps, asked of each
    end's drive.
    """
    return _Copier(request, job, cwd).run()


def _cross_device(location: Location) -> OSError:
    """What a rename between two drives fails with: ``EXDEV``, as the kernel
    says it between two file systems, so a move falls back the same way."""
    return OSError(errno.EXDEV, os.strerror(errno.EXDEV), str(location))


class _Copier:
    def __init__(self, request: CopyRequest, job: CopyJob, cwd: Path | Location) -> None:
        self.request = request
        self.job = job
        self.cwd = cwd
        #: The copy mode, which a sticky answer to *Ask* replaces.
        self.mode = request.mode
        self.follow = bool(request.options & FOLLOW_LINKS)
        self.preserve = bool(request.options & PRESERVE)
        self.check_free = bool(request.options & CHECK_FREE)
        self.flush = request.flush
        self.move = request.move
        self.is_root = hasattr(os, "geteuid") and os.geteuid() == 0
        #: The directories being copied, by identity: a loop through a
        #: followed link is refused rather than copied for ever.
        self._walking: set[tuple[Any, ...]] = set()
        #: Set by the first ``EXDEV``: a move that has to copy stops trying to
        #: rename each directory under the one that could not be.
        self._cross_device = False

    # -- asking ------------------------------------------------------------------

    def _ask(self, question: Any) -> Any:
        if self.job.stopped:
            raise Stopped
        answer = self.job.ask(question)
        if answer is None or answer is False:
            raise Stopped
        return answer

    def _fail(self, path: Location, message: str | Callable[[], str], **values: Any) -> bool:
        """Say what went wrong with *path*; False, as a skipped source is, or stop."""
        self._ask(Failure(shown(path), message, values))
        return False

    def _checkpoint(self) -> None:
        self.job.wait_while_paused()
        if self.job.stopped:
            raise Stopped

    # -- the drives --------------------------------------------------------------

    def _stat(self, location: Location) -> Any:
        drive = drive_of(location)
        return drive.stat(location) if self.follow else drive.lstat(location)

    @staticmethod
    def _identity(location: Location, st: Any) -> tuple[Any, ...]:
        """What tells one directory from another: its device and inode, or
        on a drive without them its site and path."""
        if st.st_ino:
            return (location.site, st.st_dev, st.st_ino)
        return (location.site, str(location.path))

    @staticmethod
    def _rename(source: Location, dest: Location, *, replace: bool) -> None:
        """A rename on one drive; ``EXDEV`` between two."""
        if source.site != dest.site or source.outer != dest.outer:
            raise _cross_device(source)
        drive = drive_of(source)
        if replace:
            drive.replace(source, dest)
        else:
            drive.rename(source, dest)

    # -- the whole ---------------------------------------------------------------

    def run(self) -> list[Path | Location]:
        request, job = self.request, self.job
        done: list[Path | Location] = []
        opened = None
        try:
            opened = _open_target_archive(target_location(request.target, self.cwd))
            destination = resolve_target(request.target, request.sources, self.cwd)
            if destination.create:
                directory = Location.of(destination.directory)
                self._ask(CreateDirectory(destination.directory))
                try:
                    drive_of(directory).makedirs(directory)
                except OSError as error:
                    self._fail(directory, error_message(error))
                    return done
            job.total_bytes = sum(self._measure(Location.of(source)) for source in request.sources)
            job.measuring = False
            for source in request.sources:
                self._checkpoint()
                if self._transfer(Location.of(source), Location.of(destination.path_for(source))):
                    done.append(source)
            finish_drives([*request.sources, destination.directory], self._fail)
        except Stopped:
            # What went in full stays, as it would on a disk.
            finish_drives([*request.sources, Location.of(self.cwd)], None)
        finally:
            job.measuring = False
            if opened is not None:
                from navigator.lib.drives import archive

                archive.release_unheld(opened)
        return done

    def _measure(self, path: Location) -> int:
        """Bytes in *path*, which the progress window's total gauge counts in."""
        total = 0
        seen: set[tuple[Any, ...]] = set()
        stack = [path]
        while stack:
            self._checkpoint()
            current = stack.pop()
            try:
                st = self._stat(current)
            except OSError:
                continue
            if stat.S_ISDIR(st.st_mode):
                key = self._identity(current, st)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    stack.extend(current / name for name in drive_of(current).names(current))
                except OSError:
                    continue
            elif stat.S_ISREG(st.st_mode):
                total += st.st_size
        return total

    # -- one entry ---------------------------------------------------------------

    def _transfer(self, source: Location, dest: Location) -> bool:
        self._checkpoint()
        try:
            st = self._stat(source)
        except OSError as error:
            return self._fail(source, error_message(error))
        if stat.S_ISDIR(st.st_mode):
            return self._directory(source, dest, st)
        if stat.S_ISLNK(st.st_mode):
            return self._link(source, dest, st)
        if stat.S_ISREG(st.st_mode):
            return self._file(source, dest, st)
        return self._fail(source, lambda: tr("{name} is not a regular file"), name=source.name)

    def _same(self, source: Location, dest: Location) -> bool:
        if source.site != dest.site:
            return False
        return drive_of(source).same_file(source, dest)

    # -- directories -------------------------------------------------------------

    def _directory(self, source: Location, dest: Location, st: Any) -> bool:
        source_drive, dest_drive = drive_of(source), drive_of(dest)
        if source.site == dest.site and source.outer == dest.outer:
            real_source = source_drive.realpath(source)
            real_dest = (dest_drive.realpath(dest) if dest_drive.exists(dest)
                         else dest_drive.realpath(dest.parent) / dest.name)
            if real_dest == real_source or real_source.path in real_dest.path.parents:
                return self._fail(source, lambda: tr("Cannot copy directory {name} into itself"),
                                  name=source.name)
        key = self._identity(source, st)
        if key in self._walking:
            return self._fail(source, lambda: tr("{where} loops back on itself"), where=shown(source))
        if dest_drive.is_link(dest) or (dest_drive.exists(dest) and not dest_drive.is_dir(dest)):
            return self._fail(dest, lambda: tr("Can not overwrite {name} with a directory"), name=dest.name)
        if self.move and not self._cross_device and not dest_drive.exists(dest):
            size = self._measure(source)
            try:
                self._rename(source, dest, replace=False)
                self.job.done_bytes += size
                return True
            except OSError as error:
                if error.errno != errno.EXDEV:
                    return self._fail(source, error_message(error))
                # Every directory under this one is across the same line.
                self._cross_device = True
        self._walking.add(key)
        try:
            made = False
            try:
                if not dest_drive.exists(dest):
                    # Writable by us whatever the source says, so the copy
                    # can fill it; the source's own mode comes after.
                    dest_drive.mkdir(dest, (st.st_mode & 0o7777) | 0o700)
                    made = True
            except OSError as error:
                return self._fail(dest, error_message(error))
            try:
                children = sorted(source_drive.names(source))
            except OSError as error:
                return self._fail(source, error_message(error))
            complete = True
            for name in children:
                if not self._transfer(source / name, dest / name):
                    complete = False
            if self.preserve:
                self._attributes(source, dest, st)
            elif made and st.st_mode & 0o700 != 0o700:
                # The owner's bits added above, taken back off: a plain copy
                # of a directory has the source's mode less the umask, as cp's.
                try:
                    dest_drive.chmod(dest, st.st_mode & 0o7777 & ~_UMASK)
                except OSError:
                    pass
            if self.move and complete:
                try:
                    source_drive.rmdir(source)
                except OSError as error:
                    return self._fail(source, error_message(error))
            return complete
        finally:
            self._walking.discard(key)

    # -- links -------------------------------------------------------------------

    def _link(self, source: Location, dest: Location, st: Any) -> bool:
        """A link recreated as a link, pointing where the original pointed."""
        source_drive, dest_drive = drive_of(source), drive_of(dest)
        self.job.source, self.job.dest = str(source), str(dest)
        self.job.file_bytes = self.job.file_done = 0
        if dest_drive.lexists(dest):
            if self._same_link(source, dest):
                return self._fail(source, lambda: tr("{name} can not be copied to itself"), name=source.name)
            action, dest = self._resolve_existing(source, dest, st)
            if action == "skip":
                return False
            if action == "append":
                return self._fail(source, lambda: tr("Can not append to {name}: it is a link"), name=dest.name)
        if self.move:
            try:
                self._rename(source, dest, replace=True)
                return True
            except OSError as error:
                if error.errno != errno.EXDEV:
                    return self._fail(source, error_message(error))
        try:
            target = source_drive.readlink(source)
            if dest_drive.lexists(dest):
                dest_drive.unlink(dest)
            dest_drive.symlink(target, dest)
        except OSError as error:
            return self._fail(source, error_message(error))
        if self.preserve:
            try:
                dest_drive.utime(dest, st.st_atime_ns, st.st_mtime_ns, follow=False)
            except (OSError, NotImplementedError):
                pass
            if self.is_root:
                try:
                    dest_drive.chown(dest, st.st_uid, st.st_gid, follow=False)
                except OSError:
                    pass
        if self.move:
            try:
                source_drive.unlink(source)
            except OSError as error:
                return self._fail(source, error_message(error))
        return True

    def _same_link(self, source: Location, dest: Location) -> bool:
        if source.site != dest.site or source.outer != dest.outer:
            return False
        drive = drive_of(source)
        try:
            a, b = drive.lstat(source), drive.lstat(dest)
        except OSError:
            return False
        if not a.st_ino:
            return source.normalized() == dest.normalized()
        return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)

    # -- files -------------------------------------------------------------------

    def _resolve_existing(self, source: Location, dest: Location, st: Any) -> tuple[str, Location]:
        """What to do about *dest* being there: the action, and where to.

        Loops while *Ask* is answered with a rename to a name that is taken
        too.  A directory in the way is refused rather than asked about, as
        DN's ``dlFCNotOverDir`` was.
        """
        dest_drive = drive_of(dest)
        while True:
            try:
                existing = dest_drive.lstat(dest)
            except FileNotFoundError:
                return "new", dest
            except OSError as error:
                self._fail(dest, error_message(error))
                return "skip", dest
            if stat.S_ISDIR(existing.st_mode):
                self._fail(dest, lambda: tr("Can not overwrite directory {name}"), name=dest.name)
                return "skip", dest
            mode = self.mode
            if mode == OVERWRITE:
                return "overwrite", dest
            if mode == APPEND:
                return "append", dest
            if mode == SKIP:
                return "skip", dest
            if mode == REFRESH:
                return ("skip" if existing.st_mtime >= st.st_mtime else "overwrite"), dest
            answer = self._ask(Overwrite(
                shown(source), shown(dest), st.st_size, st.st_mtime, existing.st_size, existing.st_mtime,
            ))
            if answer.action == "rename":
                if answer.name:
                    dest = dest.parent / answer.name
                continue
            if answer.all:
                self.mode = {"overwrite": OVERWRITE, "append": APPEND, "skip": SKIP}[answer.action]
            return answer.action, dest

    def _file(self, source: Location, dest: Location, st: Any) -> bool:
        job = self.job
        source_drive, dest_drive = drive_of(source), drive_of(dest)
        job.source, job.dest = str(source), str(dest)
        job.file_bytes, job.file_done = st.st_size, 0
        if dest_drive.lexists(dest) and self._same(source, dest):
            job.done_bytes += st.st_size
            return self._fail(source, lambda: tr("{name} can not be copied to itself"), name=source.name)
        action, dest = self._resolve_existing(source, dest, st)
        job.dest = str(dest)
        if action == "skip":
            job.done_bytes += st.st_size
            return False
        if self.check_free:
            free = dest_drive.free_bytes(dest.parent)
            if free is not None and free < st.st_size:
                self._ask(NoRoom(shown(dest), st.st_size, free))
                job.done_bytes += st.st_size
                return False
        if self.move and action != "append":
            try:
                self._rename(source, dest, replace=True)
                job.done_bytes += st.st_size
                job.file_done = st.st_size
                return True
            except OSError as error:
                if error.errno != errno.EXDEV:
                    job.done_bytes += st.st_size
                    return self._fail(source, error_message(error))
        if not self._copy_bytes(source, dest, st, append=action == "append"):
            return False
        if self.preserve:
            self._attributes(source, dest, st)
        if self.move:
            try:
                source_drive.unlink(source)
            except OSError as error:
                return self._fail(source, error_message(error))
        return True

    def _copy_bytes(self, source: Location, dest: Location, st: Any, *, append: bool) -> bool:
        job = self.job
        source_drive, dest_drive = drive_of(source), drive_of(dest)
        start_done = job.done_bytes
        created = False
        try:
            with source_drive.open_read(source) as reader:
                created = not dest_drive.lexists(dest) or not append
                with dest_drive.open_write(dest, append=append, mode=st.st_mode & 0o777) as writer:
                    stream(reader, writer, job)
                    if self.flush:
                        dest_drive.sync(writer)
            return True
        except Stopped:
            # A half-written copy is worse than none, and nothing of a file
            # appended to can be told apart from what was there.
            if created:
                _remove_quietly(dest)
            raise
        except OSError as error:
            if created:
                _remove_quietly(dest)
            job.done_bytes = start_done + st.st_size
            return self._fail(source, error_message(error))

    def _attributes(self, source: Location, dest: Location, st: Any) -> None:
        """*Preserve attributes*: mode, times and, as root, the owner."""
        dest_drive = drive_of(dest)
        dest_drive.copy_attributes(drive_of(source), source, dest, st, follow=self.follow)
        if self.is_root:
            try:
                dest_drive.chown(dest, st.st_uid, st.st_gid)
            except OSError:
                pass


def _open_target_archive(target: Location) -> Location | None:
    """A copy into an archive not open yet: opened -- or, named but not there,
    made empty (DN's ``ArchiveFiles``, packing by the target's name) -- for
    the copy.  Its location, to let go of after; None for any other target."""
    from navigator.lib.drives import archive

    outer = target.outer
    if outer is None or archive.find(outer) is not None:
        return None
    try:
        archive.open_archive(outer, create=True)
    except (archive.NotAnArchive, OSError):
        return None  # said by the steps that fail
    return outer


def finish_drives(places: list[Any], fail: Callable[..., Any] | None) -> None:
    """``Drive.finish`` once on each drive *places* are on: an archive
    written into or erased in is written anew.  A failure is said through
    *fail* (or passed over without one)."""
    seen: set[int] = set()
    for place in places:
        try:
            drive = drive_of(Location.of(place))
        except OSError:
            continue
        if id(drive) in seen:
            continue
        seen.add(id(drive))
        try:
            drive.finish()
        except OSError as error:
            if fail is not None:
                fail(Location.of(place), error_message(error))


def stream(reader: IO[bytes], writer: IO[bytes], job: Any, chunk: int | None = None) -> None:
    """*reader*'s bytes into *writer*, *chunk* at a time: the inner loop of
    every copy, whichever drives its ends are on.  Counts into *job*'s
    ``file_done`` and ``done_bytes``, and stops (:class:`Stopped`) between
    chunks when *job* is paused or stopped.  *chunk* is :data:`CHUNK` unless
    given, read at the call."""
    chunk = chunk or CHUNK
    while True:
        job.wait_while_paused()
        if job.stopped:
            raise Stopped
        data = reader.read(chunk)
        if not data:
            break
        writer.write(data)
        job.file_done += len(data)
        job.done_bytes += len(data)


def error_message(error: OSError) -> str:
    """``name: reason``, as an error box shows an ``OSError``."""
    name = Path(error.filename).name if error.filename else ""
    reason = error.strerror or str(error)
    return f"{name}: {reason}" if name else reason


def _remove_quietly(location: Location) -> None:
    try:
        drive_of(location).unlink(location)
    except OSError:
        pass


def _read_umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


#: Read once, at import, which is on the loop's thread: ``os.umask`` can only
#: be read by setting it, and setting it from the worker would race every
#: other thread creating a file.
_UMASK = _read_umask()


__all__ = [
    "APPEND", "ASK", "CHECK_FREE", "CopyJob", "CopyRequest", "CreateDirectory", "Destination",
    "FOLLOW_LINKS", "Failure", "MOVE", "NoRoom", "OVERWRITE", "Overwrite", "OverwriteAnswer",
    "POLL", "PRESERVE", "REFRESH", "SKIP", "Stopped", "apply_mask", "resolve_target", "run", "shown",
    "stream", "target_location",
]
