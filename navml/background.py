"""Small reads off the loop: a thread does the I/O, the loop takes the answer.

For what a widget needs to know to paint -- whether a tree node has children,
how many files a directory holds, what a file says -- and that a dead network
mount can take for ever to answer.  The widget asks, paints what it already
knows, and is painted again once the answer is in.  :class:`Background` is
one pool of threads; a widget that may wait on many slow things at once keeps
its own, so that they cannot use up another's.

**With no application running**, as in a test driving a widget by hand, the
work is done on the spot and answered at once: there is no loop to hand an
answer back to, and nobody to keep painting meanwhile.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any, Callable

from navkit.events import WakeEvent


class Outcome:
    """What the work returned, or the exception it raised."""

    __slots__ = ("value", "error")

    def __init__(self, value: Any = None, error: BaseException | None = None) -> None:
        self.value = value
        self.error = error

    def result(self) -> Any:
        if self.error is not None:
            raise self.error
        return self.value


def _run(func: Callable[..., Any], args: tuple[Any, ...]) -> Outcome:
    try:
        return Outcome(func(*args))
    except Exception as error:  # handed to whoever asked, on the loop
        return Outcome(error=error)


class Background:
    """A pool of threads for one kind of slow read."""

    def __init__(self, name: str, workers: int = 2) -> None:
        self._pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix=name)

    def run(self, widget: Any, func: Callable[..., Any], *args: Any,
            done: Callable[[Outcome], None]) -> None:
        """``func(*args)`` on a thread, then ``done(outcome)`` on the loop.

        The application is woken once *done* has run, so whatever it changed
        is painted.  Called from the loop's thread -- a handler, an effect, a
        ``render`` -- never from another.
        """
        app = widget.application
        if app is None or not app.is_running:
            done(_run(func, args))
            return
        loop = asyncio.get_running_loop()

        def finish(future: concurrent.futures.Future[Outcome]) -> None:
            outcome = future.result()

            def answer() -> None:
                done(outcome)
                if app.is_running:
                    app.post_event(WakeEvent())

            try:
                loop.call_soon_threadsafe(answer)
            except RuntimeError:
                pass  # the loop is gone: Navigator has quit meanwhile

        self._pool.submit(_run, func, args).add_done_callback(finish)
