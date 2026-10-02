## Modal and overlay: the input, not the painting

**Written**, and the fourth item of *What the widget library needs first* below — the last of them. `Widget.modal`,
`Application.modal`, `Application.overlay()`, and the two dispatch paths rerouted around them.

Z-order was never the missing piece. Rendering walks children forwards and hit-testing backwards, so a dialog added
last is painted over everything and asked about a click first; what "modal" adds is that **the widgets underneath stop
being reachable**, which is a question about input and about nothing else.

### Modality is a property of the widget, maintained by the lifecycle

`Widget.modal` is declared beside `can_focus`, and reads the same way: what kind of widget this is, on the class, with
an instance free to differ. The application is told by the **mount walks** — mounting a modal pushes it, unmounting
pops it — rather than by a `push_modal()` a caller has to remember to pair.

That is the whole reason the mechanism is small. Every route a widget can leave a live tree by already runs the unmount
walk: `remove()`, a replaced root, an ancestor carried off with it. So the input comes back on all of them without any
of them knowing what a modal is, and there is no path on which a dialog can leave the screen still holding the
keyboard. It is the second thing *Mounting: joining a live tree, and leaving one* above paid for, the first being the
effect disposal it was built for.

The flag is read **when the widget is mounted**. Flipping it on something already mounted does nothing until the next
time, which is the shape a dialog is used in — declared modal, opened, closed — and the alternative is a stack that has
to be re-derived whenever anything anywhere is assigned.

### Keys: one substitution

`Application._handle` dispatches a key on `self.modal or self._root`. That single change is the whole of keyboard
exclusivity, and it is *Focus: one pointer, and eligibility decided at delivery* above paying out: `dispatch_key` walks
from the focused widget up to the widget it was called on, so dispatching on the modal means the walk cannot start
outside it — `_focus_path()` answers empty for a focus elsewhere — and cannot bubble past it, the modal being where the
walk ends. Nothing was added to either method.

A modal with nothing focusable inside it absorbs keys itself, which falls out of the same walk: an empty focus path
leaves the widget that was dispatched on, and that is the modal.

### The mouse is where modality actually costs something

The mouse routes by **position**, not by focus, so every widget under the pointer is on its path whether or not it is
supposed to be reachable. There is no equivalent of the focus path to reroute; the event has to be moved.

`Application._dispatch_mouse` translates the event into the modal's *parent's* frame — `Widget.offset()` sums the
ancestors' positions, the root sitting at the origin — and offers it there, because `dispatch_mouse` takes an event in
the widget's parent's coordinates and shifts it inward itself. **An action landing outside the modal reaches nothing at
all**: not the widgets underneath, which is the point, and not the modal either, whose coordinate system it is not in.

**Dismissing on an outside click is a policy and is still not navkit's -- but the click is now the modal's to
decide.** An outside *press* (not a wheel, a move, a release or a double-click) goes to the modal itself as a
`ClickOutsideEvent`, in the modal's own coordinates, under `on_click_outside`; a modal with no such handler ignores it,
as every modal did before. The first version left it to a widget watching the application's `on_mouse_click`, which
put the policy on an object that does not know which modal is up. Whether to close is the library's, and it is one
property: `Dialog.close_on_outside_click`, declared in `dialog.nml` and off, so a dialog holding the user's work never
loses it to a stray click, and set in the document of a small dialog that is also opened from another one (`MkDir`,
*Choose Directory*); the drop-downs (`HistoryList`, `Calendar`, `TimePicker`) are not dialogs and get it from their own shared base,
navml's Python-only `DropDown`, under the same name and on by default.
A rule read off the modal stack -- close whatever is not the outermost -- was tried first and dropped: the same
dialog is primary from one key and secondary from another, and a property says what the dialog is, not where it
happened to open.

### Focus is confined, and handed back

Three things, and the third is the one that was promised earlier:

- `Widget.focus()` refuses a widget outside the active modal, so nothing can put the keyboard back behind the dialog.
- `Application.focus_next()` runs the tab order over `self.modal or self._root`, which is the whole of what keeps a
  dialog's Tab inside the dialog — `focusable()` was already subtree-scoped for exactly this.
- **The stack remembers what had the focus when each modal took over, and hands it back when that modal leaves.** The
  focus section above said a per-container memory is a feature that composes on top of one pointer and cannot be taken
  back out of one; this is that feature, built the day something needed it, and the stack is the only place that did.

A modal removed out of order — not the top one — simply leaves the stack without moving the focus, which stays with
whatever is still holding the input rather than being handed back past it.

Two smaller decisions inside that:

- **The focus is settled after the subtree has finished mounting**, which is why `_mount` is two methods: a modal
  choosing its first field has to be choosing from children that exist, and a mount handler that focuses something
  itself must not then be overruled by a default. Handler last wins.
- **A modal with nothing focusable takes the focus away rather than leaving it outside.** Otherwise a widget the user
  can no longer reach keeps the `:focused` highlight and goes on looking like the live one.

### Overlay is one method

`Application.overlay(widget)` adds it as the last child of the root and returns it. A widget deep in the tree opens one
with `self.application.overlay(dialog)`, which is the point: where a dialog is *created* has nothing to do with where
it belongs on the screen.

There is no `close_overlay()` to pair with it, because the inverse already exists and already does more than a wrapper
would: `app.root.remove(dialog)` unmounts the subtree, disposes its effects, releases the input if it was modal and
hands the focus back. A second name for that would only be a worse place to read about it.

### What is deliberately not here

- **Nothing dims or disables what is behind a modal, by default.** `Application.modal` is a plain property over a
  plain list rather than anything observable, so no widget can currently restyle itself for being blocked. A
  `computed` can be added the day a widget asks; guessing at the shape now would cost a cell on every widget for a look
  nothing has asked for. **Dimming is an experimental opt-in**, `Application(dim_modal=True)`: when the top modal
  is about to paint, `Widget.render_tree` calls `Application._painting_modal`, which rewrites every cell painted so far
  faint (SGR 2) with `ScreenBuffer.restyle`. It needs no widget's cooperation, and whatever is painted after the modal
  — the modal itself, and an overlay one of its controls opened — stays at full strength. `navigator` turns it on;
  `--no-dim-modal` turns it off.
  **A `dim` cell is dimmed by colour on a truecolor terminal, not by SGR 2**, because SGR 2 turned out not to be one
  behaviour: VTE (xfce4-terminal, GNOME Terminal) dims only a foreground named by *index* and draws a direct-RGB one at
  full strength, while Ghostty and JediTerm dim both — measured with the same `printf`. A pinned palette on a
  truecolor terminal sends nothing but RGB, so on VTE the dimming vanished entirely. `TerminalInfo.adapt_style` now
  scales a known background by `DIM_BACKGROUND` and mixes a known foreground `DIM_FOREGROUND` of the way toward it,
  which also dims backgrounds, something no terminal's faint does. SGR 2 survives only for a foreground whose value
  the terminal alone knows (its default, an unpinned index below 16), and below truecolor, where a computed colour
  would be quantised to something coarser than the dimming.
- ~~**The mouse is not *captured*.**~~ It is now — see *Windows: raising, capturing, painting over* below. It was
  left to "a scrollbar's problem", and a window's title bar turned out to be the first thing that needed it.
- ~~**`navigator`'s console is still the `visible`-binding trick.**~~ Rewritten: the console is the background layer
  of the screen and is always showing, and Ctrl+O hides the desktop above it. One `visible` binding is left, on the
  desktop, and that is the whole of Ctrl+O.

