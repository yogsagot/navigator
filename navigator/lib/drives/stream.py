"""A single compressed file -- ``.gz``, ``.bz2``, ``.xz``, ``.lzma``,
``.zst`` that holds no tar or cpio -- as an archive of one member: what
``gunzip`` would make of it, named as ``gunzip`` names it (the name less
its ending).

Its one member can be written -- F4's F2 -- and the file is then
compressed anew the same way (:func:`writer`); nothing can be added to it,
taken from it or renamed in it (``ArchiveDrive`` refuses, ``EROFS``).
The size is counted by one pass through it on opening, since no format but
zstd's says it (and gzip's says it modulo 4 GiB).
"""

from __future__ import annotations

import bz2
import gzip
import lzma
import os
from pathlib import Path
from typing import IO, Any

from navigator.lib.drives.arctool import ToolInfo
from navigator.lib.drives.members import ListedArchive, stopped_check

#: The endings taken off to name the member, by compression.
SUFFIXES = {"gz": (".gz", ".z"), "bz2": (".bz2", ".bz"), "xz": (".xz",), "lzma": (".lzma",),
            "zst": (".zst", ".zstd")}


def member_name(name: str, compression: str) -> str:
    """The name *name*'s one file has: less its compression's ending, else
    less its last extension, else the name itself."""
    lower = name.lower()
    for suffix in SUFFIXES.get(compression, ()):
        if lower.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    stem, dot, _ = name.rpartition(".")
    return stem if dot and stem else name


def open_path(path: Path, compression: str) -> IO[bytes]:
    """*path*'s bytes, decompressed (not zst: that one is read from its plain copy)."""
    if compression == "gz":
        return gzip.open(path, "rb")  # type: ignore[return-value]
    if compression == "bz2":
        return bz2.open(path, "rb")  # type: ignore[return-value]
    if compression in ("xz", "lzma"):
        return lzma.open(path, "rb")  # type: ignore[return-value]
    raise ValueError(compression)


def writer(path: Path, compression: str, level: int | None) -> IO[bytes]:
    """A file at *path* written *compression*-compressed at *level* (its
    default for None); not zst, which :func:`navigator.lib.drives.zstd.compress`
    makes from a plain file."""
    if compression == "gz":
        return gzip.open(path, "wb", compresslevel=6 if level is None else level)  # type: ignore[return-value]
    if compression == "bz2":
        return bz2.open(path, "wb", compresslevel=9 if level is None else level)  # type: ignore[return-value]
    if compression == "xz":
        return lzma.open(path, "wb", preset=level)  # type: ignore[return-value]
    if compression == "lzma":
        return lzma.open(path, "wb", format=lzma.FORMAT_ALONE, preset=level)  # type: ignore[return-value]
    raise ValueError(compression)


class StreamArchive(ListedArchive):
    """*path*, one *compression*-compressed file; for zst, *plain* is the
    file it was decompressed into already (the caller's to delete)."""

    def __init__(self, path: Path, compression: str, plain: Path | None = None, job: Any = None) -> None:
        self.path, self.compression, self.plain = path, compression, plain
        if plain is not None:
            size = os.stat(plain).st_size
        else:
            size = 0
            with open_path(path, compression) as reader:
                while True:
                    stopped_check(job)
                    data = reader.read(1 << 20)
                    if not data:
                        break
                    size += len(data)
        st = os.stat(path)
        super().__init__([ToolInfo(member_name(path.name, compression), False, size, st.st_size, st.st_mtime,
                                   st.st_mode & 0o666)])

    def open(self, info: ToolInfo) -> IO[bytes]:
        if self.plain is not None:
            return open(self.plain, "rb")
        return open_path(self.path, self.compression)


__all__ = ["SUFFIXES", "StreamArchive", "member_name", "open_path", "writer"]
