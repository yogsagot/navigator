"""Ctrl+L's information panel: DOS Navigator's ``TDiskInfo`` and ``ReadDiskInfo`` (DISKINFO.PAS).

What it says about the active panel's directory, line by line, each one a
box in *Information Panel Setup* (``DriveInfoData``): the directory, its
totals, the file system's size, free space and label, three lines of memory,
and the directory's information file below a rule.  ``~`` marks what DN drew
highlighted, as its resource strings marked it.

Read for POSIX: a *drive* is the file system the directory is on, named by
where it is mounted; its *label* is the one ``/dev/disk/by-label`` gives its
device, else the device and the file system's type.  DN's *conventional
memory*, *memory for user* and *memory for Navigator* are the machine's
memory, what is available to programs (``MemAvailable``) and what Navigator
holds (its resident set).  The information file is ``DirInfo``, else
``File_ID.DIZ``, as DN looked for them -- any case.  The totals count what
the panel lists, ``..`` aside, files and directories alike as
``CountDirLen`` counted them, the bytes being the files'.

Below the directory's lines, a *Current file* section describes the entry
under the panel's cursor: its type, size, times, attributes, owner, links
and inode (:func:`file_lines`).  A departure: ``TDiskInfo`` described the
directory alone.  The listing's entry gives most of it; a local entry's
access and change times, links and inode are one ``lstat`` on a thread
(:func:`stat_file`), which a remote one goes without; a media file's or a
PDF's details are a second read (:mod:`navigator.lib.system.mediainfo`).
"""

from __future__ import annotations

import mimetypes
import os
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from navkit.i18n import tr, tr_n

from navigator.lib.config import country
from navigator.lib.system import mediainfo

#: DN's ``sDirInfo`` and ``sFileID``, in the order it looked for them.
INFO_FILES = ("DirInfo", "File_ID.DIZ")

#: How much of an information file is shown (DN's ``Count < 100``).
INFO_LINES = 100


@dataclass
class DiskFacts:
    """What a read of the disk and the machine found, on a thread."""

    total: int | None = None
    free: int | None = None
    mount: str = ""
    device: str = ""
    fs_type: str = ""
    label: str = ""
    memory_total: int | None = None
    memory_available: int | None = None
    memory_navigator: int | None = None
    info_name: str = ""
    info_lines: list[str] = field(default_factory=list)


@dataclass
class FileFacts:
    """What a thread found of the current file beyond its listing entry."""

    atime: float | None = None
    ctime: float | None = None
    nlink: int | None = None
    inode: int | None = None
    #: The MIME type its name suggests (the stdlib's table, read on first use).
    mime: str = ""
    #: A media file's or PDF's details (:class:`navigator.lib.system.mediainfo.Media`),
    #: read after the rest; None until then, or for any other file.
    media: Any = None


#: The octal escapes the kernel writes in a mounts field.
_ESCAPES = {"\\040": " ", "\\011": "\t", "\\012": "\n", "\\134": "\\"}


def unescape(field: str) -> str:
    """A ``/proc/self/mounts`` field with its octal escapes undone."""
    for escape, char in _ESCAPES.items():
        field = field.replace(escape, char)
    return field


def mount_of(path: Path, mounts: str) -> tuple[str, str, str]:
    """``(mount point, device, type)`` of the longest mount holding *path*."""
    best = ("/", "", "")
    target = str(path)
    for line in mounts.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        point = unescape(parts[1])
        inside = target == point or target.startswith(point.rstrip("/") + "/")
        if inside and len(point) >= len(best[0]):
            best = (point, parts[0], parts[2])
    return best


def label_of(device: str, labels: Path = Path("/dev/disk/by-label")) -> str:
    """*device*'s file system label, from ``/dev/disk/by-label``; empty if none."""
    try:
        resolved = os.path.realpath(device)
        for entry in labels.iterdir():
            if os.path.realpath(entry) == resolved:
                return entry.name.replace("\\x20", " ")
    except OSError:
        pass
    return ""


def _meminfo(text: str) -> tuple[int | None, int | None]:
    values: dict[str, int] = {}
    for line in text.splitlines():
        name, _, rest = line.partition(":")
        words = rest.split()
        if words and words[0].isdigit():
            values[name] = int(words[0]) * 1024
    return values.get("MemTotal"), values.get("MemAvailable")


def _resident() -> int | None:
    try:
        with open("/proc/self/statm") as file:
            return int(file.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError):
        return None


def _info_file(directory: Path) -> tuple[str, list[str]]:
    try:
        names = {name.lower(): name for name in os.listdir(directory)}
    except OSError:
        return "", []
    for wanted in INFO_FILES:
        found = names.get(wanted.lower())
        if found is None:
            continue
        try:
            with open(directory / found, encoding="utf-8", errors="replace") as file:
                lines = [line.rstrip("\r\n") for _, line in zip(range(INFO_LINES), file)]
        except OSError:
            continue
        return wanted, lines
    return "", []


def gather(directory: Path, *, mounts: Path = Path("/proc/self/mounts"),
           meminfo: Path = Path("/proc/meminfo")) -> DiskFacts:
    """Everything the panel shows that is not the listing's: a thread runs it."""
    facts = DiskFacts()
    try:
        usage = shutil.disk_usage(directory)
        facts.total, facts.free = usage.total, usage.free
    except OSError:
        pass
    try:
        text = mounts.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    facts.mount, facts.device, facts.fs_type = mount_of(Path(directory).resolve(), text)
    if facts.device.startswith("/dev/"):
        facts.label = label_of(facts.device)
    try:
        facts.memory_total, facts.memory_available = _meminfo(meminfo.read_text())
    except OSError:
        pass
    facts.memory_navigator = _resident()
    facts.info_name, facts.info_lines = _info_file(Path(directory))
    return facts


def stat_file(path: Path | None, name: str) -> FileFacts:
    """The current file's :class:`FileFacts`: a thread runs it.  *path* None
    (an entry on another drive) guesses the type from *name* alone."""
    facts = FileFacts(mime=mimetypes.guess_type(name, strict=False)[0] or "")
    if path is None:
        return facts
    try:
        info = os.lstat(path)
    except OSError:
        return facts
    facts.atime, facts.ctime = info.st_atime, info.st_ctime
    facts.nlink, facts.inode = info.st_nlink, info.st_ino
    return facts


def kind_of(entry: Any) -> str:
    """What sort of thing *entry* is, in words."""
    mode = entry.mode
    if entry.is_link:
        if stat.S_ISLNK(mode):
            return tr("Broken symbolic link")
        return tr("Symbolic link to a directory") if entry.is_dir else tr("Symbolic link to a file")
    if entry.is_dir:
        return tr("Directory")
    if stat.S_ISSOCK(mode):
        return tr("Socket")
    if stat.S_ISCHR(mode):
        return tr("Character device")
    if stat.S_ISBLK(mode):
        return tr("Block device")
    if stat.S_ISFIFO(mode):
        return tr("FIFO")
    if stat.S_ISREG(mode) and mode & 0o111:
        return tr("Executable file")
    return tr("File")


def file_lines(entry: Any, facts: FileFacts | None) -> list[tuple[str, bool]]:
    """The *Current file* section for *entry*, under its rule, a
    :func:`table` centred as a block; none for no entry or ``..``.  *facts* None (not read yet) leaves out what only a
    stat says."""
    if entry is None or entry.name == "..":
        return []
    facts = facts or FileFacts()
    kind = kind_of(entry)
    if facts.mime and not entry.is_dir:
        kind = f"{kind}, {facts.mime}"
    out = [
        ("\0" + tr("Current file"), True),
        (tr("Name: ~{name}~").format(name=entry.name), False),
        (tr("Type: ~{kind}~").format(kind=kind), False),
    ]
    if entry.is_dir and not entry.counted:
        out.append((tr("Size: ~not counted~"), False))
    else:
        out.append((tr_n("Size: ~{n:,}~ byte", "Size: ~{n:,}~ bytes", entry.size), False))
    if entry.mtime:
        out.append((tr("Modified: ~{when}~").format(when=country.stamp(entry.mtime)), False))
    if facts.atime is not None:
        out.append((tr("Accessed: ~{when}~").format(when=country.stamp(facts.atime)), False))
    if facts.ctime is not None:
        out.append((tr("Changed: ~{when}~").format(when=country.stamp(facts.ctime)), False))
    if entry.mode:
        attributes = f"{entry.display_attributes} ({stat.S_IMODE(entry.mode):04o})"
        out.append((tr("Attributes: ~{attributes}~").format(attributes=attributes), False))
    owner = entry.display_owner
    if owner:
        out.append((tr("Owner: ~{owner}~").format(owner=owner), False))
    if facts.nlink is not None and facts.inode is not None:
        out.append((tr("Links: ~{links}~, inode ~{inode}~").format(links=facts.nlink, inode=facts.inode), False))
    if entry.link_target is not None:
        out.append((tr("Link to: ~{target}~").format(target=entry.link_target), False))
    for label, value in mediainfo.pairs(facts.media):
        if isinstance(value, float):
            value = country.stamp(value)
        out.append((f"{tr(label)}: ~{value}~", False))
    return out[:1] + [(text, True) for text in table([text for text, _ in out[1:]])]


def table(rows: list[str]) -> list[str]:
    """*rows*, each ``Label: value``, as a table centred as one block: the
    labels right-aligned on their colons, and every row padded to the
    widest, so that centring them one by one starts them all in one column.
    A row with no ``": "`` (a translation's) keeps its text."""
    split = [row.partition(": ") for row in rows]
    labels = max((len(label) for label, colon, _ in split if colon), default=0)
    rows = [label.rjust(labels) + colon + value if colon else label for label, colon, value in split]
    width = max(len(row.replace("~", "")) for row in rows)
    return [row + " " * (width - len(row.replace("~", ""))) for row in rows]


def lines(directory: Path, entries: Iterable[Any], facts: DiskFacts | None,
          shows: Any, entry: Any = None, file_facts: FileFacts | None = None) -> list[tuple[str, bool]]:
    """The panel's lines, ``(text, centred)``, as ``TDiskInfo.Draw`` laid
    them out: *shows* is the ``drive_info`` section, read box by box.
    *entry* is the one under the cursor, described after the directory's
    lines (:func:`file_lines`) and closed by a rule naming what follows:
    the *Drive*'s lines, else the *Memory*'s.  A blank line comes before
    each of the two rules."""
    out: list[tuple[str, bool]] = []
    current = file_lines(entry, file_facts) if shows.current_file else []
    if shows.directory_title or shows.totals:
        if shows.directory_title:
            out += [(tr("Current directory:"), True), (f"~{directory}~", True)]
        if shows.totals:
            listed = [entry for entry in entries if entry.name != ".."]
            if not listed:
                out.append((tr("No files in this directory"), True))
            else:
                size = sum(entry.size for entry in listed if not entry.is_dir)
                total = tr_n("~{n:,}~ byte", "~{n:,}~ bytes", size)
                out.append((tr_n("~{n:,}~ file with {total}", "~{n:,}~ files with {total}", len(listed),
                                 total=total), True))
        out.append(("", True))
    # The rule closing the current file's section, a blank line before it as
    # before the one opening it, named for what follows it.
    close = None
    if current:
        out += current
        out.append(("", True))
        close = len(out)
        out.append(("\0", True))
    volume = len(out)
    if facts is not None and (shows.volume_size or shows.volume_free or shows.volume_label):
        if shows.volume_size and facts.total is not None:
            out.append((tr_n("~{n:,}~ total byte on ~{mount}~", "~{n:,}~ total bytes on ~{mount}~",
                             facts.total, mount=facts.mount), True))
        if shows.volume_free and facts.free is not None:
            out.append((tr_n("~{n:,}~ free byte on ~{mount}~", "~{n:,}~ free bytes on ~{mount}~",
                             facts.free, mount=facts.mount), True))
        if shows.volume_label and facts.mount:
            if facts.label:
                out.append((tr("Volume label on ~{mount}: {label}~").format(mount=facts.mount, label=facts.label),
                            True))
            elif facts.device:
                kind = f" ({facts.fs_type})" if facts.fs_type else ""
                out.append((f"~{facts.device}{kind}~", True))
        out.append(("", True))
    memory = len(out)
    if facts is not None:
        if shows.total_memory and facts.memory_total is not None:
            out.append((tr("~{n:,}~K bytes total memory").format(n=facts.memory_total >> 10), True))
        if shows.user_memory and facts.memory_available is not None:
            out.append((tr_n("~{n:,}~ byte memory for user", "~{n:,}~ bytes memory for user",
                             facts.memory_available), True))
        if shows.navigator_memory and facts.memory_navigator is not None:
            out.append((tr_n("~{n:,}~ byte memory for Navigator", "~{n:,}~ bytes memory for Navigator",
                             facts.memory_navigator), True))
        if close is not None:
            if any(text for text, _ in out[volume:memory]):
                out[close] = ("\0" + tr("Drive"), True)
            elif len(out) > memory:
                out[close] = ("\0" + tr("Memory"), True)
        if out and shows.information_file and facts.info_lines:
            out.append((f"\0{facts.info_name}", True))  # the rule, drawn by the panel
            out += [(text, False) for text in facts.info_lines]
    # The closing rule, and the blank line before it, give way to a rule
    # after it and to nothing at all.
    if close is not None and (close + 1 == len(out) or out[close + 1][0].startswith("\0")):
        del out[close - 1:close + 1]
    while out and out[-1][0] == "":
        out.pop()
    return out
