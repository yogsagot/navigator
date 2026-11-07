"""Squashfs images -- ``.squashfs``, ``.sqfs``, and the image inside a
type 2 AppImage -- read through ``unsquashfs`` (squashfs-tools), as 7z and
rar are read through their tools (:mod:`navigator.lib.drives.arctool`).
Read-only; without ``unsquashfs`` the image is
:class:`~navigator.lib.drives.archive.NeedsTool`.

An AppImage is an ELF program with the image appended: the ``AI\\x02``
mark in the ELF identification, and the image where the ELF ends -- after
its section headers, ``e_shoff + e_shentsize * e_shnum`` -- which
``unsquashfs -o`` skips to.  A type 1 AppImage (an ISO 9660 image) is not
read.

The listing is ``unsquashfs -lls -full -UTC``, an ``ls -l`` line a file;
each file is read with ``-cat`` through a pipe, ``-no-wildcards`` so a
name is a name.  ``-cat`` came with squashfs-tools 4.6: before it a file is
extracted into a private directory and read from there.
"""

from __future__ import annotations

import calendar
import errno
import io
import shutil
import struct
import subprocess
import tempfile
import time
from functools import lru_cache
from pathlib import Path
from typing import IO, Any

from navigator.lib.drives import arctool
from navigator.lib.drives.arctool import ToolInfo
from navigator.lib.drives.members import ListedArchive
from navigator.lib.system.which import which as _which

MAGIC = b"hsqs"

#: What to install, said when ``unsquashfs`` is not here.
MISSING = "squashfs images need unsquashfs: install squashfs-tools"


def program() -> str | None:
    return _which("unsquashfs")


@lru_cache(maxsize=4)
def _has_cat(found: str) -> bool:
    try:
        done = subprocess.run([found, "-help"], capture_output=True, stdin=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return b"-cat" in done.stdout + done.stderr


def offset_of(path: Path) -> int | None:
    """Where the squashfs image in *path* starts: 0 for an image, the ELF's
    end for a type 2 AppImage; None for anything else."""
    try:
        with open(path, "rb") as file:
            head = file.read(64)
            if head.startswith(MAGIC):
                return 0
            if not head.startswith(b"\x7fELF") or head[8:11] != b"AI\x02" or len(head) < 64:
                return None
            order = "<" if head[5] == 1 else ">"
            if head[4] == 2:
                (shoff,) = struct.unpack(order + "Q", head[0x28:0x30])
                shentsize, shnum = struct.unpack(order + "HH", head[0x3A:0x3E])
            elif head[4] == 1:
                (shoff,) = struct.unpack(order + "I", head[0x20:0x24])
                shentsize, shnum = struct.unpack(order + "HH", head[0x2E:0x32])
            else:
                return None
            offset = shoff + shentsize * shnum
            file.seek(offset)
            return offset if file.read(4) == MAGIC else None
    except (OSError, struct.error):
        return None


def parse_lls(text: str) -> list[ToolInfo]:
    """``unsquashfs -lls -full -UTC -d ''``: ``mode owner/group size date
    time /path[ -> target]``; the root's line, devices, FIFOs and sockets
    left out."""
    members = []
    for line in text.splitlines():
        if not line[:1] or line[0] not in "-dl":
            continue
        words = line.split(None, 5)
        if len(words) < 6 or not words[5].startswith("/"):
            continue
        mode, letter = arctool._mode(words[0])
        name, target = words[5][1:], None
        if letter == "l":
            name, _, target = name.partition(" -> ")
        try:
            moment = calendar.timegm(time.strptime(f"{words[3]} {words[4]}", "%Y-%m-%d %H:%M:%S"))
        except (ValueError, OverflowError):
            moment = 0
        size = int(words[2]) if words[2].isdigit() else 0
        members.append(ToolInfo(name, letter == "d", 0 if letter == "d" else size, None, float(moment), mode,
                                letter == "l", False, target, words[1].replace("/", ":", 1)))
    return members


class _Extracted(io.FileIO):
    """A file extracted into a private directory, which goes with it."""

    def __init__(self, path: Path, directory: Path) -> None:
        super().__init__(path, "rb")
        self._directory = directory

    def close(self) -> None:
        try:
            super().close()
        finally:
            shutil.rmtree(self._directory, ignore_errors=True)


class SquashArchive(ListedArchive):
    """A squashfs image, from *offset* in *path*."""

    def __init__(self, path: Path, offset: int = 0) -> None:
        found = program()
        if found is None:
            raise arctool.MissingTool(MISSING)
        self.path, self.offset, self.program = path, offset, found
        done = subprocess.run(self._command("-lls", "-full", "-UTC", "-d", "", str(path)),
                              capture_output=True, stdin=subprocess.DEVNULL, start_new_session=True)
        if done.returncode != 0:
            raise OSError(errno.EIO, arctool._reason(done.stderr.decode("utf-8", "replace"))
                          or f"unsquashfs exited with {done.returncode}", str(path))
        super().__init__(parse_lls(done.stdout.decode("utf-8", "surrogateescape")))

    def _command(self, *arguments: str) -> list[str]:
        offset = ["-o", str(self.offset)] if self.offset else []
        return [self.program, "-no-wildcards", *offset, *arguments]

    def open(self, info: ToolInfo) -> IO[bytes]:
        if info.is_dir:
            raise IsADirectoryError(errno.EISDIR, "Is a directory", info.path)
        if not _has_cat(self.program):
            return self._extract(info)
        process = subprocess.Popen(self._command("-cat", str(self.path), info.path), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        return io.BufferedReader(arctool._Piped(process, info.path), 1 << 16)  # type: ignore[return-value]

    def _extract(self, info: ToolInfo) -> IO[bytes]:
        from navigator.lib.system.tempdir import private_dir

        base = private_dir() / "archive"
        base.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory = Path(tempfile.mkdtemp(dir=base))
        target = directory / "out"
        done = subprocess.run(self._command("-f", "-q", "-d", str(target), str(self.path), info.path),
                              capture_output=True, stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            if done.returncode != 0:
                raise OSError(errno.EIO, arctool._reason(done.stderr.decode("utf-8", "replace"))
                              or f"unsquashfs exited with {done.returncode}", info.path)
            return _Extracted(target / info.path, directory)  # type: ignore[return-value]
        except BaseException:
            shutil.rmtree(directory, ignore_errors=True)
            raise

    def details(self) -> list[tuple[str, str]]:
        return [("Image", f"AppImage, at {self.offset:,}")] if self.offset else []


__all__ = ["MAGIC", "MISSING", "SquashArchive", "offset_of", "parse_lls", "program"]
