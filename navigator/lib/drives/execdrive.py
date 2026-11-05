"""A drive made of commands run somewhere else: a container, a phone.

What :mod:`~navigator.lib.drives.docker` (``docker exec``, ``podman exec``)
and :mod:`~navigator.lib.drives.adb` (``adb shell -T``) have in common.  There
is no file protocol at the other end, only a POSIX shell and its tools --
GNU coreutils, busybox or Android's toybox -- so every step of a copy, an
erase or a listing is **one process**: a short ``sh`` script given the paths
as ``"$1" "$2"``, never written into it.  :meth:`ExecDrive._run` is the one
place a process is started, so a persistent shell (FISH's way) can stand in
for it later without anything above it changing.

A listing is one ``stat -c`` over the directory's names (:data:`LIST`,
parsed by :func:`parse_stat`); its links are followed in the same run.
``%f`` (the raw mode, in hex) and the rest of the format are in all three
tool sets.

**Data streams through pipes, not tar** -- a departure from the item that
asked for "exec + tar", recorded here: ``cat -- path`` reads a file and
``cat > path`` writes one, a chunk at a time, so the copier counts as it
goes, an overwritten file keeps its owner and inode (``docker cp``'s tar
writes them as uid 0), a file of a size not known beforehand can be written,
and the same works on an Android device, where there is no ``docker cp``.

Failures are the tools' own words mapped back to an ``errno``
(:func:`os_error`): every C library and busybox prints ``strerror``'s text.
A container stopped or a device unplugged is the subclass's
:meth:`ExecDrive.lost` -- :class:`DriveGone`, after ``on_lost``.
"""

from __future__ import annotations

import errno
import io
import os
import re
import stat
import subprocess
import time
from pathlib import PurePosixPath
from typing import IO, Any

from navigator.lib.drives.base import Child, Drive, DriveGone, FileStat
from navigator.lib.drives.location import Location, Site

#: ``stat -c``'s format: the raw mode in hex, size, modified, accessed, uid,
#: gid, links, inode, owner's and group's names, and the name last -- which
#: may hold spaces, and so ends the line.
STAT_FORMAT = "%f %s %Y %X %u %g %h %i %U %G %n"

#: What starts the links' part of a listing's output.
LINKS_MARK = "\x01links"
#: What starts the free space's part.
FREE_MARK = "\x01free"

#: A directory listed: ``$1`` the directory, ``$2`` ``free`` to say the
#: space free there too.  A directory that is not there or cannot be read
#: says so in ``strerror``'s words, which ``cd`` in dash does not.
LIST = r"""
if [ ! -d "$1" ]; then
  stat -c %n -- "$1" >/dev/null || exit 1
  echo "$1: Not a directory" >&2; exit 1
fi
if [ ! -r "$1" ] || [ ! -x "$1" ]; then echo "$1: Permission denied" >&2; exit 1; fi
cd -- "$1" || exit 1
want_free=$2
set --
for f in .* *; do
  case $f in .|..) continue ;; esac
  if [ -e "$f" ] || [ -L "$f" ]; then set -- "$@" "$f"; fi
done
if [ $# -gt 0 ]; then stat -c '""" + STAT_FORMAT + r"""' -- "$@" || true; fi
echo '""" + LINKS_MARK + r"""'
for f in "$@"; do
  if [ -L "$f" ]; then
    stat -L -c '%f %s %Y' -- "$f" 2>/dev/null || echo -
    readlink -- "$f" 2>/dev/null || echo
  fi
done
if [ "$want_free" = free ]; then
  echo '""" + FREE_MARK + r"""'
  df -Pk -- . 2>/dev/null | tail -n 1
fi
"""

#: One file's facts: ``$1``; ``-L`` before it to follow a link.
STAT = "exec stat -c '" + STAT_FORMAT + "' \"$@\""

#: Bytes ``$2`` on from ``$1``'s start, ``$3`` of them: F3's chunks.
READ_AT = r"""
if [ ! -r "$1" ]; then stat -c %n -- "$1" >/dev/null || exit 1; echo "$1: Permission denied" >&2; exit 1; fi
tail -c +"$2" -- "$1" | head -c "$3"
"""

#: ``$1`` written from standard input, made with mode ``$2`` when new (empty: as the umask says).
WRITE = r"""
if [ -n "$2" ] && [ ! -e "$1" ]; then : > "$1" && chmod "$2" -- "$1" || exit 1; fi
exec cat > "$1"
"""
#: The same, added to its end.
APPEND = WRITE.replace('cat > "$1"', 'cat >> "$1"')

#: ``os.rename``: ``$2`` must not be there.
RENAME = r"""
if [ -e "$2" ] || [ -L "$2" ]; then echo "$2: File exists" >&2; exit 1; fi
exec mv -f -- "$1" "$2"
"""
#: ``os.replace``: a file at ``$2`` goes; a directory there is refused, as
#: ``mv`` would move into it.
REPLACE = r"""
if [ -d "$2" ] && [ ! -L "$2" ] && [ ! -d "$1" ]; then echo "$2: Is a directory" >&2; exit 1; fi
exec mv -f -- "$1" "$2"
"""
#: *Preserve attributes*: ``$1`` given mode ``$2`` and times ``$3`` (access)
#: and ``$4`` (modified), ``touch -t``'s POSIX stamps in UTC; whatever
#: cannot be set passed over.
ATTRIBUTES = r"""
chmod "$2" -- "$1" 2>/dev/null
TZ=UTC0 touch -a -t "$3" -- "$1" 2>/dev/null
TZ=UTC0 touch -m -t "$4" -- "$1" 2>/dev/null
true
"""
#: ``$1``'s access time ``$2`` and modified time ``$3``.
UTIME = r"""
TZ=UTC0 touch -a -t "$2" -- "$1" && TZ=UTC0 touch -m -t "$3" -- "$1"
"""

#: Every ``errno`` a tool's message is read for, with the words that say it:
#: ``strerror``'s in glibc and bionic, and musl's where they differ.
_ERRORS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (errno.ENOENT, ("No such file or directory",)),
    (errno.ENOTEMPTY, ("Directory not empty",)),
    (errno.ENOTDIR, ("Not a directory",)),
    (errno.EISDIR, ("Is a directory",)),
    (errno.EEXIST, ("File exists",)),
    (errno.EACCES, ("Permission denied",)),
    (errno.EPERM, ("Operation not permitted",)),
    (errno.EROFS, ("Read-only file system",)),
    (errno.ENOSPC, ("No space left on device",)),
    (errno.ELOOP, ("Too many levels of symbolic links", "Symbolic link loop")),
    (errno.EBUSY, ("Device or resource busy", "Resource busy")),
    (errno.EXDEV, ("Invalid cross-device link", "Cross-device link")),
    (errno.EINVAL, ("Invalid argument",)),
)

_LINE = re.compile(r"^([0-9a-fA-F]+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\S+) (\S+) (.*)$", re.S)


def os_error(text: str, where: Any = None) -> OSError:
    """The ``OSError`` a tool's *text* (its standard error) says, for *where*:
    ``FileNotFoundError`` for *No such file or directory*, and so on; ``EIO``
    with the words themselves when none is recognised."""
    words = " ".join(text.split())
    for code, phrases in _ERRORS:
        if any(phrase in words for phrase in phrases):
            return OSError(code, os.strerror(code), None if where is None else str(where))
    return OSError(errno.EIO, words or os.strerror(errno.EIO), None if where is None else str(where))


class Stat:
    """One ``stat -c`` line, read: an ``os.stat_result`` look-alike, plus
    the owner's and group's names and, for a link, its target's facts."""

    __slots__ = ("st_mode", "st_size", "st_mtime", "st_atime", "st_uid", "st_gid", "st_nlink", "st_ino",
                 "user", "group", "name", "target", "link_text")

    st_dev = 0

    def __init__(self, mode: int, size: int, mtime: float, atime: float, uid: int, gid: int, nlink: int,
                 ino: int, user: str, group: str, name: str) -> None:
        self.st_mode, self.st_size, self.st_mtime, self.st_atime = mode, size, mtime, atime
        self.st_uid, self.st_gid, self.st_nlink, self.st_ino = uid, gid, nlink, ino
        self.user, self.group, self.name = user, group, name
        #: A link's target's ``(mode, size, mtime)``, or None (not a link, or pointing nowhere).
        self.target: tuple[int, int, float] | None = None
        #: What a link says it points at.
        self.link_text: str | None = None

    @property
    def st_mtime_ns(self) -> int:
        return int(self.st_mtime) * 1_000_000_000

    @property
    def st_atime_ns(self) -> int:
        return int(self.st_atime) * 1_000_000_000

    def facts(self) -> FileStat:
        return FileStat(self.st_mode, self.st_size, self.st_mtime, self.st_atime, self.st_uid, self.st_gid,
                        self.st_nlink, 0, self.st_ino)

    @property
    def owner(self) -> str:
        return f"{self.user}:{self.group}"


def parse_stat(text: str) -> list[Stat]:
    """``stat -c STAT_FORMAT``'s lines, read.  A line that does not start
    with the numbers is the rest of the name before it: a name with a
    newline in it."""
    found: list[Stat] = []
    for line in text.split("\n"):
        match = _LINE.match(line)
        if match is None:
            if found:
                found[-1].name += "\n" + line
            continue
        mode, size, mtime, atime, uid, gid, nlink, ino, user, group, name = match.groups()
        found.append(Stat(int(mode, 16), int(size), float(mtime), float(atime), int(uid), int(gid), int(nlink),
                          int(ino), user, group, name))
    return found


def parse_listing(text: str) -> tuple[list[Stat], tuple[int, str] | None]:
    """:data:`LIST`'s output: each child's facts (a link's target's in
    :attr:`Stat.target`) and the free space, if asked."""
    main, _, rest = text.partition(LINKS_MARK + "\n")
    links_part, _, free_part = rest.partition(FREE_MARK + "\n")
    stats = parse_stat(main.rstrip("\n"))
    lines = links_part.split("\n")
    at = 0
    for each in stats:
        if not stat.S_ISLNK(each.st_mode):
            continue
        facts = lines[at] if at < len(lines) else "-"
        each.link_text = (lines[at + 1] if at + 1 < len(lines) else "") or None
        at += 2
        parts = facts.split()
        if len(parts) == 3:
            try:
                each.target = (int(parts[0], 16), int(parts[1]), float(parts[2]))
            except ValueError:
                pass
    return stats, parse_df(free_part)


def parse_df(text: str) -> tuple[int, str] | None:
    """``df -Pk``'s last line: the bytes free and where it is mounted."""
    parts = text.strip().split()
    if len(parts) < 6:
        return None
    try:
        return int(parts[3]) * 1024, " ".join(parts[5:])
    except ValueError:
        return None


def stamp(seconds: float) -> str:
    """*seconds* as ``touch -t`` takes it, in UTC: ``CCYYMMDDhhmm.SS``."""
    return time.strftime("%Y%m%d%H%M.%S", time.gmtime(max(0, int(seconds))))


def _text(data: bytes) -> str:
    return os.fsdecode(data) if data else ""


class _Reader(io.RawIOBase):
    """A process's standard output; its failure, once it ends, an ``OSError``.
    Closing early stops it."""

    def __init__(self, drive: ExecDrive, process: subprocess.Popen[bytes], where: Location) -> None:
        super().__init__()
        self._drive, self._process, self._where = drive, process, where
        self._done = False

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        stdout = self._process.stdout
        assert stdout is not None
        data = stdout.read1(len(buffer)) if hasattr(stdout, "read1") else stdout.read(len(buffer))
        if not data and not self._done:
            self._done = True
            self._drive._ended(self._process, self._where)
        buffer[: len(data)] = data
        return len(data)

    def close(self) -> None:
        if not self.closed:
            process = self._process
            if process.poll() is None:
                process.kill()
            process.wait()
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        super().close()


class _Writer(io.RawIOBase):
    """A process's standard input; its failure an ``OSError`` on ``close``."""

    def __init__(self, drive: ExecDrive, process: subprocess.Popen[bytes], where: Location) -> None:
        super().__init__()
        self._drive, self._process, self._where = drive, process, where

    def writable(self) -> bool:
        return True

    def write(self, data: Any) -> int:
        stdin = self._process.stdin
        assert stdin is not None
        try:
            stdin.write(data)
        except BrokenPipeError:
            self._drive._ended(self._process, self._where)
            raise OSError(errno.EPIPE, os.strerror(errno.EPIPE), str(self._where)) from None
        return len(data)

    def close(self) -> None:
        if self.closed:
            return
        process = self._process
        try:
            if process.stdin is not None:
                try:
                    process.stdin.close()
                except BrokenPipeError:
                    pass
            self._drive._ended(process, self._where)
        finally:
            if process.stderr is not None:
                process.stderr.close()
            super().close()


class _RandomReader:
    """``read_at`` by ``tail -c | head -c``, one process a chunk."""

    def __init__(self, drive: ExecDrive, location: Location) -> None:
        self._drive, self._location = drive, location

    def read_at(self, offset: int, count: int) -> bytes:
        if count <= 0:
            return b""
        return self._drive._run(["sh", "-c", READ_AT, "sh", self._drive.path_of(self._location),
                                 str(offset + 1), str(count)], where=self._location, check_stderr=True)

    def close(self) -> None:
        pass


class ExecDrive(Drive):
    """A drive whose every step is a command run there (see the module).

    A subclass says how a command is run (:meth:`argv`) and when a failure
    means the other end is gone (:meth:`lost`)."""

    polled = True
    seekable = False

    def __init__(self, site: Site) -> None:
        self.site = site
        self.on_lost: Any = None
        #: Where ``.`` (``profiles.HOME``) opens.
        self.home = PurePosixPath("/")

    # -- what a subclass says -----------------------------------------------------------

    def argv(self, words: list[str], *, stdin: bool = False) -> list[str]:
        """The local command line that runs *words* there; *stdin* when it
        reads its standard input."""
        raise NotImplementedError

    def lost(self, text: str, status: int) -> str | None:
        """Why the other end is gone, if a command's standard error *text* and
        exit *status* say it is; None when it was the command that failed."""
        return None

    def missing_shell(self, text: str, status: int) -> bool:
        """Whether *text* says there is no ``sh`` there to run anything with."""
        return False

    @property
    def name(self) -> str:
        """What the boxes call the other end: the container's name, the device's serial."""
        return self.site.host or self.site.scheme

    # -- running ------------------------------------------------------------------------

    def path_of(self, location: Location) -> str:
        return str(location.path)

    def _gone(self, reason: str) -> DriveGone:
        on_lost = self.on_lost
        if on_lost is not None:
            try:
                on_lost()
            except Exception:
                pass
        return DriveGone(self.name, reason)

    def _failure(self, text: str, status: int, where: Any) -> OSError:
        reason = self.lost(text, status)
        if reason is not None:
            return self._gone(reason)
        if self.missing_shell(text, status):
            return OSError(errno.ENOEXEC, f"{self.name} has no shell (sh): nothing can be done there",
                           None if where is None else str(where))
        return os_error(text, where)

    def _run(self, words: list[str], *, input: bytes | None = None, where: Any = None,
             timeout: float | None = None, check_stderr: bool = False) -> bytes:
        """*words* run there; their standard output.  A failure is the
        ``OSError`` its words say (:meth:`_failure`).  *check_stderr*: a run
        that printed nothing but an error failed, whatever its status (a
        pipeline's is its last command's)."""
        argv = self.argv(words, stdin=input is not None)
        try:
            done = subprocess.run(argv, input=input, capture_output=True, timeout=timeout,
                                  stdin=None if input is not None else subprocess.DEVNULL)
        except FileNotFoundError as error:
            raise DriveGone(self.name, f"{argv[0]}: command not found") from error
        except subprocess.TimeoutExpired as error:
            raise OSError(errno.ETIMEDOUT, os.strerror(errno.ETIMEDOUT),
                          None if where is None else str(where)) from error
        text = _text(done.stderr)
        if done.returncode != 0 or (check_stderr and not done.stdout and text.strip()):
            raise self._failure(text, done.returncode, where)
        return done.stdout

    def _sh(self, script: str, *args: str, where: Any = None, timeout: float | None = None) -> bytes:
        return self._run(["sh", "-c", script, "sh", *args], where=where, timeout=timeout)

    def _start(self, words: list[str], *, stdin: bool, where: Location) -> subprocess.Popen[bytes]:
        argv = self.argv(words, stdin=stdin)
        try:
            return subprocess.Popen(argv, stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL if stdin else subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        except FileNotFoundError as error:
            raise DriveGone(self.name, f"{argv[0]}: command not found") from error

    def _ended(self, process: subprocess.Popen[bytes], where: Location) -> None:
        """A streaming process's end: its failure raised."""
        status = process.wait()
        if status != 0:
            text = _text(process.stderr.read()) if process.stderr is not None else ""
            raise self._failure(text, status, where)

    @property
    def _timeout(self) -> float:
        """How long a question (a listing, a stat) may take."""
        from navigator.settings import SETTINGS

        return float(max(30, SETTINGS.remote.timeout))

    # -- names ----------------------------------------------------------------------------

    def get_dir(self, location: Location) -> str:
        from navigator.lib.drives.sessions import protocol_sign

        return f"{protocol_sign(self.site.scheme)}:{self.name}:{location.path}"

    # -- reading --------------------------------------------------------------------------

    def listing(self, location: Location, *, free: bool = False) -> tuple[list[Stat], tuple[int, str] | None]:
        out = self._sh(LIST, self.path_of(location), "free" if free else "", where=location,
                       timeout=self._timeout)
        return parse_listing(_text(out))

    def scan(self, location: Location, show_hidden: bool, sort: str, *, free: bool,
             **options: Any) -> tuple[list, str | None, tuple[int, str] | None]:
        from navigator.lib.appearance import filetypes
        from navigator.lib.drives.listing import DirEntry, order_entries

        mask = options.get("mask", filetypes.ALL_FILES)
        filtered = mask.strip() not in ("", filetypes.ALL_FILES)
        entries: list[DirEntry] = []
        if not location.is_root:
            entries.append(DirEntry("..", True, 0, stat.S_IFDIR | 0o755))
        try:
            stats, space = self.listing(location, free=free)
        except DriveGone:
            raise
        except OSError as error:
            return entries, error.strerror or str(error), None
        for each in stats:
            name = each.name
            if not show_hidden and name.startswith("."):
                continue
            is_link = stat.S_ISLNK(each.st_mode)
            mode, size, mtime = each.st_mode, each.st_size, each.st_mtime
            if is_link and each.target is not None:
                mode, size, mtime = each.target
            is_dir = stat.S_ISDIR(mode)
            if filtered and not is_dir and not filetypes.in_filter(name, mask):
                continue
            entry = DirEntry(name, is_dir, 0 if is_dir else size, mode, mtime, is_link, each.link_text,
                             each.st_uid, each.st_gid)
            entry.owner = each.owner
            if not is_link:  # a link's own count, not its target's: left unknown
                entry.nlink = each.st_nlink
            entries.append(entry)
        order = {key: options[key] for key in ("executables_first", "archives_first", "reverse")
                 if key in options}
        return order_entries(entries, sort, **order), None, space if free else None

    def _stat(self, location: Location, follow: bool) -> FileStat:
        words = ["-L", "--", self.path_of(location)] if follow else ["--", self.path_of(location)]
        out = _text(self._sh(STAT, *words, where=location, timeout=self._timeout))
        found = parse_stat(out.rstrip("\n"))
        if not found:
            raise os_error("No such file or directory", location)
        return found[0].facts()

    def stat(self, location: Location) -> FileStat:
        return self._stat(location, True)

    def lstat(self, location: Location) -> FileStat:
        return self._stat(location, False)

    def children(self, location: Location) -> list[Child]:
        stats, _ = self.listing(location)
        return [(each.name, each.facts()) for each in stats]

    def names(self, location: Location) -> list[str]:
        return [name for name, _ in self.children(location)]

    def readlink(self, location: Location) -> str:
        out = self._run(["readlink", "--", self.path_of(location)], where=location, timeout=self._timeout)
        return _text(out).rstrip("\n")

    def free_bytes(self, location: Location) -> int | None:
        try:
            out = self._run(["df", "-Pk", "--", self.path_of(location)], where=location, timeout=self._timeout)
        except DriveGone:
            raise
        except OSError:
            return None
        space = parse_df(_text(out).strip().rpartition("\n")[2])
        return None if space is None else space[0]

    def open_read(self, location: Location) -> IO[bytes]:
        process = self._start(["cat", "--", self.path_of(location)], stdin=False, where=location)
        return io.BufferedReader(_Reader(self, process, location), 1 << 16)  # type: ignore[return-value]

    def open_random(self, location: Location) -> Any:
        return _RandomReader(self, location)

    # -- writing --------------------------------------------------------------------------

    def open_write(self, location: Location, *, append: bool = False, mode: int = 0o666) -> IO[bytes]:
        made = "" if stat.S_IMODE(mode) == 0o666 else f"{stat.S_IMODE(mode):o}"
        process = self._start(["sh", "-c", APPEND if append else WRITE, "sh", self.path_of(location), made],
                              stdin=True, where=location)
        return _Writer(self, process, location)  # type: ignore[return-value]

    def mkdir(self, location: Location, mode: int = 0o777) -> None:
        words = ["mkdir", "--", self.path_of(location)]
        if stat.S_IMODE(mode) != 0o777:
            words = ["mkdir", "-m", f"{stat.S_IMODE(mode):o}", "--", self.path_of(location)]
        self._run(words, where=location)

    def rmdir(self, location: Location) -> None:
        self._run(["rmdir", "--", self.path_of(location)], where=location)

    def unlink(self, location: Location) -> None:
        # ``rm`` without ``-f`` would ask about a read-only file; with it, a
        # file not there is no error -- so that is looked at first.
        self._sh('if [ ! -e "$1" ] && [ ! -L "$1" ]; then echo "$1: No such file or directory" >&2; exit 1; fi\n'
                 'if [ -d "$1" ] && [ ! -L "$1" ]; then echo "$1: Is a directory" >&2; exit 1; fi\n'
                 'exec rm -f -- "$1"', self.path_of(location), where=location)

    def rename(self, source: Location, dest: Location) -> None:
        self._sh(RENAME, self.path_of(source), self.path_of(dest), where=source)

    def replace(self, source: Location, dest: Location) -> None:
        self._sh(REPLACE, self.path_of(source), self.path_of(dest), where=source)

    def symlink(self, target: str, location: Location) -> None:
        self._run(["ln", "-s", "--", target, self.path_of(location)], where=location)

    def chmod(self, location: Location, mode: int) -> None:
        self._run(["chmod", f"{stat.S_IMODE(mode):o}", "--", self.path_of(location)], where=location)

    def chown(self, location: Location, uid: int, gid: int, *, follow: bool = True) -> None:
        owner = f"{uid if uid >= 0 else ''}:{gid if gid >= 0 else ''}"
        words = ["chown", owner, "--", self.path_of(location)]
        if not follow:
            words.insert(1, "-h")
        self._run(words, where=location)

    def utime(self, location: Location, atime_ns: int, mtime_ns: int, *, follow: bool = True) -> None:
        self._sh(UTIME, self.path_of(location), stamp(atime_ns / 1e9), stamp(mtime_ns / 1e9), where=location)

    def copy_attributes(self, source_drive: Drive, source: Location, dest: Location, st: Any, *,
                        follow: bool) -> None:
        """Mode and both times in one run: one round trip a file, not three."""
        if not follow and stat.S_ISLNK(getattr(st, "st_mode", 0)):
            return
        try:
            self._sh(ATTRIBUTES, self.path_of(dest), f"{stat.S_IMODE(st.st_mode):o}",
                     stamp(st.st_atime_ns / 1e9), stamp(st.st_mtime_ns / 1e9), where=dest)
        except DriveGone:
            raise
        except OSError:
            pass


__all__ = ["ExecDrive", "LIST", "STAT_FORMAT", "Stat", "os_error", "parse_df", "parse_listing", "parse_stat",
           "stamp"]
