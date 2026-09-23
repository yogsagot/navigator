"""Work that outlives the handler that started it."""

from __future__ import annotations

import asyncio

import pytest

from conftest import FakeTerminal, run_app
from navkit.application import Application
from navkit.events import KeyEvent
from navkit.screen import Surface
from navkit.widget import Widget


class Painter(Widget):
    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, ".", self.style)


def test_a_handler_that_awaits_input_never_paints():
    """The measurement the whole dialog API rests on, pinned as a fact.

    `_main_loop' awaits `_handle' and only then renders, so a handler that
    waits for a later keystroke is holding the one consumer of the queue: the
    keystroke is read and never dispatched, and no frame is produced.  This is
    why `spawn' exists, and the test is here so that a future change to the
    loop tells us the constraint has moved.
    """
    term = FakeTerminal(width=10, height=3)
    root = Painter()
    app = Application(root, terminal=term)
    waited = asyncio.Event()

    async def on_key(event):
        waited.set()
        await asyncio.sleep(0.05)   # any await at all is enough
        return True

    root.on_key = on_key

    async def main():
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.02)
        before = len(term.frames)
        app.post_event(KeyEvent(key="a"))
        await waited.wait()
        # The handler is parked.  Nothing may have painted since.
        assert len(term.frames) == before
        await asyncio.sleep(0.1)
        app.exit()
        await task

    asyncio.run(asyncio.wait_for(main(), 5))


def test_spawn_lets_the_frame_paint_before_the_work_finishes():
    term = FakeTerminal(width=10, height=3)
    root = Painter()
    app = Application(root, terminal=term)
    done = asyncio.Event()
    started = asyncio.Event()

    async def slowly():
        started.set()
        await done.wait()
        return "answer"

    async def main():
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.02)
        job = app.spawn(slowly())
        await started.wait()
        root.merge_style("bg: red")      # ask for a repaint
        await asyncio.sleep(0.05)
        assert len(term.frames) >= 2, "the loop kept painting while work waited"
        done.set()
        assert await job == "answer"
        app.exit()
        await task

    asyncio.run(asyncio.wait_for(main(), 5))


def test_a_spawned_task_is_held_and_forgotten_again():
    """An unreferenced task can be collected mid-flight, taking its error."""
    term = FakeTerminal(width=10, height=3)
    app = Application(Painter(), terminal=term)
    release = asyncio.Event()

    async def work():
        await release.wait()

    async def main():
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.02)
        job = app.spawn(work())
        assert job in app._tasks
        release.set()
        await job
        await asyncio.sleep(0)
        assert job not in app._tasks
        app.exit()
        await task

    asyncio.run(asyncio.wait_for(main(), 5))


def test_exiting_cancels_whatever_is_still_waiting():
    """A dialog left open at exit tears itself down instead of leaking."""
    term = FakeTerminal(width=10, height=3)
    app = Application(Painter(), terminal=term)
    cleaned = []

    async def work():
        try:
            await asyncio.Event().wait()     # never resolves
        except asyncio.CancelledError:
            cleaned.append("finally ran")
            raise

    async def main():
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.02)
        job = app.spawn(work())
        await asyncio.sleep(0.02)
        app.exit()
        await task
        assert cleaned == ["finally ran"]
        assert job.cancelled()
        assert not app._tasks

    asyncio.run(asyncio.wait_for(main(), 5))


def test_spawn_needs_a_running_application():
    app = Application(Painter(), terminal=FakeTerminal())
    work = asyncio.sleep(0)
    try:
        with pytest.raises(RuntimeError, match="not running"):
            app.spawn(work)
    finally:
        work.close()

    detached, work = Painter(), asyncio.sleep(0)
    try:
        with pytest.raises(RuntimeError, match="not in a running application"):
            detached.spawn(work)
    finally:
        work.close()


def test_a_widget_spawns_through_its_application():
    term = FakeTerminal(width=10, height=3)
    root = Painter()
    app = Application(root, terminal=term)
    ran = []

    async def work():
        ran.append(True)

    async def main():
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.02)
        await root.spawn(work())
        assert ran == [True]
        app.exit()
        await task

    asyncio.run(asyncio.wait_for(main(), 5))
