## Focus: one pointer, and eligibility decided at delivery

**Written**, and the first item of *What the widget library needs first* below. `Application.focused` holds the widget
keys go to, `Widget.can_focus` says which widgets may hold it, `Widget.focus()` takes it, `Application.focus_next()`
moves it along, and `Widget.dispatch_key` was rewritten around it.

### The application holds it, the widget derives it

One pointer, on the application, rather than a focused flag per widget or a remembered child per container. The flag
would need every widget that takes focus to clear every other, and a per-container memory is a *feature* — a dialog
restoring what it had — that composes on top of a pointer and cannot be taken back out of one.

`Widget.focused` is therefore a `computed` reading `self.application.focused is self`, and that buys the thing worth
having: **it is a stylesheet state for free.** `:state` selectors resolve through `getattr(widget, state, False)`
inside the style cascade's own computed, so `Panel:focused { … }` matches with nothing added to the stylesheet engine,
and moving focus restyles the widget that lost it and the one that took it without either being told. That is
`navigator`'s hand-rolled `Panel.active` — which `Manager.active_panel` assigns and `navigator.nss` reads — arriving as
a navkit notion.

### A widget is not focusable until it says so

`can_focus` is `False` on `Widget`, so a container, a frame and a label stay out of the tab order by saying nothing.
The other default would put every box in the tree in it and make opting *out* the common case, which is the wrong way
round for a library whose widgets are mostly structure.

It is `reactive` rather than a plain class attribute because a widget withdraws from the order while it is disabled,
and because a binding should be able to decide it. That costs one cell per widget and makes `Panel:focused` and
a disabled button's exit from the tab order the same kind of fact.

### Eligibility is decided when the key arrives, not when focus is set

`focus()` refuses a widget that is not focusable, not visible, or not attached to an application. It does **not** walk
up checking that every ancestor is visible, and `Application.focused` is not policed at all on assignment.

The reason is that the alternative is worse than it looks. A focused widget can stop being reachable without anything
touching it — `navigator` hides a whole band of the desktop when the console opens, by flipping one reactive flag that
three `visible` bindings read — so keeping the pointer correct would mean an effect watching the visibility of every
ancestor of the focused widget, re-established whenever focus moves. Instead `dispatch_key` walks from the focused
widget up to itself and abandons the walk at the first invisible step, which is a walk it has to make anyway:

- the focus is a *pointer*, and it stays where the author put it;
- whether the keyboard can reach it is a question about the tree right now, asked once per key.

So hiding a container does not have to chase the focus inside it, and showing it again does not have to restore
anything. What the walk costs is one `parent` hop per level, on the key path, against an effect per focused widget on
the write path.

**`inert` is asked at the same moment, for the same reason.** `Widget.disabled` is the flag, and `Widget.inert` is a
computed that is true when the widget or any ancestor has it set. `focus()` refuses an inert widget,
`focusable()` skips an inert subtree, and the walk to the focused widget abandons at an inert step exactly as it does
at an invisible one. `dispatch_mouse` and `widget_at` pass over an inert child the way they pass over a hidden one.
So disabling a group does not move the focus out of it. It stops delivering to it, and enabling the group again
needs nothing restored.

The one place the pointer *is* corrected is `remove()`: a focus left pointing into a detached subtree would send every
key to a widget that is no longer on screen and can never be reached again. `remove()` clears it before the unlink,
while the focused widget can still be walked back to the child being removed.

### A key goes to the focused widget and bubbles up

`dispatch_key` was a positional lottery — every visible descendant offered the key, deepest and last-added first, until
one returned `True`. It now walks the focus path: the focused widget, then its ancestors up to the widget dispatch was
called on. The same shape as `emit`, started from where the keyboard is rather than from where an event was raised,
so a container can carry the bindings its children share and an unhandled key finds it.

**With nothing focused, the widget dispatch was called on is offered the key and nobody else.** That is a deliberate
change rather than a fallback: a key belongs to whatever holds the keyboard, and when nothing does, to nothing. The old
behaviour only looked harmless because no widget in the repository defines `on_key` — `navigator` routes every key from
one `if/elif` chain in `Navigator.on_key`, which runs before the tree and is untouched by this.

Two things this deliberately does not do, both of them the widget library's:

- **Nothing binds Tab.** navkit provides `focus_next(reverse=…)` and no key binding for it, because `navigator` spends
  Tab on switching panels and a library that took it would be wrong there first.
- **A mouse press does not focus what it hits.** `dispatch_mouse` routes by position and says nothing about the
  keyboard; a Button that wants the pair calls `focus()` in its own `on_mouse_click`, which is one line and a policy.

### The tab order is a walk, not a list

`Widget.focusable()` returns the visible, focusable widgets of a subtree in tree order, pre-order, so a container that
takes focus comes before the children it contains. `Application.focus_next()` runs it over the root each time rather
than keeping one: the tree is reactive, so a kept order would be stale the moment a widget is added, hidden or
disabled, and the walk is over a tree the loop already repaints whole.

**It is scoped to a subtree because that is what modal will need.** A dialog runs the same walk over itself and nothing
outside it is reachable — which is the half of *Modal and overlay* below that focus is responsible for, left in the
right shape rather than built now.

A focus that has left the order — hidden, or removed — does not stop a move: the search starts from the end it came
from, so Tab out of a vanished widget lands on the first widget rather than on nothing.

