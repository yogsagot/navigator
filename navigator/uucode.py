"""File > UU Encode (Ctrl+F7) and UU Decode (Ctrl+F8): DOS Navigator's
``UuEncode`` and ``UU_Decode`` (UUCODE.PAS, UUE2INC.ASM).

**Encoding** writes DN's own flavour of uuencode, transcribed: a file split
into sections of at most *lines per section* lines, one output file each --
``NAME.uue`` alone, else ``NAME.uu1``, ``NAME.uu2`` .. ``NAME.u10`` ..
``NAME.100`` -- each under a ``section N of M of file NAME`` header; the
first section after DN's optional prefixes (statistics, ``filetime``, the
character ``table``) and ``begin 644 NAME``; the last ending in the
zero-length line and ``end``.  The checksum level adds, cumulatively,
``sum -r/size`` of the whole input, ``sum -r/size`` of each section's lines,
a check character after each line, and DN's 64-bit ``crc64``.  Lines map
through ``UUxlt``, in which 0 is a backquote.

**Decoding** reads one file, which may hold several encoded files and their
sections in any order -- as mail and news delivered them -- and puts each
file together in the target directory.  It understands what the encoder
writes: section headers, ``table``, ``filetime``, ``begin``/``end``, the
``sum -r/size`` lines (checked), and lines with or without their check
character; anything else between them is passed over.  Each error found is
counted, and a file with a severe one is *broken*: written only with *Save
broken files*.

Departures, each recorded where it is made: names keep their case and their
length (DN upper-cased them to 8.3); a section's file names keep the case of
the name given; a blank line ends the data as the backquote does, as other
encoders wrote it; ``crc64`` lines are written but not checked on decoding,
as DN's decoder never read them either.

Both touch the file system and run on a thread.  A question -- a file that is
there already, an error to show -- goes to the job (:class:`navigator.job.Job`).
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from navigator.job import Job, Stopped

#: ``UUxlt``: a six-bit value's character.  0 is a backquote, never a blank.
UUXLT = "`!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_"
#: What DN signed its sections with.
TITLE = "< uuencode by Navigator >"
#: Bytes on one encoded line.
LINE_BYTES = 45
#: ``Clear64``'s starting value: eight bytes of ``Poly64``, from its 65th.
CRC64_START = int.from_bytes(bytes((137, 57, 139, 122, 249, 109, 97, 124)), "little")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
CHECKSUMS = ("none", "entire", "section", "line", "crc64")

#: ``dlFileIsSmall``.
TOO_SMALL = "The input file is too small to UU-Encode."
#: ``eruuNoStuff``.
NO_STUFF = "There is no UUCode stuff in this file"


# -- the questions ---------------------------------------------------------------------


@dataclass
class FileExists:
    """``dlFileExist``: *path* is there already.  Answered ``"yes"``,
    ``"all"``, ``"no"`` or ``"cancel"`` (None is Cancel)."""

    path: Path


@dataclass
class DecodeError:
    """One of the decoder's errors, shown with *Display error messages*."""

    text: str


# -- the arithmetic ----------------------------------------------------------------------


def sum_r(data: bytes, total: int = 0) -> int:
    """``cCrc``: BSD ``sum -r``, sixteen bits rotated right and added to."""
    for byte in data:
        total = ((total >> 1) | ((total & 1) << 15)) + byte & 0xFFFF
    return total


class Crc64:
    """DN's ``Crc64``: each byte and the low byte of a running count added
    into 64 bits, each add followed by a one-bit rotation left."""

    MASK = (1 << 64) - 1

    def __init__(self) -> None:
        self.value = CRC64_START
        self.count = 0

    def _add(self, byte: int) -> None:
        value = (self.value + byte) & self.MASK
        self.value = ((value << 1) | (value >> 63)) & self.MASK

    def update(self, data: bytes) -> None:
        for byte in data:
            self._add(byte)
            self._add(self.count & 0xFF)
            self.count = (self.count + 1) & 0xFFFF

    def hex(self) -> str:
        return f"{self.value:016x}"


def encode_line(chunk: bytes, check: bool = False) -> str:
    """One encoded line: the length, the groups, and with *check* ``GetLnCrc``'s character."""
    padded = chunk + bytes(-len(chunk) % 3)
    out = []
    for i in range(0, len(padded), 3):
        a, b, c = padded[i:i + 3]
        out += (a >> 2, (a & 3) << 4 | b >> 4, (b & 15) << 2 | c >> 6, c & 63)
    data = "".join(UUXLT[v] for v in out)
    line = UUXLT[len(chunk)] + data
    if check:
        line += UUXLT[sum((ord(ch) - 0x20) & 0x3F for ch in data) & 0x3F]
    return line


def decode_line(line: str, table: dict[str, int] | None = None) -> bytes | None:
    """The bytes of one encoded line, or None if it is not one.

    The standard mapping takes any character from blank to backquote, the
    six bits of ``ch - 32`` (so a blank and a backquote are both 0); a
    ``table`` line pair gives another.
    """
    if not line:
        return None
    if table is not None:
        values = [table.get(ch) for ch in line]
        if any(v is None for v in values):
            return None
    else:
        if any(not " " <= ch <= "`" for ch in line) or line[0] == " ":
            return None
        values = [(ord(ch) - 0x20) & 0x3F for ch in line]
    count = values[0]
    need = (count + 2) // 3 * 4
    data = values[1:]
    if len(data) < need:
        if len(data) < need - 2:
            return None
        data += [0] * (need - len(data))  # trailing blanks a mailer took off
    out = bytearray()
    for i in range(0, need, 4):
        a, b, c, d = data[i:i + 4]
        out += bytes(((a << 2 | b >> 4) & 0xFF, (b << 4 | c >> 2) & 0xFF, (c << 6 | d) & 0xFF))
    return bytes(out[:count])


def dos_time(mtime: float) -> int:
    """``GetFTime``'s packed local date and time, as ``filetime`` writes it."""
    t = time.localtime(mtime)
    year = max(0, min(127, t.tm_year - 1980))
    return (year << 25 | t.tm_mon << 21 | t.tm_mday << 16
            | t.tm_hour << 11 | t.tm_min << 5 | t.tm_sec // 2)


def from_dos_time(packed: int) -> float | None:
    """The time *packed* stands for, or None for a nonsense one."""
    try:
        return time.mktime((1980 + (packed >> 25 & 127), packed >> 21 & 15, packed >> 16 & 31,
                            packed >> 11 & 31, packed >> 5 & 63, (packed & 31) * 2, 0, 0, -1))
    except (OverflowError, ValueError):
        return None


def std_date_time(t: time.struct_time) -> str:
    """``StdDateTime``: ``07-Oct-26 12:34:56``."""
    return (f"{t.tm_mday:02d}-{MONTHS[t.tm_mon - 1]}-{t.tm_year % 100:02d} "
            f"{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}")


def _ceil_div(a: int, b: int) -> int:
    """``SmartDIV``: a division rounded up."""
    return -(-a // b)


# -- encoding ---------------------------------------------------------------------------------


@dataclass
class EncodeRequest:
    """What *UU Encode* was answered: the file, where to, and how."""

    source: Path
    target: str
    file_time: bool = True
    map_table: bool = False
    statistics: bool = True
    checksum: str = "section"
    lines: int = 100
    crlf: bool = False


@dataclass
class Plan:
    """How a file of *size* bytes is cut: ``NumSect`` + 1 sections, all but
    the last ``SectSize`` bytes long."""

    size: int
    sections: int
    section_size: int
    last_size: int

    @property
    def lines(self) -> int:
        return _ceil_div(self.section_size, LINE_BYTES)

    @property
    def last_lines(self) -> int:
        return _ceil_div(self.last_size, LINE_BYTES)


def plan(size: int, lines: int) -> Plan:
    """DN's sectioning: as few sections as *lines* allows, evened out, the
    last no shorter than half the others (``CalcLSsize``)."""
    biggest = max(10, lines) * LINE_BYTES
    others = _ceil_div(size, biggest) - 1
    if others <= 0:
        return Plan(size, 1, 0, size)
    section = _ceil_div(_ceil_div(size, others + 1), LINE_BYTES) * LINE_BYTES
    last = size - section * others
    while last < section // 2:
        last += section
        others -= 1
    while last > section:
        last -= section
        others += 1
    return Plan(size, others + 1, section, last)


def target_names(source: Path, target: str, sections: int, here: Path) -> list[Path]:
    """Each section's file: the target's name, its extension's first three
    characters and the section's number, then two and the number, then the
    number alone.  A target that names a directory takes the source's name;
    no extension is ``.uue``."""
    path = Path(os.path.expanduser(target))
    if not path.is_absolute():
        path = here / path
    if target.endswith("/") or path.is_dir():
        directory, stem, ext = path, source.stem, ".uue"
    else:
        directory, stem, ext = path.parent, path.stem, path.suffix
        if ext in ("", "."):
            ext = ".uue"
    if sections == 1:
        return [directory / (stem + ext)]
    names = []
    for number in range(1, sections + 1):
        if number < 10:
            tail = ext[:3] + str(number)
        elif number < 100:
            tail = ext[:2] + str(number)
        else:
            tail = "." + str(number)
        names.append(directory / (stem + tail))
    return names


def encode(request: EncodeRequest, job: Job, here: Path, *, now: float | None = None) -> list[Path]:
    """``UuEncode``: the files written, all of them or none.

    ``OSError`` for a source that cannot be read or a target that cannot be
    written; ``ValueError`` (:data:`TOO_SMALL`) for a source under three
    bytes; :class:`~navigator.job.Stopped` if a question was cancelled.
    """
    source = request.source
    data = source.read_bytes()
    if len(data) < 3:
        raise ValueError(TOO_SMALL)
    info = source.stat()
    cut = plan(len(data), request.lines)
    names = target_names(source, request.target, cut.sections, here)
    level = CHECKSUMS.index(request.checksum) if request.checksum in CHECKSUMS else 2
    entire, by_section, by_line, wide = level >= 1, level >= 2, level >= 3, level >= 4
    eol = "\r\n" if request.crlf else "\n"
    # ``dlFileExist`` for each file there already, until *All*; anything but
    # Yes or All abandons the encoding before a byte is written.
    asking = True
    for name in names:
        if asking and name.exists():
            answer = job.ask(FileExists(name))
            if answer == "all":
                asking = False
            elif answer != "yes":
                raise Stopped
    names[0].parent.mkdir(parents=True, exist_ok=True)

    entire_sum = sum_r(data) if entire else 0
    entire_crc = Crc64()
    if wide:
        entire_crc.update(data)
    title = source.name
    written: list[Path] = []
    offset = 0
    for number, name in enumerate(names, 1):
        job.wait_while_paused()
        if job.stopped:
            raise Stopped
        last = number == cut.sections
        size = cut.last_size if last else cut.section_size
        chunk = data[offset:offset + size]
        offset += size
        out: list[str] = []
        section_sum, section_size, section_crc = 0, 0, Crc64()

        def counted(line: str) -> None:
            nonlocal section_sum, section_size
            if by_section:
                raw = (line + "\n").encode("latin-1")
                section_sum = sum_r(raw, section_sum)
                section_size += len(raw)
                if wide:
                    section_crc.update(raw)
            out.append(line)

        header = f"section {number}" + (f" of {cut.sections}" if cut.sections > 1 else "")
        header += f" of file {title}  {TITLE}"
        if number == 1:
            if request.statistics:
                out += _statistics(title, info.st_mtime, cut, now)
            out += [header, ""]
            if request.file_time:
                out.append(f"filetime {dos_time(info.st_mtime)}")
            if request.map_table:
                counted("table")
                counted(UUXLT[:32])
                counted(UUXLT[32:])
            counted(f"begin 644 {title}")
        else:
            out += [header, ""]
        for start in range(0, len(chunk), LINE_BYTES):
            counted(encode_line(chunk[start:start + LINE_BYTES], by_line))
        if last:
            counted("``" if by_line else "`")
            counted("end")
        else:
            out.append("")
        where = ""
        if by_section:
            if cut.sections == 1:
                ends = '"begin"', '"end"'
            elif number == 1:
                ends = '"begin"', "last encoded line"
            elif last:
                ends = "first encoded line", '"end"'
            else:
                ends = "first", "last encoded line"
            where = f" section (from {ends[0]} to {ends[1]})"
            out.append(f"sum -r/size {section_sum}/{section_size}{where}")
        if entire and last:
            out.append(f"sum -r/size {entire_sum}/{len(data)} entire input file")
        if wide:
            out += ["", f"crc64 {section_crc.hex()}{where}"]
            if last:
                out.append(f"crc64 {entire_crc.hex()} entire input file")
        out.append("")
        name.write_bytes(eol.join(out).encode("latin-1") + eol.encode())
        written.append(name)
    return written


def _statistics(title: str, mtime: float, cut: Plan, now: float | None) -> list[str]:
    """``InsertStatistics``: DN's block, labels right-aligned to 31 columns."""
    def info(label: str, value: str) -> str:
        return f"{label:>31} : {value}"

    if cut.sections == 1:
        per = str(cut.last_lines)
    elif cut.lines == cut.last_lines:
        per = str(cut.lines)
    else:
        per = f"{cut.lines} ({cut.last_lines})"
    encoded = max(cut.lines, cut.last_lines) * 70 * cut.sections
    return [
        info("source file name", title),
        info("original size", f"{cut.size} ({_ceil_div(cut.size, 1024)}Kb)"),
        info("created on", std_date_time(time.localtime(mtime))),
        info("encoded on", std_date_time(time.localtime(now))),
        info("approximate encoded size", f"{_ceil_div(encoded, 1024)}Kb"),
        info("number of sections", str(cut.sections)),
        info("lines per section", per),
        "",
        "",
    ]


# -- decoding ------------------------------------------------------------------------------------


@dataclass
class _File:
    """``TFile``: one file being put together from its sections."""

    name: str
    sections: dict[int, bytearray] = field(default_factory=dict)
    total: int | None = None
    end_found: bool = False
    file_time: int | None = None
    listed: tuple[int, int] | None = None
    broken: bool = False
    skip: bool = False


@dataclass
class DecodeResult:
    """How it went: files decoded whole, errors counted, whether there was
    anything to decode at all, and the files written."""

    decoded: int = 0
    errors: int = 0
    found: bool = False
    written: list[Path] = field(default_factory=list)


_SECTION = re.compile(r"section\s+(\d+)(?:\s+of\s+(\d+))?.*?\bfile\s+(\S+)")
_SUM = re.compile(r"sum -r/size\s+(\d+)/(\d+)\s+(section|entire)")


class _Decoder:
    """The state ``UU_Decode`` carried from line to line."""

    def __init__(self, out_dir: Path, job: Job, check_existing: bool, display_errors: bool,
                 save_broken: bool) -> None:
        self.out_dir = out_dir
        self.job = job
        self.check_existing = check_existing
        self.display_errors = display_errors
        self.save_broken = save_broken
        self.result = DecodeResult()
        self.files: dict[str, _File] = {}
        self.current: _File | None = None
        self.number = 1
        self.data = False
        self.ended = False
        self.table: dict[str, int] | None = None
        self.table_lines: list[str] | None = None
        self.pending_time: int | None = None
        self.sum = 0
        self.size = 0
        self.stop = False
        #: Where the current section's bytes go; None for a duplicate.
        self._sink: bytearray | None = None
        #: A first section's header was seen and its ``begin`` is still to come.
        self.headed = False
        #: A ``table`` was read, which ``begin`` counts in with its section.
        self.tabled = False
        #: The current section has had an encoded line.
        self.seen = False

    # -- errors -----------------------------------------------------------------

    def error(self, text: str, severe: bool = True) -> None:
        """``Local_Error``: counted, shown with *Display error messages*, and
        a severe one breaks the file it is about."""
        self.result.errors += 1
        if self.display_errors:
            self.job.ask(DecodeError(text))
        current = self.current
        if severe and current is not None and not current.broken:
            current.broken = True
            if not self.save_broken and self.display_errors:
                self.job.ask(DecodeError(f"Failed to decode {current.name}"))

    # -- what a line is ----------------------------------------------------------

    def count(self, line: str) -> None:
        """``CalcCRC``: the line, and its line end, into the section's sum."""
        raw = (line + "\n").encode("latin-1", "replace")
        self.sum = sum_r(raw, self.sum)
        self.size += len(raw)

    def clear(self) -> None:
        self.sum = self.size = 0

    def open_file(self, name: str) -> _File:
        """The file *name* is being decoded into, asked about the first time
        if it is there already (``CheckExist``)."""
        name = os.path.basename(name) or "unknown"
        known = self.files.get(name)
        if known is not None:
            return known
        record = self.files[name] = _File(name)
        target = self.out_dir / name
        if self.check_existing and target.exists():
            answer = self.job.ask(FileExists(target))
            if answer == "all":
                self.check_existing = False
            elif answer == "no":
                record.skip = True
            elif answer != "yes":
                record.skip = True
                self.stop = True
        return record

    def start_section(self, record: _File, number: int) -> None:
        """Lines from here on are *record*'s section *number* -- or nobody's,
        for a section already had (``DuplicateSection``, a warning)."""
        self.current, self.number = record, number
        self.seen = False
        if number in record.sections:
            self.error(f"Duplicate section {number} of file {record.name}", severe=False)
            self._sink = None
        else:
            self._sink = record.sections.setdefault(number, bytearray())
        if self.pending_time is not None:
            record.file_time, self.pending_time = self.pending_time, None

    def end_of_data(self, text: str) -> None:
        """The zero-length line or ``end``: the file's last section is done."""
        self.count(text)
        current = self.current
        if current is not None:
            current.end_found = True
            if current.total is None:
                current.total = self.number
        self.data, self.ended = False, True

    def line(self, raw: str) -> None:
        text = raw.rstrip("\r\n")
        stripped = text.strip()
        if self.table_lines is not None:
            # The two lines after ``table``: the mapping this file is in.
            if stripped:
                self.table_lines.append(text)
                self.count(text)
                if len(self.table_lines) == 2:
                    chars = "".join(self.table_lines)
                    self.table = {ch: index for index, ch in enumerate(chars[:64])}
                    self.table_lines = None
            return
        if stripped.startswith("section "):
            match = _SECTION.match(stripped)
            self.data = self.ended = False
            if match is None:
                self.error("Can not interpret section header")
                self._sink = None
                return
            number, total, name = int(match[1]), match[2], match[3]
            self.result.found = True
            record = self.open_file(name)
            if total is not None:
                if record.total is not None and record.total != int(total):
                    self.current = record
                    self.error("Maximal section number mismatch")
                record.total = int(total)
            self.start_section(record, number)
            self.clear()
            self.headed = number == 1
            # A later section's lines follow its header; the first's, ``begin``.
            self.data = number > 1
            return
        if stripped == "table" and not self.data:
            self.clear()
            self.count(text)
            self.table_lines = []
            self.tabled = True
            return
        if stripped.startswith("filetime ") and not self.data:
            try:
                stamp = int(stripped.split()[1])
            except (IndexError, ValueError):
                self.error("Invalid filetime number", severe=False)
                return
            if self.headed and self.current is not None:
                self.current.file_time = stamp
            else:
                self.pending_time = stamp
            return
        if stripped.startswith("begin "):
            parts = stripped.split(None, 2)
            if len(parts) < 3:
                self.error("File name expected")
                return
            name = os.path.basename(parts[2]) or "unknown"
            self.result.found = True
            if self.headed and self.current is not None:
                # The first section's header named the file already.
                if self.current.name != name:
                    self.error('Filenames of "section" and "begin" mismatch')
            else:
                self.start_section(self.open_file(name), 1)
            if not self.tabled:
                self.clear()
                self.table = None
            self.headed = self.tabled = False
            self.count(text)
            self.data, self.ended = True, False
            return
        if stripped.startswith("sum -r/size "):
            self._checksum(stripped)
            return
        if stripped.startswith("crc64 "):
            return
        if stripped == "end" and (self.data or self.ended):
            if self.data:
                self.error('Unexpected "end" encountered', severe=False)
            self.end_of_data(text)
            return
        if not self.data:
            return
        if stripped in ("`", "``") or (text and not stripped):
            # The zero-length line -- a blank one, as other encoders wrote it.
            self.end_of_data(text)
            return
        if not text:
            # The empty line a section that is not the last ends with --
            # once it has had a line: one stands under every header too.
            if self.seen:
                self.data = False
            return
        decoded = decode_line(text.rstrip(), self.table)
        if decoded is None:
            return  # a mail header, a signature: not ours
        self.count(text)
        self.seen = True
        current = self.current
        if self._sink is not None and current is not None and not current.skip:
            self._sink += decoded

    def _checksum(self, stripped: str) -> None:
        """``CheckSum``: a section's lines against their listed sum and size,
        or the whole file's listed sum and size kept for the end."""
        match = _SUM.match(stripped)
        current = self.current
        if match is None:
            self.error("Can not interpret CheckSum format", severe=False)
            return
        listed, size, what = int(match[1]), int(match[2]), match[3]
        if current is None or current.skip:
            return
        if what == "section":
            if self._sink is not None:
                if listed != self.sum:
                    self.error(f"CRC error - {current.name}, Section {self.number}")
                if size != self.size:
                    self.error(f"Size mismatch - {current.name}, Section {self.number}")
        else:
            current.listed = (listed, size)
        self.clear()
        self.data = False

    # -- the end -----------------------------------------------------------------

    def finish(self) -> None:
        """``FlushLeftSections``: every file put together, checked and written
        -- a broken one only with *Save broken files*."""
        for record in self.files.values():
            if record.skip:
                continue
            self.current = record
            total = record.total or max(record.sections, default=1)
            missing = [n for n in range(1, total + 1) if n not in record.sections]
            if missing:
                ranges = _ranges(missing)
                plural = len(missing) > 1
                self.error(f"{'Sections' if plural else 'Section'} {ranges} of file {record.name} "
                           f"({total}) {'are absent' if plural else 'is absent'}")
                self.error(f"Failed to decode completely {record.name}")
            elif not record.end_found:
                self.error(f"File is not terminated ({record.name})")
            data = b"".join(bytes(record.sections[n]) for n in sorted(record.sections))
            if record.listed is not None and not missing:
                listed, size = record.listed
                if size != len(data):
                    self.error(f"Size mismatch of file {record.name}, Listed={size}, Calculated={len(data)}")
                elif listed != sum_r(data):
                    self.error(f"CRC mismatch of file {record.name}, Listed={listed}, "
                               f"Calculated={sum_r(data)}")
            if record.broken and not self.save_broken:
                continue
            target = self.out_dir / record.name
            try:
                target.write_bytes(data)
            except OSError as error:
                self.error(f"Can not create {record.name}: {error.strerror or error}")
                continue
            self.result.written.append(target)
            if record.file_time is not None:
                stamp = from_dos_time(record.file_time)
                if stamp is not None:
                    try:
                        os.utime(target, (stamp, stamp))
                    except OSError:
                        pass
            if not record.broken:
                self.result.decoded += 1


def _ranges(numbers: list[int]) -> str:
    """``SetMiss``: ``1, 3-5``."""
    runs: list[list[int]] = []
    for n in numbers:
        if runs and runs[-1][1] + 1 == n:
            runs[-1][1] = n
        else:
            runs.append([n, n])
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in runs)


def decode(source: Path, out_dir: Path, job: Job, *, check_existing: bool = True,
           display_errors: bool = True, save_broken: bool = False) -> DecodeResult:
    """``UU_Decode``: every file *source* holds, decoded into *out_dir*.

    ``OSError`` for a source that cannot be read; ``Stopped`` if the job is.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    decoder = _Decoder(out_dir, job, check_existing, display_errors, save_broken)
    with open(source, encoding="latin-1", newline="") as text:
        for raw in text:
            job.wait_while_paused()
            if job.stopped:
                raise Stopped
            decoder.line(raw)
            if decoder.stop:
                break
    if not decoder.stop:
        decoder.finish()
    if not decoder.result.found and display_errors:
        job.ask(DecodeError(NO_STUFF))
    return decoder.result
