"""An archive as a drive: DOS Navigator's ``TArcDrive`` (``ARCVIEW.PAS``).

Enter on an archive put a ``TArcDrive`` on top of the panel's drive, through
``Prev``; the panel then listed the archive's directories as a disk's, F3 and
F5 took files out of it, F5 into it packed them (``ArchiveFiles``, by the
target's sign), F8 erased in it, and ``..`` at its root (``ChangeUp``) went
back to the drive below with the cursor on the archive.  :class:`ArchiveDrive`
is that, over Python's own :mod:`zipfile` and :mod:`tarfile` -- where DN ran a
packer for every step -- and over 7-Zip's command line for 7z and rar
(:mod:`navigator.lib.drives.arctool`), where Python reads neither.

A location in an archive has the archive's own location as its ``outer``
(``Location.outer`` is DN's ``Prev``) and the path inside as its path; its
text is ``/dir/name.zip#/inside``.  The drive is found by that ``outer``
(:func:`navigator.lib.drives.drive_of`), registered by :func:`open_archive`
and let go once no panel is in it.

**Writing is a rewrite**, as DN's packers rewrote: neither format can take a
member out, and a compressed tar cannot even take one in.  Each step --
a file written, a directory made, a name erased or renamed -- changes the
drive's index in memory, a new file's bytes staged on the disk beside it;
:meth:`ArchiveDrive.finish`, which whoever did the steps calls once at the
end (``Drive.finish``), writes the whole archive anew from the index beside
the old one, keeping each member's compression, and renames it over -- the
old archive whole until the new one is.  An archive on another drive was
fetched to be opened; it is put back there afterwards.

Everything here blocks: opening reads the whole index, which for a
compressed tar is the whole file, and a rewrite writes it all again.  A
thread runs it.
"""

from __future__ import annotations

import errno
import io
import lzma
import os
import shutil
import stat
import tarfile
import tempfile
import threading
import time
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import IO, Any

from navigator.lib.drives.base import CHMOD, RENAME, SYMLINK, WRITE, Child, Drive, FileStat
from navigator.lib.drives.location import Location, Site

#: Every archive location's site: which archive is the ``outer``'s business.
ARCHIVE_SITE = Site("arc")

#: The names a new archive may be made under -- a copy's target that is not
#: there yet -- and what each is written as.
NEW_KINDS: tuple[tuple[str, str, str], ...] = (
    (".zip", "zip", ""), (".jar", "zip", ""),
    (".tar.gz", "tar", "gz"), (".tgz", "tar", "gz"),
    (".tar.bz2", "tar", "bz2"), (".tbz", "tar", "bz2"), (".tbz2", "tar", "bz2"),
    (".tar.xz", "tar", "xz"), (".txz", "tar", "xz"),
    (".tar", "tar", ""),
    (".7z", "7z", ""),
)

#: The kinds read through an archiver's command line (``arctool``).
TOOL_KINDS = ("7z", "rar")


class NotAnArchive(Exception):
    """The file is not one this drive can read: Enter runs it instead."""


class NeedsTool(NotAnArchive):
    """An archive by its signature -- a 7z, a rar -- with nothing here to read
    it: Enter says what to install rather than running it."""


@dataclass
class _Member:
    name: str
    is_dir: bool
    size: int = 0
    mtime: float = 0.0
    mode: int = 0
    link: str | None = None
    owner: str | None = None
    #: How many bytes it takes in the archive (DN's ``PSize``); None where
    #: that is not known -- a tar's, a solid 7z block's, one written since.
    packed: int | None = None
    #: The ``ZipInfo``, ``TarInfo`` or ``ToolInfo`` in the archive as it is on disk; None
    #: for a directory only implied, or one made since.
    info: Any = None
    #: New bytes, written since the archive was read: the file they wait in.
    staged: Path | None = None
    children: dict[str, _Member] = field(default_factory=dict)

    def stat(self) -> FileStat:
        kind = stat.S_IFDIR if self.is_dir else (stat.S_IFLNK if self.link is not None else stat.S_IFREG)
        perms = self.mode & 0o7777 or (0o755 if self.is_dir else 0o644)
        size, mtime = self.size, self.mtime
        if self.staged is not None:
            try:
                st = os.stat(self.staged)
                size, mtime = st.st_size, st.st_mtime
            except OSError:
                pass
        return FileStat(kind | perms, 0 if self.is_dir else size, mtime, mtime)


def _error(code: int, where: Any) -> OSError:
    kind = {errno.ENOENT: FileNotFoundError, errno.ENOTDIR: NotADirectoryError,
            errno.EISDIR: IsADirectoryError, errno.EEXIST: FileExistsError}.get(code, OSError)
    return kind(code, os.strerror(code), str(where))


class _Locked(io.RawIOBase):
    """A member being read, one read at a time across every thread: a tar's
    members share its one file, each read seeking where it needs."""

    def __init__(self, handle: IO[bytes], lock: threading.Lock) -> None:
        super().__init__()
        self._handle, self._lock = handle, lock

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        with self._lock:
            return self._handle.read(size)

    def readinto(self, buffer: Any) -> int:
        data = self.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)

    def close(self) -> None:
        with self._lock:
            self._handle.close()
        super().close()


def _compression_of(path: Path) -> str:
    """A tar's compression, by its first bytes: ``gz``, ``bz2``, ``xz`` or ``""``."""
    try:
        with open(path, "rb") as file:
            head = file.read(6)
    except OSError:
        return ""
    if head[:2] == b"\x1f\x8b":
        return "gz"
    if head[:3] == b"BZh":
        return "bz2"
    if head == b"\xfd7zXZ\x00":
        return "xz"
    return ""


class ArchiveDrive(Drive):
    """One archive's files, read and rewritten through :mod:`zipfile` or
    :mod:`tarfile`, or read (and a 7z rewritten) through 7-Zip."""

    capabilities = frozenset((WRITE, RENAME, CHMOD, SYMLINK))
    site = ARCHIVE_SITE

    def __init__(self, outer: Location, local: Path, *, use: Any = None,
                 new: tuple[str, str] | None = None) -> None:
        """*new* -- ``(kind, compression)`` -- makes an empty archive, written
        at the first :meth:`finish`, where *local* is not there yet."""
        self.outer = outer
        self.local = local
        #: The fetched copy, for an archive on another drive; discarded on close.
        self.use = use
        #: One read of the archive's file at a time.
        self._lock = threading.Lock()
        #: The index: every step that reads or changes it holds this.
        self._tree = threading.RLock()
        self._staging: Path | None = None
        self._dirty = False
        if new is not None:
            self.kind, self.compression = new
            self._archive = None
            self._dirty = True
        else:
            self.kind, self._archive = _open(local)
            self.compression = _compression_of(local) if self.kind == "tar" else ""
        if self.kind == "rar":
            # Nothing writes a rar but rar itself, which is not free.
            self.capabilities = frozenset()
        self.root = _Member("", True)
        self._index()

    # -- the index -----------------------------------------------------------------------------

    def _place(self, path: str, member: _Member) -> None:
        parts = [part for part in PurePosixPath(path).parts if part not in ("/", ".", "..")]
        if not parts:
            return
        node = self.root
        for part in parts[:-1]:
            child = node.children.get(part)
            if child is None or not child.is_dir:
                child = node.children[part] = _Member(part, True, mtime=member.mtime)
            node = child
        last = parts[-1]
        existing = node.children.get(last)
        if existing is not None and existing.is_dir and member.is_dir:
            existing.info, existing.mode, existing.mtime = member.info, member.mode, member.mtime
            existing.owner = member.owner
            return
        member.name = last
        if existing is not None and existing.is_dir:
            member.children = existing.children
        node.children[last] = member

    def _index(self) -> None:
        if self._archive is None:
            return
        if self.kind == "zip":
            for info in self._archive.infolist():
                mode = (info.external_attr >> 16) & 0xFFFF
                is_dir = info.is_dir() or stat.S_ISDIR(mode)
                mtime = time.mktime(info.date_time + (0, 0, -1)) if info.date_time[0] >= 1980 else 0.0
                link = None
                if stat.S_ISLNK(mode):
                    link = self._archive.read(info).decode("utf-8", "surrogateescape")
                self._place(info.filename, _Member(info.filename, is_dir, info.file_size, mtime,
                                                   stat.S_IMODE(mode), link, None,
                                                   None if is_dir else info.compress_size, info))
        elif self.kind in TOOL_KINDS:
            for info in self._archive.infolist():
                link = None
                if info.is_link:
                    try:
                        link = self._archive.read_link(info)
                    except OSError:
                        link = ""  # damaged: listed still, for Test to say so
                self._place(info.path, _Member(info.path, info.is_dir, info.size, info.mtime, info.mode,
                                               link, None, None if info.is_dir else info.packed, info))
        else:
            for info in self._archive.getmembers():
                if not (info.isfile() or info.isdir() or info.issym()):
                    continue  # devices, FIFOs, hard links: not files to list
                owner = f"{info.uname or info.uid}:{info.gname or info.gid}"
                link = info.linkname if info.issym() else None
                self._place(info.name, _Member(info.name, info.isdir(), info.size, float(info.mtime),
                                               info.mode, link, owner, None, info))

    def _member(self, location: Location) -> _Member:
        node = self.root
        for part in location.path.parts:
            if part == "/":
                continue
            if not node.is_dir:
                raise _error(errno.ENOTDIR, location)
            child = node.children.get(part)
            if child is None:
                raise _error(errno.ENOENT, location)
            node = child
        return node

    def _parent(self, location: Location) -> tuple[_Member, str]:
        if location.is_root:
            raise _error(errno.EINVAL, location)
        parent = self._member(location.parent)
        if not parent.is_dir:
            raise _error(errno.ENOTDIR, location)
        return parent, location.name

    def at(self, inner: str = "/") -> Location:
        """*inner* in this archive."""
        return Location(ARCHIVE_SITE, PurePosixPath(inner), self.outer)

    # -- names ---------------------------------------------------------------------------------

    @property
    def sign(self) -> str:
        """DN's ``GetSign``: ``ZIP``, ``TAR``."""
        return self.kind.upper()

    def get_dir(self, location: Location) -> str:
        """``ZIP:name.zip:/inside``: DN's ``ZIP:C:NAME.ZIP\\INSIDE``, the
        archive's own directory left out as DN left it out."""
        return f"{self.sign}:{self.outer.name}:{location.path}"

    # -- reading -------------------------------------------------------------------------------

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.appearance import filetypes
        from navigator.lib.drives.listing import DirEntry, order_entries

        mask = options.get("mask", filetypes.ALL_FILES)
        filtered = mask.strip() not in ("", filetypes.ALL_FILES)
        # Always a way up: at the root it leaves the archive (``ChangeUp``).
        entries = [DirEntry("..", True, 0, stat.S_IFDIR | 0o755)]
        with self._tree:
            try:
                node = self._member(location)
            except OSError as error:
                return entries, error.strerror, None
            for name, member in list(node.children.items()):
                if not show_hidden and name.startswith("."):
                    continue
                if filtered and not member.is_dir and not filetypes.in_filter(name, mask):
                    continue
                # A link is described by what it points at, as on a disk.
                st = self.stat(location / name) if member.link is not None else member.stat()
                entry = DirEntry(name, stat.S_ISDIR(st.st_mode), st.st_size, st.st_mode, st.st_mtime,
                                 member.link is not None, member.link)
                entry.owner = member.owner
                entry.packed = None if member.staged is not None else member.packed
                entries.append(entry)
        order = {key: options[key] for key in ("executables_first", "archives_first", "reverse")
                 if key in options}
        return order_entries(entries, sort, **order), None, None

    def stat(self, location: Location) -> FileStat:
        with self._tree:
            member = self._member(location)
            if member.link is not None:
                # Followed by name inside the archive, if it points anywhere in it.
                target = location.parent.path / member.link
                try:
                    return self._member(Location(ARCHIVE_SITE, PurePosixPath(os.path.normpath(target)),
                                                 self.outer)).stat()
                except OSError:
                    pass
            return member.stat()

    def lstat(self, location: Location) -> FileStat:
        with self._tree:
            return self._member(location).stat()

    def children(self, location: Location) -> list[Child]:
        with self._tree:
            node = self._member(location)
            if not node.is_dir:
                raise _error(errno.ENOTDIR, location)
            return [(name, member.stat()) for name, member in sorted(node.children.items())]

    def names(self, location: Location) -> list[str]:
        return [name for name, _ in self.children(location)]

    def readlink(self, location: Location) -> str:
        with self._tree:
            member = self._member(location)
        if member.link is None:
            raise _error(errno.EINVAL, location)
        return member.link

    def open_read(self, location: Location) -> IO[bytes]:
        with self._tree:
            member = self._member(location)
        if member.is_dir:
            raise _error(errno.EISDIR, location)
        if member.staged is not None:
            return open(member.staged, "rb")
        if member.info is None or self._archive is None:
            raise _error(errno.ENOENT, location)
        with self._lock:
            if self.kind != "tar":
                handle = self._archive.open(member.info)
            else:
                handle = self._archive.extractfile(member.info)
                if handle is None:
                    raise _error(errno.EINVAL, location)
        return io.BufferedReader(_Locked(handle, self._lock), 1 << 16)  # type: ignore[return-value]

    # -- writing: the index changed, the bytes staged --------------------------------------------

    def _stage(self) -> Path:
        """A new file to hold bytes written into the archive until it is rewritten."""
        if self._staging is None:
            from navigator.lib.system.tempdir import private_dir

            base = private_dir() / "archive" / str(os.getpid())
            base.mkdir(parents=True, exist_ok=True, mode=0o700)
            self._staging = Path(tempfile.mkdtemp(dir=base))
        fd, name = tempfile.mkstemp(dir=self._staging)
        os.close(fd)
        return Path(name)

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        with self._tree:
            parent, name = self._parent(location)
            member = parent.children.get(name)
            if member is not None and member.is_dir:
                raise _error(errno.EISDIR, location)
            staged = self._stage()
            if member is not None and append:
                with self.open_read(location) as reader, open(staged, "wb") as writer:
                    shutil.copyfileobj(reader, writer)
            if member is None:
                member = parent.children[name] = _Member(name, False, mode=mode & 0o7777 & ~_UMASK)
            member.staged, member.info, member.link = staged, None, None
            member.mtime = time.time()
            self._dirty = True
        return open(staged, "ab" if append else "wb")

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        with self._tree:
            parent, name = self._parent(location)
            if name in parent.children:
                raise _error(errno.EEXIST, location)
            parent.children[name] = _Member(name, True, mtime=time.time(), mode=mode & 0o7777 & ~_UMASK)
            self._dirty = True

    def rmdir(self, location: Location) -> None:
        with self._tree:
            parent, name = self._parent(location)
            member = parent.children.get(name)
            if member is None:
                raise _error(errno.ENOENT, location)
            if not member.is_dir:
                raise _error(errno.ENOTDIR, location)
            if member.children:
                raise _error(errno.ENOTEMPTY, location)
            del parent.children[name]
            self._dirty = True

    def unlink(self, location: Location) -> None:
        with self._tree:
            parent, name = self._parent(location)
            member = parent.children.get(name)
            if member is None:
                raise _error(errno.ENOENT, location)
            if member.is_dir:
                raise _error(errno.EISDIR, location)
            del parent.children[name]
            self._dirty = True

    def _move(self, source: Location, dest: Location, *, replace: bool) -> None:
        with self._tree:
            source_parent, source_name = self._parent(source)
            member = source_parent.children.get(source_name)
            if member is None:
                raise _error(errno.ENOENT, source)
            dest_parent, dest_name = self._parent(dest)
            if member.is_dir and dest.path.is_relative_to(source.path):
                raise _error(errno.EINVAL, dest)
            there = dest_parent.children.get(dest_name)
            if there is not None:
                if there.is_dir and (not member.is_dir or there.children):
                    raise _error(errno.EISDIR if not member.is_dir else errno.ENOTEMPTY, dest)
                if not replace and member.is_dir and not there.is_dir:
                    raise _error(errno.ENOTDIR, dest)
            del source_parent.children[source_name]
            member.name = dest_name
            dest_parent.children[dest_name] = member
            self._dirty = True

    def rename(self, source: Location, dest: Location) -> None:
        self._move(source, dest, replace=False)

    def replace(self, source: Location, dest: Location) -> None:
        self._move(source, dest, replace=True)

    def symlink(self, target: str, location: Location) -> None:
        with self._tree:
            parent, name = self._parent(location)
            if name in parent.children:
                raise _error(errno.EEXIST, location)
            parent.children[name] = _Member(name, False, len(target), time.time(), 0o777, target)
            self._dirty = True

    def chmod(self, location: Location, mode: int) -> None:
        with self._tree:
            self._member(location).mode = mode & 0o7777
            self._dirty = True

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        with self._tree:
            member = self._member(location)
            member.mtime = mtime_ns / 1e9
            if member.staged is not None:
                os.utime(member.staged, ns=(atime_ns, mtime_ns))
            self._dirty = True

    # -- the rewrite ---------------------------------------------------------------------------

    def finish(self) -> None:
        """Every change since the last, written into the archive: the whole of
        it anew beside it, renamed over it, and -- for one fetched from another
        drive -- put back there.  Nothing to do when nothing changed."""
        with self._tree:
            if not self._dirty:
                return
            directory = self.local.parent
            fd, name = tempfile.mkstemp(prefix=f".{self.local.name}.", dir=directory)
            os.close(fd)
            new = Path(name)
            try:
                with self._lock:
                    if self.kind == "zip":
                        self._write_zip(new)
                    elif self.kind == "7z":
                        self._write_7z(new)
                    else:
                        self._write_tar(new)
                if self.local.exists():
                    shutil.copymode(self.local, new)
                else:
                    os.chmod(new, 0o666 & ~_UMASK)
                os.replace(new, self.local)
            except BaseException:
                try:
                    new.unlink()
                except OSError:
                    pass
                raise
            if self._archive is not None:
                self._archive.close()
            self.kind, self._archive = _open(self.local)
            self.root = _Member("", True)
            self._index()
            self._dirty = False
            if self._staging is not None:
                shutil.rmtree(self._staging, ignore_errors=True)
                self._staging = None
            if self.use is not None:
                self._put_back()

    def _put_back(self) -> None:
        """The rewritten copy of an archive from another drive, back there."""
        from navigator.lib.drives import usefile

        class _Quiet:
            position = total = 0
            stopped = False

            def wait_while_paused(self) -> None:
                pass

        copy = self.use.copies[0]
        usefile.upload([copy], _Quiet())

    def _walk(self, node: _Member, prefix: str = "") -> Any:
        """``(path, member)`` for every member of *node*, parents first."""
        for name, member in sorted(node.children.items()):
            path = f"{prefix}{name}"
            yield path, member
            if member.is_dir:
                yield from self._walk(member, path + "/")

    def _write_zip(self, target: Path) -> None:
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
            for path, member in self._walk(self.root):
                old = member.info if member.staged is None else None
                if member.is_dir:
                    info = zipfile.ZipInfo(path + "/", _zip_time(member.mtime))
                    info.external_attr = ((stat.S_IFDIR | (member.mode & 0o7777 or 0o755)) << 16) | 0x10
                    out.writestr(info, b"")
                    continue
                if member.link is not None:
                    info = zipfile.ZipInfo(path, _zip_time(member.mtime))
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    info.create_system = 3
                    out.writestr(info, member.link.encode("utf-8", "surrogateescape"))
                    continue
                # A new header, never the old one -- the old archive is read
                # through it meanwhile -- keeping the member's compression.
                info = zipfile.ZipInfo(path, _zip_time(member.mtime))
                info.compress_type = old.compress_type if old is not None else zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | (member.mode & 0o7777 or 0o644)) << 16
                info.create_system = 3
                info.date_time = _zip_time(member.mtime)
                size = member.stat().st_size
                with self._source(member) as reader, out.open(info, "w", force_zip64=size >= 1 << 31) as writer:
                    shutil.copyfileobj(reader, writer, 1 << 20)

    def _write_tar(self, target: Path) -> None:
        mode = f"w:{self.compression}" if self.compression else "w"
        with tarfile.open(target, mode) as out:
            for path, member in self._walk(self.root):
                old = member.info if member.staged is None else None
                info = tarfile.TarInfo(path)
                if old is not None:
                    info.uid, info.gid, info.uname, info.gname = old.uid, old.gid, old.uname, old.gname
                info.mtime = int(member.mtime)
                info.mode = member.mode & 0o7777 or (0o755 if member.is_dir else 0o644)
                if member.is_dir:
                    info.type = tarfile.DIRTYPE
                    out.addfile(info)
                elif member.link is not None:
                    info.type, info.linkname = tarfile.SYMTYPE, member.link
                    out.addfile(info)
                else:
                    info.size = member.stat().st_size
                    with self._source(member) as reader:
                        out.addfile(info, reader)

    def _write_7z(self, target: Path) -> None:
        """The archive laid out as a directory -- the old one unpacked once,
        not a member at a time, its solid blocks being whole -- and packed
        anew by 7-Zip."""
        from navigator.lib.drives import arctool

        tree = Path(tempfile.mkdtemp(dir=self._stage().parent))
        old = Path(tempfile.mkdtemp(dir=tree.parent))
        try:
            if self._archive is not None and any(
                    member.staged is None and member.info is not None and not member.is_dir
                    for _, member in self._walk(self.root)):
                self._archive.extract_all(old)
            directories = []
            for path, member in self._walk(self.root):
                place = tree / path
                if member.is_dir:
                    place.mkdir()
                    directories.append((place, member))
                    continue
                if member.link is not None:
                    os.symlink(member.link, place)
                    continue
                if member.staged is not None:
                    shutil.copyfile(member.staged, place)
                elif member.info is not None:
                    os.replace(old / member.info.path, place)
                else:
                    place.touch()
                os.chmod(place, member.mode & 0o7777 or 0o644)
                os.utime(place, (member.mtime, member.mtime))
            for place, member in reversed(directories):
                os.chmod(place, member.mode & 0o7777 or 0o755)
                os.utime(place, (member.mtime, member.mtime))
            arctool.write_7z(target, tree)
        finally:
            shutil.rmtree(tree, ignore_errors=True)
            shutil.rmtree(old, ignore_errors=True)

    def _source(self, member: _Member) -> IO[bytes]:
        """Where *member*'s bytes are: its staged file, or the archive as it was."""
        if member.staged is not None:
            return open(member.staged, "rb")
        if self.kind != "tar":
            return self._archive.open(member.info)
        handle = self._archive.extractfile(member.info)
        return handle if handle is not None else io.BytesIO(b"")

    def describe(self) -> list[tuple[str, str]]:
        """``TArcDrive.GetDirInfo``: the archive, what kind, how many files,
        and the packed and unpacked size totals."""
        with self._tree:
            members = sum(1 for _, member in self._walk(self.root) if not member.is_dir)
            unpacked = sum(member.stat().st_size for _, member in self._walk(self.root) if not member.is_dir)
        try:
            packed = os.stat(self.local).st_size
        except OSError:
            packed = 0
        kind = self.sign + (f" ({self.compression})" if self.compression else "")
        return [("Archive", str(self.outer)), ("Kind", kind), ("Files", f"{members:,}"),
                ("Packed", f"{packed:,}"), ("Unpacked", f"{unpacked:,}")]

    # -- testing -------------------------------------------------------------------------------

    def test(self, job: Any, locations: list[Location] | None = None) -> list[tuple[str, str]]:
        """DN's ``cmArcTest``: every member under *locations* (the whole
        archive, for None) read through, its check -- a zip's CRC, a 7z's --
        made on the way.  ``(path, why)`` for each that fails.  7z and rar are
        tested whole by their tool (``7z t``), as DN's archivers were."""
        from navigator.lib.system.job import Stopped

        if self.kind in TOOL_KINDS and self._archive is not None:
            with self._lock:
                return self._archive.test()
        with self._tree:
            nodes = ([(str(location.path).lstrip("/"), self._member(location)) for location in locations]
                     if locations else [("", self.root)])
            members = []
            for path, node in nodes:
                if node.is_dir:
                    prefix = f"{path}/" if path else ""
                    members.extend(self._walk(node, prefix))
                else:
                    members.append((path, node))
            members = [(path, member) for path, member in members
                       if not member.is_dir and member.link is None and member.info is not None
                       and member.staged is None]
        job.total = sum(member.size for _, member in members)
        job.position = 0
        failures = []
        for path, member in members:
            if job.stopped:
                raise Stopped
            try:
                with self._lock:
                    reader = self._source(member)
                with reader:
                    while True:
                        job.wait_while_paused()
                        if job.stopped:
                            raise Stopped
                        with self._lock:
                            chunk = reader.read(1 << 20)
                        if not chunk:
                            break
                        job.position += len(chunk)
            except Stopped:
                raise
            except (OSError, EOFError, zipfile.BadZipFile, tarfile.TarError, zlib.error,
                    lzma.LZMAError, ValueError) as error:
                failures.append((path, str(error) or type(error).__name__))
        return failures

    # -- leaving -------------------------------------------------------------------------------

    def change_up(self, location: Location) -> tuple[Location, str] | None:
        """``TArcDrive.ChangeUp`` at the root: back where the archive is, the
        cursor on it.  By the letters alone, as a handler may ask on the loop."""
        return self.outer.parent, self.outer.name

    def close(self) -> None:
        try:
            self.finish()
        except Exception:
            pass
        try:
            if self._archive is not None:
                self._archive.close()
        except Exception:
            pass
        if self._staging is not None:
            shutil.rmtree(self._staging, ignore_errors=True)
            self._staging = None
        if self.use is not None:
            from navigator.lib.drives import usefile

            usefile.discard(self.use)
            self.use = None


def _zip_time(mtime: float) -> tuple[int, int, int, int, int, int]:
    """*mtime* as a zip keeps it: local time, from 1980, to two seconds."""
    moment = time.localtime(max(mtime, 315532800))
    return moment[:6]


def _read_umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


#: Read once, at import, as ``filecopy``'s is: what a member made here is given.
_UMASK = _read_umask()


def _open(local: Path) -> tuple[str, Any]:
    """``(kind, archive)`` for *local*, by what is in it, not its name."""
    from navigator.lib.drives import arctool

    kind = arctool.kind_of(local)
    if kind is not None:
        try:
            return kind, arctool.ToolArchive(local, kind)
        except arctool.MissingTool as error:
            raise NeedsTool(str(error)) from error
        except OSError as error:
            raise NotAnArchive(error.strerror or str(error)) from error
    try:
        if zipfile.is_zipfile(local):
            return "zip", zipfile.ZipFile(local)
        if tarfile.is_tarfile(local):
            return "tar", tarfile.open(local)
    except (OSError, zipfile.BadZipFile, tarfile.TarError, EOFError) as error:
        raise NotAnArchive(str(error)) from error
    raise NotAnArchive(str(local))


def new_kind(name: str) -> tuple[str, str] | None:
    """``(kind, compression)`` a new archive called *name* is written as, or None."""
    lower = name.lower()
    for suffix, kind, compression in NEW_KINDS:
        if lower.endswith(suffix) and len(lower) > len(suffix):
            return kind, compression
    return None


# -- which archives are open ------------------------------------------------------------------------

_LOCK = threading.Lock()
_OPEN: dict[Location, ArchiveDrive] = {}
#: Who is in each archive open: the panels showing a place in it.  The last
#: one out closes it.
_HOLDERS: dict[Location, set[int]] = {}


def find(outer: Location) -> ArchiveDrive | None:
    with _LOCK:
        return _OPEN.get(outer)


def open_archive(outer: Location, job: Any = None, *, create: bool = False) -> ArchiveDrive:
    """The archive at *outer*, opened (or the one open already) and found by
    :func:`~navigator.lib.drives.drive_of` from now on.  A file on another
    drive is fetched first.  :class:`NotAnArchive` for anything else.

    *create*: where nothing is there yet and the name says what kind
    (:data:`NEW_KINDS`), an empty archive to write into -- DN's
    ``ArchiveFiles`` packing into an archive named on the target line.
    Only on the disk.
    """
    existing = find(outer)
    if existing is not None:
        return existing
    use = None
    if outer.is_local:
        local = outer.local
        if create and not os.path.lexists(local):
            kind = new_kind(local.name)
            if kind is None:
                raise NotAnArchive(str(local))
            drive = ArchiveDrive(outer, local, new=kind)
            return _register(outer, drive)
    else:
        from navigator.lib.drives import usefile

        use = usefile.fetch([outer], job if job is not None else _NoJob())
        local = use.local_for(outer)
    try:
        drive = ArchiveDrive(outer, local, use=use)
    except BaseException:
        if use is not None:
            from navigator.lib.drives import usefile

            usefile.discard(use)
        raise
    return _register(outer, drive)


class _NoJob:
    position = total = 0
    stopped = False

    def wait_while_paused(self) -> None:
        pass


def _register(outer: Location, drive: ArchiveDrive) -> ArchiveDrive:
    with _LOCK:
        if outer in _OPEN:  # opened meanwhile by another panel
            drive.close()
            return _OPEN[outer]
        _OPEN[outer] = drive
    return drive


def hold(outer: Location, holder: object) -> None:
    with _LOCK:
        _HOLDERS.setdefault(outer, set()).add(id(holder))


def leave(outer: Location, holder: object) -> ArchiveDrive | None:
    """*holder* out of *outer*'s archive; the drive, taken out of the open
    ones, when that was the last -- for the caller to close, on a thread."""
    with _LOCK:
        holders = _HOLDERS.get(outer)
        if holders is not None:
            holders.discard(id(holder))
            if holders:
                return None
            del _HOLDERS[outer]
        return _OPEN.pop(outer, None)


def release_unheld(outer: Location) -> None:
    """*outer*'s archive closed if no panel is in it: one opened only to be
    written into (a copy's target), once the copy is done."""
    with _LOCK:
        if _HOLDERS.get(outer):
            return
        drive = _OPEN.pop(outer, None)
    if drive is not None:
        drive.close()


def release_unused(in_use: set[Location]) -> None:
    """Every archive no panel is in any more, closed: DN's ``TArcDrive.Done``."""
    with _LOCK:
        gone = [outer for outer in _OPEN if outer not in in_use]
        drives = [_OPEN.pop(outer) for outer in gone]
        for outer in gone:
            _HOLDERS.pop(outer, None)
    for drive in drives:
        drive.close()


def close_all() -> None:
    release_unused(set())


__all__ = ["ARCHIVE_SITE", "ArchiveDrive", "NEW_KINDS", "NeedsTool", "NotAnArchive", "TOOL_KINDS", "close_all", "find", "hold", "leave",
           "new_kind", "open_archive", "release_unheld", "release_unused"]
