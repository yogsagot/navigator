"""Inode flags, ``lsattr``/``chattr``'s: the *Flags* page of Alt+E.

Not DN's, and a departure, asked for -- the nearest DOS had were its four
attribute bits, which Alt+E's *Mode* page already reads as the mode.  The
flags are the file system's (ext2/3/4, XFS, Btrfs and others answer; tmpfs
and most network file systems do not), read and written with the
``FS_IOC_GETFLAGS``/``FS_IOC_SETFLAGS`` ioctls on the file held open, so
neither ``e2fsprogs`` nor a subprocess is needed.

**Only regular files and directories are opened** -- ``lsattr`` reads no
other kind either, and opening a device can do something to it.  A link is
opened only when asked to follow it, never under a recursion.

**Twelve flags are set from the dialog** (:data:`EDITABLE`), the ones
``chattr`` lets a user ask for; the others the file system keeps for itself
-- extents, encryption, inline data, verity -- are shown in the ``lsattr``
line (:func:`lsattr`) and never changed: a flag nobody pressed is carried
over as the file has it.
"""

from __future__ import annotations

import errno
import fcntl
import os
import stat
import struct
from typing import Any

#: ``linux/fs.h``'s flags, as ``chattr`` spells them, in ``lsattr``'s order.
FLAGS: tuple[tuple[str, int], ...] = (
    ("s", 0x00000001),  # FS_SECRM_FL: secure deletion
    ("u", 0x00000002),  # FS_UNRM_FL: undeletable
    ("S", 0x00000008),  # FS_SYNC_FL: synchronous updates
    ("D", 0x00010000),  # FS_DIRSYNC_FL: synchronous directory updates
    ("i", 0x00000010),  # FS_IMMUTABLE_FL
    ("a", 0x00000020),  # FS_APPEND_FL: append only
    ("d", 0x00000040),  # FS_NODUMP_FL
    ("A", 0x00000080),  # FS_NOATIME_FL
    ("c", 0x00000004),  # FS_COMPR_FL: compressed
    ("E", 0x00000800),  # FS_ENCRYPT_FL
    ("j", 0x00004000),  # FS_JOURNAL_DATA_FL
    ("I", 0x00001000),  # FS_INDEX_FL: hashed directory
    ("t", 0x00008000),  # FS_NOTAIL_FL
    ("T", 0x00020000),  # FS_TOPDIR_FL
    ("e", 0x00080000),  # FS_EXTENT_FL
    ("C", 0x00800000),  # FS_NOCOW_FL
    ("x", 0x02000000),  # FS_DAX_FL
    ("F", 0x40000000),  # FS_CASEFOLD_FL
    ("N", 0x10000000),  # FS_INLINE_DATA_FL
    ("P", 0x20000000),  # FS_PROJINHERIT_FL
    ("V", 0x00100000),  # FS_VERITY_FL
)

BY_LETTER = dict(FLAGS)

IMMUTABLE = BY_LETTER["i"]
APPEND = BY_LETTER["a"]
#: The flags that refuse every other change while set: cleared first, set last.
LOCKING = IMMUTABLE | APPEND

#: The dialog's grid, item *i* of it ``EDITABLE[i]``: four columns of three.
EDITABLE: tuple[str, ...] = ("i", "a", "d", "A", "S", "D", "C", "c", "j", "T", "s", "u")

#: Every bit the dialog can change.
EDITABLE_MASK = sum(BY_LETTER[letter] for letter in EDITABLE)

#: What a file system without flags answers.
UNSUPPORTED = frozenset({errno.ENOTTY, errno.EOPNOTSUPP, errno.ENOTSUP, errno.EINVAL, errno.ENOSYS})


def _ioc(direction: int, number: int) -> int:
    # _IOR/_IOW('f', number, long): the kernel's numbers name a long, though
    # what it reads and writes is an int.
    return (direction << 30) | (struct.calcsize("l") << 16) | (ord("f") << 8) | number


FS_IOC_GETFLAGS = _ioc(2, 1)
FS_IOC_SETFLAGS = _ioc(1, 2)


def unsupported(error: OSError) -> bool:
    """Whether *error* says the file system has no flags at all."""
    return error.errno in UNSUPPORTED


def has_flags(mode: int) -> bool:
    """Whether a file of *mode* is one whose flags are read: a regular file or a directory."""
    return stat.S_ISREG(mode) or stat.S_ISDIR(mode)


def _open(path: Any, follow: bool) -> int:
    st = os.stat(path, follow_symlinks=follow)
    if not has_flags(st.st_mode):
        raise OSError(errno.ENOTTY, os.strerror(errno.ENOTTY), str(path))
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | (0 if follow else os.O_NOFOLLOW))
    try:
        held = os.fstat(fd)
        if (held.st_dev, held.st_ino) != (st.st_dev, st.st_ino):
            raise OSError(errno.EAGAIN, "The file changed while it was opened", str(path))
    except BaseException:
        os.close(fd)
        raise
    return fd


def get_flags(path: Any, *, follow: bool = True) -> int:
    """*path*'s flags; ``OSError`` as the open or ioctl raises it."""
    fd = _open(path, follow)
    try:
        buffer = bytearray(struct.calcsize("l"))
        fcntl.ioctl(fd, FS_IOC_GETFLAGS, buffer, True)
        return struct.unpack_from("I", buffer)[0]
    finally:
        os.close(fd)


def set_flags(path: Any, flags: int, *, follow: bool = True) -> None:
    """Give *path* *flags*, every one of them."""
    fd = _open(path, follow)
    try:
        buffer = bytearray(struct.calcsize("l"))
        struct.pack_into("I", buffer, 0, flags & 0xFFFFFFFF)
        fcntl.ioctl(fd, FS_IOC_SETFLAGS, buffer, True)
    finally:
        os.close(fd)


def to_items(flags: int) -> int:
    """*flags* as the grid's item mask."""
    return sum(1 << index for index, letter in enumerate(EDITABLE) if flags & BY_LETTER[letter])


def from_items(mask: int) -> int:
    """The grid's item *mask* as flags."""
    return sum(BY_LETTER[letter] for index, letter in enumerate(EDITABLE) if mask & (1 << index))


def lsattr(flags: int, mixed: int = 0) -> str:
    """``----i---------e------``, as ``lsattr`` spells it, ``?`` for a *mixed* flag."""
    return "".join("?" if mixed & bit else letter if flags & bit else "-" for letter, bit in FLAGS)


__all__ = [
    "APPEND", "EDITABLE", "EDITABLE_MASK", "FLAGS", "IMMUTABLE", "LOCKING", "from_items", "get_flags",
    "has_flags", "lsattr", "set_flags", "to_items", "unsupported",
]
