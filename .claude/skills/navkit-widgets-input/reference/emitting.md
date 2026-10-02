## Emitting: a widget event walks up

**Written**, and decided ahead of the code because `navml/DESIGN.md` had written its handler rules against it —
*A handler body is one line* and *The handler's one argument is `event`* — and *What the widget library needs first*
below said the two halves had to be settled together. This is navkit's half: `Event.handler` and `emitted()` in
`navkit/events.py`, `Widget.emit()` and `emits` in `navkit/widget.py`, and one fallback branch in
`Application._handle`.

The verb was `announce` for one commit and is now `emit`, renamed throughout on the author's preference. Nothing about
the mechanism moved with the name.

`Widget.emit(event)` offers the event to the widget itself, then to each of its ancestors in turn, then to the
application, and stops at the first handler that returns `True`:

```python
async def emit(self, event: Event) -> bool:
    """Offer *event* to this widget, then to its ancestors, then to the application."""
    widget: Widget | None = self
    while widget is not None:
        handler = getattr(widget, event.handler, None)
        if handler is not None and await _call(widget, event, handler):
            return True
        widget = widget.parent
    app = self.application
    if app is not None:
        handler = getattr(app, event.handler, None)
        if handler is not None and await _call(app, event, handler):
            return True
    return False
```

That is the whole mechanism, `_call` being the one line that holds an instance-assigned handler to the async rule
below. **A handler is an `async def on_*`, or an instance attribute of the same name, taking one argument and
returning a bool** — which is what `Widget.on_key` and `Application.on_mouse_click` already are, so a signal
introduces no second convention for handlers, no second one for consumption, and no new kind of object. A widget
emits something by declaring an `Event` subclass and calling the one method.

### The handler name is read off the event class, not invented

`Event` gains a `handler` class attribute, derived from the class name at class creation: strip a trailing `Event`,
snake-case what is left, prefix `on_`. **The rule was not chosen, it was measured** — every event that existed when
it was written down already obeyed it, the one that is never dispatched included:

| event              | derived          | today                                                    |
|--------------------|------------------|----------------------------------------------------------|
| `KeyEvent`         | `on_key`         | `Widget.on_key`, `Application.on_key`                    |
| `MouseClickEvent`  | `on_mouse_click` | `Widget.on_mouse_click`, `Application.on_mouse_click`    |
| `DoubleClickEvent` | `on_double_click`| a widget's, when it wants one                            |
| `ResizeEvent`      | `on_resize`      | `Application.on_resize`                                  |
| `PasteEvent`       | `on_paste`       | `Application.on_paste`                                   |
| `WakeEvent`        | `on_wake`        | never dispatched                                         |

The second row is the one honest exception to "measured": it was `MouseEvent` reaching `on_mouse` when the rule was
written, and the class was **renamed to `MouseClickEvent` so that `on_mouse_click` would derive** rather than being
pinned with an explicit `handler`. That is the trade the rule asks for and the right way round — an override would
have put the first hole in a table whose whole value is that a reader can predict the handler from the class. What it
costs is that the class name is narrower than the class: a `MouseClickEvent` still carries `action="move"` for a drag
and `button="wheel_up"` for the wheel, so **the name says click and the type says every mouse action**. The docstring
says so too, since the name no longer can.

so `ClickEvent` reaches `on_click` and `SelectionChanged` reaches `on_selection_changed` without anything being
registered anywhere. A class may set `handler` explicitly and is then left alone. **A subclass derives its own name
rather than inheriting one**: `DoubleClickEvent(MouseClickEvent)` reaches `on_double_click` and not `on_mouse_click`,
because a refinement that arrived at the handler for the thing it refines would be indistinguishable from it, and the
widget that wanted only the plain event could not say so.

One measured trap, because it costs an hour to find and a line to avoid: **`@dataclass(slots=True)` replaces the class
it decorates**, so the `__class__` cell a zero-argument `super()` closes over inside `__init_subclass__` names the
*pre-slots* class, and every subclass then fails to be created with
`TypeError: super(type, obj): obj must be an instance or subtype of type`. Spelling it `super(Event, cls)` resolves the
global at call time and works. Every event in `navkit/events.py` is `frozen=True, slots=True`, so this is not a corner
case, it is the first line written.

### Every handler is `async def`, and a synchronous one raises

`Widget.on_key`, `Widget.on_mouse_click`, `Widget.emit`, both dispatchers, every `Application` hook, and every `on_*` a
widget library or an application declares. `_main_loop` awaits `_handle`; the emit walk awaits each handler in turn,
which is what keeps consumption meaning what it meant.

**The reason is not symmetry with the reactive layer**, and it is worth writing down because it reads as though it
should be: `navkit/reactive.py` contains no `async` and no `await` at all. Observable attributes are *deferred* — a
write marks dependents stale, values recompute lazily on read, effects queue to a scheduler flushed once per frame —
and deferred is a different property from asynchronous. The reason is the plain one: a handler that wants to read a
file, start a process or talk to a socket should be able to, and a synchronous handler can only block the loop while
it does.

**A hook that cannot be awaited where it is called does not get an `on_*` name.** That is the whole of the rule's
boundary, and it is what `Widget.mounted()` and `Widget.unmounting()` are called that instead — see *Why the hook is
not an event, and not called `on_*`* above. `Application.on_start` and `on_stop` take no event either and keep their
names, because `run_async` can await them.

**Enforced in two places, because neither can see what the other does.**

- `Widget.__init_subclass__` and `Application.__init_subclass__` call `check_handlers(cls)`, which refuses a class
  whose own body defines a synchronous `on_*`. It fires at import, naming the class and the method — a traceback at
  class creation otherwise points at the `class` statement and nothing else.
- The emit and dispatch walks check a handler found on the **instance** before calling it. That is what markup
  compiles to and what no class-creation check can see. Without it the failure is
  `TypeError: object bool can't be used in 'await' expression`, which names neither the widget nor the handler.

**What the frame model gives up is less than it looks.** A handler that awaits lets the loop run mid-batch — reading
input, pty output, timers, signals — so a batch is no longer an uninterrupted stretch of Python. But **it cannot cause
a repaint**: `_render` has exactly two call sites, both inside `_main_loop`, so nothing paints until the batch has
drained. One frame per batch survives untouched, and `tests/test_application.py` pins it with a handler that yields.
The real cost is bigger than "the frame waits for it", and the omission was paid for. **The batch waits too.**
`Application._events` has exactly one consumer — the `while` loop in `_main_loop` — so a handler that awaits is
holding it: input is read and queued by the reader callback and *nothing dispatches it*. For a handler awaiting
something that will resolve on its own, that is only latency. For a handler awaiting something a **later keystroke**
must resolve, it is a deadlock with the old frame still on the screen: the widget library's first dialog was written
this way, mounted correctly, took the modal focus correctly, and was never painted and never answered.

So `Application.spawn(coro)` exists, and the rule is **a handler starts work that waits; it does not wait itself.**
The task is held rather than left to the caller — an unreferenced `create_task` may be collected mid-flight and takes
its exception with it — and whatever is still pending when the application stops is cancelled, so a dialog left open
at exit tears itself down through its own `finally`. `Application._dispatching` is set around `_handle` so that the
mistake can be *refused*: `navml.widgets.Dialog.execute` reads it and raises a `RuntimeError` naming `spawn`, which
is three lines and the difference between a diagnosable error and a frozen terminal.

### A widget declares what it emits

`emits = (ClickEvent,)`, a class attribute on `Widget` defaulting to `()`, read through `navkit.events.emitted(cls)`.

It exists because **emitting is otherwise invisible**. `Event.handler` means nothing has to be registered for an event
to be *delivered*, which is the mechanism's best property — but it also means a component's events can only be
discovered by reading its method bodies for `emit` calls. The declaration is the public surface instead: what a reader
consults, what a `.pyi` carries, and what navml's generator checks an `on_click:` line against.

**`emitted()` unions over the MRO where `declarations()` shadows**, and the difference is not an inconsistency. Two
declarations of one attribute are two versions of the same thing, so the nearest wins. A subclass that emits something
new is *adding* to what its base emits — `FramedButton` keeps `Button`'s `ClickEvent` without naming it — because
nothing about emitting one event says anything about another.

### What belongs in `navkit/events.py`, and what does not

**Only events navkit itself raises**: `KeyEvent`, `MouseClickEvent`, `ResizeEvent` and `PasteEvent` come from the
terminal, and `WakeEvent` from the loop. A `ClickEvent` does not belong here however generally useful it sounds,
because a click is something a *widget* means and navkit has no widgets beyond the base class.

The boundary is the layering rule read at the level of one module, and it is what the deleted `MountEvent` was already
straining: navkit knew what it meant, but nothing in navkit ever emitted it. The widget library declares its own,
beside the component that emits them — `navml/DESIGN.md`, *Declaring an event*.

### Why synchronous, and not through the queue

`post_event` exists and an emitted event could have gone through it. It does not, for three reasons and at one cost:

- **The return value is the protocol.** A queued event's answer goes nowhere, and consumption is what `dispatch_key`
  already means by `True` — and what navml made load-bearing when it settled that a markup handler always consumes.
- **The batching that matters happens at the frame, not at the queue.** The loop dispatches a whole batch, flushes the
  effects it queued and paints once; a handler that changes reactive state during dispatch is already inside that
  batch. So queueing an emitted event would buy none of the coalescing the queue exists for.
- **Cause and effect stay adjacent.** A queued event is handled after everything else the terminal has delivered
  in the meantime, so the press and its consequence would be separated by whatever arrived between them — for no gain,
  since both land in the same frame either way.

The cost is that a handler which emits back into its own emitter recurses. That is the author's cycle rather than
the mechanism's, and the stack names every frame of it; the same cycle through the queue would spin the loop forever
and leave no trace of where it started.

### Why up, and what the application sees

Input travels **down** because the user pointed at a place, or at what focus will eventually designate. An emitted event
travels **up** because it already knows its sender and does not know its audience. So the application sees input
*before* the tree and emitted events *after* it, which is the same asymmetry read from the other end.

`Application.on_event` is **not** offered an emitted event. Its contract is to intercept an event before the widgets get
it, and an emitted event reaching the application has already passed every widget that could have claimed it; the named
hook is offered instead.

**The emitter is offered its own event first.** Without that a component could not handle what it itself raises, which
is exactly what markup writes — `on_click:` sits on the `Button:` block that emits it. And it agrees with the two
notes' other precedence rules: `dispatch_key` offers a key innermost-first, and navml resolves a bare name to the
widget's own property before anything else. The most specific claim wins in all three.

### One handler per widget per event

A slot, not a list. `w.on_click = handler` is the whole of connecting, and there is no `connect()`, no
`disconnect()` and no `Signal` object.

- **Bubbling already covers the second listener.** The usual reason for a listener list is that two objects care, and
  here the second one is an ancestor, which the walk reaches anyway.
- **A list would need a disconnect story navkit does not have.** `Effect.dispose()` exists and nothing calls it, and
  `remove()` sets `parent = None` and stops — *Mount and unmount* below. A listener list would add a second kind of
  reference held across a detach, on top of the one already unresolved.
- **Markup assigns.** navml's generator emits `self.b.on_click = _on_click`; a list would need a different spelling
  there for no benefit the walk does not already give.

**The one hazard is a precedence inversion, and it is worth stating plainly.** An instance attribute beats a class
method, so a handler assigned onto the instance wins over one defined on the class. For a component written as both
halves that is backwards: `button.py`'s `def on_click` is on the *derived* class, which wins everywhere else in the
language, and the generated `__init__`'s assignment silently beats it. navkit cannot catch this — the assignment is
legal and the two names are equal — so it is navml's to catch when the document is compiled. The rule it catches it
with is about the **object the assignment lands on** rather than about a name: a markup `on_X:` line may not land on
an object whose class already implements `on_X`. Phrased by name alone it was wrong in both directions — it refused a
line that lands on a *child* and shadows nothing, and it never saw a line on a child block quietly beating that
child's own `on_key`. `navml/DESIGN.md`, *What the generator checks about a handler line*, has the whole of it.

The same inversion is what makes navml's `on_<id>_<event>` convention safe, by turning it the right way up: the
generated half declares a no-op handler for each id'd child and *assigns a bound method of the component*, so the
hand-written half overrides it as an ordinary derived class and nothing is assigned onto an instance at all. The
component's own `on_click` still sits behind it on the walk, because the stub returns False.

### What it cost `Application`

One fix, small and owed anyway: `_handle` dispatched only the four types it knew, so an event posted with `post_event`
reached `on_event` and then nothing. It now falls back to `event.handler`, so `post_event(TickEvent())` reaches
`Application.on_tick`. There are then three paths and each has a reason: input arrives from outside and goes **down**;
a widget's own event goes **up**; a posted event has no sender in the tree and stops at the application.

**One edge came out of writing it**, and it is the reason the fallback is four lines rather than two: a bare `Event`
derives `on_event`, which `_handle` has *already* offered every event to at the top — so the fallback called the same
hook a second time, measured at two calls for one `post_event(Event())`. The guard compares the bound method rather
than the name, which also covers an event class that names `on_event` deliberately.

### What the tests pin

`tests/test_widget.py` holds the walk and `tests/test_events.py` the naming. Four of them are pinning a decision rather
than an implementation, and should be read as the decision: the emitter is offered its own event before its ancestors;
a handler returning `True` stops the walk where it stands; `Application.on_event` is **not** offered an emitted event;
and a widget with no parent and no application emits into nothing and returns `False` rather than raising. A fifth
pins the derivation against the four events that predate it, so a renamed hook cannot drift from the class it serves.

The last one is the useful one: **a mouse press is turned into an emitted event with no focus notion anywhere**, which
is a whole mouse-driven button in twelve lines of test, and it corrects the build order below. `dispatch_mouse` already
routes by position, so emitting never needed focus. What waits for focus is a button driven by the *keyboard*, which
is a different sentence than the one that list was making.

