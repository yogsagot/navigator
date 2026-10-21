"""Work on a thread, with a box that appears if it takes a while.

The loop is the only thing that paints and reads keys, so anything that may
take longer than a frame -- reading a file, writing one, searching it -- runs
on a thread, and the loop watches.  DN's loops looked at the keyboard between
blocks and put up a box once a timer ran out (``TWhileView``, ``WriteMsg``);
:func:`run_with_progress` is that, for a worker that shares only plain fields
and a stop flag with the loop -- a :class:`navigator.lib.system.job.Job`, or anything
with ``stop()`` and ``stopped``.

``Manager._watch_job`` is the larger version, for jobs that also ask the user
questions on the way and pause behind *Abort operation?*.
"""

from __future__ import annotations

import asyncio
from collections import deque
from typing import Any, Callable, TypeVar

T = TypeVar("T")

#: How long work runs before it shows its progress: DN's two timer ticks
#: (``NewTimer(Tmr, 2)``) at 18.2 Hz.
PROGRESS_DELAY = 2 / 18.2

#: How often a box is brought up to date.
PROGRESS_TICK = 0.1

#: How long reading or writing a file goes before *Reading file* comes up.  A
#: departure: DN's ``WriteMsg`` was up before the first byte was read, which
#: on a floppy took long enough to read it; a box that flashes for every small
#: file read from a page cache is only noise.
SLOW_PROGRESS_DELAY = 1.0

#: How far back :class:`Rate` looks: long enough to smooth one slow file out,
#: short enough to follow a copy that moves from a disk to a network.
RATE_WINDOW = 5.0


class Rate:
    """How fast a count grows, over the last :data:`RATE_WINDOW` seconds.

    A departure: DN's progress boxes showed bytes and a gauge, never a
    speed.  :meth:`add` takes the count at a moment (``loop.time()``);
    the speed is the growth between the oldest sample in the window and
    the newest, so time spent behind a question drops out once it is
    older than the window.
    """

    def __init__(self, window: float = RATE_WINDOW) -> None:
        self.window = window
        self.samples: deque[tuple[float, int]] = deque()

    def add(self, now: float, done: int) -> None:
        self.samples.append((now, done))
        while len(self.samples) > 2 and now - self.samples[0][0] > self.window:
            self.samples.popleft()

    def speed(self) -> float | None:
        """Units a second, or None before there is anything to go by."""
        if len(self.samples) < 2:
            return None
        (began, first), (now, last) = self.samples[0], self.samples[-1]
        if now - began < PROGRESS_TICK / 2:
            return None
        return max(0, last - first) / (now - began)

    def left(self, total: int) -> float | None:
        """Seconds until the count reaches *total* at :meth:`speed`; None if it is not moving."""
        speed = self.speed()
        if not speed or not self.samples:
            return None
        return max(0, total - self.samples[-1][1]) / speed


def duration_text(seconds: float) -> str:
    """``0:42``, ``12:05``, ``1:02:03``: *seconds* rounded up, as a clock shows them."""
    whole = int(-(-seconds // 1))
    hours, rest = divmod(whole, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02}:{secs:02}" if hours else f"{minutes}:{secs:02}"


async def run_with_progress(
    app: Any,
    func: Callable[[], T],
    job: Any,
    make_box: Callable[[], Any],
    refresh: Callable[[Any], None] | None = None,
    *,
    delay: float = PROGRESS_DELAY,
    tick: float = PROGRESS_TICK,
) -> T:
    """Run *func* on a thread; if it is still going after *delay*, show a box.

    *make_box* builds the box, a dialog whose any answer means *stop*: the
    job is stopped and the worker's own way of ending -- ``Stopped`` raised,
    or an early return -- is what this returns or raises.  *refresh* copies
    the job's fields into the box, once when it opens and every *tick*.

    **The job is stopped whenever this ends with the work unfinished**: a
    cancelled task -- its window closed, Navigator quitting -- would otherwise
    leave a thread reading to the end of a file that nobody is waiting for,
    and ``asyncio.run`` waits for that thread before it returns.
    """
    work = asyncio.ensure_future(asyncio.to_thread(func))
    repeat = None
    shown: asyncio.Future[Any] | None = None
    try:
        done, _ = await asyncio.wait({work}, timeout=delay)
        if not done and app is not None:
            box = make_box()
            if refresh is not None:
                refresh(box)

                async def update() -> None:
                    refresh(box)

                repeat = app.call_every(tick, update)
            shown = asyncio.ensure_future(box.execute(app))
            await asyncio.wait({work, shown}, return_when=asyncio.FIRST_COMPLETED)
            if not work.done():
                job.stop()
        return await work
    finally:
        if repeat is not None:
            repeat.cancel()
        if shown is not None and not shown.done():
            # Cancelled, not closed: a box whose ``execute`` has not run yet
            # has nothing to close, and would open after the work was over.
            shown.cancel()
            await asyncio.wait({shown})
        if not work.done():
            job.stop()
