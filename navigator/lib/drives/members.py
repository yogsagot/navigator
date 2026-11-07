"""The shape every read-only archive back-end has -- deb, rpm, cpio,
squashfs, a single compressed file -- the one
:class:`~navigator.lib.drives.arctool.ToolArchive` already has, so
:class:`~navigator.lib.drives.archive.ArchiveDrive` indexes and reads them
all the same way: :meth:`ListedArchive.infolist` of
:class:`~navigator.lib.drives.arctool.ToolInfo`, :meth:`ListedArchive.open`
a member to read, :meth:`ListedArchive.close`.

Nothing here is DN's: DOS Navigator's archivers were ARC to ZOO.
"""

from __future__ import annotations

import errno
import io
import os
from pathlib import Path
from typing import IO, Any

from navkit.i18n import tr
from navigator.lib.drives.arctool import ToolInfo


class ListedArchive:
    """An archive whose members were listed once, on opening."""

    #: Never: none of these formats is encrypted.
    encrypted = False

    def __init__(self, members: list[ToolInfo]) -> None:
        self._members = members

    def infolist(self) -> list[ToolInfo]:
        return list(self._members)

    def open(self, info: ToolInfo) -> IO[bytes]:  # pragma: no cover - every back-end has its own
        raise NotImplementedError

    def read_link(self, info: ToolInfo) -> str:
        """A symbolic link's target: what the listing said, else its bytes."""
        if info.target is not None:
            return info.target
        with self.open(info) as reader:
            return reader.read().decode("utf-8", "surrogateescape")

    def details(self) -> list[tuple[str, str]]:
        """Lines for the information panel's *Connection* (``Drive.describe``)."""
        return []

    def close(self) -> None:
        pass


class _Window(io.RawIOBase):
    """*size* bytes of a file from *offset*, read with ``pread``: no seeking,
    so any number of them read one file at once, from any thread."""

    def __init__(self, path: Path, offset: int, size: int) -> None:
        super().__init__()
        self._fd = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
        self._offset, self._end = offset, offset + size

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        count = min(len(buffer), self._end - self._offset)
        if count <= 0:
            return 0
        data = os.pread(self._fd, count, self._offset)
        if not data:
            raise OSError(errno.EIO, tr("The archive ends before this member does"))
        self._offset += len(data)
        buffer[: len(data)] = data
        return len(data)

    def close(self) -> None:
        if not self.closed:
            os.close(self._fd)
        super().close()


def window(path: Path, offset: int, size: int) -> IO[bytes]:
    """A reader of *size* bytes of *path* from *offset*."""
    return io.BufferedReader(_Window(path, offset, size), 1 << 16)  # type: ignore[return-value]


def stopped_check(job: Any) -> None:
    """``Stopped`` if *job* (may be None) was stopped; waits while paused."""
    if job is None:
        return
    from navigator.lib.system.job import Stopped

    waiting = getattr(job, "wait_while_paused", None)
    if waiting is not None:
        waiting()
    if getattr(job, "stopped", False):
        raise Stopped


def compression_of_bytes(head: bytes) -> str:
    """``gz``, ``bz2``, ``xz``, ``zst``, ``lzma`` (the old ``.lzma``) or ``""``."""
    if head[:2] == b"\x1f\x8b":
        return "gz"
    if head[:3] == b"BZh":
        return "bz2"
    if head[:6] == b"\xfd7zXZ\x00":
        return "xz"
    if head[:4] == b"\x28\xb5\x2f\xfd":
        return "zst"
    if head[:3] == b"\x5d\x00\x00":
        return "lzma"
    return ""


def open_decompressed(handle: IO[bytes], compression: str) -> IO[bytes]:
    """*handle*'s bytes, decompressed as *compression* says (not ``zst`` --
    :mod:`navigator.lib.drives.zstd` does that one whole)."""
    import bz2
    import gzip
    import lzma

    if compression == "gz":
        return gzip.GzipFile(fileobj=handle, mode="rb")  # type: ignore[return-value]
    if compression == "bz2":
        return bz2.BZ2File(handle, "rb")  # type: ignore[return-value]
    if compression in ("xz", "lzma"):
        return lzma.LZMAFile(handle, "rb")  # type: ignore[return-value]
    if compression == "":
        return handle
    raise ValueError(compression)


def decompress_to(reader: IO[bytes], compression: str, target: Path, job: Any = None) -> None:
    """*reader* (positioned at a compressed stream) decompressed into
    *target*; zst through a temporary file and
    :func:`navigator.lib.drives.zstd.decompress`."""
    if compression == "zst":
        from navigator.lib.drives import zstd

        packed = target.with_name(target.name + ".zst")
        try:
            with open(packed, "wb") as writer:
                _copy(reader, writer, job)
            zstd.decompress(packed, target)
        finally:
            try:
                packed.unlink()
            except OSError:
                pass
        return
    with open(target, "wb") as writer:
        _copy(open_decompressed(reader, compression), writer, job)


def _copy(reader: IO[bytes], writer: IO[bytes], job: Any) -> None:
    while True:
        stopped_check(job)
        data = reader.read(1 << 20)
        if not data:
            return
        writer.write(data)


__all__ = ["ListedArchive", "compression_of_bytes", "decompress_to", "open_decompressed", "stopped_check",
           "window"]
