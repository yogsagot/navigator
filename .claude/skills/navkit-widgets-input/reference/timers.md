## Timers: through the queue

**Written.** `Application.call_every(seconds, callback)` and the `Repeat` handle it returns, in
`navkit/application.py`; `navml`'s `Timer` is the one caller.

**navkit's by the resource it needs**, the argument *Double-click* made: the loop is the only clock event handling can
reach, so a widget library ticking by itself would reach into `Application._loop`. What navkit offers is the bare
fact — *this much time passed* — and the event that means something (`TimerEvent`) is the library's.

**A tick is posted, never run from the loop's timer callback.** `Repeat._fire` puts a private `_Tick` on the event
queue and `_handle` awaits the callback from there, inside the dispatch. So a tick is a handler in every way that
matters: whatever it changes is flushed and painted as one frame with the rest of its batch, and an exception it raises
stops the application as a handler's does. A spawned task that slept and emitted would have worked by accident — its
writes would invalidate and wake the loop — but ran outside every batch, with its failure reported by the task
machinery rather than the loop. `_flush_escape` is the precedent: a timer callback is *outside any dispatch, where the
queue is the only door in*. `_Tick` is not offered to `on_event`, because it is not input.

Three details, each for a reason:

- **It may be called before the loop exists.** A tree is mounted from `Application.__init__`, so a `Timer` in the
  tree asks for its clock long before `run_async`. A handle registered early waits in `_repeats` and is armed when the
  loop starts; stopping the application cancels every one.
- **Scheduled against the start, not against the last tick** (`loop.call_at(start + n·period)`), so a slow batch does
  not push every later tick back. A loop stalled for more than a period **skips** the slots it missed rather than
  queueing a burst — a blinking colon has nothing to catch up on.
- **A cancelled handle's queued tick is dropped at dispatch.** The tick may already be in the queue when its owner
  lets go — a timer removed in the same batch — and cancelling the loop's timer cannot reach that.

