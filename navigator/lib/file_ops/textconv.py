"""File > Encoding > Convert text: the tagged text files written again in
another encoding and with other line endings -- **a departure, asked for**:
DOS Navigator converted nothing but through the viewer's ``*.XLT`` tables.

Each file is read through its drive, so a server or an archive serves as
well as the disk, and is **rewritten in place**: a new file beside it, given
its mode, renamed over it -- a crash halfway leaves the old text.  A file
with other hard links, or reached through a symbolic link, is written into
instead, as the editor writes one (:mod:`navigator.lib.editor.save`), so the
links stay what they were.  A tagged directory is walked to the bottom, as
Checksums walk one (:func:`navigator.lib.file_ops.checksum.walk`).

What a file is read as: what its byte order mark says, else UTF-8 when it
decodes as UTF-8, else the legacy *fallback* (``Options.fallback``) when
one is given -- otherwise it is left alone.  Left alone too, and said why:
a file that looks binary (a NUL in its first bytes, unless it is UTF-16), one
whose text the target encoding cannot write, and one larger than
:data:`LIMIT`.  A file that would come out as it went in is not written at
all, so its time stays.

**As root** (a departure, as everywhere: :mod:`navigator.lib.system.elevate`):
a file on the disk whose read or write is refused permission is not an
error but goes in :attr:`TextJob.refused`; the loop asks once for all of
them, and :func:`convert` runs again over those with *as_root*, every step
through the root helper.  A root drive writes with its ``write_file``, the
editor's save done as root, which keeps the file's owner, mode and links --
a new file renamed over would be root's.

The encodings are the editor's (:mod:`navigator.lib.editor.encodings`), and
so is how a text is cut into lines (:data:`navigator.lib.editor.document.BREAK`).

Nothing here may run on the loop.
"""

from __future__ import annotations

import stat
from dataclasses import dataclass
from typing import Any, Iterable

from navigator.lib.drives import Location, drive_of
from navigator.lib.editor import encodings
from navigator.lib.editor.document import BREAK, NEWLINES
from navigator.lib.file_ops.checksum import ChecksumJob, walk
from navigator.lib.system.elevate import refused
from navigator.lib.system.job import Stopped

#: The line endings a file may be given, ``""`` keeping each line's own.
ENDINGS = ("", "lf", "crlf", "cr")

#: How much of a file is looked at for a NUL before it is taken as binary.
BINARY_PROBE = 8192

#: The largest file converted: the whole text is held while it is.
LIMIT = 256 << 20

#: Why a file was left alone, as :attr:`TextJob.skipped` says.
BINARY = "binary"
UNDECODABLE = "undecodable"
UNENCODABLE = "unencodable"
TOO_LARGE = "too large"

CHUNK = 1 << 20


@dataclass
class Options:
    """What the files become: *encoding* (a key of ``encodings.CODECS``, or
    ``""`` to keep each file's), *ending* (``ENDINGS``), what a file that is
    not UTF-8 is read as (*fallback*, a legacy code page, or ``utf-8`` to
    leave such a file alone), and whether its times are put back."""

    encoding: str = ""
    ending: str = ""
    fallback: str = encodings.UTF8
    keep_times: bool = False


class TextJob(ChecksumJob):
    """Files being converted, as the checksums box shows them, and what came
    of each: converted, unchanged, or skipped with a reason."""

    def __init__(self) -> None:
        super().__init__()
        self.converted: list[Location] = []
        self.unchanged: list[Location] = []
        #: ``(name, kind, detail)``: why each file was left alone.
        self.skipped: list[tuple[str, str, str]] = []
        #: ``(location, size, reason)``: files on the disk refused permission,
        #: which *As root* may get past.
        self.refused: list[tuple[Location, int, str]] = []


def plan(sources: Iterable[Location], job: TextJob) -> list[tuple[Location, int]]:
    """Every file *sources* name, a directory's to the bottom, with its size."""
    return walk(sources, job)


def read_text(data: bytes, fallback: str = encodings.UTF8) -> tuple[str, str] | str:
    """*data*'s text and its encoding, or why it is not text: :data:`BINARY`
    or :data:`UNDECODABLE`."""
    key, skip = encodings.sniff(data)
    if encodings.ascii_compatible(key) and b"\0" in data[:BINARY_PROBE]:
        return BINARY
    body = data[skip:]
    if key == encodings.UTF8:
        try:
            return body.decode("utf-8"), key
        except UnicodeDecodeError:
            if fallback in ("", encodings.UTF8):
                return UNDECODABLE
            try:
                return body.decode(fallback), fallback
            except UnicodeDecodeError:
                return UNDECODABLE
    try:
        return body.decode(encodings.python_codec(key)), key
    except UnicodeDecodeError:
        return UNDECODABLE


def converted(text: str, source: str, options: Options) -> bytes:
    """*text*, read as *source*, as *options* would have it written.  Raises
    ``UnicodeEncodeError`` for a character the target encoding has not."""
    if options.ending:
        text = BREAK.sub(NEWLINES[options.ending], text)
    target = options.encoding or source
    return encodings.bom(target) + encodings.encode(text, target)


def _place(text: str, index: int) -> tuple[int, int]:
    """The line and column, counted from 1, of *index* in *text*."""
    line = len(BREAK.findall(text, 0, index))
    start = max(text.rfind("\n", 0, index), text.rfind("\r", 0, index)) + 1
    return line + 1, index - start + 1


def _drive(location: Location, as_root: bool) -> Any:
    """The drive *location* is reached through: the root helper's for one on
    the disk *as_root*."""
    if as_root and location.is_local:
        from navigator.lib.drives.root import ROOT_DRIVE

        return ROOT_DRIVE
    return drive_of(location)


def _read(location: Location, job: TextJob, drive: Any) -> bytes:
    parts = []
    with drive.open_read(location) as handle:
        while True:
            if job.stopped:
                raise Stopped
            block = handle.read(CHUNK)
            if not block:
                return b"".join(parts)
            parts.append(block)


def convert_file(location: Location, size: int, options: Options, job: TextJob,
                 drive: Any = None) -> None:
    """*location* converted as *options* say, through *drive* (its own by
    default), its outcome put on *job*.  Raises ``OSError`` when it cannot be
    read or written."""
    drive = drive if drive is not None else drive_of(location)
    name = str(location)
    if size > LIMIT:
        job.skipped.append((name, TOO_LARGE, ""))
        return
    data = _read(location, job, drive)
    read = read_text(data, options.fallback)
    if isinstance(read, str):
        job.skipped.append((name, read, ""))
        return
    text, source = read
    try:
        out = converted(text, source, options)
    except UnicodeEncodeError as error:
        line, column = _place(text, error.start)
        job.skipped.append((name, UNENCODABLE, f"{line}:{column}"))
        return
    if out == data:
        job.unchanged.append(location)
        return
    _write(location, out, options.keep_times, drive)
    job.converted.append(location)


def _write(location: Location, data: bytes, keep_times: bool, drive: Any) -> None:
    """*data* as *location*'s new contents: a new file renamed over it, or --
    with other hard links, or through a symbolic link -- written into it.  A
    root drive writes with its ``write_file``, which keeps the owner too."""
    st = drive.stat(location)
    write_file = getattr(drive, "write_file", None)
    if write_file is not None:
        from pathlib import Path

        write_file(Path(str(location.path)), [data])
        if keep_times:
            drive.utime(location, st.st_atime_ns, st.st_mtime_ns)
        return
    linked = stat.S_ISLNK(drive.lstat(location).st_mode) or st.st_nlink > 1
    mode = stat.S_IMODE(st.st_mode)
    if linked:
        with drive.open_write(location) as handle:
            handle.write(data)
    else:
        temporary = location.parent / f".{location.name}.navigator~"
        try:
            with drive.open_write(temporary, mode=mode) as handle:
                handle.write(data)
            drive.chmod(temporary, mode)
            drive.replace(temporary, location)
        except BaseException:
            try:
                drive.unlink(temporary)
            except OSError:
                pass
            raise
    if keep_times:
        drive.utime(location, st.st_atime_ns, st.st_mtime_ns)


def convert(files: list[tuple[Location, int]], options: Options, job: TextJob, *,
            as_root: bool = False) -> None:
    """Every one of *files* converted; one that cannot be read or written
    goes in ``job.errors`` -- or, refused permission on the disk and not
    *as_root* yet, in ``job.refused`` -- and the rest go on.  Esc stops
    between files.  *as_root* reaches every file on the disk through the
    root helper.

    Every drive written to is finished once at the end, as Encryption's are
    -- an archive is rewritten once, not once a file."""
    drives: dict[int, Any] = {}
    try:
        for location, size in files:
            if job.stopped:
                raise Stopped
            job.current = str(location)
            start = job.position
            try:
                drive = _drive(location, as_root)
                drives[id(drive)] = drive
                convert_file(location, size, options, job, drive)
            except OSError as error:
                reason = error.strerror or str(error)
                if not as_root and location.is_local and refused(error):
                    job.refused.append((location, size, reason))
                else:
                    job.errors.append((str(location), reason))
            job.position = start + size
            job.files_done += 1
    finally:
        for drive in drives.values():
            try:
                drive.finish()
            except OSError as error:
                job.errors.append((str(drive), error.strerror or str(error)))
