### Windows, the desktop and the modal

The library's first `Window` was a framed box a dialog was made of. It is `Modal` now, and `Window` is what Turbo
Vision meant by one: a detached, overlapping rectangle on a desktop that the user drags, resizes, zooms and brings
forward. The two differ in **where they live**, and every other difference follows from that.

- **A modal is overlaid on the application's root; a window lives on a `Desktop` one level below it.** `overlay()` is
  `root.add()`, and every desktop is a child of the root, so no window can be raised past a modal however it is
  raised — the guarantee is structural, not a z-index to keep in order. Blocking the input outside it was already
  navkit's (`modal = True`, read by the mount walk), and the one leak was the *application's* own hooks, which run
  before routing: `Navigator.on_key` and `on_mouse_click` return early while `app.modal` is set, or Ctrl+O would put
  the windows away under an open dialog.
- **A modal's geometry is bound; a window's is state.** A drag assigns `x`/`y`, a resize `width`/`height`, a zoom all
  four — and by *A property a widget navigates cannot be bound*, those four are plain values. So `Window.layout()` is
  not the cascade: it keeps its own rectangle and only clamps it into the desktop, leaving eight columns and the title
  row to take hold of again, or, zoomed, takes the desktop's size. A derived document gives a starting size with
  literal lines — `zoomed: True` is one — because a literal is an assignment and not a binding.
- **A desktop re-fits its windows from an effect on its own size.** A markup parent does not cascade `layout()`, so a
  resize reaches a bound desktop as a changed value and never as a call; `Desktop.mounted()` watches its width and
  height and lays out every window, untracked, so the window geometry it assigns does not wake it again.
- **Raising is a reorder** (`Widget.raise_child`, navkit's), because re-adding unmounts. `Desktop.active_window` is
  reactive because the children list is not, and it is what `Window.active` — the `:active` state — reads.
- **The focus moves with the activation, in the same call.** Each window remembers what had the keyboard when it went
  to the back, and `Desktop.activate()` gives it back — so Ctrl+O's return and a click on a background window both
  land on exactly the widget that had it. Not from an effect, for `toggle_console`'s reason.
- **A window with nothing focusable holds the keyboard itself** (`Window.take_keyboard`), as a `TWindow` was the
  selected view when it had nothing else to select. Leaving the focus at None would mean no widget is offered a
  key, so the window's own key table and the desktop's window keys would stop working while it was on top. The
  fallback is decided again on every activation, and a window that has since gained a control hands that control
  the keyboard. Keyboard move mode keeps the window holding the keyboard when it ends.
- **The first click on a background window is delivered, not swallowed**, as in Turbo Vision: it activates the
  window and then reaches the child under it, so one click selects the other file manager *and* moves its cursor. The
  exception is the chrome: an inactive window does not paint its icons, so it cannot be closed by a click on where
  one would have been.
- **Chrome is tested before the children.** A frameless window has children on row 0 — the file manager's panels are
  its frame — and they would otherwise claim every press on the title. `chrome_hit()` and the painter read one column
  table, so the icons drawn and the icons clicked cannot drift apart; a frameless window paints them in
  `render_after`, over the panels. `Panel.title_margin` keeps a long path from running under them.
- **A drag holds the mouse** through navkit's `capture_mouse`, so the pointer outrunning the window does not end it.
- **Every window and every modal casts Turbo Vision's shadow** (`shadow = True` on `Window` and `Modal`, and on
  `MenuBox` and `HistoryList` too): navkit's `Widget.shadow`, painted into the desktop's or the root's surface as part
  of painting the window, so a window above shades the one below and a zoomed one's falls off the desktop. The shadow
  is outside the rectangle, so a click on it reaches what is beneath, as `TView` hit-tested. *Shadows* in
  `navkit/DESIGN.md` has the order against the dim.
- **The window keys are `Desktop.keys`**, reached after the active window's children, so a panel or an input
  line keeps first refusal. They are one table of `navml.commands`, checked against DOS Navigator's own *Window*
  menu: Ctrl+F5 `SizeMoveWindow`, Alt+Z `ZoomWindow`, Ctrl+F4 `CloseWindow`. The original's Next and Previous are
  Alt+Tab and Ctrl+Tab, which a terminal cannot deliver (the window manager takes one, the other arrives as Tab),
  so `NextWindow` and `PreviousWindow` take F9 and Shift+F9, where every one of DOS Navigator's status lines binds
  `cmNext` and `cmPrev`. `Desktop.enables` vetoes zoom and close for
  a window that refuses them. Turbo Vision's plain F5 and F6 are Copy and RenMov in DOS
  Navigator's panels, which is why Size/Move carries a modifier; the table has now been checked against both the
  window menu and the `StatusDef`s in `DN.DNR`.
- **An emptied desktop says so** with `EmptiedEvent`, whose handler name makes the generator's stub for a child with
  id `desktop` read `on_desktop_emptied` — the name was chosen for that. The event is emitted from a spawned task
  because closing is synchronous and emitting is not, so a key in the same batch as the close still meets the old
  focus; that is one of the two places the same-call rule is bent.
- **So does an opening**, with `OpenedEvent` from `Desktop.open()`, emitted the same way and bending the rule the
  same way. It exists because the desktop can be out of sight: Navigator's `Shell.on_desktop_opened` hides the console
  when a window opens behind it. That used to be a check inside Manager > New alone, so Disk > Directory tree opened a
  window nobody could see until Ctrl+O. **Revealing a window belongs to opening it, not to the command that asked**,
  so a plugin opening one gets the same behaviour for free. Nothing is announced while the tree is being built.
- **Window › List (Alt+0) is DOS Navigator's *Windows Manager*.** It is `cmWindowManager`, run by `WindowManager` in
  `COLORS.PAS`, with its dialog `dlgWindowManager` from `DN.DNR`: 70x14, a `~W~indows` label, the list from
  column 2 to the scroll bar at 57, and OK, Close, Cancel and Help ten wide down the right. Help is disabled
  because nothing handles it yet. `navml/widgets/window_manager/` is the dialog, and `navml/widgets/window_list/`
  is `TWindowList`, a `ListViewer` whose items are the windows themselves, top first.
  - **A row is `Window.list_name()`**, which stands in for `cmGetName`. It defaults to the title, and an empty
    name keeps a window out of the list, which is what the original did.
  - `Manager` names itself after its active panel's directory, because the double window forwarded `cmGetName` to
    its panel. **The names are read when a window enters the list, not while painting**, because while the dialog
    is up the focus is in the dialog, and "which panel is active" is a question the focus answers. A background
    manager answers from `_saved_focus`, which is what it will get back.
  - **Close stays in the dialog.** The original looped: it freed the window, listed the desktop again and ran the
    dialog again. The last window closing ends it.
  - **OK activates only once the modal is down**, so the keyboard goes to the chosen window. `Desktop.activate`
    under a modal raises the window and leaves the focus where it is.
- **Window › Tile, Cascade and Close all are `cmTile`, `cmCascade` and `cmClearDesktop`**, with no key, as in
  `DN.DNR`. The arithmetic is `TDesktop.Tile`/`Cascade` from `DNAPP.PAS`, ported rather than redesigned:
  - **Every window is arranged unless it opts out** with `tileable: False`. This departs from the original on
    purpose: Turbo Vision's `ofTileable` was off by default and DOS Navigator set it only on the double window, the
    viewer, the editor and the calculator — not on `TTreeWindow`. Every `Window` on a desktop is free-floating, so
    every one takes part, including the ones not written yet; dialogs are `Modal`, not `Window`, and never do.
  - **Tile favours rows** (`TileColumnsFirst` was never set): two windows lie one above the other, four make a 2x2
    grid, and the rightmost columns a grid cannot fill evenly take a row more. The bottom window gets the top-left
    tile and the z-order is not touched. **Cascade** moves each window one cell down and right of the one under it,
    and — departing from `TDesktop.Cascade` on purpose — **makes them all the same size**, the desktop's less the
    steps the stack takes, so only the top window reaches the bottom-right corner. The original kept every
    window's corner on the desktop's, so a lower window was larger and, brought forward, hid every window above
    it; equal sizes leave their edges showing. Cascade does nothing when that size is below any window's minimum
    — `TileError` was empty, so a desktop too small for either is simply left alone.
  - Both place a window through **`Window.locate()`**, Turbo Vision's `Locate`: the size is raised to the minimum
    and a zoomed window stops being one.
  - **Close all closes every `closable` window**, front to back, through `Window.close()`: the original broadcast
    `cmClose`, which a window without a close icon ignored. The last close raises `EmptiedEvent` as any close does.

