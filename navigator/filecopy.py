"""Copying and moving files: DOS Navigator's ``FILECOPY.PAS``.

The model half of F5 and F6, with no widget in it.  :func:`run` is the worker
the file manager starts on a thread; everything it needs to tell the user or
ask of them goes through a :class:`CopyJob`, which is the only thing the
thread and the loop share -- :class:`navigator.job.Job`'s *Stop*, pause and
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
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from navkit.i18n import tr

from navigator.job import POLL, Job, Stopped

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

    sources: list[Path]
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

    source: Path
    dest: Path
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

    dest: Path
    size: int
    free: int


@dataclass
class Failure:
    """Something went wrong with *path*.  True skips it, False stops.

    *reason* may be a callable giving a template for *values*, so that a
    worker thread names a message that is put into words on the loop, where
    the language is read.
    """

    path: Path
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

    path: Path


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
    """Where each source goes: into *directory*, named as :meth:`name_for` says."""

    directory: Path
    #: The new name of a single source, or ``""`` to keep each source's own.
    name: str = ""
    #: A rename mask, or ``""``.
    mask: str = ""
    #: True when *directory* does not exist yet and has to be made.
    create: bool = False

    def name_for(self, source: Path) -> str:
        if self.name:
            return self.name
        if self.mask:
            return apply_mask(source.name, self.mask) or source.name
        return source.name

    def path_for(self, source: Path) -> Path:
        return self.directory / self.name_for(source)


def resolve_target(target: str, sources: list[Path], cwd: Path) -> Destination:
    """Read the dialog's target line as DN's ``CopyDialog`` read it."""
    text = os.path.expanduser(target.strip())
    path = Path(text) if os.path.isabs(text) else cwd / text
    if text.endswith("/") or path.is_dir():
        return Destination(path, create=not path.is_dir())
    parent = path.parent
    if has_wildcards(path.name):
        return Destination(parent, mask=path.name, create=not parent.is_dir())
    if len(sources) == 1:
        return Destination(parent, name=path.name, create=not parent.is_dir())
    return Destination(path, create=True)


# -- the work --------------------------------------------------------------------


def run(request: CopyRequest, job: CopyJob, cwd: Path) -> list[Path]:
    """Copy (or move) what *request* says; answer the sources done in full.

    A source skipped, or one that failed in part, is not in the answer -- the
    file manager untags only what went, as DN deselected a file as it copied.
    """
    return _Copier(request, job, cwd).run()


class _Copier:
    def __init__(self, request: CopyRequest, job: CopyJob, cwd: Path) -> None:
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
        self._walking: set[tuple[int, int]] = set()
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

    def _fail(self, path: Path, message: str | Callable[[], str], **values: Any) -> bool:
        """Say what went wrong with *path*; False, as a skipped source is, or stop."""
        self._ask(Failure(path, message, values))
        return False

    def _checkpoint(self) -> None:
        self.job.wait_while_paused()
        if self.job.stopped:
            raise Stopped

    # -- the whole ---------------------------------------------------------------

    def run(self) -> list[Path]:
        request, job = self.request, self.job
        done: list[Path] = []
        try:
            destination = resolve_target(request.target, request.sources, self.cwd)
            if destination.create:
                self._ask(CreateDirectory(destination.directory))
                try:
                    destination.directory.mkdir(parents=True, exist_ok=True)
                except OSError as error:
                    self._fail(destination.directory, error_message(error))
                    return done
            job.total_bytes = sum(self._measure(source) for source in request.sources)
            job.measuring = False
            for source in request.sources:
                self._checkpoint()
                if self._transfer(source, destination.path_for(source)):
                    done.append(source)
        except Stopped:
            pass
        finally:
            job.measuring = False
        return done

    def _measure(self, path: Path) -> int:
        """Bytes in *path*, which the progress window's total gauge counts in."""
        total = 0
        seen: set[tuple[int, int]] = set()
        stack = [path]
        while stack:
            self._checkpoint()
            current = stack.pop()
            try:
                st = os.stat(current) if self.follow else os.lstat(current)
            except OSError:
                continue
            if stat.S_ISDIR(st.st_mode):
                key = (st.st_dev, st.st_ino)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    with os.scandir(current) as it:
                        stack.extend(Path(entry.path) for entry in it)
                except OSError:
                    continue
            elif stat.S_ISREG(st.st_mode):
                total += st.st_size
        return total

    # -- one entry ---------------------------------------------------------------

    def _transfer(self, source: Path, dest: Path) -> bool:
        self._checkpoint()
        try:
            st = os.stat(source) if self.follow else os.lstat(source)
        except OSError as error:
            return self._fail(source, error_message(error))
        if stat.S_ISDIR(st.st_mode):
            return self._directory(source, dest, st)
        if stat.S_ISLNK(st.st_mode):
            return self._link(source, dest, st)
        if stat.S_ISREG(st.st_mode):
            return self._file(source, dest, st)
        return self._fail(source, lambda: tr("{name} is not a regular file"), name=source.name)

    def _same(self, source: Path, dest: Path) -> bool:
        try:
            return os.path.samefile(source, dest)
        except OSError:
            return False

    # -- directories -------------------------------------------------------------

    def _directory(self, source: Path, dest: Path, st: os.stat_result) -> bool:
        real_source = source.resolve()
        real_dest = dest.resolve() if dest.exists() else dest.parent.resolve() / dest.name
        if real_dest == real_source or real_source in real_dest.parents:
            return self._fail(source, lambda: tr("Cannot copy directory {name} into itself"), name=source.name)
        key = (st.st_dev, st.st_ino)
        if key in self._walking:
            return self._fail(source, lambda: tr("{where} loops back on itself"), where=source)
        if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
            return self._fail(dest, lambda: tr("Can not overwrite {name} with a directory"), name=dest.name)
        if self.move and not self._cross_device and not dest.exists():
            size = self._measure(source)
            try:
                os.rename(source, dest)
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
                if not dest.exists():
                    # Writable by us whatever the source says, so the copy
                    # can fill it; the source's own mode comes after.
                    os.mkdir(dest, (st.st_mode & 0o7777) | 0o700)
                    made = True
            except OSError as error:
                return self._fail(dest, error_message(error))
            try:
                with os.scandir(source) as it:
                    children = sorted(entry.name for entry in it)
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
                    os.chmod(dest, st.st_mode & 0o7777 & ~_UMASK)
                except OSError:
                    pass
            if self.move and complete:
                try:
                    os.rmdir(source)
                except OSError as error:
                    return self._fail(source, error_message(error))
            return complete
        finally:
            self._walking.discard(key)

    # -- links -------------------------------------------------------------------

    def _link(self, source: Path, dest: Path, st: os.stat_result) -> bool:
        """A link recreated as a link, pointing where the original pointed."""
        self.job.source, self.job.dest = str(source), str(dest)
        self.job.file_bytes = self.job.file_done = 0
        if os.path.lexists(dest):
            if self._same_link(source, dest):
                return self._fail(source, lambda: tr("{name} can not be copied to itself"), name=source.name)
            action, dest = self._resolve_existing(source, dest, st)
            if action == "skip":
                return False
            if action == "append":
                return self._fail(source, lambda: tr("Can not append to {name}: it is a link"), name=dest.name)
        if self.move:
            try:
                os.replace(source, dest)
                return True
            except OSError as error:
                if error.errno != errno.EXDEV:
                    return self._fail(source, error_message(error))
        try:
            target = os.readlink(source)
            if os.path.lexists(dest):
                os.unlink(dest)
            os.symlink(target, dest)
        except OSError as error:
            return self._fail(source, error_message(error))
        if self.preserve:
            try:
                os.utime(dest, ns=(st.st_atime_ns, st.st_mtime_ns), follow_symlinks=False)
            except (OSError, NotImplementedError):
                pass
            if self.is_root:
                try:
                    os.lchown(dest, st.st_uid, st.st_gid)
                except OSError:
                    pass
        if self.move:
            try:
                os.unlink(source)
            except OSError as error:
                return self._fail(source, error_message(error))
        return True

    def _same_link(self, source: Path, dest: Path) -> bool:
        try:
            a, b = os.lstat(source), os.lstat(dest)
        except OSError:
            return False
        return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)

    # -- files -------------------------------------------------------------------

    def _resolve_existing(self, source: Path, dest: Path, st: os.stat_result) -> tuple[str, Path]:
        """What to do about *dest* being there: the action, and where to.

        Loops while *Ask* is answered with a rename to a name that is taken
        too.  A directory in the way is refused rather than asked about, as
        DN's ``dlFCNotOverDir`` was.
        """
        while True:
            try:
                existing = os.lstat(dest)
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
                source, dest, st.st_size, st.st_mtime, existing.st_size, existing.st_mtime,
            ))
            if answer.action == "rename":
                if answer.name:
                    dest = dest.parent / answer.name
                continue
            if answer.all:
                self.mode = {"overwrite": OVERWRITE, "append": APPEND, "skip": SKIP}[answer.action]
            return answer.action, dest

    def _file(self, source: Path, dest: Path, st: os.stat_result) -> bool:
        job = self.job
        job.source, job.dest = str(source), str(dest)
        job.file_bytes, job.file_done = st.st_size, 0
        if os.path.lexists(dest) and self._same(source, dest):
            job.done_bytes += st.st_size
            return self._fail(source, lambda: tr("{name} can not be copied to itself"), name=source.name)
        action, dest = self._resolve_existing(source, dest, st)
        job.dest = str(dest)
        if action == "skip":
            job.done_bytes += st.st_size
            return False
        if self.check_free:
            free = _free_space(dest.parent)
            if free is not None and free < st.st_size:
                self._ask(NoRoom(dest, st.st_size, free))
                job.done_bytes += st.st_size
                return False
        if self.move and action != "append":
            try:
                os.replace(source, dest)
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
                os.unlink(source)
            except OSError as error:
                return self._fail(source, error_message(error))
        return True

    def _copy_bytes(self, source: Path, dest: Path, st: os.stat_result, *, append: bool) -> bool:
        job = self.job
        start_done = job.done_bytes
        flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if append else os.O_TRUNC)
        created = False
        try:
            with open(source, "rb") as reader:
                created = not os.path.lexists(dest) or not append
                fd = os.open(dest, flags, st.st_mode & 0o777)
                with os.fdopen(fd, "wb") as writer:
                    while True:
                        job.wait_while_paused()
                        if job.stopped:
                            raise Stopped
                        chunk = reader.read(CHUNK)
                        if not chunk:
                            break
                        writer.write(chunk)
                        job.file_done += len(chunk)
                        job.done_bytes += len(chunk)
                    if self.flush:
                        writer.flush()
                        _sync(writer.fileno())
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

    def _attributes(self, source: Path, dest: Path, st: os.stat_result) -> None:
        """*Preserve attributes*: mode, times and, as root, the owner."""
        try:
            shutil.copystat(source, dest, follow_symlinks=self.follow)
        except OSError:
            pass
        if self.is_root:
            try:
                os.chown(dest, st.st_uid, st.st_gid)
            except OSError:
                pass


def error_message(error: OSError) -> str:
    """``name: reason``, as an error box shows an ``OSError``."""
    name = Path(error.filename).name if error.filename else ""
    reason = error.strerror or str(error)
    return f"{name}: {reason}" if name else reason


def _free_space(directory: Path) -> int | None:
    try:
        fs = os.statvfs(directory)
    except OSError:
        return None
    return fs.f_bavail * fs.f_frsize


def _sync(fd: int) -> None:
    """``fsync`` *fd*; a write-back error raises, as a failed write would.

    A file system that cannot sync at all (``EINVAL``, ``ENOTSUP``) has
    nothing to flush, which is not a failure of the copy.
    """
    try:
        os.fsync(fd)
    except OSError as error:
        if error.errno not in (errno.EINVAL, errno.ENOTSUP):
            raise


def _remove_quietly(path: Path) -> None:
    try:
        os.unlink(path)
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
    "POLL", "PRESERVE", "REFRESH", "SKIP", "Stopped", "apply_mask", "resolve_target", "run",
]
