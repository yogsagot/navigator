## Hover: a position the application keeps

`:hovered` needs the pointer's position when no button is held. Terminals report that only under mode 1003 (*any
motion*), which `MOUSE_ON` now asks for next to 1000, 1002 and 1006. A terminal without it ignores the request, and
hover then follows presses alone.

- **A plain motion reaches no widget, and not `on_event` either.** Mode 1003 reports one event per cell crossed, and
  every `on_mouse_click` in the tree was written for presses, releases and drags. `Application._handle` recognises a
  `move` with button `none` before anything else, moves `Application.hovered`, and returns. A drag (a move with a
  button held) is delivered as before, and the `ClickTracker` never sees a plain motion.
- **`Application.hovered` is the innermost widget under the pointer**, found by `Widget.widget_at(x, y)`. That is
  `dispatch_mouse`'s hit test asked as a question: topmost child first, skipping invisible and inert children. It is
  confined to the active modal, since outside it nothing is reachable. It is left alone while the mouse is captured,
  because a drag is not the pointer wandering. A press moves it too, so hover is right on a terminal that sends no
  motion. `remove()` clears it the way it clears the focus.
- **`Widget.hovered` is a computed**, true for the widget under the pointer *and every ancestor of it*, as CSS's
  `:hover` is. So `:hovered` is a stylesheet state for free, spelled like `focused`.
- **What it costs.** `hovered` is an application reactive, so a change asks for a frame. It changes only when the
  pointer crosses into a different widget, not per cell, since the reactive guard sees the same widget. Rows are
  painted rather than being widgets, so sweeping down a panel is one widget. A frame nothing restyled writes nothing.
  No sheet uses `:hovered` yet, so Navigator paints exactly what it did before.

