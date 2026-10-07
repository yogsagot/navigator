"""Utilities > System Information: DOS Navigator's ``SystemInfo`` (MEMINFO.PAS), read for Linux.

DN's four boxes, filled with what this machine says where DN probed the
BIOS: *Main board* -- the machine (DMI's vendor and product), the CPU's model
and speed, and how many it has where DN had the co-processor; *Disk drivers* --
each disk (``/sys/block``, loop, RAM and mapper devices left out), its model
and size, where DN had the floppies and the two hard drives' geometry;
*Memory* -- total, available and swap (``/proc/meminfo``), where DN had
conventional, extended and expanded; *Other* -- the system, its kernel, the
host and how long it has been up, where DN had the COM and LPT ports and
the DOS version.  What cannot be read is left out.

Everything is read from files under a *root* (``/`` but for tests), on a
thread: ``/sys`` and ``/proc`` answer at once, but this keeps to the rule.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path

#: Block devices that are not disks.
_NOT_DISKS = ("loop", "ram", "zram", "dm-", "md", "sr", "fd")


@dataclass
class SystemFacts:
    """The four boxes' lines, ``(label, value)`` each."""

    board: list[tuple[str, str]] = field(default_factory=list)
    disks: list[tuple[str, str]] = field(default_factory=list)
    memory: list[tuple[str, str]] = field(default_factory=list)
    other: list[tuple[str, str]] = field(default_factory=list)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def size_text(size: int) -> str:
    """*size* bytes as DN-like ``nnn,nnnK``, or in M or G once it is large."""
    for unit, scale in (("G", 1 << 30), ("M", 1 << 20)):
        if size >= 10 * scale:
            return f"{size // scale:,}{unit}"
    return f"{size // 1024:,}K"


def _board(root: Path) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    dmi = root / "sys/class/dmi/id"
    vendor, product = _read(dmi / "sys_vendor"), _read(dmi / "product_name")
    machine = " ".join(part for part in (vendor, product) if part and part.lower() != "to be filled by o.e.m.")
    found.append(("Machine type", machine or platform.machine()))
    cpuinfo = _read(root / "proc/cpuinfo")
    model = next((line.split(":", 1)[1].strip() for line in cpuinfo.splitlines()
                  if line.startswith(("model name", "Model", "cpu model"))), "")
    top = _read(root / "sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
    speed = f"{int(top) // 1000} MHz" if top.isdigit() else ""
    if model or speed:
        found.append(("CPU", " ".join(part for part in (model, speed) if part)))
    cores = sum(1 for line in cpuinfo.splitlines() if line.startswith("processor")) or os.cpu_count()
    if cores:
        found.append(("CPUs", str(cores)))
    return found


def _disks(root: Path) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    block = root / "sys/block"
    try:
        names = sorted(entry.name for entry in block.iterdir())
    except OSError:
        return found
    for name in names:
        if name.startswith(_NOT_DISKS):
            continue
        sectors = _read(block / name / "size")
        if not sectors.isdigit() or int(sectors) == 0:
            continue
        model = _read(block / name / "device/model")
        removable = _read(block / name / "removable") == "1"
        what = size_text(int(sectors) * 512)
        if model:
            what += f", {model}"
        if removable:
            what += ", removable"
        found.append((name, what))
    return found


def _memory(root: Path) -> list[tuple[str, str]]:
    values: dict[str, int] = {}
    for line in _read(root / "proc/meminfo").splitlines():
        name, _, rest = line.partition(":")
        words = rest.split()
        if words and words[0].isdigit():
            values[name] = int(words[0]) * 1024
    found: list[tuple[str, str]] = []
    for label, key in (("Total", "MemTotal"), ("Available", "MemAvailable"), ("Swap", "SwapTotal")):
        if key in values:
            found.append((label, size_text(values[key])))
    return found


def _other(root: Path) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    release = {}
    for line in _read(root / "etc/os-release").splitlines():
        key, _, value = line.partition("=")
        release[key] = value.strip().strip('"')
    system = release.get("PRETTY_NAME") or platform.system()
    found.append(("OS", system))
    kernel = _read(root / "proc/sys/kernel/osrelease") or platform.release()
    if kernel:
        found.append(("Kernel", f"{kernel} {platform.machine()}".strip()))
    host = _read(root / "proc/sys/kernel/hostname") or platform.node()
    if host:
        found.append(("Host", host))
    uptime = _read(root / "proc/uptime").split()
    if uptime:
        try:
            seconds = int(float(uptime[0]))
        except ValueError:
            seconds = -1
        if seconds >= 0:
            days, rest = divmod(seconds, 86400)
            found.append(("Up", (f"{days}d " if days else "") + f"{rest // 3600}:{rest % 3600 // 60:02d}"))
    return found


def gather(root: Path = Path("/")) -> SystemFacts:
    """Everything the dialog shows: a thread runs it."""
    return SystemFacts(_board(root), _disks(root), _memory(root), _other(root))


def lines(rows: list[tuple[str, str]], width: int) -> str:
    """A box's text, DN's way: the labels right-aligned to a colon, values cut
    to the box (*width* cells)."""
    if not rows:
        return " None"
    room = max(len(label) for label, _ in rows)
    out = []
    for label, value in rows:
        text = f"{label:>{room}} : {value}"
        out.append(text if len(text) <= width else text[: max(0, width - 3)] + "...")
    return "\n".join(out)
