"""File > Split/combine: one file cut into parts of a given size, and put back.

DOS Navigator's ``cmPanelLongCopy`` (``FBB.PAS``, ``LongCopy``), with its
``dlgSplitFile`` and ``dlgCombineFile``.  As in DN, one command does both and
the file's name decides which (DN's ``Tuda``): a part -- ``NAME.001``,
``NAME.002`` ... -- or the set's ``NAME.crc`` is combined; anything else is
split.

**Departures**, each for a reason:

- *By size*, not by the disk filling.  DN wrote each part until the floppy
  was full and asked for the next disk; a POSIX disk does not fill a part at a
  time, so the size of a part is asked for (:func:`parse_size`).
- *``.001`` and a ``.crc``*, not ``.D01`` behind a ``Navigator Long Copy``
  header.  The parts are the bytes alone, numbered as Total Commander, Double
  Commander and 7-Zip number them, and the set's ``NAME.crc`` is Total
  Commander's (``filename=``, ``size=``, ``crc32=``): those programs combine
  what this splits, and this combines theirs.  DN checked nothing; the CRC is
  checked when the ``.crc`` is there, and its size says when a part is
  missing or a stale one is left over.

Every read and write goes through ``drive_of(...)``, so both work on any
drive; each target drive's ``finish()`` is called once, at the end.  The
workers run on a thread (``Manager._run_uucode``), asking only
:class:`~navigator.lib.file_ops.uucode.FileExists`.
"""

from __future__ import annotations

import re
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from navkit.i18n import tr

from navigator.lib.drives import Location
from navigator.lib.file_ops.uucode import FileExists
from navigator.lib.system.job import Stopped

#: A part's name: the set's base, a dot, and three digits or more.
PART_RE = re.compile(r"^(?P<base>.+)\.(?P<number>\d{3,})$")
#: The set's checksum file's ending (Total Commander's).
CRC_SUFFIX = ".crc"
#: How much is read and written at a time.
CHUNK = 1 << 20

_UNITS = {"": 1, "k": 1 << 10, "m": 1 << 20, "g": 1 << 30, "t": 1 << 40}
_SIZE_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?|[.,]\d+)\s*([kmgt]?)(?:i?b)?\s*$", re.IGNORECASE)


class SplitError(ValueError):
    """A split or combine refused, its text already translated."""


# -- names -------------------------------------------------------------------------------------


def parse_size(text: str) -> int:
    """``1.44M``, ``100m``, ``4G``, ``650 MB``, ``512k`` or plain bytes, in
    powers of 1024; raises :class:`SplitError` for anything else or for none."""
    match = _SIZE_RE.match(text)
    if match is None:
        raise SplitError(tr("{text} is not a size: write it as 100M, 1.44M, 4G or in bytes").format(
            text=text.strip() or '""'))
    number = float(match.group(1).replace(",", "."))
    size = int(number * _UNITS[match.group(2).lower()])
    if size <= 0:
        raise SplitError(tr("A part must be at least one byte"))
    return size


def part_name(base: str, number: int) -> str:
    """``base.001``: three digits, more once there are more than 999 parts."""
    return f"{base}.{number:03d}"


def base_of(name: str) -> str | None:
    """The set's base a part or the ``.crc`` is named for, else None."""
    match = PART_RE.match(name)
    if match is not None:
        return match.group("base")
    if name.lower().endswith(CRC_SUFFIX) and len(name) > len(CRC_SUFFIX):
        return name[:-len(CRC_SUFFIX)]
    return None


def mode_for(name: str, siblings: set[str] | None = None) -> str:
    """``"combine"`` for a part, or for a ``.crc`` beside its ``.001``;
    ``"split"`` for anything else (DN's ``Tuda``)."""
    match = PART_RE.match(name)
    if match is not None and int(match.group("number")) > 0:
        return "combine"
    base = base_of(name)
    if base is not None and siblings is not None and part_name(base, 1) in siblings:
        return "combine"
    return "split"


@dataclass
class CrcInfo:
    """What a ``.crc`` says; None for a line it does not have."""

    filename: str | None = None
    size: int | None = None
    crc32: int | None = None


def read_crc(text: str) -> CrcInfo:
    """Total Commander's ``key=value`` lines, LF or CRLF, keys in any case;
    a line that does not read is passed over."""
    info = CrcInfo()
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key, value = key.strip().lower(), value.strip()
        try:
            if key == "filename" and value:
                info.filename = value
            elif key == "size":
                info.size = int(value)
            elif key == "crc32":
                info.crc32 = int(value, 16)
        except ValueError:
            continue
    return info


def crc_text(filename: str, size: int, crc: int) -> str:
    """The ``.crc`` for a file *filename* of *size* bytes whose CRC-32 is *crc*."""
    return f"filename={filename}\nsize={size}\ncrc32={crc & 0xFFFFFFFF:08X}\n"


# -- the requests ------------------------------------------------------------------------------


@dataclass
class SplitRequest:
    """*source* cut into parts of *size* bytes, where *target* says --
    a directory (the parts named for the source), or a name in one (the
    parts named for that) -- relative to *cwd*.  *checksum* writes the
    ``.crc``."""

    source: Location
    target: str
    cwd: Location
    size: int
    checksum: bool = True


@dataclass
class CombineRequest:
    """The set *part* (any part, or its ``.crc``) belongs to, put together
    where *target* says -- a directory, or a name in one -- relative to *cwd*."""

    part: Location
    target: str
    cwd: Location


@dataclass
class Result:
    """What was written; *crc_checked* when a ``.crc`` said what to expect."""

    written: list[Location] = field(default_factory=list)
    crc_checked: bool = False


def _drive(location: Location, as_root: bool) -> Any:
    """*location*'s drive -- the root helper's on the disk *as_root* (``root.rooted``)."""
    from navigator.lib.drives.root import rooted

    return rooted(location, as_root)


def _resolve(target: str, cwd: Location, name: str, as_root: bool = False) -> tuple[Location, str]:
    """The target line as ``(directory, name)``, *name* when it is a directory."""
    from navigator.lib.file_ops.filecopy import target_location

    text = target.strip()
    if not text:
        return cwd, name
    location = target_location(text, cwd)
    if text.endswith("/") or _drive(location, as_root).is_dir(location):
        return location, name
    return location.parent, location.name


def _shown(location: Location) -> Path | Location:
    return location.local if location.is_local else location


def _ask_over(existing: list[Location], job: Any) -> None:
    """``dlFBBOver1``: each file there already, until *All*; anything but
    Yes or All abandons before a byte is written."""
    for location in existing:
        answer = job.ask(FileExists(_shown(location)))
        if answer == "all":
            return
        if answer != "yes":
            raise Stopped


def _step(job: Any) -> None:
    job.wait_while_paused()
    if job.stopped:
        raise Stopped


def _set_mtime(drive: Any, location: Location, st: Any) -> None:
    """DN's ``SetFTime(F2, OldDate)``, where the drive can."""
    try:
        drive.utime(location, st.st_atime_ns, st.st_mtime_ns)
    except (OSError, AttributeError):
        pass


def _remove(drive: Any, locations: list[Location]) -> None:
    for location in locations:
        try:
            drive.unlink(location)
        except OSError:
            pass


# -- split -------------------------------------------------------------------------------------


def split(request: SplitRequest, job: Any, *, as_root: bool = False) -> Result:
    """Cut the file into ``base.001``, ``base.002`` ... and write
    ``base.crc``.  A Stop or a failure removes everything written.
    *as_root*: every step on the disk through the root helper -- *As root*,
    after a refusal (a departure; ``navigator-elevation``)."""
    source_drive = _drive(request.source, as_root)
    st = source_drive.stat(request.source)
    total = st.st_size
    if total <= request.size:
        raise SplitError(tr("{name} is no larger than one part").format(name=request.source.name))
    count = -(-total // request.size)
    directory, base = _resolve(request.target, request.cwd, request.source.name, as_root)
    drive = _drive(directory, as_root)
    if drive.exists(directory):
        names = set(drive.names(directory))
    else:
        drive.makedirs(directory)
        names = set()
    crc_name = base + CRC_SUFFIX
    ours = {part_name(base, number) for number in range(1, count + 1)}
    if request.checksum:
        ours.add(crc_name)
    stale = sorted((name for name in names if name not in ours and base_of(name) == base
                    and PART_RE.match(name)), key=lambda name: int(PART_RE.match(name).group("number")))
    existing = sorted(name for name in names if name in ours)
    if not request.checksum and crc_name in names:
        # A ``.crc`` left from before would say the wrong thing of these parts.
        stale.append(crc_name)
    _ask_over([directory / name for name in existing + stale], job)
    job.total = total
    job.position = 0
    result = Result()
    crc = 0
    try:
        _remove(drive, [directory / name for name in stale])
        with source_drive.open_read(request.source) as handle:
            for number in range(1, count + 1):
                location = directory / part_name(base, number)
                job.current = str(location)
                result.written.append(location)
                left = min(request.size, total - job.position)
                with drive.open_write(location) as out:
                    while left > 0:
                        _step(job)
                        chunk = handle.read(min(CHUNK, left))
                        if not chunk:
                            raise SplitError(tr("{name} ended before its size said").format(
                                name=request.source.name))
                        out.write(chunk)
                        crc = zlib.crc32(chunk, crc)
                        left -= len(chunk)
                        job.position += len(chunk)
                _set_mtime(drive, location, st)
        if request.checksum:
            location = directory / crc_name
            result.written.append(location)
            with drive.open_write(location) as out:
                out.write(crc_text(request.source.name, total, crc).encode("utf-8"))
        drive.finish()
    except BaseException:
        _remove(drive, result.written)
        try:
            drive.finish()
        except OSError:
            pass
        raise
    return result


# -- combine -----------------------------------------------------------------------------------


def combine(request: CombineRequest, job: Any, *, as_root: bool = False) -> Result:
    """Put ``base.001``, ``base.002`` ... back together, checking them
    against ``base.crc`` when it is there.  A Stop or a failure removes the
    file; a CRC that does not match keeps it and raises :class:`SplitError`.
    *as_root* as :func:`split`'s."""
    base = base_of(request.part.name)
    if base is None:
        raise SplitError(tr("{name} is not a part of a split file").format(name=request.part.name))
    here = request.part.parent
    source_drive = _drive(here, as_root)
    names = set(source_drive.names(here))
    crc_name = base + CRC_SUFFIX
    info = CrcInfo()
    if crc_name in names:
        with source_drive.open_read(here / crc_name) as handle:
            info = read_crc(handle.read(64 * 1024).decode("utf-8", "replace"))
    parts: list[tuple[Location, int]] = []
    number = 1
    while part_name(base, number) in names:
        location = here / part_name(base, number)
        parts.append((location, source_drive.stat(location).st_size))
        number += 1
    if not parts:
        raise SplitError(tr("{name} is missing").format(name=part_name(base, 1)))
    total = sum(size for _, size in parts)
    if info.size is not None:
        # Only the parts the size reaches; one left from an older set is not read.
        kept, reached = [], 0
        for location, size in parts:
            if reached >= info.size:
                break
            kept.append((location, size))
            reached += size
        if reached < info.size:
            raise SplitError(tr("{name} is missing").format(name=part_name(base, len(kept) + 1)))
        if reached > info.size:
            raise SplitError(tr("The parts of {name} do not add up to the size {crc} says").format(
                name=base, crc=crc_name))
        parts, total = kept, reached
    directory, name = _resolve(request.target, request.cwd, info.filename or base, as_root)
    target = directory / name
    if any(target == location for location, _ in parts) or target == here / crc_name:
        raise SplitError(tr("The parts cannot be combined over one of themselves"))
    drive = _drive(directory, as_root)
    if drive.exists(target):
        _ask_over([target], job)
    elif not drive.exists(directory):
        drive.makedirs(directory)
    job.total = total
    job.position = 0
    first = source_drive.stat(parts[0][0])
    crc = 0
    written = False
    try:
        with drive.open_write(target) as out:
            written = True
            for location, size in parts:
                job.current = str(location)
                with source_drive.open_read(location) as handle:
                    while True:
                        _step(job)
                        chunk = handle.read(CHUNK)
                        if not chunk:
                            break
                        out.write(chunk)
                        crc = zlib.crc32(chunk, crc)
                        job.position += len(chunk)
        _set_mtime(drive, target, first)
        drive.finish()
    except BaseException:
        if written:
            _remove(drive, [target])
        try:
            drive.finish()
        except OSError:
            pass
        raise
    result = Result(written=[target], crc_checked=info.crc32 is not None)
    if info.crc32 is not None and crc != info.crc32:
        raise SplitError(tr("{name} does not match {crc}: a part is damaged").format(name=name, crc=crc_name))
    return result
