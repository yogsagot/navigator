## Mounting: joining a live tree, and leaving one

**Written**, and the third item of *What the widget library needs first* below. `Widget.mounted`, `on_mount`,
`on_unmount`, the walks behind them, and `navkit.reactive.dispose_effects()`.

**Mounted means reachable from an application, not "has a parent".** A tree under construction is not mounted, however
deeply it is nested; the whole of it mounts at once when its root is handed to `Application.root`, which is how
`navigator` builds its desktop and then attaches it. A widget added to a tree that is already mounted mounts
immediately, and that case — a dialog opened at run time — is the one the whole section exists for.

The transition is **driven by the three operations that can cause it** — the `root` setter, `add()` and `remove()` —
rather than derived from `Widget.application`. Deriving would be the tidier-looking answer and does not work: a
`computed` is lazy, so nothing would notice the change until something happened to read it, and "notice" is the entire
job. An effect per widget watching its own `application` would work and costs one eager cell per widget for a fact
three methods already know.

### Why the hook is not an event, and not called `on_*`

`Widget.mounted()` and `Widget.unmounting()`: synchronous, argumentless, and outside the `on_*` namespace altogether.

**This was decided twice, and the second answer is the one that stands.** The first design made them `on_mount(event)`
and `on_unmount(event)` with two fieldless event classes, on the argument that markup fixes every handler at exactly
one argument so a hook taking none is the one shape a `.nml` document could not spell. That argument died with
*Every handler is `async def`* below: **the mount walk runs from `add()`, which runs from `__init__` when a widget is
constructed with a parent, and a constructor cannot await.** A lifecycle hook therefore cannot be a handler, whatever
it is called, and `MountEvent`/`UnmountEvent` were deleted with the names.

What survives is the better rule, stated once and applying to both: **a hook that cannot be awaited where it is called
does not get an `on_*` name.** `Application.on_start` and `on_stop` take no event either and *keep* their names,
because `run_async` can await them — so the line is drawn by what the call site can do, not by whether an event object
happens to exist.

The cost, recorded rather than glossed: **markup can no longer write a mount hook.** A markup-only component that needs
work at mount gains a `.py`. That is the same line *A handler body is one line* draws in `navml/DESIGN.md` — markup
says what, Python says how — falling where it already falls.

The hooks are **called directly, never emitted.** Emitting walks up, so mounting a subtree of twenty widgets would
deliver twenty mounts to the root, each of which it can do nothing with. A widget that wants its ancestors to know it
has arrived emits something of its own, which is one line and says what it actually means.

### Parents first, children first

Mounting is parents first, so a child's handler finds every ancestor already mounted. Unmounting is children first, so
a child is taken apart while its parent is still whole. Both walk in child order, the tree told about in the order it
is written.

`on_unmount` runs **before** the unlink and before the effects are disposed. It is the only moment a leaving widget has
everything it needs: still parented, still sized, still reachable through `application`. A handler releasing something
outside the reactive graph — a subprocess, an open file, a timer — has no other place to do it from.

### Why removal disposes effects, and what that asks of a widget

This is the part that was a bug rather than a missing feature. **An effect is eager**, so an effect whose expression
stops making sense does not wait to be read before it fails: `remove()` sets `parent = None`, that write queues every
effect that read it, and the next flush raises `AttributeError: 'NoneType' object has no attribute 'width'` — which
`Application._flush_effects` turns into an `exit()` and a re-raise. **Removing a widget took the application down**, and
it is measured rather than argued: switching the disposal off and removing a widget whose effect reads
`self.parent.width` reproduces it in six lines.

So `remove()` disposes every effect registered on each widget of the subtree, through the new
`reactive.dispose_effects(obj)` — the counterpart to calling `effect()` without keeping the handle, which is how every
effect in this repository is created. `Effect.dispose()` existed and nothing called it; this is its caller.

A binding needs no such rescue, and the asymmetry is the point: a binding is lazy, so a detached widget's
`w.parent.width` is never evaluated while nothing paints it, and re-attaching writes `parent` again, which invalidates
the cell and lets the cached failure recover. Eagerness is what makes effects the ones that have to be stopped.

**What it asks of a widget is one sentence: a widget that can be removed and put back declares its effects in
`on_mount`.** Disposal is permanent, so effects created in `__init__` do not come back — the widget would be detached
once and dead afterwards, which is worse than the crash it replaces if it is not written down. A widget built once and
never detached may keep declaring them in `__init__`, which is what `navigator`'s `Panel` does and why nothing in the
application had to change: its panels are never removed. The flush order that `Panel.__init__`'s comment calls
load-bearing is preserved either way, being the order the `effect()` calls are made in.

### Two smaller things that fell out

- **`add()` lays a child out, but only into a mounted parent.** Otherwise the child is 0x0 until the next terminal
  resize and a run-time dialog paints nothing, silently. The restriction to mounted parents is not timidity: `layout()`
  hands the parent's size to every child whose size is not bound, so laying out during construction would overwrite a
  `width=` the caller had just passed to the constructor. A tree still being assembled has no size to cascade anyway,
  and `Application.root` lays the whole of it out when it is attached.
- **`Application.root = None` unmounts the outgoing tree and drops the focus into it.** The focus half was already
  owed — *Focus: one pointer, and eligibility decided at delivery* above clears focus in `remove()` for the same reason
  — and replacing the root is the other way a focused widget can leave the screen.

