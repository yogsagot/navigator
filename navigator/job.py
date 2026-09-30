"""What a worker thread and the loop watching it share: DN's ``TWhileView`` contract.

A file operation runs on a thread so the screen keeps painting, and a
:class:`Job` is the only thing that thread and the loop share -- plain fields
the worker writes and the loop reads, a ``threading.Event`` for *Stop*, a
second one that holds the worker while *Abort operation?* is up, and one
question at a time handed across as a ``concurrent.futures.Future``.  Nothing
reactive crosses, which is the loop's alone.

Copying (:class:`navigator.filecopy.CopyJob`) and erasing
(:class:`navigator.fileerase.EraseJob`) add their own progress fields to it.
"""

from __future__ import annotations

import concurrent.futures
import threading
from typing import Any, Callable

#: How long the worker waits on an unanswered question before looking at
#: ``stopped`` again -- so a Navigator that quits with a question up does not
#: leave a thread waiting for an answer that will never come.
POLL = 0.1


class Stopped(Exception):
    """The user stopped the operation, by *Stop* or by answering Cancel."""


class Job:
    """A running operation, as the thread doing it and the loop watching it see it."""

    def __init__(self, asker: Callable[[Any], Any] | None = None) -> None:
        self._stop = threading.Event()
        #: Clear while the work is held -- *Abort operation?* is up, and DN's
        #: loops were the ones asking it, so nothing was done meanwhile.
        self._going = threading.Event()
        self._going.set()
        self._lock = threading.Lock()
        self._pending: tuple[Any, concurrent.futures.Future[Any]] | None = None
        #: Answers questions in the worker's own thread, if given: for tests,
        #: and for anything that has no loop to hand the question to.
        self._asker = asker

    def stop(self) -> None:
        self._stop.set()
        self._going.set()

    def pause(self) -> None:
        self._going.clear()

    def resume(self) -> None:
        self._going.set()

    def wait_while_paused(self) -> None:
        """Hold the worker while the job is paused (worker side)."""
        self._going.wait()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    def ask(self, question: Any) -> Any:
        """Put *question* to the user and wait for the answer (worker side).

        Raises :class:`Stopped` if the job is stopped while it waits.
        """
        if self._asker is not None:
            return self._asker(question)
        future: concurrent.futures.Future[Any] = concurrent.futures.Future()
        with self._lock:
            self._pending = (question, future)
        while True:
            try:
                return future.result(timeout=POLL)
            except concurrent.futures.TimeoutError:
                if self.stopped:
                    with self._lock:
                        self._pending = None
                    raise Stopped from None

    def take_question(self) -> tuple[Any, concurrent.futures.Future[Any]] | None:
        """The question waiting for an answer, handed over once (loop side)."""
        with self._lock:
            pending, self._pending = self._pending, None
        return pending
