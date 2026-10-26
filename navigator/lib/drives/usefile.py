"""Files from another drive made local for a program: DN's ``UseFile``.

``TLinkDrive.UseFile`` (``NAVYLINK.PAS``) copied a file from the other PC
into the swap directory before F3 or Enter ran anything on it, because a
program can only open a file the system can name.  :func:`fetch` is that:
the files asked for, downloaded into a directory of their own under
Navigator's private temporary directory
(:func:`navigator.lib.system.tempdir.private_dir`), their names kept.

**And back again**, a departure: DN's link drive refused to edit across the
cable.  What a program changed is told by :func:`changed` -- the local
copy's size or time no longer what the download left -- and
:func:`upload` puts it back: written beside the original under a name of its
own and renamed over it, so the original is whole until the new one is.
:func:`conflicts` says which originals changed on the drive meanwhile, for
the caller to ask about first.

Everything here blocks: a thread runs it, under a progress box.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from navigator.lib.drives import Location, drive_of
from navigator.lib.system.job import Stopped


@dataclass
class TempCopy:
    """One file made local: where it came from, where it is, and how both
    stood when it was fetched."""

    origin: Location
    local: Path
    #: The local copy's size and ``st_mtime_ns`` as fetched.
    size: int = 0
    mtime_ns: int = 0
    #: The original's, as fetched: what :func:`conflicts` compares against.
    origin_size: int = 0
    origin_mtime: float = 0.0
    #: The drive it was fetched through and goes back through, when not
    #: *origin*'s own: the root helper's, for a file opened *As root*.
    drive: Any = None

    def through(self) -> Any:
        return self.drive or drive_of(self.origin)


@dataclass
class UseSet:
    """The files one command, viewer or editor was given, in one directory."""

    directory: Path
    copies: list[TempCopy] = field(default_factory=list)

    def local_for(self, origin: Location) -> Path | None:
        for copy in self.copies:
            if copy.origin == origin:
                return copy.local
        return None


#: Where the copies are kept, under the private directory.
REMOTE = "remote"


def _scratch(origin: Location) -> Path:
    """A fresh directory for one set of copies: under one for this process,
    which :func:`sweep` tells from a dead one's, and one for *origin*'s site."""
    from navigator.lib.system.tempdir import private_dir

    site = hashlib.sha1(str(origin.site).encode()).hexdigest()[:12]
    base = private_dir() / REMOTE / str(os.getpid()) / site
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    return Path(tempfile.mkdtemp(dir=base))


def fetch(origins: list[Location], job: Any, drive: Any = None) -> UseSet:
    """*origins* downloaded into one new directory.  *job*'s ``position``
    and ``total`` count the bytes; stopping it leaves nothing behind.
    *drive*, when given, is what they are read through (and put back
    through) instead of their own."""
    if not origins:
        raise ValueError("nothing to fetch")
    directory = _scratch(origins[0])
    use = UseSet(directory)
    try:
        stats = [(drive or drive_of(origin)).stat(origin) for origin in origins]
        job.total = sum(st.st_size for st in stats)
        job.position = 0
        for origin, st in zip(origins, stats):
            local = directory / origin.name
            # Never readable by others, whatever the original allowed: a
            # copy made as root may hold what only root could read.
            with (drive or drive_of(origin)).open_read(origin) as reader, \
                    open(os.open(local, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "wb") as writer:
                _pump(reader, writer, job)
            os.utime(local, ns=(st.st_atime_ns, st.st_mtime_ns))
            os.chmod(local, st.st_mode & 0o700 | 0o600 if drive is not None else st.st_mode & 0o777 | 0o600)
            mine = os.stat(local)
            use.copies.append(TempCopy(origin, local, mine.st_size, mine.st_mtime_ns, st.st_size, st.st_mtime,
                                       drive=drive))
    except BaseException:
        discard(use)
        raise
    return use


def _pump(reader: Any, writer: Any, job: Any, chunk: int = 1 << 20) -> None:
    while True:
        job.wait_while_paused()
        if job.stopped:
            raise Stopped
        data = reader.read(chunk)
        if not data:
            return
        writer.write(data)
        job.position += len(data)


def blank(origin: Location) -> UseSet:
    """An empty copy of a file not there yet on its drive: what Shift+F4
    edits for a new name there, which F2's upload then makes."""
    directory = _scratch(origin)
    use = UseSet(directory)
    local = directory / origin.name
    local.touch(mode=0o600)
    use.copies.append(TempCopy(origin, local, 0, -1))  # an unchanged copy too is put back
    return use


def put_files(files: list[Path], directory: Location, job: Any,
              ask: Callable[[list[Location]], set[Location]] | None = None,
              drive: Any = None) -> list[Location]:
    """Files made on the disk -- a staging directory's -- written into
    *directory* on its drive under their own names, each beside under a name
    of its own and renamed over: what a command that can only write to the
    disk (UU encode and decode) leaves where it was asked to.  *ask* is
    given those there already, before anything is written, and answers the
    ones to leave alone (or raises ``Stopped``).  Answers the places written.
    *drive*, when given, writes them instead of *directory*'s own (the root
    helper's, for *As root*)."""
    drive = drive or drive_of(directory)
    drive.makedirs(directory)
    keep: set[Location] = set()
    if ask is not None:
        existing = [directory / local.name for local in files]
        existing = [target for target in existing if drive.exists(target)]
        if existing:
            keep = ask(existing)
    written = []
    for local in files:
        target = directory / local.name
        if target in keep:
            continue
        beside = directory / f".{local.name}.nav-{secrets.token_hex(3)}"
        replace = drive.can("rename")
        try:
            with open(local, "rb") as reader, drive.open_write(beside if replace else target) as writer:
                _pump(reader, writer, job)
            if replace:
                drive.replace(beside, target)
        except BaseException:
            if replace:
                try:
                    drive.unlink(beside)
                except OSError:
                    pass
            raise
        written.append(target)
    drive.finish()
    return written


#: How much of a file on another drive a quick view fetches.
HEAD_LIMIT = 1 << 20


def fetch_head(origin: Location, limit: int = HEAD_LIMIT) -> UseSet:
    """The first *limit* bytes of *origin*, in a directory of their own under
    its name: what Ctrl+Q's quick view shows of a file on another drive,
    whose whole is not worth a round trip per cursor move."""
    directory = _scratch(origin)
    use = UseSet(directory)
    try:
        local = directory / origin.name
        with drive_of(origin).open_read(origin) as reader, open(local, "wb") as writer:
            left = limit
            while left > 0:
                data = reader.read(min(left, 1 << 16))
                if not data:
                    break
                writer.write(data)
                left -= len(data)
        use.copies.append(TempCopy(origin, local))
    except BaseException:
        discard(use)
        raise
    return use


def changed(use: UseSet) -> list[TempCopy]:
    """The copies a program has written to since they were fetched."""
    found = []
    for copy in use.copies:
        try:
            st = os.stat(copy.local)
        except OSError:
            continue
        if (st.st_size, st.st_mtime_ns) != (copy.size, copy.mtime_ns):
            found.append(copy)
    return found


def conflicts(copies: list[TempCopy]) -> list[TempCopy]:
    """Those of *copies* whose original changed on its drive since the fetch."""
    found = []
    for copy in copies:
        try:
            st = copy.through().stat(copy.origin)
        except FileNotFoundError:
            continue
        if (st.st_size, int(st.st_mtime)) != (copy.origin_size, int(copy.origin_mtime)):
            found.append(copy)
    return found


def upload(copies: list[TempCopy], job: Any) -> None:
    """*copies* put back over their originals, each whole or not at all."""
    job.total = sum(os.stat(copy.local).st_size for copy in copies)
    job.position = 0
    for copy in copies:
        origin = copy.origin
        drive = copy.through()
        if getattr(drive, "write_file", None) is not None and origin.is_local:
            # As root: the editor's write, owner and mode kept, in one rename
            # -- a new file made by root would be root's.
            def chunks(local: Path = copy.local) -> Any:
                with open(local, "rb") as reader:
                    while data := reader.read(1 << 20):
                        job.position += len(data)
                        yield data

            drive.write_file(Path(origin.local), chunks(), job)
            st = drive.stat(origin)
            mine = os.stat(copy.local)
            copy.size, copy.mtime_ns = mine.st_size, mine.st_mtime_ns
            copy.origin_size, copy.origin_mtime = st.st_size, st.st_mtime
            continue
        try:
            mode = drive.stat(origin).st_mode & 0o7777
        except FileNotFoundError:
            mode = os.stat(copy.local).st_mode & 0o777
        beside = origin.parent / f".{origin.name}.nav-{secrets.token_hex(3)}"
        replace = drive.can("rename")
        target = beside if replace else origin
        try:
            with open(copy.local, "rb") as reader, drive.open_write(target, mode=mode) as writer:
                _pump(reader, writer, job)
            if replace:
                try:
                    drive.chmod(beside, mode)
                except OSError:
                    pass
                drive.replace(beside, origin)
        except BaseException:
            if replace:
                try:
                    drive.unlink(beside)
                except OSError:
                    pass
            raise
        drive.finish()
        st = drive.stat(origin)
        mine = os.stat(copy.local)
        copy.size, copy.mtime_ns = mine.st_size, mine.st_mtime_ns
        copy.origin_size, copy.origin_mtime = st.st_size, st.st_mtime


def discard(use: UseSet) -> None:
    """The copies gone, and their directory."""
    shutil.rmtree(use.directory, ignore_errors=True)


def sweep() -> None:
    """The copies a Navigator that is gone left behind -- quit while a program
    had them open, or killed.  Another one still running keeps its own.  Run
    once, at start, on a thread."""
    from navigator.lib.system.tempdir import private_dir, temp_root

    if not (temp_root() / f"navigator-{os.getuid()}" / REMOTE).is_dir():
        return  # nothing was ever fetched: nothing is made just to look
    try:
        holders = list((private_dir() / REMOTE).iterdir())
    except OSError:
        return
    for holder in holders:
        try:
            pid = int(holder.name)
        except ValueError:
            continue
        if pid == os.getpid() or _alive(pid):
            continue
        shutil.rmtree(holder, ignore_errors=True)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


__all__ = ["HEAD_LIMIT", "TempCopy", "UseSet", "changed", "conflicts", "discard", "fetch", "fetch_head", "sweep",
           "upload"]
