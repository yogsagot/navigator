## Windows: raising, capturing, painting over

**Written**, for navml's overlapping `Window` and its `Desktop`. Three additions, each small, each something a widget
library could not do for itself without reaching into navkit's privates.

### Raising is a reorder, never a re-add

*Z-order needed nothing* was true while the only thing on top was a dialog added last. A window that is clicked has to
*become* the last child, and `add()` already moves a child — by detaching it first, which unmounts the subtree,
disposes its effects, takes the focus away if the focus was inside it and pops it off the modal stack. Bringing a
window forward must do none of that: it is the same window, still holding the same keyboard.
`Widget.raise_child(child)` and `lower_child(child)` reorder `children` in place and call `invalidate()` by hand,
because the children list is not reactive. Anything that needs to *observe* the order — a window's `:active` state —
is given a reactive of its own by whoever does the raising (`Desktop.active_window`), rather than navkit making every
children list observable to serve one reader.

### Mouse capture

Routing is by position, and a pointer dragging a window's edge is routinely outside the window by the time the
terminal reports it — a fast hand, or a resize the window refuses past its minimum. So
`Application.capture_mouse(widget)` sends every mouse action to *widget*'s handler, under `event.handler` and in its
own coordinates, with **no hit test**. It is the application's rather than the widget's because `_dispatch_mouse` is
the one place every action passes through. The application's own `on_mouse_click` hook still sees each action first,
as it always has.

It is released in three places, each of which would otherwise leave the mouse stuck on something unreachable: **after
a `release` is delivered** (the ordinary end of a drag), **when the holder is unmounted** (a window closed mid-drag),
and **when a modal opens that does not hold it** (the modal's rule is that nothing outside it is reachable, and a
capture is a way of reaching). A double-click, which is dispatched inline right after its second press, goes to the
holder too — which is how a window zooms on a double-click on the title it has just started dragging.

### `render_after`: painting over the children

`render_tree` paints a widget and then its children, so nothing a widget draws in `render()` can sit on top of them.
A frameless window needs exactly that: the file manager's panels *are* its frame, and its close and zoom icons belong
on their top edge. `Widget.render_after(surface)` is an empty hook called after the children, on the same view. The
alternative — asking the panels to leave gaps for icons they know nothing about — would have put a window's chrome
into a list widget.

### Shadows: painted from the parent's surface

Turbo Vision's `sfShadow` — two columns down a view's right and one row along its bottom, offset one row and two
columns, the character beneath kept and recoloured to `ShadowAttr` (dark grey on black) — lies *outside* the widget
casting it, and a widget can only paint through a view of itself. So it is `render_tree`'s, which still holds the
parent's surface: `Widget.shadow` (a class attribute, like `dims_behind`) makes it paint the shadow there **just
before `render`**. That is Turbo Vision's own order, a view drawing its shadow as part of drawing itself, so three
things come for free: a sibling painted later covers the shadow of one painted earlier and is shaded by nothing
beneath it; a nested menu box shades its parent box; and the parent's clip cuts the shadow off, so a zoomed window's
falls entirely outside the desktop. **It is laid after a modal's dim**, and replaces the cell's style whole
(`style.SHADOW`), so a dialog's own shadow is at full strength over what it blocks and a console cell under a shadow
loses its unpinned palette like any other. It is a constant, not a sheet property, because it was a constant in the
original and no palette slot names it. A wide character's empty continuation cell is left alone. `navml` turns it on
for `Window`, `Modal`, `MenuBox` and `HistoryList`.

