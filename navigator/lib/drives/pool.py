"""A small pool of connections or channels a drive's threads share.

SFTP's channels (``sftp.Connection``) and FTP's control connections
(``ftp.FtpDrive``'s) are few, each used by one thread at a time.  A thread
that finds them all in use waits for one.

**Not a** :class:`queue.Queue`: a waiter there is woken only by an item put
back, and three other things have to wake it too -- a slot freed by an item
thrown away (a broken connection), a new generation (the drive connected
again, its old items useless) and the end (the drive closed).  A queue left
the waiter asleep through every one of those, and its operation's progress
box up for good.  And as a backstop, :meth:`Pool.take` waits a second at a
time and answers None, so the caller looks again at its own state -- the
connection's life, a stop -- before it waits on.

Blocking: only ever on a drive's worker threads.
"""

from __future__ import annotations

import threading
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class PoolClosed(Exception):
    """The pool was closed: its drive is gone."""


class Pool(Generic[T]):
    """At most *limit* items made, each taken by one thread at a time."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._ready = threading.Condition()
        self._free: list[T] = []
        self._made = 0
        self._generation = 0
        #: ``id(item)`` -> the generation it was made in.
        self._born: dict[int, int] = {}
        self._closed = False

    @property
    def made(self) -> int:
        with self._ready:
            return self._made

    def take(self, make: Callable[[], T], *, wait: float = 1.0) -> T | None:
        """A free item; else a new one from *make()*, while fewer than
        :attr:`limit` are made; else None once *wait* seconds passed with
        neither -- the caller looks at its own state and asks again.
        :class:`PoolClosed` once :meth:`close` was called.  *make* runs
        outside the lock; what it raises is the caller's, its slot given back."""
        with self._ready:
            while True:
                if self._closed:
                    raise PoolClosed()
                if self._free:
                    return self._free.pop()
                if self._made < self.limit:
                    self._made += 1
                    generation = self._generation
                    break
                if not self._ready.wait(wait):
                    return None
        try:
            item = make()
        except BaseException:
            with self._ready:
                if generation == self._generation:
                    self._made -= 1
                self._ready.notify()
            raise
        with self._ready:
            self._born[id(item)] = generation
        return item

    def give(self, item: T, *, discard: bool = False) -> None:
        """*item* back for the next thread -- or, *discard*, thrown away (the
        caller closes it), freeing its slot if it is of this generation.  An
        item of an earlier generation is always thrown away."""
        with self._ready:
            born = self._born.pop(id(item), self._generation)
            current = born == self._generation
            if discard or not current or self._closed:
                if current:
                    self._made -= 1
            else:
                self._born[id(item)] = born
                self._free.append(item)
            self._ready.notify()

    def reset(self) -> list[T]:
        """A new generation -- the drive connected again: nothing made yet,
        and the free items handed back for the caller to close.  Every waiter
        is woken to make one anew."""
        with self._ready:
            free, self._free = self._free, []
            for item in free:
                self._born.pop(id(item), None)
            self._made = 0
            self._generation += 1
            self._ready.notify_all()
        return free

    def close(self) -> list[T]:
        """Closed for good: every waiter woken with :class:`PoolClosed`, and
        the free items handed back for the caller to close."""
        with self._ready:
            self._closed = True
            free, self._free = self._free, []
            for item in free:
                self._born.pop(id(item), None)
            self._ready.notify_all()
        return free

    def adopt(self, item: T) -> T:
        """*item*, made by the caller, counted as one of this generation's and
        taken -- the one made at once in place of one thrown away, or the
        first, made while connecting."""
        with self._ready:
            self._made += 1
            self._born[id(item)] = self._generation
        return item


__all__ = ["Pool", "PoolClosed"]
