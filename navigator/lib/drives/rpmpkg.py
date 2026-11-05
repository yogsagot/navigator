"""RPM packages, read in Python: the lead, the signature header (padded to
eight bytes), the header -- whose name, version, release and architecture
the information panel shows -- and then the payload, a cpio archive
compressed with gzip, bzip2, xz, the old lzma or zstd.  The payload is
decompressed into a private plain cpio, which :mod:`navigator.lib.drives.cpio`
reads.  Read-only.

rpm 4.12's "stripped" payload for files over 4 GiB keeps the sizes and names
in the header instead; it is not read.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import IO, Any

from navigator.lib.drives import cpio
from navigator.lib.drives.arctool import ToolInfo
from navigator.lib.drives.members import ListedArchive, compression_of_bytes, decompress_to

#: The lead's first bytes.
MAGIC = b"\xed\xab\xee\xdb"
_HEADER = b"\x8e\xad\xe8"

_NAME, _VERSION, _RELEASE, _ARCH = 1000, 1001, 1002, 1022
_STRING_TYPES = (6, 8, 9)


class RpmError(Exception):
    """Not an rpm, or one cut short."""


def is_rpm(head: bytes) -> bool:
    return head.startswith(MAGIC)


def _read_header(file: IO[bytes]) -> tuple[dict[int, str], int]:
    """The header at *file*'s position: its string tags, and its length."""
    intro = file.read(16)
    if len(intro) < 16 or not intro.startswith(_HEADER):
        raise RpmError("bad header")
    count, size = struct.unpack(">II", intro[8:16])
    index = file.read(16 * count)
    store = file.read(size)
    if len(index) < 16 * count or len(store) < size:
        raise RpmError("cut short")
    tags: dict[int, str] = {}
    for at in range(0, 16 * count, 16):
        tag, kind, offset, _count = struct.unpack(">IIII", index[at:at + 16])
        if kind in _STRING_TYPES and tag in (_NAME, _VERSION, _RELEASE, _ARCH) and offset < size:
            end = store.find(b"\x00", offset)
            tags[tag] = store[offset:end if end >= 0 else None].decode("utf-8", "replace")
    return tags, 16 + 16 * count + size


def read_package(path: Path) -> tuple[dict[int, str], int]:
    """*path*'s header tags, and where its payload starts."""
    with open(path, "rb") as file:
        lead = file.read(96)
        if len(lead) < 96 or not is_rpm(lead):
            raise RpmError("not an rpm")
        _, signature = _read_header(file)
        file.seek(96 + signature + (8 - signature % 8) % 8)
        tags, header = _read_header(file)
        return tags, file.tell()


class RpmArchive(ListedArchive):
    """An ``.rpm``'s files, from its payload."""

    def __init__(self, path: Path, job: Any = None) -> None:
        from navigator.lib.drives.archive import _private_file

        self.path = path
        self.tags, payload = read_package(path)
        self._plain: Path | None = _private_file(".cpio")
        try:
            with open(path, "rb") as reader:
                reader.seek(payload)
                compression = compression_of_bytes(reader.read(6))
                reader.seek(payload)
                decompress_to(reader, compression, self._plain, job)
            with open(self._plain, "rb") as plain:
                head = plain.read(6)
            if head.startswith(cpio.STRIPPED):
                raise cpio.CpioError("rpm large-file payloads are not read")
            if not cpio.is_cpio(head):
                raise RpmError("the payload is not a cpio archive")
            self._cpio = cpio.CpioArchive(self._plain, job)
        except BaseException:
            self.close()
            raise
        super().__init__(self._cpio.infolist())

    def open(self, info: ToolInfo) -> IO[bytes]:
        return self._cpio.open(info)

    def details(self) -> list[tuple[str, str]]:
        name = self.tags.get(_NAME)
        if not name:
            return []
        text = "-".join(part for part in (name, self.tags.get(_VERSION), self.tags.get(_RELEASE)) if part)
        if self.tags.get(_ARCH):
            text += f".{self.tags[_ARCH]}"
        return [("Package", text)]

    def close(self) -> None:
        if self._plain is not None:
            try:
                self._plain.unlink()
            except OSError:
                pass
            self._plain = None


__all__ = ["MAGIC", "RpmArchive", "RpmError", "is_rpm", "read_package"]
