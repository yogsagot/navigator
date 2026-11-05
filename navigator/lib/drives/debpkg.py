"""Debian packages, and the ``ar`` archives they are made of.

A ``.deb`` is an ``ar`` archive of ``debian-binary``, ``control.tar*`` and
``data.tar*`` (gz, xz, zst, bz2 or none).  It is shown as ``dpkg-deb -R``
unpacks it -- the installed files at the root, the control files under
``DEBIAN/`` -- since an archive is never opened from inside another (DN's
rule), so the two tars as files would be no use.  Each tar is decompressed
into a private plain one, which :mod:`tarfile` reads anywhere in.

An ``ar`` that is no package (a static library's ``.a``) lists its members
as they are (:class:`ArArchive`), reached by Ctrl+PgDn.  Both read-only.
"""

from __future__ import annotations

import errno
import tarfile
from pathlib import Path
from typing import IO, Any

from navigator.lib.drives.arctool import ToolInfo
from navigator.lib.drives.members import ListedArchive, compression_of_bytes, decompress_to, window

MAGIC = b"!<arch>\n"


class ArError(Exception):
    """Not an ``ar`` archive, or one cut short."""


def is_ar(head: bytes) -> bool:
    return head.startswith(MAGIC)


def parse_ar(path: Path) -> list[tuple[str, int, int, float, int]]:
    """``(name, offset, size, mtime, mode)`` for each member of *path*: GNU
    (``name/``, ``/123`` into the ``//`` table) and BSD (``#1/len``) names;
    the symbol tables left out."""
    members = []
    long_names = b""
    with open(path, "rb") as file:
        if file.read(8) != MAGIC:
            raise ArError("not an ar archive")
        position = 8
        while True:
            header = file.read(60)
            if not header:
                break
            if len(header) < 60 or header[58:60] != b"`\n":
                raise ArError("bad member header")
            raw = header[:16].rstrip(b" ")
            try:
                mtime = float(int(header[16:28].strip() or b"0"))
                mode = int(header[40:48].strip() or b"0", 8)
                size = int(header[48:58].strip())
            except ValueError as error:
                raise ArError("bad member header") from error
            position += 60
            offset = position
            if raw.startswith(b"#1/"):  # BSD: the name is the data's first bytes
                length = int(raw[3:])
                name = file.read(length).rstrip(b"\x00")
                offset, size = offset + length, size - length
                file.seek(size, 1)
            else:
                file.seek(size, 1)
                name = raw
            position = offset + size + (offset + size) % 2
            file.seek(position)
            if raw == b"//":
                with open(path, "rb") as table:
                    table.seek(offset)
                    long_names = table.read(size)
                continue
            if raw in (b"/", b"/SYM64/", b"__.SYMDEF", b"__.SYMDEF SORTED") or name.startswith(b"__.SYMDEF"):
                continue
            if raw.startswith(b"/") and raw[1:].isdigit():
                start = int(raw[1:])
                end = long_names.find(b"/\n", start)
                name = long_names[start:end if end >= 0 else None]
            elif name.endswith(b"/"):
                name = name[:-1]
            members.append((name.decode("utf-8", "surrogateescape"), offset, size, mtime, mode))
    return members


class ArArchive(ListedArchive):
    """An ``ar`` archive's members, as they are."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__([ToolInfo(name, False, size, size, mtime, mode & 0o7777, ref=(offset, size))
                          for name, offset, size, mtime, mode in parse_ar(path)])

    def open(self, info: ToolInfo) -> IO[bytes]:
        offset, size = info.ref
        return window(self.path, offset, size)


class DebArchive(ListedArchive):
    """A ``.deb``, laid out as ``dpkg-deb -R`` unpacks it."""

    def __init__(self, path: Path, job: Any = None) -> None:
        self.path = path
        self._tars: list[tarfile.TarFile] = []
        self._plain: list[Path] = []
        self._control = ""
        try:
            members = {name: (offset, size) for name, offset, size, _, _ in parse_ar(path)}
            if "debian-binary" not in members:
                raise ArError("not a Debian package")
            listed: list[ToolInfo] = []
            for prefix in ("data.tar", "control.tar"):
                name = next((name for name in members if name.startswith(prefix)), None)
                if name is None:
                    if prefix == "data.tar":
                        raise ArError("no data.tar in the package")
                    continue
                tar = self._open_tar(*members[name], job)
                into = "DEBIAN/" if prefix == "control.tar" else ""
                for info in tar.getmembers():
                    listed.extend(self._member(tar, info, into))
                if into:
                    self._control = self._read_control(tar)
            super().__init__(listed)
        except BaseException:
            self.close()
            raise

    def _open_tar(self, offset: int, size: int, job: Any) -> tarfile.TarFile:
        from navigator.lib.drives.archive import _private_file

        with window(self.path, offset, size) as reader:
            compression = compression_of_bytes(reader.peek(6)[:6])
            plain = _private_file(".tar")
            self._plain.append(plain)
            decompress_to(reader, compression, plain, job)
        tar = tarfile.open(plain)
        self._tars.append(tar)
        return tar

    @staticmethod
    def _member(tar: tarfile.TarFile, info: tarfile.TarInfo, into: str) -> list[ToolInfo]:
        if not (info.isfile() or info.isdir() or info.issym() or info.islnk()):
            return []  # devices, FIFOs: not files to list
        name = info.name[2:] if info.name.startswith("./") else info.name
        if name in ("", "."):
            return []
        size = info.size
        if info.islnk():
            try:
                size = tar.getmember(info.linkname).size
            except KeyError:
                size = 0
        owner = f"{info.uname or info.uid}:{info.gname or info.gid}"
        return [ToolInfo(into + name, info.isdir(), 0 if info.isdir() else size, None, float(info.mtime),
                         info.mode & 0o7777, info.issym(), False, info.linkname if info.issym() else None,
                         owner, (tar, info))]

    @staticmethod
    def _read_control(tar: tarfile.TarFile) -> str:
        for name in ("./control", "control"):
            try:
                handle = tar.extractfile(name)
            except KeyError:
                continue
            if handle is not None:
                return handle.read(1 << 20).decode("utf-8", "replace")
        return ""

    def open(self, info: ToolInfo) -> IO[bytes]:
        tar, member = info.ref
        handle = tar.extractfile(member)
        if handle is None:
            raise IsADirectoryError(errno.EISDIR, "Is a directory", info.path)
        return handle  # type: ignore[return-value]

    def details(self) -> list[tuple[str, str]]:
        fields: dict[str, str] = {}
        for line in self._control.splitlines():
            key, found, value = line.partition(":")
            if found and not line[:1].isspace():
                fields.setdefault(key.strip(), value.strip())
        if "Package" not in fields:
            return []
        text = " ".join(part for part in (fields["Package"], fields.get("Version", "")) if part)
        if fields.get("Architecture"):
            text += f" ({fields['Architecture']})"
        return [("Package", text)]

    def close(self) -> None:
        for tar in self._tars:
            try:
                tar.close()
            except Exception:
                pass
        self._tars = []
        for plain in self._plain:
            try:
                plain.unlink()
            except OSError:
                pass
        self._plain = []


__all__ = ["MAGIC", "ArArchive", "ArError", "DebArchive", "is_ar", "parse_ar"]
