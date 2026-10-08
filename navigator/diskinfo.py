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
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from navkit.i18n import tr, tr_n

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


def mount_of(path: Path, mounts: str) -> tuple[str, str, str]:
    """``(mount point, device, type)`` of the longest mount holding *path*."""
    best = ("/", "", "")
    target = str(path)
    for line in mounts.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        point = parts[1].replace("\\040", " ")
        inside = target == point or target.startswith(point.rstrip("/") + "/")
        if inside and len(point) >= len(best[0]):
            best = (point, parts[0], parts[2])
    return best


def _label_of(device: str, labels: Path = Path("/dev/disk/by-label")) -> str:
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
        facts.label = _label_of(facts.device)
    try:
        facts.memory_total, facts.memory_available = _meminfo(meminfo.read_text())
    except OSError:
        pass
    facts.memory_navigator = _resident()
    facts.info_name, facts.info_lines = _info_file(Path(directory))
    return facts


def lines(directory: Path, entries: Iterable[Any], facts: DiskFacts | None,
          shows: Any) -> list[tuple[str, bool]]:
    """The panel's lines, ``(text, centred)``, as ``TDiskInfo.Draw`` laid
    them out: *shows* is the ``drive_info`` section, read box by box."""
    out: list[tuple[str, bool]] = []
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
    if facts is not None:
        if shows.total_memory and facts.memory_total is not None:
            out.append((tr("~{n:,}~K bytes total memory").format(n=facts.memory_total >> 10), True))
        if shows.user_memory and facts.memory_available is not None:
            out.append((tr_n("~{n:,}~ byte memory for user", "~{n:,}~ bytes memory for user",
                             facts.memory_available), True))
        if shows.navigator_memory and facts.memory_navigator is not None:
            out.append((tr_n("~{n:,}~ byte memory for Navigator", "~{n:,}~ bytes memory for Navigator",
                             facts.memory_navigator), True))
        if out and shows.information_file and facts.info_lines:
            out.append((f"\0{facts.info_name}", True))  # the rule, drawn by the panel
            out += [(text, False) for text in facts.info_lines]
    while out and out[-1][0] == "":
        out.pop()
    return out
