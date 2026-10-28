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


## Tooltips: hover that waits

`Widget.tooltip` is HTML's `title` for a cell grid: neither Turbo Vision nor DOS Navigator had one, and the option
strips' symbols (`[§]`, `[⇥]`) were what made it worth having.

- **Armed by a plain motion, and by nothing else.** Each one cancels the pending timer and starts another
  (`Application.call_later(tooltip_delay / 1000, ...)`, the delay being milliseconds), so the timer fires only once the pointer has stayed in one cell that
  long. A press or a key drops it and does not re-arm: after a click, nothing pops up until the mouse moves again.
  Every event but a `_Tick`, a `ModifiersEvent` or the wake drops a tooltip shown or waiting -- a resize included.
- **What it says is decided when it shows**, not when the pointer arrived: `Application.tooltip_here()` asks
  `tooltip_at(x, y)` of `hovered` and its ancestors, each in its own coordinates, nearest first. Confinement to the
  modal comes for free from `hovered`.
- **`call_later` is `call_every` ticking once** (`Repeat(once=True)`): the same queue path, so the tooltip appears as
  one frame of its own batch, and the same cancellable handle.
- **Shown as an overlay, the root's last child.** What stands after a modal is painted after it (`_render_above`), so
  a tooltip shows over dialogs. It sits outside the modal, so adding and removing it marks below dirty and the frame
  is painted whole -- twice per tooltip, which is nothing. Its geometry is bound (the root's `layout` would otherwise
  hand it the screen on a resize), a cell right of and below the pointer, before it where it would pass an edge; it
  never covers the pointer's cell, so the hit test cannot find it.
- Styled as `Tooltip` in a sheet; Navigator gives it the key bar's colours.


## Tooltips: the second round

What the first round's backlog asked for, done (October 2026), and why each went the way it did.

- **The follow-on.** Sweeping the key bar or a menu restarted the whole wait at every item. A tooltip taken down
  by a plain motion now leaves `_tooltip_warm_until` two seconds ahead; a motion inside it arms with
  `TOOLTIP_FOLLOW_ON_DELAY` -- short, but not zero, so the cells crossed on the way show nothing. Any other input
  ends it, as it ends the tooltip: after a key or a click the next one waits the whole delay again.
- **Keys set apart, opt-in by type.** Marking keys with `~` in every tooltip would have made every file name and
  path in one need escaping, and the first one forgotten would paint half a name bright. So only a `Markup` -- a
  `str` subclass that `with_keys` and `lines` build -- is read as markup; everything else is painted literally.
  `caption_runs` moved down to `navkit/text.py` because the tooltip is navkit's and navkit imports nothing above it.
- **Shift+F11.** A terminal with no mode 1003 never reports a resting pointer; the keyboard user never had one
  either. Shift+F1 is DN's *Copy to archive* and every other F1 is taken, so F11's Shift. Bound in the
  application's table (so `keybindings.ini` rebinds it) but read past a modal by `Application._handle` itself,
  since a dialog's check box is where it is most wanted. *Where* is `tooltip_anchor()`, not `cursor_position()`:
  most focused widgets have no caret, and the panel's caret is the command line's.
- **Why a command is greyed.** "Greyed" says nothing about what to do. `refusal()` returns the reason and
  `enables()` is derived from it, rather than a `disabled_reason` beside `enables`, so the two cannot disagree.
  `Manager`, `Shell`, the editor, the viewer, the windows, `Desktop` and `InputLine` say why; `Dialog`'s
  `Default` and `TreeView`'s `QuickSearch` still only veto -- they are keys falling through, never shown greyed.
- **The menu's hint on the key bar.** Keyboard navigation of the menus showed none of their tooltips. While a
  menu is open the key bar is useless anyway (the application's table stands aside), so it shows the
  highlighted row's tooltip and reason across its width, as Turbo Vision's `THintStatusLine` did.
- **History times.** `HistoryEntry`, `ViewRecord` and `EditRecord` gained `used` (`time.time()`, 0 for a row
  from before), a departure DN's histories lacked; the lists' rows say *Last used* in the Country format.
- **A sweep** in `tests/test_tooltip.py`: every top-level menu (a window's joins the bar) has a tooltip, no item's
  tooltip repeats its caption, every tab view's tooltips match its pages, and every focusable control in
  Options > Settings but a button answers Shift+F11.
