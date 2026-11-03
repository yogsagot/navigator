"""Utilities > System monitor: the processors, the memory and the sensors, read live.

**Not DOS Navigator's.** A departure that was asked for: DOS had one processor, no swap and no sensors to read, and
DN had nothing like this. It is the window beside Process list (:mod:`navigator.lib.system.processes`), and like that
one it reads ``/proc`` and ``/sys`` itself, with no psutil, so the run-time dependencies stay pure Python.

- **Processors.** ``/proc/stat``'s ``cpu`` line and one ``cpuN`` line per processor. Each read is turned into a busy
  share by :class:`CpuSampler`, top-style: the busy ticks since the last read over all the ticks. Idle and I/O wait
  count as idle. The first read has nothing before it, so it is all zeros. A processor that went offline or came back
  online changes the set of lines, and the lines it changed start again at 0 instead of being guessed. Each
  processor's clock is ``cpufreq``'s ``scaling_cur_freq``, else ``/proc/cpuinfo``'s ``cpu MHz``, else unknown.
- **Memory.** ``/proc/meminfo``: *Memory* is total less available. *Virtual* is the commit charge, ``Committed_AS``
  of ``CommitLimit``: what the programs were promised, which overcommit lets pass the limit. *Swap* is total less
  free.
- **Sensors.** Each ``/sys/class/hwmon`` chip's temperatures (``tempN_input`` in thousandths of a degree, with
  ``_label``, ``_max`` and ``_crit``) and fans (``fanN_input`` in RPM). Two chips of one name, such as two NVMe
  disks, are told apart by the device they sit on. A reading that cannot be read is left out, and the rest of its
  chip stays. Without hwmon temperatures, ``/sys/class/thermal``'s zones stand in.

Everything is read under a *root* (``/`` but for tests), on the window's thread: ``/proc`` and ``/sys`` answer at
once, but a read on the loop breaks the rule even so.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from navigator.lib.system.memory import meminfo

ROOT = Path("/")


@dataclass(frozen=True, slots=True)
class Ticks:
    """One ``/proc/stat`` processor line: its busy ticks and all its ticks."""

    busy: int
    total: int


@dataclass(frozen=True, slots=True)
class Cpu:
    """A processor's share since the last read, in percent, and its clock in MHz (None: unknown).
    *number* is ``cpuN``'s N, or -1 for the line that sums them all."""

    number: int
    percent: float
    mhz: float | None = None


@dataclass(frozen=True, slots=True)
class Memory:
    """``/proc/meminfo``'s figures, in bytes; 0 for one it does not have."""

    total: int = 0
    available: int = 0
    cached: int = 0
    swap_total: int = 0
    swap_free: int = 0
    committed: int = 0
    commit_limit: int = 0

    @property
    def used(self) -> int:
        return max(0, self.total - self.available)

    @property
    def swap_used(self) -> int:
        return max(0, self.swap_total - self.swap_free)


@dataclass(frozen=True, slots=True)
class Temperature:
    """One temperature sensor's reading, in degrees Celsius, with the limits its chip gives."""

    label: str
    celsius: float
    high: float | None = None
    critical: float | None = None

    @property
    def level(self) -> str:
        """``"hot"`` at or past the critical limit, ``"warm"`` at or past the high one, else ``""``."""
        if self.critical is not None and self.critical > 0 and self.celsius >= self.critical:
            return "hot"
        if self.high is not None and self.high > 0 and self.celsius >= self.high:
            return "warm"
        return ""


@dataclass(frozen=True, slots=True)
class Fan:
    """One fan's speed, in revolutions a minute."""

    label: str
    rpm: int


@dataclass(frozen=True, slots=True)
class Chip:
    """A sensor chip: what the kernel calls it, the device it sits on, and its readings."""

    name: str
    device: str = ""
    temperatures: tuple[Temperature, ...] = ()
    fans: tuple[Fan, ...] = ()

    @property
    def lines(self) -> int:
        """How many readings it has."""
        return len(self.temperatures) + len(self.fans)


@dataclass(frozen=True, slots=True)
class Snapshot:
    """One read: the processors' total and each one's share, the memory, and the sensor chips."""

    total: Cpu = Cpu(-1, 0.0)
    cpus: tuple[Cpu, ...] = ()
    memory: Memory = Memory()
    chips: tuple[Chip, ...] = ()

    def shape(self) -> tuple[int, bool, tuple[tuple[str, int], ...]]:
        """What the window's size depends on: how many processors, whether any has a clock, and each chip's name
        with its number of readings. The window refits only when this changes."""
        return (len(self.cpus), any(cpu.mhz is not None for cpu in self.cpus),
                tuple((chip.name, chip.lines) for chip in self.chips))


def short_size(size: int) -> str:
    """*size* bytes in five cells or fewer: ``512K``, ``900M``, ``12.5G``, ``1.2T``."""
    value = float(max(0, size))
    for unit in ("K", "M", "G", "T", "P"):
        value /= 1024
        if value < 1000 or unit == "P":
            return f"{value:.1f}{unit}" if value < 100 and unit != "K" else f"{value:.0f}{unit}"
    return f"{value:.0f}P"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _number(path: Path) -> int | None:
    text = _read(path)
    try:
        return int(text)
    except ValueError:
        return None


# -- the processors --------------------------------------------------------------------


def cpu_times(text: str) -> dict[int, Ticks]:
    """``/proc/stat``'s processor lines, by number; -1 is the ``cpu`` line that sums them all.

    The fields are user, nice, system, idle, iowait, irq, softirq, steal, guest and guest_nice. Guest time is counted
    in user and nice already, so it is left out of the total.
    """
    found: dict[int, Ticks] = {}
    for line in text.splitlines():
        if not line.startswith("cpu"):
            continue
        name, *fields = line.split()
        number = name[3:]
        if number and not number.isdigit():
            continue
        try:
            values = [int(value) for value in fields[:8]]
        except ValueError:
            continue
        if len(values) < 4:
            continue
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        total = sum(values)
        found[int(number) if number else -1] = Ticks(total - idle, total)
    return found


class CpuSampler:
    """Turns each read of ``/proc/stat`` into the share every processor was busy since the read before.

    Not reactive: it lives on the reading thread between reads, and one read runs at a time.
    """

    def __init__(self) -> None:
        self._before: dict[int, Ticks] = {}

    def sample(self, now: dict[int, Ticks]) -> dict[int, float]:
        """Each line's busy percent since the last call: 0 for a line the last call did not have, or whose ticks went
        backwards (a processor brought online again starts its count over)."""
        shares: dict[int, float] = {}
        for number, ticks in now.items():
            before = self._before.get(number)
            share = 0.0
            if before is not None:
                elapsed = ticks.total - before.total
                busy = ticks.busy - before.busy
                if elapsed > 0 and busy >= 0:
                    share = min(100.0, busy * 100.0 / elapsed)
            shares[number] = share
        self._before = dict(now)
        return shares


def frequencies(root: Path = ROOT) -> dict[int, float]:
    """Each processor's clock in MHz: ``cpufreq``'s, else ``/proc/cpuinfo``'s, else nothing."""
    found: dict[int, float] = {}
    base = root / "sys/devices/system/cpu"
    try:
        names = os.listdir(base)
    except OSError:
        names = []
    for name in names:
        if not re.fullmatch(r"cpu\d+", name):
            continue
        khz = _number(base / name / "cpufreq/scaling_cur_freq")
        if khz is not None and khz > 0:
            found[int(name[3:])] = khz / 1000.0
    if found:
        return found
    number = None
    for line in _read(root / "proc/cpuinfo").splitlines():
        key, _, value = line.partition(":")
        key = key.strip()
        if key == "processor":
            try:
                number = int(value)
            except ValueError:
                number = None
        elif key == "cpu MHz" and number is not None:
            try:
                found[number] = float(value)
            except ValueError:
                pass
    return found


# -- the memory --------------------------------------------------------------------------


def memory(root: Path = ROOT) -> Memory:
    """``/proc/meminfo``'s memory, commit charge and swap."""
    values = meminfo(_read(root / "proc/meminfo"))
    available = values.get("MemAvailable", values.get("MemFree", 0))
    cached = values.get("Buffers", 0) + values.get("Cached", 0)
    return Memory(values.get("MemTotal", 0), available, cached, values.get("SwapTotal", 0),
                  values.get("SwapFree", 0), values.get("Committed_AS", 0), values.get("CommitLimit", 0))


# -- the sensors ---------------------------------------------------------------------------


def _sorted_by_number(names: list[str], pattern: str) -> list[tuple[int, str]]:
    found = []
    for name in names:
        matched = re.fullmatch(pattern, name)
        if matched:
            found.append((int(matched.group(1)), name))
    return sorted(found)


def _degrees(path: Path) -> float | None:
    value = _number(path)
    return None if value is None else value / 1000.0


def _chip(path: Path) -> Chip | None:
    try:
        names = os.listdir(path)
    except OSError:
        return None
    name = _read(path / "name") or path.name
    try:
        device = os.path.basename(os.readlink(path / "device"))
    except OSError:
        device = ""
    temperatures = []
    for number, _ in _sorted_by_number(names, r"temp(\d+)_input"):
        celsius = _degrees(path / f"temp{number}_input")
        if celsius is None:
            continue
        label = _read(path / f"temp{number}_label") or f"temp{number}"
        temperatures.append(Temperature(label, celsius, _degrees(path / f"temp{number}_max"),
                                        _degrees(path / f"temp{number}_crit")))
    fans = []
    for number, _ in _sorted_by_number(names, r"fan(\d+)_input"):
        rpm = _number(path / f"fan{number}_input")
        if rpm is None:
            continue
        fans.append(Fan(_read(path / f"fan{number}_label") or f"fan{number}", rpm))
    if not temperatures and not fans:
        return None
    return Chip(name, device, tuple(temperatures), tuple(fans))


def _thermal_zones(root: Path) -> list[Chip]:
    base = root / "sys/class/thermal"
    try:
        names = os.listdir(base)
    except OSError:
        return []
    temperatures = []
    for number, name in _sorted_by_number(names, r"thermal_zone(\d+)"):
        celsius = _degrees(base / name / "temp")
        if celsius is not None:
            temperatures.append(Temperature(_read(base / name / "type") or name, celsius))
    return [Chip("thermal", "", tuple(temperatures))] if temperatures else []


def sensors(root: Path = ROOT) -> list[Chip]:
    """Every hwmon chip that has a reading, in the kernel's order. Two of one name are told apart by their device.
    Without a single hwmon temperature, the thermal zones as one chip."""
    base = root / "sys/class/hwmon"
    try:
        names = os.listdir(base)
    except OSError:
        names = []
    chips = [chip for _, name in _sorted_by_number(names, r"hwmon(\d+)") if (chip := _chip(base / name))]
    counted: dict[str, int] = {}
    for chip in chips:
        counted[chip.name] = counted.get(chip.name, 0) + 1
    chips = [chip if counted[chip.name] > 1 else Chip(chip.name, "", chip.temperatures, chip.fans)
             for chip in chips]
    if not any(chip.temperatures for chip in chips):
        chips = _thermal_zones(root) + chips
    return chips


# -- a read --------------------------------------------------------------------------------


def available(root: Path = ROOT) -> bool:
    """Whether there is a ``/proc/stat`` to read the processors from."""
    return os.access(root / "proc/stat", os.R_OK)


class Monitor:
    """Reads a :class:`Snapshot`; called on the window's reading thread, one read at a time."""

    def __init__(self, root: Path = ROOT) -> None:
        self.root = root
        self._sampler = CpuSampler()

    def __call__(self) -> Snapshot:
        root = self.root
        shares = self._sampler.sample(cpu_times(_read(root / "proc/stat")))
        clocks = frequencies(root)
        cpus = tuple(Cpu(number, shares[number], clocks.get(number)) for number in sorted(shares) if number >= 0)
        total = Cpu(-1, shares.get(-1, 0.0))
        return Snapshot(total, cpus, memory(root), tuple(sensors(root)))
