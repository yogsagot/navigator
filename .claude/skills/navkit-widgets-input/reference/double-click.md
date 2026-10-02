## Double-click: a timer, not a meaning

**Written.** `DoubleClickEvent` in `navkit/events.py`, `ClickTracker` and `DOUBLE_CLICK_TIMEOUT` in
`navkit/application.py`, and a `getattr` at each of the two mouse dispatch points.

### Why it is navkit's, when `ClickEvent` is not

*What belongs in `navkit/events.py`* refuses `ClickEvent` because a click is something a widget *means*. A
double-click is not a meaning, it is a **temporal disambiguation of raw terminal input**, and the kit already does one
of those. A lone `ESC` byte is indistinguishable from the start of a sequence, so `InputParser` states the ambiguity,
`_schedule_escape_flush` arms a timer and `_flush_escape` manufactures a `KeyEvent("escape")` that was never on the
wire. SGR 1006 reports `press`, `release` and `move` and nothing else; two presses close together in one cell are a
fact neither press carries, and the same machine produces it.

The membership test that section states is **does navkit raise it**, and navkit raises this one — which is exactly
what `ClickEvent` fails, nothing in navkit emitting it, and what the deleted `MountEvent` failed for the same reason.
Excluding a double-click would mean adding a second, unstated test after the fact, to rule out the first case that
passes the first one.

What settles it is not taste, though. **`Application._loop.time()` is the only clock reachable from event handling** —
`Widget` has no timer of its own, and the one navkit later grew (*Timers: through the queue*) ticks at an interval
rather than measuring one between two inputs — so a widget library doing this itself would have to reach into the
private loop of the one object that owns it. That is the layering violation the boundary rule exists to prevent, so
the feature lands on navkit's side of the layer by the resource it needs rather than by argument.

**navkit raises the fact and never the meaning.** `DoubleClickEvent` asserts only that one button went down twice in
one cell inside the window. "Enter the directory" is `Panel.on_double_click`; "select the word" would be a text
widget's; `navml`'s `Button` gets nothing, because a double-click on a button is two clicks and that is already what
it receives. The same division as `KeyEvent`: navkit says F10 was pressed and never that F10 quits.

The honest concession: **what counts as "the same thing" under the pointer is arguably the widget's to say** — a row,
a cell, a word — and navkit has no way to ask. That is a *Still open* line below rather than a reason to refuse,
because the cell is the only answer navkit can give and it is the right default.

### The dispatch had to learn to read `event.handler`

*The handler name is read off the event class* promised that `DoubleClickEvent(MouseClickEvent)` reaches
`on_double_click` and not `on_mouse_click`. **It was not true when it was written.** `Widget.dispatch_mouse` ended in
`await self.on_mouse_click(local)`, and `Application._handle` matched `isinstance(event, MouseClickEvent)` and called
`self.on_mouse_click(event)` — so the one worked example in this file would have gone to the very handler it was the
example of not going to. Both now look the handler up the way `emit` already did:

```python
handler = getattr(self, event.handler, None)
return handler is not None and await _call(self, local, handler)
```

Four consequences, none of which needed anything else written:

- **A plain `MouseClickEvent` is unchanged.** `Widget.on_mouse_click` and `Application.on_mouse_click` are defined
  on the base classes, so the lookup always finds them and the call is the one that was always made. It *gains* the
  instance-handler async check `_call` carries, which *Every handler is `async def`* above already claimed both
  dispatch walks had and which only `emit` actually did.
- **A widget defining no `on_double_click` is skipped, and skipped already means unclaimed** — so the event falls
  outward to an overlapping sibling and then to an ancestor, exactly as an unhandled press does, and no widget needs a
  stub. The same property `emit` has for the same reason.
- **Modal routing cost nothing.** `translated()` rebuilds through `dataclasses.replace`, which keeps the subclass, so
  `_dispatch_mouse` reroutes a double-click into the modal's parent's frame and drops one landing outside it without
  knowing the class exists.
- **`isinstance(event, MouseClickEvent)` is true of it** — relied on in `_handle`'s branch chain, and a trap
  anywhere that meant only a plain mouse action. That is the price of the subclass and it is the right price: a
  standalone class would have needed a duplicate of every field, a duplicate `translated()`, and a second
  positional-routing path.

Refused: **a `clicks: int = 1` field on `MouseClickEvent`**. It is the cheapest option mechanically, needing no
routing change at all, and it is the case *The handler name is read off the event class* already refuses — "a
refinement that arrived at the handler for the thing it refines would be indistinguishable from it, and the widget
that wanted only the plain event could not say so". A field is opt-*out*: every `on_mouse_click` acting on a press
would act twice, silently, until its author noticed a field they had never heard of.

### Additive, and inline

**The second press is still delivered.** Suppressing it needs no deferral — the count is known *at* press two — so it
is the serious alternative, and it loses because it takes input away from code that never asked for the feature:
`Navigator.on_mouse_click` would stop moving the cursor onto the row it was clicked on, and a double-clicked `Button`
would fire one `ClickEvent` instead of two. A facility is not added to a kit by changing the contract of the stream
every existing widget is written against.

**Deferring the press until a timer expires is refused harder.** `ESCAPE_TIMEOUT` can spend 50ms because a lone `ESC`
is genuinely undecidable until then — there is no correct thing to do with it meanwhile. A press is a press whatever
follows it, and deferring would tax every single click in the application with 400ms of latency to serve the one in a
hundred that turns out to be a double.

The cost of additive, named: **a widget acting on both a press and a double-click acts twice.** That is the widget's
to arbitrate, and it is the right way round — "move the cursor to this row" on the press *composes with* "enter it" on
the double-click, which is exactly why `Panel.on_double_click` is three lines and not a rewrite.

**Dispatched inline**, immediately after the press, not through `post_event`. *Why synchronous, and not through the
queue* argues every clause of this already: the batching that matters happens at the frame and not at the queue, so
queueing buys no coalescing, and cause and effect stay adjacent. Concretely the press's own `release` is usually
already in the queue from the same read burst, so queueing would deliver press, release, double-click; inline delivers
press, double-click, release, which is what Qt and GTK both do. `_flush_escape` is not a counter-precedent — it runs
from a timer callback, *outside* any dispatch, where the queue is the only door in.

It re-enters `_handle` rather than being pushed straight at the tree, so `on_event` sees it, as it sees the escape key
navkit manufactures. The cost is that an `on_event` swallowing the press swallows the double-click too, which is
`on_event` being the outermost door and not a special case.

**The count is taken from the press before it is delivered, and regardless of who consumes it.** Whether a widget
claimed a press says nothing about whether the user clicked twice — and `Navigator.on_mouse_click` returns True for
every press inside a panel, so the other choice would have made the feature unreachable in the only application here.
A `DoubleClickEvent` is never counted as a press, which is what bounds the recursion at one level.

### What the detector keys on

`ClickTracker.press(event, now)` returns how many clicks the press completes, and only a count of exactly **2** raises
anything.

- **The run counts upward and never restarts inside itself.** A triple click is 1, 2, 3 and a fourth press is 4, so
  one double-click is raised and no more. Resetting to 1 after each pair would have entered the same directory twice
  on a fast triple click.
- **The exact cell, with no tolerance**, and the asymmetry is the argument: exact fails by *missing* a double-click,
  which the user repeats at the cost of a second; a one-cell tolerance fails by *inventing* one on the item next door,
  which opens something nobody asked to open. A missed double-click is an annoyance, an unasked-for one is
  destructive. navkit also cannot see the pointer wander between the presses — `MOUSE_ON` asks for 1000/1002/1006, and
  1002 reports motion only while a button is held, so the press coordinates are the only positional evidence there is.
- **Button identity is part of the key**, and all three buttons count; a handler filters by button the way one reading
  a plain press already does.
- **A wheel detent is not a click.** It arrives as `action="press"`, and two notches in one cell inside the window is
  the *normal* way to use a wheel. It also ends the run, which is the general rule the other resets follow: **the run
  is forgotten whenever navkit knows the cell no longer denotes the same thing** — a wheel scrolled the content, a
  resize moved the layout, a modal pushed or popped put something else under the pointer. That last one closes a real
  hole: press one on the desktop opens a dialog under the pointer, and press two at the same screen cell would
  otherwise arrive at the dialog as a double-click it never earned.

### The timeout is a constructor argument, and `ESCAPE_TIMEOUT` is not

`DOUBLE_CLICK_TIMEOUT = 0.4`, what GTK and Qt both default to, and `Application(double_click=...)` overrides it; `0`
disables the feature. The inconsistency is deliberate: the escape window is calibrated against a terminal's
transmission, which is nobody's preference, and the double-click window against a user's hand, which is the
application's to state. `Terminal(mouse=…)` against `info.mouse` is the same shape — the caller's wish and the
device's ability, either vetoing.

It also buys the test, and that earns it a place independently. **`ClickTracker` is clockless by construction** —
`press()` is *told* `now` rather than reading one — so the whole rule, triple clicks included, is tested in a plain
function with no loop, no application and no fake clock, which `tests/conftest.py` has no way to provide and should
not grow for one feature. The integration tests then work the real clock from both ends: `run_app` leaves 0.02s
between actions, twenty times inside the default window, and a test needing a pair to be *too slow* shrinks the window
to 0.001 instead of sleeping 0.4s of real time.

