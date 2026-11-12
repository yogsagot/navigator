"""File > Replace in files: Find File's search, each file holding the text changed.

Not DOS Navigator's -- a departure, asked for: DN's ``FindFile``
(FILEFIND.PAS) found and never changed, and its editor's replace was one
file's.  The search is :func:`navigator.lib.file_ops.filefind.search`, the
same mask, scope, limits, case, whole words and *Regular expression*, with a
*match* that replaces: each file that holds the text is planned
(:func:`plan`), put to the user as a :class:`ReplaceQuestion` -- its changed
lines, *before* over *after* -- and written when the answer is Yes or All.
What was changed goes into the panel as Find's listing does.

**Bytes, not text.**  The file is matched and rewritten as its bytes, the
pattern and the replacement encoded as UTF-8 (``surrogateescape``), so a
file in another encoding, or with CRLF line ends, keeps whatever the
replacement does not touch.  A file with a NUL byte in its first
:data:`BINARY_PROBE` bytes is taken for binary and passed over, and so is
one larger than :data:`LARGEST`: a file is held whole while it is asked
about.

**The replacement** is the text itself; with *Regular expression*, Python's
``re`` template, ``\\1`` or ``\\g<name>`` a group's text.

**Writing**: on the disk through the editor's
:func:`navigator.lib.editor.save.write_file` -- a temporary file renamed
over the old, its mode and owner kept, through links to what they name,
never over a file another program holds locked; on another drive by
writing it again through the drive, finished (``Drive.finish``: an archive
packed) once the walk ends.  A file changed while its question was
up is left as it is, and said so.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from navkit.i18n import tr

from navigator.lib.file_ops.filecopy import AS_ROOT, Failure, error_message
from navigator.lib.system.elevate import refused
from navigator.lib.file_ops.filefind import WHOLE_LARGEST, FindJob, FindRequest, search
from navigator.lib.system.job import Stopped

#: How much of a file's head is looked at for a NUL byte.
BINARY_PROBE = 8192

#: The largest file replaced in, in bytes.
LARGEST = WHOLE_LARGEST  # one number with Find's *Regular expression*

#: How many changes a question shows; the rest are counted.
SHOWN = 500

#: How much of a line a change keeps, in characters.
LINE_WIDTH = 1000

#: A :class:`ReplaceQuestion`'s answers; ``None`` is Cancel.
YES, ALL, SKIP = "yes", "all", "skip"


@dataclass(frozen=True)
class ReplaceRequest:
    """What *Replace in files* asked for: Find's request and what replaces its text."""

    find: FindRequest
    replacement: str = ""

    def template(self) -> bytes:
        return self.replacement.encode("utf-8", "surrogateescape")


@dataclass(frozen=True)
class Change:
    """A run of lines a replacement touches: where it starts, and the lines
    as they are and as they will be, made printable."""

    line: int
    old: tuple[str, ...]
    new: tuple[str, ...]


@dataclass(frozen=True)
class Plan:
    """What :func:`plan` makes of a file: its new bytes, how many
    replacements, the first :data:`SHOWN` changes and how many more there are."""

    data: bytes
    count: int
    changes: tuple[Change, ...] = ()
    more: int = 0


@dataclass
class ReplaceQuestion:
    """A file holds the text: replace in it?  Answered :data:`YES`,
    :data:`ALL`, :data:`SKIP`, or ``None`` for Cancel."""

    path: Path | Any
    count: int
    changes: tuple[Change, ...]
    more: int = 0


class ReplaceJob(FindJob):
    """A replace under way: :class:`FindJob`'s files, here the ones changed,
    and how many held the text, how many replacements were made, and
    whether All was answered."""

    def __init__(self, asker: Any = None) -> None:
        super().__init__()
        self._asker = asker
        self.matched = 0
        self.replacements = 0
        self.all = False
        #: *As root* answered to a refused write: every write on the disk
        #: through the root helper from then on, unasked (as a copy's).
        self.as_root = False


def printable(line: bytes) -> str:
    """*line* as a row shows it: UTF-8 where it is, a tab four blanks, a
    carriage return dropped, any other control character ``·``."""
    text = line.decode("utf-8", "replace").rstrip("\r")
    if len(text) > LINE_WIDTH:
        text = text[:LINE_WIDTH]
    out = []
    for char in text:
        if char == "\t":
            out.append("    ")
        elif ord(char) < 32 or ord(char) == 127:
            out.append("·")
        else:
            out.append(char)
    return "".join(out)


def plan(data: bytes, pattern: re.Pattern[bytes], replacement: bytes, *, regex: bool) -> Plan:
    """*pattern* replaced in *data* as ``re.sub`` would -- *replacement* a
    template with *regex*, the bytes themselves without -- and the lines it
    touches.  Raises ``re.error`` for a template naming a group there is not."""
    pieces: list[bytes] = []
    #: Each block of lines touched: its start and end in *data*, and the
    #: matches in it with what replaces them.
    blocks: list[tuple[int, int, list[tuple[int, int, bytes]]]] = []
    last = 0
    count = 0
    for match in pattern.finditer(data):
        start, end = match.span()
        new = match.expand(replacement) if regex else replacement
        pieces.append(data[last:start])
        pieces.append(new)
        last = end
        count += 1
        if new == data[start:end]:
            continue  # nothing changes there: no row for it
        head = data.rfind(b"\n", 0, start) + 1
        tail = data.find(b"\n", end)
        if tail < 0:
            tail = len(data)
        if blocks and head <= blocks[-1][1]:
            blocks[-1] = (blocks[-1][0], max(tail, blocks[-1][1]), blocks[-1][2] + [(start, end, new)])
        else:
            blocks.append((head, tail, [(start, end, new)]))
    if not count:
        return Plan(data, 0)
    pieces.append(data[last:])
    changes = []
    line, counted = 1, 0
    for head, tail, spans in blocks[:SHOWN]:
        line += data.count(b"\n", counted, head)
        counted = head
        old = data[head:tail]
        parts, at = [], head
        for start, end, new in spans:
            parts.append(data[at:start])
            parts.append(new)
            at = end
        parts.append(data[at:tail])
        changes.append(Change(line, tuple(printable(row) for row in old.split(b"\n")),
                              tuple(printable(row) for row in b"".join(parts).split(b"\n"))))
    return Plan(b"".join(pieces), count, tuple(changes), max(0, len(blocks) - SHOWN))


def _stamp(info: os.stat_result) -> tuple[int, int]:
    return info.st_size, info.st_mtime_ns


def replace(request: ReplaceRequest, start: Any, make_entry: Any, job: ReplaceJob,
            *, show_hidden: bool = True, mounts: Iterable[Path] = ()) -> list[Any]:
    """Search as *request*'s Find asks, replacing in each file that holds
    the text once the user says so; ``job.found`` gets the files changed,
    as :func:`~navigator.lib.file_ops.filefind.search` makes them with
    *make_entry*.  Cancel, or *job* stopped, ends it with what was done.
    Touches only the file system and ``job``: a thread runs it."""
    template = request.template()
    regex = request.find.regex
    #: The drives written to, each finished at the end -- an archive packs
    #: its changes then (``Drive.finish``).
    written: dict[int, Any] = {}

    def read(place: Any) -> tuple[bytes, Any, tuple[int, int]] | None:
        """The file's bytes, its drive (None on the disk) and its stamp;
        None for one not to touch."""
        if isinstance(place, str):
            info = os.stat(place)
            drive = None
        else:
            from navigator.lib.drives import drive_of

            drive = drive_of(place)
            info = drive.stat(place)
        if info.st_size > LARGEST:
            return None
        if drive is None:
            with open(place, "rb") as file:
                data = file.read()
        else:
            with drive.open_read(place) as file:
                data = file.read()
        if b"\0" in data[:BINARY_PROBE]:
            return None
        return data, drive, _stamp(info)

    def write_on_disk(place: Any, data: bytes) -> None:
        """The editor's write -- owner and mode kept, one rename -- or the root
        helper's, once *As root* was answered (``RootDrive.write_file``)."""
        if job.as_root:
            from navigator.lib.drives.root import ROOT_DRIVE

            ROOT_DRIVE.write_file(Path(place), [data], job)
            return
        from navigator.lib.editor.save import write_file

        write_file(Path(place), data)

    def fail(place: Any, reason: Any, values: dict[str, Any] | None = None) -> bool:
        """A failure put to the user: False skips the file, Cancel stops."""
        shown = Path(place) if isinstance(place, str) else place
        if not job.ask(Failure(shown, reason, values or {})):
            raise Stopped
        return False

    def match(place: Any, pattern: re.Pattern[bytes]) -> bool:
        try:
            got = read(place)
        except OSError:
            return False  # not readable: not found, as Find passes it over
        if got is None:
            return False
        data, drive, stamp = got
        done = plan(data, pattern, template, regex=regex)
        if not done.count:
            return False
        job.matched += 1
        if done.data == data:
            return False
        if not job.all:
            shown = Path(place) if isinstance(place, str) else place
            answer = job.ask(ReplaceQuestion(shown, done.count, done.changes, done.more))
            if answer is None:
                raise Stopped
            if answer == SKIP:
                return False
            if answer == ALL:
                job.all = True
        try:
            now = os.stat(place) if drive is None else drive.stat(place)
            if _stamp(now) != stamp:
                return fail(place, lambda: tr("File {name}\nchanged while it was asked about; it is left as it is"),
                            {"name": shown_name(place)})
            if drive is None:
                write_on_disk(place, done.data)
            else:
                written[id(drive)] = drive
                with drive.open_write(place) as file:
                    file.write(done.data)
        except OSError as error:
            if drive is None and not job.as_root and refused(error):
                # Refused on the disk: *As root* offered with Skip and Cancel.
                # As :func:`fail`: True skips the file, anything false stops.
                answer = job.ask(Failure(Path(place), error_message(error), elevate=True))
                if answer == AS_ROOT:
                    job.as_root = True
                    try:
                        write_on_disk(place, done.data)
                    except OSError as again:
                        return fail(place, error_message(again))
                    job.replacements += done.count
                    return True
                if not answer:
                    raise Stopped from None
                return False
            return fail(place, error_message(error))
        job.replacements += done.count
        return True

    try:
        search(request.find, start, make_entry, job, show_hidden=show_hidden, mounts=mounts, match=match)
    except Stopped:
        job.stop()
    finally:
        for drive in written.values():
            try:
                drive.finish()
            except OSError as error:
                # Said, Skip or Cancel alike: nothing is left to do after it.
                try:
                    job.ask(Failure(start, error_message(error)))
                except Stopped:
                    pass
    return job.found


def shown_name(place: Any) -> str:
    """The file's own name, from a path's text or a ``Location``."""
    return os.path.basename(place) if isinstance(place, str) else place.name


def check(request: ReplaceRequest) -> str | None:
    """Why *request* cannot run -- its pattern or its template invalid --
    or None."""
    from navigator.lib.file_ops.filefind import request_pattern

    try:
        pattern = request_pattern(request.find)
    except re.error as error:
        return tr("Invalid regular expression: {reason}").format(reason=str(error))
    if pattern is not None and request.find.regex:
        try:
            pattern.sub(request.template(), b"")
        except (re.error, IndexError) as error:
            return tr("Invalid replacement: {reason}").format(reason=str(error))
    return None


__all__ = ["ALL", "SKIP", "YES", "Change", "Plan", "ReplaceJob", "ReplaceQuestion", "ReplaceRequest", "check",
           "plan", "printable", "replace"]

