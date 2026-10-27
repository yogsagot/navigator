"""The Trash: the freedesktop.org Trash specification 1.0.

Not DOS Navigator's, which erased for good and offered undelete through its
*Reanimator* (``REANIMAT.PAS``, a raw disk walk no POSIX file system allows).
It is the Trash GNOME, KDE and ``gio trash`` keep, so a file moved there by
one is seen and restored by the others.  Off by default: File Manager Setup's
*Use Trash* (``[file_manager] use_trash``) makes F8 move files here.

* **The home trash** is ``$XDG_DATA_HOME/Trash`` (else
  ``~/.local/share/Trash``), with ``files/`` and ``info/``; a file on
  another file system goes to that file system's own trash -- ``$top/.Trash/$uid``
  when ``$top/.Trash`` is a sticky directory and not a link, else
  ``$top/.Trash-$uid`` -- and **never across file systems**, which the
  specification forbids: :func:`move` raises ``EXDEV`` and the caller asks
  whether to erase instead.
* **The name is reserved by its info file**, made with ``O_EXCL`` before the
  file is renamed into ``files/``; a name taken gets ``.2``, ``.3`` before its
  extension.  ``Path=`` is percent-encoded, absolute in the home trash and
  relative to the top in another; ``DeletionDate=`` is local time.
* ``directorysizes`` is not kept, which the specification allows.

Every function blocks on the disk and runs on a thread.
"""

from __future__ import annotations

import errno
import os
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from navigator.lib.system.job import Job, Stopped
from navigator.lib.system.volumes import parse_mounts

#: An info file's suffix, and its first line.
INFO_SUFFIX = ".trashinfo"
HEADER = "[Trash Info]"
#: ``DeletionDate``'s form: RFC 3339 without a zone, as the specification has it.
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


@dataclass(frozen=True)
class Item:
    """One thing in a trash directory.

    *trash* is the directory holding ``files/`` and ``info/``, *name* the
    name in ``files/``; *original* is where it came from and *deleted* when
    (a ``time.time()``), each None when its info file does not say.
    """

    trash: Path
    name: str
    original: Path | None = None
    deleted: float | None = None

    @property
    def path(self) -> Path:
        """Where the item is now."""
        return self.trash / "files" / self.name

    @property
    def info(self) -> Path:
        return self.trash / "info" / (self.name + INFO_SUFFIX)


def home_trash() -> Path:
    """The home trash directory, whether or not it exists yet."""
    data = os.environ.get("XDG_DATA_HOME") or ""
    base = Path(data) if os.path.isabs(data) else Path.home() / ".local" / "share"
    return base / "Trash"


def _mounts() -> list[str]:
    try:
        text = Path("/proc/self/mounts").read_text(errors="replace")
    except OSError:
        return []
    return [point for _device, point, _type in parse_mounts(text)]


def top_of(path: Path, mounts: list[str] | None = None) -> Path:
    """The mount point *path* is under: the longest one that is a prefix of it."""
    text = str(path)
    best = "/"
    for point in _mounts() if mounts is None else mounts:
        stem = point.rstrip("/")
        if (text == stem or text.startswith(stem + "/")) and len(point) > len(best):
            best = point
    return Path(best)


def _ready(trash: Path, *, make: bool) -> bool:
    """*trash*'s ``files/`` and ``info/`` there, made 0o700 when *make*."""
    try:
        if make:
            for part in (trash / "files", trash / "info"):
                part.mkdir(mode=0o700, parents=True, exist_ok=True)
        return (trash / "files").is_dir() and (trash / "info").is_dir()
    except OSError:
        return False


def _top_trashes(top: Path) -> list[Path]:
    """The specification's two trash directories on the file system at *top*, in its order."""
    uid = str(os.getuid())
    found: list[Path] = []
    shared = top / ".Trash"
    try:
        st = os.lstat(shared)
        if stat.S_ISDIR(st.st_mode) and st.st_mode & stat.S_ISVTX:
            found.append(shared / uid)
    except OSError:
        pass
    found.append(top / f".Trash-{uid}")
    return found


def trash_for(path: Path, mounts: list[str] | None = None) -> tuple[Path, Path | None] | None:
    """The trash directory *path* goes to, and the top its ``Path=`` is relative
    to (None for the home trash, whose paths are absolute); None when there is none."""
    home = home_trash()
    try:
        device = os.lstat(path).st_dev
    except OSError:
        return None
    # The home trash's own file system: where ``$XDG_DATA_HOME`` (or its
    # nearest existing parent) is.
    anchor = home
    while not anchor.exists() and anchor != anchor.parent:
        anchor = anchor.parent
    try:
        if os.stat(anchor).st_dev == device:
            return (home, None) if _ready(home, make=True) else None
    except OSError:
        pass
    top = top_of(path, mounts)
    for trash in _top_trashes(top):
        try:
            if os.lstat(trash.parent).st_dev != device:
                continue
        except OSError:
            continue
        if _ready(trash, make=True):
            return trash, top
    return None


def _candidates(name: str):
    """*name*, then ``stem.2.ext``, ``stem.3.ext``...: ``gio trash``'s spelling."""
    yield name
    stem, extension = os.path.splitext(name)
    number = 2
    while True:
        yield f"{stem}.{number}{extension}"
        number += 1


def info_text(original: str, deleted: float) -> str:
    """An info file's contents for *original* (already relative where it must be)."""
    when = time.strftime(DATE_FORMAT, time.localtime(deleted))
    return f"{HEADER}\nPath={quote(original, safe='/')}\nDeletionDate={when}\n"


def move(path: Path, mounts: list[str] | None = None) -> Item:
    """*path* moved into its trash; the item it became.

    Raises ``OSError`` -- ``EXDEV`` when there is no trash on its file system
    -- and leaves *path* where it was.
    """
    path = Path(os.path.abspath(path))
    os.lstat(path)  # gone already is FileNotFoundError, not "no trash"
    found = trash_for(path, mounts)
    if found is None:
        raise OSError(errno.EXDEV, "No trash on this file system", str(path))
    trash, top = found
    original = str(path) if top is None else os.path.relpath(path, top)
    deleted = time.time()
    text = info_text(original, deleted).encode()
    for name in _candidates(path.name):
        info = trash / "info" / (name + INFO_SUFFIX)
        try:
            fd = os.open(info, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        try:
            os.write(fd, text)
        finally:
            os.close(fd)
        if os.path.lexists(trash / "files" / name):
            # An orphan holds the name: leave it, and try the next.
            os.unlink(info)
            continue
        try:
            os.rename(path, trash / "files" / name)
        except OSError:
            os.unlink(info)
            raise
        return Item(trash, name, path, deleted)
    raise AssertionError("unreachable")


def read_info(trash: Path, name: str, top: Path | None) -> tuple[Path | None, float | None]:
    """What *name*'s info file says: where it came from, and when it went."""
    try:
        text = (trash / "info" / (name + INFO_SUFFIX)).read_text(errors="replace")
    except OSError:
        return None, None
    original: Path | None = None
    deleted: float | None = None
    seen = False
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            seen = line == HEADER
            continue
        if not seen or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key == "Path" and original is None:
            where = unquote(value)
            original = Path(where) if os.path.isabs(where) or top is None else top / where
        elif key == "DeletionDate" and deleted is None:
            try:
                deleted = time.mktime(time.strptime(value, DATE_FORMAT))
            except ValueError:
                pass
    return original, deleted


def trashes(mounts: list[str] | None = None) -> list[tuple[Path, Path | None]]:
    """Every trash directory there is: the home one first, then each mount's."""
    found: list[tuple[Path, Path | None]] = []
    home = home_trash()
    if _ready(home, make=False):
        found.append((home, None))
    seen = {home}
    for point in _mounts() if mounts is None else mounts:
        for trash in _top_trashes(Path(point)):
            if trash not in seen and _ready(trash, make=False):
                seen.add(trash)
                found.append((trash, Path(point)))
    return found


def items(mounts: list[str] | None = None) -> list[Item]:
    """Everything in every trash.  A file with no info file is listed with
    nothing known of it; an info file with no file is not listed."""
    found: list[Item] = []
    for trash, top in trashes(mounts):
        try:
            names = sorted(os.listdir(trash / "files"))
        except OSError:
            continue
        for name in names:
            original, deleted = read_info(trash, name, top)
            found.append(Item(trash, name, original, deleted))
    return found


def restore(item: Item, target: Path | None = None) -> Path:
    """*item* put back where it came from (or at *target*); where it went.

    Never over anything: a name taken there is ``FileExistsError``.  The
    directories on the way are made.
    """
    target = target or item.original
    if target is None:
        raise OSError(errno.ENOENT, "Where it came from is not known", item.name)
    if os.path.lexists(target):
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    os.rename(item.path, target)
    forget(item)
    return target


class RestoreJob(Job):
    """Restore under way: how far it is, and the items put back."""

    def __init__(self, asker: Any = None) -> None:
        super().__init__(asker)
        self.done: list[Item] = []
        self.count = 0
        self.total = 0
        self.current = ""


def restore_all(chosen: list[Item], job: RestoreJob) -> list[Item]:
    """*chosen* restored on a thread, one after another; a failure asks
    (:class:`~navigator.lib.file_ops.filecopy.Failure`) whether to skip it or
    stop.  What was put back, also kept in ``job.done``."""
    from navigator.lib.file_ops.filecopy import Failure, error_message

    job.total = len(chosen)
    try:
        for item in chosen:
            job.wait_while_paused()
            if job.stopped:
                break
            job.current = str(item.original or item.name)
            try:
                restore(item)
            except OSError as error:
                answer = job.ask(Failure(item.original or item.path, error_message(error)))
                if answer is None or answer is False:
                    break
            else:
                job.done.append(item)
            job.count += 1
    except Stopped:
        pass
    return list(job.done)


def forget(item: Item) -> None:
    """*item*'s info file gone, once the item itself is."""
    try:
        os.unlink(item.info)
    except FileNotFoundError:
        pass


__all__ = [
    "Item", "RestoreJob", "forget", "restore_all", "home_trash", "info_text", "items", "move", "read_info", "restore", "top_of",
    "trash_for", "trashes",
]
