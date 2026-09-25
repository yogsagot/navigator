"""An invisible widget that emits :class:`TimerEvent` every :attr:`Timer.interval`.

The library's first component with nothing to show.  It paints nothing and
places nothing, so it is Python alone: a markup half would say only what the
``class`` statement says -- the rule that took ``CheckBoxes``' document away.
What a document does with one is put it in a tree and handle what it raises::

    Timer:
        interval: 1000
        on_timer: root.blink = not root.blink

**The clock is navkit's**, :meth:`~navkit.application.Application.call_every`,
because the event loop is the only one event handling can reach.  A tick is
delivered through the event queue, so a handler runs inside a batch like any
other and whatever it changes is painted in the frame after it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit.events import Event
from navkit.reactive import effect, reactive, untracked
from navkit.widget import Widget


@dataclass(frozen=True, slots=True)
class TimerEvent(Event):
    """One interval elapsed.  Reaches ``on_timer``, and carries nothing."""


class Timer(Widget):
    """Emits a :class:`TimerEvent` every :attr:`interval` milliseconds.

    **Only while mounted.**  The count starts when the timer joins a live tree
    -- or, for a tree mounted before the application runs, when it does -- and
    stops when it leaves one; putting it back starts a fresh count.
    """

    emits = (TimerEvent,)

    #: Milliseconds between events.  Zero or less stops the timer; changing it
    #: starts the count again from the change.
    interval: int = reactive(1000)

    def __init__(self, **kwargs: Any) -> None:
        #: The running :class:`~navkit.application.Repeat`, or None.  Set
        #: before the base constructor, which joins the parent and so may call
        #: :meth:`mounted` from inside itself.
        self._repeat: Any = None
        super().__init__(**kwargs)

    def mounted(self) -> None:
        super().mounted()
        # An effect, and declared here rather than in ``__init__``, so that a
        # change of interval re-arms and ``remove()`` disposes it.
        effect(self, Timer._arm)

    def unmounting(self) -> None:
        self._stop()
        super().unmounting()

    def _arm(self) -> None:
        interval = self.interval
        self._stop()
        with untracked():
            app = self.application
        if interval > 0 and app is not None:
            self._repeat = app.call_every(interval / 1000, self._tick)

    def _stop(self) -> None:
        if self._repeat is not None:
            self._repeat.cancel()
            self._repeat = None

    async def _tick(self) -> None:
        # Not ``on_*``: navkit does not find this under ``event.handler``, it
        # is the callback the application was handed.
        await self.emit(TimerEvent())
