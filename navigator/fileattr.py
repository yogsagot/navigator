"""File attributes: the model half of Alt+E, with no widget in it.

DOS Navigator's ``cmSetFAttr`` edited the four DOS bits -- Archive, Hidden,
Read-Only, System -- and a date and time, and none of the four means anything
on Linux.  This is that command's Linux reading, and a departure: the twelve
mode bits, the owner and the group (Midnight Commander's *Advanced chown*),
and the modification time, which is DN's own.

What is DN's and what is not:

* **One dialog for every tagged file**, as ``dlgFilesAttr`` was.  DN gave each
  bit a *Set* and a *Clear* box and left a bit ticked in neither alone; here
  that is one box with a third state, ``[?]``, for a bit the files disagree
  on -- :func:`survey` finds them, and an :class:`AttrRequest` carries only
  the bits the user actually moved.
* **The owner and group are left alone unless named**, and the time unless
  changed.  A ``None`` in the request is *leave it*.
* **The owner goes first**, then the mode: ``chown`` clears set-user-ID and
  set-group-ID, and the mode written after it puts back what was asked for.
* **A tagged symbolic link is followed**, as the panel shows its target's
  mode.  Under a directory being recursed into, a link is **never** followed
  and never changed -- what it points at may be anywhere.
* **Recursion picks what it touches**: the files, the directories, or both,
  under every tagged directory.  The tagged entries themselves are always
  changed.  A directory is changed after its contents, unless it cannot be
  read into now -- then before, because the change is presumably what lets
  it be.
* **A failure asks whether to skip**, as Copy's and erase's do.
"""

from __future__ import annotations

import grp
import os
import pwd
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from navigator.filecopy import Failure, error_message
from navigator.job import Job, Stopped

#: The mode bits the dialog's grid shows, in its order: owner, group and
#: others, each read/write/execute, then set-user-ID, set-group-ID, sticky.
#: Item *i* of the grid is ``BITS[i]``.
BITS = (
    stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
    stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
    stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH,
    stat.S_ISUID, stat.S_ISGID, stat.S_ISVTX,
)

#: Every bit the dialog can change.
MODE_MASK = 0o7777

#: What recursion touches under a tagged directory.
NONE, FILES, DIRS, ALL = "none", "files", "dirs", "all"
RECURSE = (NONE, FILES, DIRS, ALL)

#: The *Attributes* box's first line while it works.
CHANGING = "Changing attributes of"

#: DN's ``Date (D-M-Y)`` and ``Time (H:M:S)``, with a four-digit year.
DATE_FORMAT = "%d-%m-%Y"
TIME_FORMAT = "%H:%M:%S"


# -- bits ------------------------------------------------------------------------


def to_items(mode: int) -> int:
    """*mode*'s bits as the grid's item mask."""
    return sum(1 << index for index, bit in enumerate(BITS) if mode & bit)


def from_items(mask: int) -> int:
    """The grid's item *mask* as mode bits."""
    return sum(bit for index, bit in enumerate(BITS) if mask & (1 << index))


def octal(mode: int, mixed: int = 0) -> str:
    """``0644``, with ``?`` for a digit any *mixed* bit falls in."""
    digits = []
    for shift in (9, 6, 3, 0):
        if (mixed >> shift) & 0o7:
            digits.append("?")
        else:
            digits.append(str((mode >> shift) & 0o7))
    return "".join(digits)


def symbolic(mode: int, mixed: int = 0) -> str:
    """``rwxr-sr-t``, as ``ls -l`` spells it, with ``?`` for a *mixed* bit."""
    chars = []
    triplets = (
        (stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR, stat.S_ISUID, "s"),
        (stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP, stat.S_ISGID, "s"),
        (stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH, stat.S_ISVTX, "t"),
    )
    for read, write, execute, special, letter in triplets:
        chars.append("?" if mixed & read else "r" if mode & read else "-")
        chars.append("?" if mixed & write else "w" if mode & write else "-")
        if mixed & (execute | special):
            chars.append("?")
        elif mode & special:
            chars.append(letter if mode & execute else letter.upper())
        else:
            chars.append("x" if mode & execute else "-")
    return "".join(chars)


def parse_octal(text: str) -> int:
    """One to four octal digits as mode bits; ``ValueError`` otherwise."""
    text = text.strip()
    if not 1 <= len(text) <= 4 or any(c not in "01234567" for c in text):
        raise ValueError(f"{text!r} is not an octal mode")
    return int(text, 8)


# -- what the files are now ------------------------------------------------------


@dataclass
class Survey:
    """What a selection has in common, which is what the dialog opens on."""

    #: The bits set on every file.
    mode: int = 0
    #: The bits set on some files and not on others.
    mixed: int = 0
    #: The owner and group every file has, or ``None`` where they differ.
    uid: int | None = None
    gid: int | None = None
    #: The modification time every file has, to the second, or ``None``.
    mtime: float | None = None
    files: int = 0
    dirs: int = 0
    #: A lone entry's own ``stat``, for the info line.
    single: os.stat_result | None = None
    #: A lone link's target, as ``readlink`` gives it.
    link_target: str | None = None


def survey(paths: Sequence[Path]) -> Survey:
    """What every one of *paths* has, and what they disagree on.

    A link is read through, as the panel reads it; one pointing nowhere is
    read as itself.  An entry that cannot be read at all counts for nothing.
    """
    result = Survey()
    first = True
    uids: set[int] = set()
    gids: set[int] = set()
    mtimes: set[int] = set()
    on, off = 0, 0
    for path in paths:
        try:
            st = os.stat(path)
        except OSError:
            try:
                st = os.lstat(path)
            except OSError:
                continue
        mode = stat.S_IMODE(st.st_mode)
        on |= mode
        off |= ~mode & MODE_MASK
        uids.add(st.st_uid)
        gids.add(st.st_gid)
        mtimes.add(int(st.st_mtime))
        if stat.S_ISDIR(st.st_mode):
            result.dirs += 1
        else:
            result.files += 1
        if first:
            result.single = st
            first = False
        else:
            result.single = None
    result.mixed = on & off
    result.mode = on & ~result.mixed
    result.uid = uids.pop() if len(uids) == 1 else None
    result.gid = gids.pop() if len(gids) == 1 else None
    result.mtime = float(mtimes.pop()) if len(mtimes) == 1 else None
    if result.single is not None and len(paths) == 1 and os.path.islink(paths[0]):
        try:
            result.link_target = os.readlink(paths[0])
        except OSError:
            pass
    return result


# -- owners ----------------------------------------------------------------------


def users() -> list[str]:
    """Every user name the passwd database knows, sorted."""
    return sorted({entry.pw_name for entry in pwd.getpwall()})


def groups() -> list[str]:
    """Every group name the group database knows, sorted."""
    return sorted({entry.gr_name for entry in grp.getgrall()})


def can_chown_user() -> bool:
    """Whether a file may be given to another user: root's alone on Linux."""
    return os.geteuid() == 0


def assignable_groups() -> list[str]:
    """The groups a file may be given to: all of them for root, else the user's own."""
    if can_chown_user():
        return groups()
    names = set()
    for gid in {os.getegid(), *os.getgroups()}:
        names.add(group_name(gid))
    return sorted(names)


def user_name(uid: int) -> str:
    """*uid*'s name, or the number when it has none."""
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def group_name(gid: int) -> str:
    """*gid*'s name, or the number when it has none."""
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return str(gid)


def parse_user(text: str) -> int | None:
    """A user named or numbered; ``None`` for blank, ``ValueError`` for nobody."""
    return _parse_id(text, lambda name: pwd.getpwnam(name).pw_uid, "user")


def parse_group(text: str) -> int | None:
    """A group named or numbered; ``None`` for blank, ``ValueError`` for none."""
    return _parse_id(text, lambda name: grp.getgrnam(name).gr_gid, "group")


def _parse_id(text: str, lookup: Callable[[str], int], kind: str) -> int | None:
    text = text.strip()
    if not text:
        return None
    try:
        return lookup(text)
    except KeyError:
        pass
    if text.isdigit():
        return int(text)
    raise ValueError(f"There is no {kind} {text}")


# -- the time --------------------------------------------------------------------


def date_text(mtime: float | None) -> str:
    return "" if mtime is None else time.strftime(DATE_FORMAT, time.localtime(mtime))


def time_text(mtime: float | None) -> str:
    return "" if mtime is None else time.strftime(TIME_FORMAT, time.localtime(mtime))


def parse_mtime(date: str, clock: str, base: float | None) -> float | None:
    """The modification time *date* and *clock* name, or ``None`` to leave it.

    Both blank is *leave it*.  One blank takes that half from *base*, the
    time every file has now -- and with none to take it from, the whole is
    needed.  A time that comes to *base* again is *leave it* too, so that
    opening the dialog and pressing OK does not round a nanosecond stamp to
    the second.  ``ValueError`` for anything unreadable.
    """
    date, clock = date.strip(), clock.strip()
    if not date and not clock:
        return None
    if base is None and not (date and clock):
        raise ValueError("Give both a date and a time")
    when = time.localtime(base) if base is not None else None
    if date:
        day, month, year = _numbers(date, "-", "date")
        if year < 100:
            year += 2000 if year < 70 else 1900
    else:
        day, month, year = when.tm_mday, when.tm_mon, when.tm_year
    if clock:
        parts = _numbers(clock, ":", "time", minimum=2)
        hour, minute = parts[0], parts[1]
        second = parts[2] if len(parts) > 2 else 0
    else:
        hour, minute, second = when.tm_hour, when.tm_min, when.tm_sec
    try:
        stamp = time.mktime((year, month, day, hour, minute, second, 0, 0, -1))
        check = time.localtime(stamp)
    except (OverflowError, ValueError):
        raise ValueError(f"{date or clock} is not a valid date") from None
    if (check.tm_mday, check.tm_mon) != (day, month) or not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 62):
        raise ValueError(f"{date} {clock}".strip() + " is not a valid date")
    if base is not None and int(stamp) == int(base):
        return None
    return stamp


def _numbers(text: str, separator: str, what: str, minimum: int = 3) -> tuple[int, ...]:
    parts = text.split(separator)
    if not minimum <= len(parts) <= 3 or not all(p.strip().isdigit() for p in parts):
        raise ValueError(f"{text} is not a valid {what}")
    return tuple(int(p) for p in parts)


# -- the request and the work ----------------------------------------------------


@dataclass
class AttrRequest:
    """What the File Attributes dialog was accepted with."""

    sources: list[Path]
    #: Mode bits to turn on, and to turn off; a bit in neither is left alone.
    set_bits: int = 0
    clear_bits: int = 0
    #: The new owner and group, or ``None`` to leave them.
    uid: int | None = None
    gid: int | None = None
    #: The new modification time, or ``None`` to leave it.
    mtime: float | None = None
    #: What to change under a tagged directory: one of :data:`RECURSE`.
    recurse: str = NONE

    @property
    def changes_nothing(self) -> bool:
        return not (
            self.set_bits or self.clear_bits or self.uid is not None
            or self.gid is not None or self.mtime is not None
        )


class AttrJob(Job):
    """A running change of attributes, as the thread and the loop see it."""

    def __init__(self, asker: Callable[[Any], Any] | None = None) -> None:
        super().__init__(asker)
        self.total = 0
        self.done = 0
        self.action = CHANGING
        self.path = ""
        self.measuring = True


def apply_one(path: Path, request: AttrRequest, *, follow: bool = True) -> None:
    """Change *path* as *request* says.  ``OSError`` as the calls raise it."""
    st = os.stat(path, follow_symlinks=follow)
    chowned = False
    uid = -1 if request.uid is None or request.uid == st.st_uid else request.uid
    gid = -1 if request.gid is None or request.gid == st.st_gid else request.gid
    if uid != -1 or gid != -1:
        os.chown(path, uid, gid, follow_symlinks=follow)
        chowned = True
    old = stat.S_IMODE(st.st_mode)
    new = (old & ~request.clear_bits) | request.set_bits
    if new != old or (chowned and old & (stat.S_ISUID | stat.S_ISGID)):
        os.chmod(path, new)
    if request.mtime is not None:
        os.utime(path, (st.st_atime, request.mtime), follow_symlinks=follow)


def run(request: AttrRequest, job: AttrJob) -> list[Path]:
    """Change what *request* says; answer the sources changed without a failure."""
    return _Changer(request, job).run()


class _Changer:
    def __init__(self, request: AttrRequest, job: AttrJob) -> None:
        self.request = request
        self.job = job

    def _checkpoint(self) -> None:
        self.job.wait_while_paused()
        if self.job.stopped:
            raise Stopped

    def _fail(self, path: Path, error: OSError) -> bool:
        """Ask whether to skip *path*; False, or stop."""
        if self.job.stopped:
            raise Stopped
        if not self.job.ask(Failure(path, error_message(error))):
            raise Stopped
        return False

    def _wants(self, is_dir: bool) -> bool:
        recurse = self.request.recurse
        return recurse == ALL or recurse == (DIRS if is_dir else FILES)

    def run(self) -> list[Path]:
        job = self.job
        done: list[Path] = []
        try:
            counts = [self._measure(source) for source in self.request.sources]
            job.total = sum(counts)
            job.measuring = False
            for source, count in zip(self.request.sources, counts):
                before = job.done
                try:
                    if self._source(source):
                        done.append(source)
                finally:
                    job.done = before + count
        except Stopped:
            pass
        return done

    def _measure(self, path: Path) -> int:
        """Entries the gauge counts at and under *path*, never through a link."""
        if self.request.recurse == NONE:
            return 1
        self._checkpoint()
        try:
            if not stat.S_ISDIR(os.lstat(path).st_mode):
                return 1
            with os.scandir(path) as entries:
                children = list(entries)
        except OSError:
            return 1
        count = 1
        for child in children:
            if child.is_dir(follow_symlinks=False):
                count += self._measure(Path(child.path))
            else:
                count += 1
        return count

    def _change(self, path: Path, *, follow: bool) -> bool:
        self._checkpoint()
        self.job.path = str(path)
        try:
            apply_one(path, self.request, follow=follow)
        except OSError as error:
            return self._fail(path, error)
        return True

    def _source(self, path: Path) -> bool:
        """A tagged entry: always changed, and recursed into if asked."""
        try:
            is_dir = stat.S_ISDIR(os.lstat(path).st_mode)
        except OSError as error:
            return self._fail(path, error)
        if not is_dir or self.request.recurse == NONE:
            ok = self._change(path, follow=True)
            self.job.done += 1
            return ok
        return self._tree(path, always=True)

    def _tree(self, path: Path, *, always: bool) -> bool:
        """*path*'s contents, depth first, and *path*; True if nothing failed."""
        mine = always or self._wants(True)
        whole = True
        early = mine and not os.access(path, os.R_OK | os.X_OK)
        if early:
            whole = self._change(path, follow=False)
        try:
            with os.scandir(path) as entries:
                children = list(entries)
        except OSError as error:
            children = []
            whole = self._fail(path, error) and whole
        for child in children:
            self._checkpoint()
            try:
                st = child.stat(follow_symlinks=False)
            except FileNotFoundError:
                continue
            except OSError as error:
                whole = self._fail(Path(child.path), error) and whole
                continue
            if stat.S_ISLNK(st.st_mode):
                self.job.done += 1
            elif stat.S_ISDIR(st.st_mode):
                whole = self._tree(Path(child.path), always=False) and whole
            else:
                if self._wants(False):
                    whole = self._change(Path(child.path), follow=False) and whole
                self.job.done += 1
        if mine and not early:
            whole = self._change(path, follow=False) and whole
        self.job.done += 1
        return whole


__all__ = [
    "ALL", "AttrJob", "AttrRequest", "BITS", "CHANGING", "DIRS", "FILES", "MODE_MASK", "NONE",
    "RECURSE", "Survey", "apply_one", "assignable_groups", "can_chown_user", "date_text",
    "from_items", "group_name", "groups", "octal", "parse_group", "parse_mtime", "parse_octal",
    "parse_user", "run", "survey", "symbolic", "time_text", "to_items", "user_name", "users",
]
