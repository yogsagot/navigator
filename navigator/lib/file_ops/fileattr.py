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

import datetime
import grp
import os
import pwd
import re
import stat
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from navkit.i18n import tr

from navml.widgets.dialog.masked_line import spell_time

from navigator.lib.file_ops import acl as acls
from navigator.lib.file_ops import fsflags
from navigator.lib.file_ops.filecopy import Elevated, Failure, error_message, finish_drives
from navigator.lib.system.job import Job, Stopped

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
        raise ValueError(tr("{text} is not an octal mode").format(text=repr(text)))
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
    #: The access and default ACLs' named entries and masks
    #: (:meth:`navigator.lib.file_ops.acl.Acl.entries`) every file has,
    #: ``None`` for one some have and others lack or have otherwise.
    acl: dict[tuple[str, int | None], int | None] = field(default_factory=dict)
    default_acl: dict[tuple[str, int | None], int | None] = field(default_factory=dict)
    #: Extended attributes, the ACLs' two left out, as :attr:`acl` is.
    xattrs: dict[str, bytes | None] = field(default_factory=dict)
    #: Whether any file's extended attributes could be read at all.
    xattrs_supported: bool = False
    #: The inode flags every file has, and the ones they disagree on.
    flags: int = 0
    flags_mixed: int = 0
    #: Whether any file's flags could be read at all.
    flags_supported: bool = False


# -- the disk, or another drive -----------------------------------------------------
#
# Every call below goes through these, which are :mod:`os`'s on a path and the
# drive's (:mod:`navigator.lib.drives`) on a location elsewhere: a server's
# files have modes and times to change too.


def _elsewhere(path: Any) -> bool:
    return not isinstance(path, (str, os.PathLike)) and not path.is_local


def _local(path: Any) -> Any:
    return path if isinstance(path, (str, os.PathLike)) else path.local


def _stat(path: Any, *, follow: bool = True) -> Any:
    if _elsewhere(path):
        from navigator.lib.drives import drive_of

        drive = drive_of(path)
        return drive.stat(path) if follow else drive.lstat(path)
    return os.stat(_local(path), follow_symlinks=follow)


def _children(path: Any) -> list[tuple[Any, Any]]:
    """``(child, its lstat or the error)`` for each entry of *path*."""
    if _elsewhere(path):
        from navigator.lib.drives import drive_of

        return [(path / name, st) for name, st in drive_of(path).children(path)]
    found = []
    with os.scandir(_local(path)) as entries:
        for entry in entries:
            try:
                found.append((Path(entry.path), entry.stat(follow_symlinks=False)))
            except OSError as error:
                found.append((Path(entry.path), error))
    return found


@dataclass
class _Extended:
    """One file's ACLs, extended attributes and flags, ``None`` where unreadable."""

    acl: dict[tuple[str, int | None], int] | None = None
    default_acl: dict[tuple[str, int | None], int] | None = None
    xattrs: dict[str, bytes] | None = None
    flags: int | None = None


def _place(path: Any) -> tuple[Any, Any]:
    """The drive *path* is on and the location it names there."""
    from navigator.lib.drives import drive_of
    from navigator.lib.drives.local import LOCAL
    from navigator.lib.drives.location import Location

    if _elsewhere(path):
        return drive_of(path), path
    return LOCAL, Location.of(Path(_local(path)))


def read_xattrs(drive: Any, where: Any, *, follow: bool = True) -> dict[str, bytes]:
    """Every extended attribute of *where* that can be read, by name."""
    found = {}
    for name in drive.listxattr(where, follow=follow):
        try:
            found[name] = drive.getxattr(where, name, follow=follow)
        except OSError:
            pass  # trusted.* and the like, unreadable to whoever asks
    return found


def read_acl(xattrs: dict[str, bytes], name: str) -> acls.Acl | None:
    """The ACL in *xattrs* under *name*, or ``None`` where there is none."""
    data = xattrs.get(name)
    if data is None:
        return None
    try:
        return acls.parse(data)
    except ValueError:
        return None


def _extended(path: Any, st: Any) -> _Extended:
    found = _Extended()
    drive, where = _place(path)
    if drive.can("xattr"):
        try:
            xattrs = read_xattrs(drive, where)
        except OSError:
            pass
        else:
            access = read_acl(xattrs, acls.ACCESS)
            found.acl = access.entries() if access is not None else {}
            if stat.S_ISDIR(st.st_mode):
                default = read_acl(xattrs, acls.DEFAULT)
                found.default_acl = default.entries() if default is not None else {}
            found.xattrs = {name: value for name, value in xattrs.items() if name not in (acls.ACCESS, acls.DEFAULT)}
    if drive.can("fsflags") and fsflags.has_flags(st.st_mode):
        try:
            found.flags = drive.get_flags(where)
        except OSError:
            pass
    return found


def _common(values: list[dict[Any, Any]]) -> dict[Any, Any]:
    """What every one of *values* has the same, ``None`` for a key some lack or differ on."""
    if not values:
        return {}
    keys = set().union(*values)
    result = {}
    for key in sorted(keys, key=repr):
        seen = [value.get(key, _MISSING) for value in values]
        result[key] = seen[0] if all(item == seen[0] for item in seen) and seen[0] is not _MISSING else None
    return result


_MISSING = object()


def _combine(result: Survey, extended: list[_Extended]) -> None:
    acl_maps = [item.acl for item in extended if item.acl is not None]
    result.acl = _common(acl_maps)
    result.default_acl = _common([item.default_acl for item in extended if item.default_acl is not None])
    xattr_maps = [item.xattrs for item in extended if item.xattrs is not None]
    result.xattrs = _common(xattr_maps)
    result.xattrs_supported = bool(xattr_maps)
    flags = [item.flags for item in extended if item.flags is not None]
    result.flags_supported = bool(flags)
    on = off = 0
    for value in flags:
        on |= value
        off |= ~value & 0xFFFFFFFF
    result.flags_mixed = on & off
    result.flags = on & ~result.flags_mixed


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
    extended: list[_Extended] = []
    for path in paths:
        try:
            st = _stat(path)
        except OSError:
            try:
                st = _stat(path, follow=False)
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
        extended.append(_extended(path, st))
    result.mixed = on & off
    result.mode = on & ~result.mixed
    result.uid = uids.pop() if len(uids) == 1 else None
    result.gid = gids.pop() if len(gids) == 1 else None
    result.mtime = float(mtimes.pop()) if len(mtimes) == 1 else None
    _combine(result, extended)
    if result.single is not None and len(paths) == 1:
        try:
            if _elsewhere(paths[0]):
                from navigator.lib.drives import drive_of

                drive = drive_of(paths[0])
                if drive.is_link(paths[0]):
                    result.link_target = drive.readlink(paths[0])
            elif os.path.islink(paths[0]):
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
    return _parse_id(text, lambda name: pwd.getpwnam(name).pw_uid, tr("There is no user {name}"))


def parse_group(text: str) -> int | None:
    """A group named or numbered; ``None`` for blank, ``ValueError`` for none."""
    return _parse_id(text, lambda name: grp.getgrnam(name).gr_gid, tr("There is no group {name}"))


def _parse_id(text: str, lookup: Callable[[str], int], missing: str) -> int | None:
    text = text.strip()
    if not text:
        return None
    try:
        return lookup(text)
    except KeyError:
        pass
    if text.isdigit():
        return int(text)
    raise ValueError(missing.format(name=text))


# -- extended attributes ---------------------------------------------------------

#: The namespaces a name may be in; ``system.*`` is the kernel's (the ACLs).
XATTR_NAMESPACES = ("user.", "trusted.", "security.")


def spell_value(value: bytes) -> str:
    """*value* as ``getfattr`` would write it: text where it is printable
    UTF-8 -- quoted when it would otherwise read as hex, base64 or quoted --
    and ``0x`` and hex digits where it is not."""
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        return "0x" + value.hex()
    if not text.isprintable():
        return "0x" + value.hex()
    if text[:2].lower() in ("0x", "0s") or text.startswith('"'):
        return f'"{text}"'
    return text


def parse_value(text: str) -> bytes:
    """What :func:`spell_value` writes, read back: ``"text"``, ``0x`` hex,
    ``0s`` base64, or anything else as text.  ``ValueError`` for bad digits."""
    import base64
    import binascii

    if len(text) >= 2 and text.startswith('"') and text.endswith('"'):
        return text[1:-1].encode("utf-8")
    prefix = text[:2].lower()
    if prefix == "0x":
        try:
            return bytes.fromhex(text[2:])
        except ValueError:
            raise ValueError(tr("{text} is not hexadecimal").format(text=text)) from None
    if prefix == "0s":
        try:
            return base64.b64decode(text[2:], validate=True)
        except (binascii.Error, ValueError):
            raise ValueError(tr("{text} is not base64").format(text=text)) from None
    return text.encode("utf-8")


def check_xattr_name(name: str) -> str:
    """*name*, stripped, if it is one a file may be given; ``ValueError`` if not."""
    name = name.strip()
    if not any(name.startswith(space) and len(name) > len(space) for space in XATTR_NAMESPACES):
        raise ValueError(tr("{name} is not in the user, trusted or security namespace").format(name=name or '""'))
    if len(name.encode("utf-8")) > 255:
        raise ValueError(tr("{name} is too long").format(name=name))
    return name


# -- the time --------------------------------------------------------------------


def date_text(mtime: float | None, format: str = DATE_FORMAT) -> str:
    return "" if mtime is None else time.strftime(format, time.localtime(mtime))


def time_text(mtime: float | None, format: str = TIME_FORMAT) -> str:
    """*mtime*'s time in *format*, ``%p`` as ``am``/``pm`` (``spell_time``)."""
    if mtime is None:
        return ""
    return spell_time(datetime.datetime.fromtimestamp(mtime), format)


def parse_mtime(
    date: str, clock: str, base: float | None,
    date_format: str = DATE_FORMAT, time_format: str = TIME_FORMAT,
) -> float | None:
    """The modification time *date* and *clock* name, or ``None`` to leave it.

    *date* is read in *date_format*, numbers only (``%d``, ``%m``, ``%y``,
    ``%Y`` and literals): *Country support*'s order, as the dialog's mask
    spells it.  *clock* is ``H:M[:S]``, or with *time_format* holding ``%p``
    ``h:M[:S]`` and ``am``/``pm`` after it, the hour 1 to 12.

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
        raise ValueError(tr("Give both a date and a time"))
    when = time.localtime(base) if base is not None else None
    if date:
        day, month, year = _date_numbers(date, date_format, tr("{text} is not a valid date"))
        if year < 100:
            year += 2000 if year < 70 else 1900
    else:
        day, month, year = when.tm_mday, when.tm_mon, when.tm_year
    if clock:
        invalid = tr("{text} is not a valid time")
        half = None
        if "%p" in time_format:
            clock, half = clock[:-2].strip(), clock[-2:].lower()
            if half not in ("am", "pm"):
                raise ValueError(invalid.format(text=clock + half))
        parts = _numbers(clock, ":", invalid, minimum=2)
        hour, minute = parts[0], parts[1]
        second = parts[2] if len(parts) > 2 else 0
        if half is not None:
            if not 1 <= hour <= 12:
                raise ValueError(invalid.format(text=clock + half))
            hour = hour % 12 + (12 if half == "pm" else 0)
    else:
        hour, minute, second = when.tm_hour, when.tm_min, when.tm_sec
    try:
        stamp = time.mktime((year, month, day, hour, minute, second, 0, 0, -1))
        check = time.localtime(stamp)
    except (OverflowError, ValueError):
        raise ValueError(tr("{text} is not a valid date").format(text=date or clock)) from None
    if (check.tm_mday, check.tm_mon) != (day, month) or not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 62):
        raise ValueError(tr("{text} is not a valid date").format(text=f"{date} {clock}".strip()))
    if base is not None and int(stamp) == int(base):
        return None
    return stamp


def _date_numbers(text: str, format: str, invalid: str) -> tuple[int, int, int]:
    """Day, month and year from *text* in *format*: each directive a run of
    digits (a year's up to four, the others' up to two), blanks allowed
    round them, the literals between as the format has them."""
    pattern, index, fields = [], 0, []
    while index < len(format):
        char = format[index]
        if char == "%" and index + 1 < len(format):
            directive = format[index + 1]
            if directive not in "dmyY":
                raise ValueError(f"%{directive} is not a date's number")
            fields.append(directive)
            pattern.append(r"\s*(\d{1,%d})\s*" % (4 if directive == "Y" else 2))
            index += 2
        else:
            pattern.append(re.escape(char))
            index += 1
    found = re.fullmatch("".join(pattern), text)
    kinds = [directive.lower() for directive in fields]
    if found is None or sorted(kinds) != ["d", "m", "y"]:
        raise ValueError(invalid.format(text=text))
    values = {kind: int(number) for kind, number in zip(kinds, found.groups())}
    return values["d"], values["m"], values["y"]


def _numbers(text: str, separator: str, invalid: str, minimum: int = 3) -> tuple[int, ...]:
    parts = text.split(separator)
    if not minimum <= len(parts) <= 3 or not all(p.strip().isdigit() for p in parts):
        raise ValueError(invalid.format(text=text))
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
    #: Access-ACL entries to set and to remove, keyed as
    #: :meth:`~navigator.lib.file_ops.acl.Acl.entries` keys them, the mask
    #: (:data:`~navigator.lib.file_ops.acl.MASK_KEY`) among them.
    acl_set: dict[tuple[str, int | None], int] = field(default_factory=dict)
    acl_remove: set[tuple[str, int | None]] = field(default_factory=set)
    #: The same for a directory's default ACL; a file is never given one.
    default_set: dict[tuple[str, int | None], int] = field(default_factory=dict)
    default_remove: set[tuple[str, int | None]] = field(default_factory=set)
    #: Extended attributes to set, by name, and to remove.
    xattr_set: dict[str, bytes] = field(default_factory=dict)
    xattr_remove: set[str] = field(default_factory=set)
    #: Inode flags to turn on, and off (:mod:`~navigator.lib.file_ops.fsflags`).
    flags_set: int = 0
    flags_clear: int = 0

    @property
    def changes_acl(self) -> bool:
        return bool(self.acl_set or self.acl_remove or self.default_set or self.default_remove)

    @property
    def changes_flags(self) -> bool:
        return bool(self.flags_set or self.flags_clear)

    @property
    def changes_nothing(self) -> bool:
        return not (
            self.set_bits or self.clear_bits or self.uid is not None
            or self.gid is not None or self.mtime is not None
            or self.changes_acl or self.xattr_set or self.xattr_remove or self.changes_flags
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


def apply_one(path: Path, request: AttrRequest, *, follow: bool = True, as_root: bool = False) -> None:
    """Change *path* as *request* says.  ``OSError`` as the calls raise it.
    *as_root* makes the same calls through the root helper
    (:data:`~navigator.lib.drives.root.ROOT_DRIVE`).

    In this order, each step passed over when it changes nothing: the
    locking flags (``i``, ``a``) cleared, the owner, the ACLs, the mode, the
    extended attributes, the time, and the flags set -- ``chattr +i`` last, as
    it refuses everything after it, and ``-i`` first, for the same reason.
    """
    elsewhere = _elsewhere(path) and not as_root
    if as_root:
        from navigator.lib.drives.location import Location
        from navigator.lib.drives.root import ROOT_DRIVE

        drive, where = ROOT_DRIVE, Location.of(Path(_local(path)))
    else:
        drive, where = _place(path)
    st = drive.stat(where) if follow else drive.lstat(where)
    if elsewhere and stat.S_ISLNK(st.st_mode):
        return  # a server sets a link's target's attributes, never its own

    flags = None
    if request.changes_flags and fsflags.has_flags(st.st_mode):
        old_flags = drive.get_flags(where, follow=follow)
        flags = (old_flags & ~request.flags_clear) | request.flags_set
        if flags == old_flags:
            flags = None
        elif old_flags & fsflags.LOCKING & ~flags:
            drive.set_flags(where, old_flags & ~(fsflags.LOCKING & ~flags), follow=follow)

    chowned = False
    uid = -1 if request.uid is None or request.uid == st.st_uid else request.uid
    gid = -1 if request.gid is None or request.gid == st.st_gid else request.gid
    if uid != -1 or gid != -1:
        if elsewhere:
            drive.chown(where, st.st_uid if uid == -1 else uid, st.st_gid if gid == -1 else gid)
        else:
            drive.chown(where, uid, gid, follow=follow)
        chowned = True

    if request.changes_acl and not stat.S_ISLNK(st.st_mode):
        if _apply_acls(drive, where, request, st, follow=follow):
            # The access ACL's mask is the mode's group bits.
            st = drive.stat(where) if follow else drive.lstat(where)

    old = stat.S_IMODE(st.st_mode)
    new = (old & ~request.clear_bits) | request.set_bits
    if new != old or (not elsewhere and chowned and old & (stat.S_ISUID | stat.S_ISGID)):
        drive.chmod(where, new)

    if request.xattr_remove or request.xattr_set:
        present = set(drive.listxattr(where, follow=follow))
        for name in sorted(request.xattr_remove):
            if name in present:
                drive.removexattr(where, name, follow=follow)
        for name, value in sorted(request.xattr_set.items()):
            drive.setxattr(where, name, value, follow=follow)

    if request.mtime is not None:
        drive.utime(where, st.st_atime_ns, int(request.mtime * 1e9), follow=follow)

    if flags is not None:
        drive.set_flags(where, flags, follow=follow)


def _apply_acls(drive: Any, where: Any, request: AttrRequest, st: Any, *, follow: bool) -> bool:
    """*request*'s ACL deltas on *where*; whether the access ACL was written."""
    access_changed = False
    present = set(drive.listxattr(where, follow=follow))
    current = (acls.parse(drive.getxattr(where, acls.ACCESS, follow=follow))
               if acls.ACCESS in present else acls.from_mode(st.st_mode))
    if request.acl_set or request.acl_remove:
        new = acls.apply_deltas(current, request.acl_set, request.acl_remove)
        if new != current:
            _write_acl(drive, where, acls.ACCESS, new, acls.ACCESS in present, follow=follow)
            access_changed = True
            current = new
    if (request.default_set or request.default_remove) and stat.S_ISDIR(st.st_mode):
        default = (acls.parse(drive.getxattr(where, acls.DEFAULT, follow=follow))
                   if acls.DEFAULT in present else None)
        base = default if default is not None else acls.seed_default(current)
        new = acls.apply_deltas(base, request.default_set, request.default_remove)
        if new != default:
            _write_acl(drive, where, acls.DEFAULT, new, default is not None, follow=follow)
    return access_changed


def _write_acl(drive: Any, where: Any, name: str, acl: acls.Acl, present: bool, *, follow: bool) -> None:
    """*acl* written under *name*, or removed when minimal (``setfacl -b``).

    A minimal access ACL is the mode's three triplets, which the mode already
    says; a minimal default ACL is no default at all.
    """
    if acl.minimal:
        if name == acls.ACCESS:
            # The group entry back as the group bits, which the mask held.
            st = drive.stat(where) if follow else drive.lstat(where)
            mode = stat.S_IMODE(st.st_mode) & ~0o070 | (acl.group << 3)
            if present:
                drive.removexattr(where, name, follow=follow)
            drive.chmod(where, mode)
        elif present:
            drive.removexattr(where, name, follow=follow)
        return
    drive.setxattr(where, name, acls.pack(acl), follow=follow)


def run(request: AttrRequest, job: AttrJob) -> list[Path]:
    """Change what *request* says; answer the sources changed without a failure."""
    return _Changer(request, job).run()


class _Changer(Elevated):
    def __init__(self, request: AttrRequest, job: AttrJob) -> None:
        self.request = request
        self.job = job

    def _ask(self, question: Any) -> Any:
        if self.job.stopped:
            raise Stopped
        answer = self.job.ask(question)
        if answer is None or answer is False:
            raise Stopped
        return answer

    def _as_root(self, path: Any) -> bool:
        """Whether *path*'s steps are now the root helper's."""
        return self.elevated and not _elsewhere(path)

    def _stat(self, path: Any, *, follow: bool = True) -> Any:
        if self._as_root(path):
            from navigator.lib.drives.location import Location
            from navigator.lib.drives.root import ROOT_DRIVE

            where = Location.of(Path(_local(path)))
            return ROOT_DRIVE.stat(where) if follow else ROOT_DRIVE.lstat(where)
        return _stat(path, follow=follow)

    def _children(self, path: Any) -> list[tuple[Any, Any]]:
        if self._as_root(path):
            from navigator.lib.drives.location import Location
            from navigator.lib.drives.root import ROOT_DRIVE

            local = Path(_local(path))
            return [(local / name, st) for name, st in ROOT_DRIVE.children(Location.of(local))]
        return _children(path)

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
            # An archive changed is written anew -- a refused rewrite of one on
            # the disk offered *As root*; any other failure passed over, as before.
            finish_drives(list(self.request.sources), None, self._finish_as_root)
        except Stopped:
            finish_drives(list(self.request.sources), None)
        finally:
            self._release()
        return done

    def _measure(self, path: Path) -> int:
        """Entries the gauge counts at and under *path*, never through a link."""
        if self.request.recurse == NONE:
            return 1
        self._checkpoint()
        try:
            if not stat.S_ISDIR(self._stat(path, follow=False).st_mode):
                return 1
            children = self._children(path)
        except OSError:
            return 1
        count = 1
        for child, st in children:
            if not isinstance(st, OSError) and stat.S_ISDIR(st.st_mode):
                count += self._measure(child)
            else:
                count += 1
        return count

    def _change(self, path: Path, *, follow: bool) -> bool:
        self._checkpoint()
        self.job.path = str(path)
        while True:
            try:
                apply_one(path, self.request, follow=follow, as_root=self._as_root(path))
                return True
            except OSError as error:
                if not self._failed(path, error):
                    return False

    def _source(self, path: Path) -> bool:
        """A tagged entry: always changed, and recursed into if asked."""
        while True:
            try:
                is_dir = stat.S_ISDIR(self._stat(path, follow=False).st_mode)
                break
            except OSError as error:
                if not self._failed(path, error):
                    return False
        if not is_dir or self.request.recurse == NONE:
            ok = self._change(path, follow=True)
            self.job.done += 1
            return ok
        return self._tree(path, always=True)

    def _tree(self, path: Path, *, always: bool) -> bool:
        """*path*'s contents, depth first, and *path*; True if nothing failed."""
        mine = always or self._wants(True)
        whole = True
        early = (mine and not _elsewhere(path) and not self.elevated
                 and not os.access(_local(path), os.R_OK | os.X_OK))
        if early:
            whole = self._change(path, follow=False)
        children: list[tuple[Any, Any]] = []
        while True:
            try:
                children = self._children(path)
                break
            except OSError as error:
                if not self._failed(path, error):
                    whole = False
                    break
        for child, st in children:
            self._checkpoint()
            if isinstance(st, FileNotFoundError):
                continue
            if isinstance(st, OSError):
                whole = self._fail(child, st) and whole
                continue
            if stat.S_ISLNK(st.st_mode):
                self.job.done += 1
            elif stat.S_ISDIR(st.st_mode):
                whole = self._tree(child, always=False) and whole
            else:
                if self._wants(False):
                    whole = self._change(child, follow=False) and whole
                self.job.done += 1
        if mine and not early:
            whole = self._change(path, follow=False) and whole
        self.job.done += 1
        return whole


__all__ = [
    "XATTR_NAMESPACES", "check_xattr_name", "parse_value", "spell_value", "read_acl", "read_xattrs",
    "ALL", "AttrJob", "AttrRequest", "BITS", "CHANGING", "DIRS", "FILES", "MODE_MASK", "NONE",
    "RECURSE", "Survey", "apply_one", "assignable_groups", "can_chown_user", "date_text",
    "from_items", "group_name", "groups", "octal", "parse_group", "parse_mtime", "parse_octal",
    "parse_user", "run", "survey", "symbolic", "time_text", "to_items", "user_name", "users",
]
