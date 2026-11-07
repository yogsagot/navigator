"""cpio archives -- and so an rpm's payload and an initramfs -- read in
Python: the ``newc`` (``070701``), ``crc`` (``070702``), portable ``odc``
(``070707``) and old binary (``070707`` as a 16-bit word, either byte
order) headers, each followed by the name and the bytes.  Read-only: the
listing is made once, each member then read from where its bytes lie
(:func:`navigator.lib.drives.members.window`).

Hard links: ``newc`` gives the bytes to the last name of a group only, the
others a size of 0; each of those reads the one that has them.  Devices,
FIFOs and sockets are not listed, as a tar's are not.
"""

from __future__ import annotations

import errno
import stat
import struct
from pathlib import Path
from typing import IO, Any

from navkit.i18n import tr
from navigator.lib.drives.arctool import ToolInfo
from navigator.lib.drives.members import ListedArchive, stopped_check, window

#: Every header's first bytes.
MAGICS = (b"070701", b"070702", b"070707", b"\xc7\x71", b"\x71\xc7")

#: rpm's "stripped" header (rpm 4.12 on, for files over 4 GiB): the sizes
#: and names are in the rpm header, not here.
STRIPPED = b"07070X"

_TRAILER = "TRAILER!!!"


class CpioError(Exception):
    """Not a cpio archive, or one cut short."""


def is_cpio(head: bytes) -> bool:
    return head.startswith(MAGICS[:3]) or head[:2] in MAGICS[3:]


def _pad(position: int, align: int) -> int:
    return (align - position % align) % align


def parse(path: Path, job: Any = None, *, base: int = 0) -> list[ToolInfo]:
    """Every member of the cpio archive at *path* (from *base*), in order;
    the trailer and what follows it left out."""
    members: list[ToolInfo] = []
    links: dict[tuple[int, int], list[ToolInfo]] = {}
    with open(path, "rb") as file:
        file.seek(base)
        position = base
        while True:
            stopped_check(job)
            magic = file.read(6)
            if not magic:
                break  # no trailer: taken as the end
            if magic.startswith(STRIPPED):
                raise CpioError("rpm large-file payloads are not read")
            if magic in (b"070701", b"070702"):
                header = file.read(104)
                if len(header) < 104:
                    raise CpioError("cut short")
                try:
                    fields = [int(header[i:i + 8], 16) for i in range(0, 104, 8)]
                except ValueError as error:
                    raise CpioError("bad header") from error
                ino, mode, uid, gid, nlink, mtime, size, major, minor, _rmaj, _rmin, namesize, _check = fields
                dev = (major << 32) | minor
                position += 110
                name = file.read(namesize)
                position += namesize
                skip = _pad(position, 4)
                file.seek(skip, 1)
                position += skip
                data_at, data_pad = position, _pad(position + size, 4)
            elif magic == b"070707":
                header = file.read(70)
                if len(header) < 70:
                    raise CpioError("cut short")
                try:
                    dev, ino, mode, uid, gid, nlink = (int(header[i:i + 6], 8) for i in range(0, 36, 6))
                    mtime = int(header[42:53], 8)
                    namesize = int(header[53:59], 8)
                    size = int(header[59:70], 8)
                except ValueError as error:
                    raise CpioError("bad header") from error
                position += 76
                name = file.read(namesize)
                position += namesize
                data_at, data_pad = position, 0
            elif magic[:2] in (b"\xc7\x71", b"\x71\xc7"):
                order = "<" if magic[:2] == b"\xc7\x71" else ">"
                header = magic[2:] + file.read(20)
                if len(header) < 24:
                    raise CpioError("cut short")
                dev, ino, mode, uid, gid, nlink, _rdev, mt_hi, mt_lo, namesize, fs_hi, fs_lo = struct.unpack(
                    order + "12H", header)
                mtime, size = (mt_hi << 16) | mt_lo, (fs_hi << 16) | fs_lo
                position += 26
                name = file.read(namesize)
                position += namesize
                skip = _pad(position, 2)
                file.seek(skip, 1)
                position += skip
                data_at, data_pad = position, _pad(position + size, 2)
            else:
                raise CpioError("bad magic")
            text = name.rstrip(b"\x00").decode("utf-8", "surrogateescape")
            if text == _TRAILER:
                break
            kind = stat.S_IFMT(mode)
            target = None
            if kind == stat.S_IFLNK:
                target = file.read(size).decode("utf-8", "surrogateescape")
                file.seek(data_pad, 1)
            else:
                file.seek(size + data_pad, 1)
            position = data_at + size + data_pad
            if kind not in (stat.S_IFREG, stat.S_IFDIR, stat.S_IFLNK) or text in ("", ".", "./"):
                continue
            info = ToolInfo(text, kind == stat.S_IFDIR, 0 if kind == stat.S_IFDIR else size, None, float(mtime),
                            stat.S_IMODE(mode), kind == stat.S_IFLNK, False, target, f"{uid}:{gid}",
                            (data_at, size))
            members.append(info)
            if kind == stat.S_IFREG and nlink > 1:
                links.setdefault((dev, ino), []).append(info)
    for group in links.values():
        carrier = next((info for info in reversed(group) if info.size), None)
        if carrier is None:
            continue
        for info in group:
            if info.size == 0:
                info.size, info.ref = carrier.size, carrier.ref
    return members


class CpioArchive(ListedArchive):
    """A cpio archive on the disk (or the plain one an rpm's payload or a
    ``.cpio.gz`` was decompressed into)."""

    def __init__(self, path: Path, job: Any = None, *, base: int = 0) -> None:
        self.path = path
        super().__init__(parse(path, job, base=base))

    def open(self, info: ToolInfo) -> IO[bytes]:
        if info.is_dir or info.ref is None:
            raise IsADirectoryError(errno.EISDIR, tr("Is a directory"), info.path)
        offset, size = info.ref
        return window(self.path, offset, size)


__all__ = ["MAGICS", "CpioArchive", "CpioError", "is_cpio", "parse"]
