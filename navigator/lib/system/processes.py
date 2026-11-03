"""Utilities > Process list's model: the running processes, read from ``/proc``.

**Not DOS Navigator's**: a departure, asked for.  DOS ran one program at a
time and DN had nothing to list; this is FAR Manager's process panel, read
the way ``ps`` and ``top`` read it -- ``/proc/<pid>/stat``, ``status`` and
``cmdline`` -- with no ``psutil`` (the run-time dependencies stay pure
Python).  Linux only: elsewhere :func:`available` is False and the menu entry
says so.

Nothing here touches a widget, and everything that reads ``/proc`` is meant
for a thread (``navml.background.Background``): a process's files are small,
but there may be a thousand of them.  A process that ends while it is being
read is left out, not an error -- the list is a snapshot, and the snapshot is
a little blurred.

**CPU %** is ``top``'s: the ticks a process used since the last read, over
the ticks the whole machine had in that time (``/proc/stat``'s first line),
times the processor count -- so one busy thread on a four-way machine reads
100%, as ``top`` says it.  The first read has nothing to compare with and
says 0.  :class:`Sampler` keeps what the last read saw.

:func:`send` refuses pid 1 and Navigator itself before ``os.kill`` is asked,
so a slip of the cursor cannot take the system or the file manager down; the
root helper's ``kill`` op refuses the same, and its own pid and its parent's.
"""

from __future__ import annotations

import errno
import os
import pwd
import signal
import time
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from navkit.i18n import tr

#: Where the kernel lists its processes.
PROC = Path("/proc")

#: The keys a list can be sorted by.
SORTS = ("pid", "user", "state", "cpu", "memory", "command")
#: The ones whose biggest is wanted first.
DESCENDING_FIRST = frozenset({"cpu", "memory"})



def state_words(letter: str) -> str:
    """``ps``'s state *letter* in words, translated; "" for one it does not know."""
    words = {
        "R": tr("running"), "S": tr("sleeping"), "D": tr("waiting for disk"), "Z": tr("zombie"),
        "T": tr("stopped"), "t": tr("traced"), "X": tr("dead"), "I": tr("idle"), "P": tr("parked"),
        "W": tr("paging"),
    }
    return words.get(letter, "")


def _clock_ticks() -> int:
    try:
        return os.sysconf("SC_CLK_TCK")
    except (ValueError, OSError, AttributeError):
        return 100


def _page_size() -> int:
    try:
        return os.sysconf("SC_PAGE_SIZE")
    except (ValueError, OSError, AttributeError):
        return 4096


CLOCK_TICKS = _clock_ticks()
PAGE_SIZE = _page_size()


def available(proc: Path = PROC) -> bool:
    """Whether there is a ``/proc`` to read processes from."""
    return (proc / "self" / "stat").is_file()


@dataclass(frozen=True)
class Process:
    """One process, as one read of ``/proc/<pid>`` found it."""

    pid: int
    ppid: int
    uid: int
    user: str
    #: ``ps``'s letter: R, S, D, Z, T...
    state: str
    threads: int
    #: Resident memory, in bytes.
    rss: int
    #: Virtual memory, in bytes.
    vsize: int
    #: User and system time used so far, in clock ticks.
    ticks: int
    #: When it started, in clock ticks after boot.
    started: int
    #: The kernel's name for it (``comm``), at most 15 bytes.
    name: str
    #: Its command line, its arguments joined by spaces; ``[name]`` for a
    #: kernel thread, which has none.
    command: str
    nice: int = 0
    #: CPU share since the last read, as a percentage of one processor.
    cpu: float = 0.0

    @property
    def kernel_thread(self) -> bool:
        return self.command.startswith("[") and self.command.endswith("]")


@dataclass(frozen=True)
class Row:
    """One row of the tree: a process and how deep it sits, and the box
    drawing's say -- whether each level above it has more to come."""

    process: Process
    depth: int = 0
    #: One per level above this one: whether that ancestor has a later sibling.
    rails: tuple[bool, ...] = ()
    #: Whether this is its parent's last child.
    last: bool = True
    #: Shown only as the parent of a match: the filter did not pick it.
    context: bool = False


_USERS: dict[int, str] = {}


def user_name(uid: int) -> str:
    """*uid*'s login name, else the number; remembered."""
    name = _USERS.get(uid)
    if name is None:
        try:
            name = pwd.getpwuid(uid).pw_name
        except (KeyError, OverflowError):
            name = str(uid)
        _USERS[uid] = name
    return name


def _read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def parse_stat(text: str) -> tuple[str, list[str]]:
    """``/proc/<pid>/stat``: the name between the parentheses and the
    fields after it.  The name may hold spaces and ``)`` itself, so the split
    is at the last ``)``."""
    start = text.index("(")
    end = text.rindex(")")
    return text[start + 1:end], text[end + 2:].split()


def read(pid: int, proc: Path = PROC) -> Process | None:
    """Process *pid*, or None when it is gone (or never was)."""
    where = proc / str(pid)
    raw = _read_bytes(where / "stat")
    if raw is None:
        return None
    try:
        name, fields = parse_stat(raw.decode("utf-8", "replace"))
        state = fields[0]
        ppid = int(fields[1])
        ticks = int(fields[11]) + int(fields[12])
        nice = int(fields[16])
        threads = int(fields[17])
        started = int(fields[19])
        vsize = int(fields[20])
        rss = int(fields[21]) * PAGE_SIZE
    except (ValueError, IndexError):
        return None
    uid = -1
    status = _read_bytes(where / "status")
    if status is not None:
        for line in status.decode("utf-8", "replace").splitlines():
            if line.startswith("Uid:"):
                parts = line.split()
                if len(parts) > 1 and parts[1].isdigit():
                    uid = int(parts[1])
                break
    if uid < 0:
        try:
            uid = where.stat().st_uid
        except OSError:
            return None
    cmdline = _read_bytes(where / "cmdline") or b""
    words = [word.decode("utf-8", "replace") for word in cmdline.split(b"\0") if word]
    command = " ".join(words) if words else f"[{name}]"
    return Process(pid=pid, ppid=ppid, uid=uid, user=user_name(uid), state=state, threads=threads,
                   rss=rss, vsize=vsize, ticks=ticks, started=started, name=name, command=command, nice=nice)


def pids(proc: Path = PROC) -> list[int]:
    """Every process's number."""
    try:
        return sorted(int(name) for name in os.listdir(proc) if name.isdigit())
    except OSError:
        return []


def gather(proc: Path = PROC) -> list[Process]:
    """Every process still there by the time it is read."""
    found = []
    for pid in pids(proc):
        process = read(pid, proc)
        if process is not None:
            found.append(process)
    return found


def machine_ticks(proc: Path = PROC) -> int:
    """All the clock ticks every processor has had since boot: ``/proc/stat``'s ``cpu`` line."""
    raw = _read_bytes(proc / "stat")
    if raw is None:
        return 0
    for line in raw.decode("ascii", "replace").splitlines():
        if line.startswith("cpu "):
            return sum(int(field) for field in line.split()[1:] if field.isdigit())
    return 0


def processors() -> int:
    try:
        return len(os.sched_getaffinity(0)) or 1
    except (AttributeError, OSError):
        return os.cpu_count() or 1


class Sampler:
    """Reads the processes and gives each its CPU share since the last read.

    Not reactive: it lives on the reading thread between reads, and one read
    runs at a time (the window's ``Background`` has one worker).
    """

    def __init__(self, proc: Path = PROC) -> None:
        self.proc = proc
        self._ticks: dict[tuple[int, int], int] = {}
        self._machine = 0

    def sample(self, found: Iterable[Process], machine: int, cpus: int) -> list[Process]:
        """*found* with ``cpu`` set from what changed since the last call.
        A process is known by its pid and start time, so a pid used again is
        not taken for the one before."""
        elapsed = machine - self._machine if self._machine else 0
        previous = self._ticks
        current: dict[tuple[int, int], int] = {}
        shown = []
        for process in found:
            key = (process.pid, process.started)
            current[key] = process.ticks
            before = previous.get(key)
            share = 0.0
            if elapsed > 0 and before is not None:
                share = max(0, process.ticks - before) * 100.0 * cpus / elapsed
            shown.append(replace(process, cpu=share))
        self._ticks = current
        self._machine = machine
        return shown

    def __call__(self) -> list[Process]:
        return self.sample(gather(self.proc), machine_ticks(self.proc), processors())


def sort_key(by: str) -> Any:
    """What *by* sorts on; the pid breaks ties, so the order holds still."""
    if by == "user":
        return lambda p: (p.user.casefold(), p.pid)
    if by == "state":
        return lambda p: (p.state, p.pid)
    if by == "cpu":
        return lambda p: (p.cpu, -p.pid)
    if by == "memory":
        return lambda p: (p.rss, -p.pid)
    if by == "command":
        return lambda p: (p.command.casefold(), p.pid)
    return lambda p: p.pid


def ordered(found: Iterable[Process], by: str, descending: bool) -> list[Process]:
    """*found* sorted *by* one of :data:`SORTS`."""
    return sorted(found, key=sort_key(by), reverse=descending)


def matches(process: Process, text: str) -> bool:
    """Whether the window's filter *text* -- any case, anywhere -- is in
    *process*'s command, its name, its owner or its number.  Empty matches all."""
    text = text.strip().casefold()
    if not text:
        return True
    return any(text in each.casefold() for each in (process.command, process.name, process.user, str(process.pid)))


def with_ancestors(found: Iterable[Process], picked: Iterable[Process]) -> tuple[list[Process], set[int]]:
    """*picked*, and every ancestor of one of them that is in *found*: what a
    filtered tree shows.  Also the pids of the ancestors added, which the
    filter did not pick."""
    by_pid = {process.pid: process for process in found}
    shown = {process.pid: process for process in picked}
    added: set[int] = set()
    for process in list(shown.values()):
        parent = by_pid.get(process.ppid)
        while parent is not None and parent.pid not in shown:
            shown[parent.pid] = parent
            added.add(parent.pid)
            parent = by_pid.get(parent.ppid) if parent.ppid != parent.pid else None
    return list(shown.values()), added


def tree(found: Iterable[Process], by: str = "pid", descending: bool = False,
         context: Iterable[int] = ()) -> list[Row]:
    """*found* as a tree, depth first: each process under its parent, the
    children of one parent in the order *by* gives.  One whose parent is not
    in *found* -- pid 1, the kernel's threads under 2 when 2 is filtered
    out, an orphan of a filter -- is a root.  A pid in *context* is a
    parent shown for a match's sake (:attr:`Row.context`)."""
    context = set(context)
    found = list(found)
    known = {process.pid for process in found}
    children: dict[int, list[Process]] = {}
    roots: list[Process] = []
    for process in found:
        if process.ppid in known and process.ppid != process.pid:
            children.setdefault(process.ppid, []).append(process)
        else:
            roots.append(process)
    rows: list[Row] = []
    seen: set[int] = set()

    def walk(level: list[Process], depth: int, rails: tuple[bool, ...]) -> None:
        level = ordered(level, by, descending)
        for index, process in enumerate(level):
            if process.pid in seen:
                continue
            seen.add(process.pid)
            last = index == len(level) - 1
            rows.append(Row(process, depth, rails, last, process.pid in context))
            below = children.get(process.pid)
            if below:
                walk(below, depth + 1, rails + (not last,) if depth else rails)

    walk(roots, 0, ())
    return rows


# -- details --------------------------------------------------------------------------


def boot_time(proc: Path = PROC) -> float | None:
    raw = _read_bytes(proc / "stat")
    if raw is None:
        return None
    for line in raw.decode("ascii", "replace").splitlines():
        if line.startswith("btime "):
            try:
                return float(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None


def details(pid: int, proc: Path = PROC) -> list[tuple[str, str]]:
    """What F3 shows of *pid*: ``(caption, value)`` pairs, the captions
    translated.  A value the user may not read is ``?``; a process gone
    raises ``ProcessLookupError``."""
    process = read(pid, proc)
    if process is None:
        raise ProcessLookupError(errno.ESRCH, tr("The process has ended"), str(pid))
    where = proc / str(pid)

    def link(name: str) -> str:
        try:
            return os.readlink(where / name)
        except OSError:
            return "?"

    def count(name: str) -> str:
        try:
            return str(len(os.listdir(where / name)))
        except OSError:
            return "?"

    environ = _read_bytes(where / "environ")
    variables = "?" if environ is None else str(sum(1 for each in environ.split(b"\0") if each))
    boot = boot_time(proc)
    started = "?"
    if boot is not None:
        started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(boot + process.started / CLOCK_TICKS))
    parent = read(process.ppid, proc) if process.ppid else None
    state = state_words(process.state)
    return [
        (tr("Process"), str(process.pid)),
        (tr("Name"), process.name),
        (tr("Command"), process.command),
        (tr("Program"), link("exe")),
        (tr("Directory"), link("cwd")),
        (tr("User"), f"{process.user} ({process.uid})"),
        (tr("State"), f"{process.state} ({state})" if state else process.state),
        (tr("Parent"), f"{process.ppid} {parent.name}" if parent is not None else str(process.ppid)),
        (tr("Started"), started),
        (tr("Threads"), str(process.threads)),
        (tr("Nice"), str(process.nice)),
        (tr("Resident"), f"{process.rss:,}"),
        (tr("Virtual"), f"{process.vsize:,}"),
        (tr("Open files"), count("fd")),
        (tr("Environment"), variables),
    ]


# -- signals ---------------------------------------------------------------------------

#: What the signal box offers, most wanted first.
SIGNALS: tuple[signal.Signals, ...] = tuple(
    getattr(signal, name) for name in
    ("SIGTERM", "SIGKILL", "SIGHUP", "SIGINT", "SIGQUIT", "SIGSTOP", "SIGCONT", "SIGUSR1", "SIGUSR2")
    if hasattr(signal, name)
)


def signal_caption(sig: signal.Signals) -> str:
    """``SIGTERM (Terminated)``: the name and what the C library calls it."""
    try:
        meaning = signal.strsignal(sig) or ""
    except (ValueError, AttributeError):
        meaning = ""
    return f"{sig.name} ({meaning})" if meaning else sig.name


def protected(pid: int) -> bool:
    """Whether *pid* is one :func:`send` refuses: init, and this process."""
    return pid <= 1 or pid == os.getpid()


def send(pid: int, sig: int) -> None:
    """*sig* to *pid*, as ``kill`` sends it; init and Navigator itself refused."""
    if protected(pid):
        raise PermissionError(1, tr("Navigator does not signal that process"), str(pid))
    os.kill(pid, sig)


def still(process: Process, proc: Path = PROC) -> None:
    """Raise ``ProcessLookupError`` unless *process* is still running: its
    number not given to another since it was read -- the start time says."""
    now = read(process.pid, proc)
    if now is None or now.started != process.started:
        raise ProcessLookupError(errno.ESRCH, tr("The process has ended"), str(process.pid))


def signal_process(process: Process, sig: int, proc: Path = PROC) -> None:
    """*sig* to *process*, as long as it is the very one that was read."""
    still(process, proc)
    send(process.pid, sig)
