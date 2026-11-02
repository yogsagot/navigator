"""Operations sent to the background: what the menu bar's mark reads.

A departure: DOS Navigator's ``TWhileView`` loops held the screen until a
copy or an erase ended.  Here the progress box's *Background* button takes
the box down and lets the work go on (``Manager._watch_job``), and the
operation is registered here for as long as it is away -- the menu bar's
mark (``navigator.widgets.shell.job_mark``) shows how far they all are, and a
click on it, or Window > *Background operation*, brings one back.

**The loop's alone.**  The worker thread never touches this; ``_watch_job``
copies the job's counts in at every tick, as it does into a box.  Reactive,
and each field replaced, never mutated, so the mark repaints when one
changes -- through :attr:`Background.listener`, the application's
``invalidate``, since these are not a widget's attributes.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from navkit.reactive import reactive


class Running:
    """One operation in the background, as its watcher keeps it up to date."""

    #: What it is, as its box was titled: *Copy*, *Rename/move*, *Erase*.
    title: str = reactive("")
    #: How far: bytes for a copy, entries for an erase.
    done: int = reactive(0)
    total: int = reactive(0)
    #: The worker has a question and waits for the box to come back.
    asking: bool = reactive(False)

    def __init__(self, job: Any, title: str, owner: Background | None = None) -> None:
        self._owner = owner
        #: The worker's :class:`~navigator.lib.system.job.Job`, for quitting to stop.
        self.job = job
        self.title = title
        #: Set when the user asks for the box back; its watcher waits on it.
        self.recalled = asyncio.Event()

    def _reactive_changed(self, name: str) -> None:
        if self._owner is not None:
            self._owner._reactive_changed(name)

    @property
    def percent(self) -> int:
        """Whole percent, rounded down as ``ProgressBar.percent`` is."""
        return percent(self.done, self.total)


def percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, done * 100 // total))


class Background:
    """Every operation in the background, oldest first."""

    jobs: tuple[Running, ...] = reactive(())

    def __init__(self) -> None:
        #: Called on every change: the application's ``invalidate``.
        self.listener: Callable[[], None] | None = None

    def _reactive_changed(self, name: str) -> None:
        if self.listener is not None:
            self.listener()

    def add(self, job: Any, title: str) -> Running:
        entry = Running(job, title, self)
        self.jobs = (*self.jobs, entry)
        return entry

    def remove(self, entry: Running) -> None:
        if entry in self.jobs:
            self.jobs = tuple(other for other in self.jobs if other is not entry)

    @property
    def asking(self) -> bool:
        return any(entry.asking for entry in self.jobs)

    def percent(self) -> int:
        """How far they all are together.  Bytes and entries do not add up,
        so each counts by its own fraction, weighted alike."""
        if not self.jobs:
            return 0
        return sum(entry.percent for entry in self.jobs) // len(self.jobs)

    def recall(self, entry: Running | None = None) -> bool:
        """Bring *entry*'s box back -- by default one with a question, else
        the newest.  Whether there was one to bring back."""
        if entry is None:
            waiting = [other for other in self.jobs if other.asking]
            entry = waiting[0] if waiting else self.jobs[-1] if self.jobs else None
        if entry is None:
            return False
        entry.recalled.set()
        return True

    def stop_all(self) -> None:
        """Every worker told to stop: quitting."""
        for entry in self.jobs:
            entry.job.stop()


#: The one registry, shared by every file manager window.
BACKGROUND = Background()
