"""Work on a thread, with a box that appears if it takes a while.

The loop is the only thing that paints and reads keys, so anything that may
take longer than a frame -- reading a file, writing one, searching it -- runs
on a thread, and the loop watches.  DN's loops looked at the keyboard between
blocks and put up a box once a timer ran out (``TWhileView``, ``WriteMsg``);
:func:`run_with_progress` is that, for a worker that shares only plain fields
and a stop flag with the loop -- a :class:`navigator.job.Job`, or anything
with ``stop()`` and ``stopped``.

``Manager._watch_job`` is the larger version, for jobs that also ask the user
questions on the way and pause behind *Abort operation?*.
"""

from __future__ import annotations

import asyncio
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
