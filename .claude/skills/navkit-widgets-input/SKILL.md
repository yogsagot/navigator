---
name: navkit-widgets-input
description: navkit's widget tree and input routing (navkit/widget.py, application.py, events.py, commands.py, screen.py) -- the event loop and frame order, Widget geometry and render_tree, focus and dispatch_key, emitting events, async `on_*` handlers, mounted()/unmounting(), modal and overlay, the cursor, mouse routing and capture, raise_child, shadows, double-click, call_every timers, hover, commands, key tables, enables()/checks(), and the key bar. Use when handling keys, mouse or events, adding a command or key binding, or debugging focus.
---

# Widgets, events, focus and commands

## The loop and the tree

- `Application` owns the only asyncio loop. Input arrives through `loop.add_reader` into `InputParser`. **One turn:
  dispatch the whole batch, flush the reactive effects it queued, then paint one frame** -- a paste or drag costs one
  repaint. `SIGWINCH` becomes a `ResizeEvent`; events reach `Application.on_*` hooks first and the tree second.
- `Surface` is what widgets paint into; `ScreenBuffer` owns cells; `surface.view(x, y, w, h)` is a clipped window.
  `render_tree` hands each widget a view of its own area, so **widgets paint from `0, 0` in their own size and cannot
  draw outside themselves**. Wide characters occupy a cell plus a continuation; at a right edge one degrades to a blank.
  `render_diff()` emits only changed escapes. `Widget.render_after` paints over children.
- `Widget` geometry, `visible`, `style` and `parent` are reactive. **All coordinates are relative to the parent**
  (`x`/`y`, `contains()`, a `MouseClickEvent`'s position, shifted by `dispatch_mouse`); the root sits at the origin.
  `render(surface)` paints; `layout(width, height)` is called on the root at every resize and steps around any size
  that carries a binding (no `self.x +` arithmetic anywhere).

## Focus and keys

- `Application.focused` holds the widget keys go to; `Widget.can_focus` (False by default) says who may; `focus()` takes
  it, `Application.focus_next()` moves it. `Widget.focused` is a computed (so `:focused` is a sheet state).
  `dispatch_key` walks the focus path, nearest first -- **with nothing focused a key reaches no widget at all**.
  Eligibility is decided when the key arrives.

## Events and handlers

- `Widget.emit(event)` walks from the widget up through ancestors to the application, stopping at the first handler
  returning True. An event class names its handler (`ClickEvent` -> `on_click`, `Event.handler`). A widget declares
  what it raises with `emits = (ClickEvent,)`, read through `navkit.events.emitted(cls)`, which unions down the MRO.
- **Every `on_*` handler is `async def`**; navkit refuses a synchronous one (at class creation, or at the call for one
  assigned onto an instance). **A hook that cannot be awaited where it is called gets no `on_*` name**: `mounted()` and
  `unmounting()` are plain sync callbacks. `Application.on_start`/`on_stop` are awaited by `run_async`. An awaiting
  handler lets the loop run mid-batch but **cannot cause a repaint**.
- `navkit/events.py` carries only events navkit itself raises (terminal input, the loop's wake); everything a widget
  means belongs to the library.
- `dispatch_mouse` offers to the topmost child first under `event.handler` (so a refinement reaches its own handler).
  `Application.capture_mouse` gives a dragging widget the mouse.

## Lifecycle, modal, cursor

- `Widget.is_mounted` says whether a widget is in an application's tree; `mounted()`/`unmounting()` are called by the
  walks `Application.root`, `add()` and `remove()` drive. **`remove()` disposes the subtree's effects** -> effects go in
  `mounted()`.
- `Widget.modal` makes a widget take all input while mounted (the mount walks maintain `Application.modal`);
  `Application.overlay(widget)` puts one on top, closed with `app.root.remove(widget)`. Focus is confined and handed
  back. `Widget.dims_behind = False` keeps a modal layer from dimming (`--no-dim-modal` turns dimming off globally).
- **Raising is a reorder**: `raise_child`/`lower_child`, never re-`add()` (that unmounts). `Widget.shadow` is painted by
  `render_tree` into the parent's surface.
- `Widget.cursor_position()` says where the terminal cursor belongs; the application asks **the whole focus path,
  nearest first**, at the end of each frame, so a caret only shows where keys go. The `caret` property sets DECSCUSR
  from a sheet.

## Double-click and timers

- `ClickTracker` synthesises `DoubleClickEvent` from two presses and a clock. **The press is still delivered** (the
  double-click is additional); dispatched inline after that press, re-entering `_handle` so `on_event` sees it; navkit's rather than the library's
  because `Application._loop.time()` is the only clock event handling can reach; keyed on exact cell and button; counts upward
  (a triple click raises one); forgotten on wheel, resize or modal push/pop. `DOUBLE_CLICK_TIMEOUT` 0.4, overridable via
  `Application(double_click=...)`. Clockless by construction (told `now`).
- **The one clock is `Application.call_every(seconds, async_callback)`**, returning a cancellable `Repeat`; callable
  before the loop runs; every tick is posted and awaited inside a dispatch.
- Hover: a position the application keeps (`hovered` state). `Application.pointer` is the last reported `(x, y)` of
  any mouse report, plain motion included -- a plain attribute, not reactive (the screen savers' corners read it).

## Commands and key tables

- A command is an `Event` subclass (`class MakeDirectory(Command)` -> `on_make_directory`), emitted from the focused
  widget up. A key table is a class attribute `keys = {"f7": MakeDirectory}` or a markup `keys:` block, consulted at
  each step of the focus path before that widget's `on_key`; the application's table before the tree, **never under a
  modal**.
- **The nearest widget with the handler decides whether the command is enabled** (`enables(command)`); a command nobody
  handles is disabled, and a disabled command's key falls through as if unbound. `checks(command)` gives menu ticks.
- Where bindings sit: `Navigator.keys` holds Ctrl+O, F1, F10 (the menu), Alt+X, and Enter/Home/End for the command
  line (Alt+X is on the application because a way out cannot live on a window the user can close); `manager.nml`
  holds Tab, Alt+R/Ctrl+R and F2-F8; `Desktop.keys` the window keys; `dialog.nml` Esc, Enter and Tab.
- **Chords**: a spec may be keys separated by a blank, `"ctrl+k b"` (`parse_key`, `key_label` -> `Ctrl-K B`). A table
  may not bind a key both alone and as a chord's start. `Application._chord_key` runs before the key tables: a key
  that begins a chord bound by a table *on the current path* (the application's unless a modal is up, then the focus
  path's) is held in the reactive `Application.chord`; the next key completes it -- looked up in the same tables,
  same order -- or is swallowed with it, never typed. Off the path a prefix key is an ordinary key, so Ctrl+K still
  reaches a program in the console.
- An instance in a table (`GoParent(by_key=True)`) lets `enables` treat the key and the menu differently.
- Key names: a bare `+` is `plus`, a bare Space is named `space` (its `key` is `" "`), keypad operators
  `kp_plus`/`kp_minus`/`kp_multiply`/`kp_divide`.
- **Where commands live**: with the group that handles them, one `commands.py` per group (`navigator/widgets/shell/`,
  `manager/`, `viewer/`, `editor/`, `file_ops/`); `navigator/commands.py` keeps Help, Quit, ToggleConsole.
  `navml/commands.py` holds the window set, `navml/widgets/dialog/commands.py` and `navml/widgets/menu/commands.py`
  theirs. Per group because a component's `__init__.py` imports its widget.
- **The key bar reads captions off the bindings** (`app.bindings()`), greys disabled commands in `$bar-disabled`, and a
  click runs the command. While Alt/Ctrl/Shift is held it shows that modifier's row (`StatusDef hcFilePanel`'s `-`/`+`/`:` items, bound in
  `manager.nml`) (`Application.modifiers`, needs the
  kitty protocol -- see `navkit-terminal`).

## Read when

| Reference | Read when |
|---|---|
| `reference/cursor.md` | the cursor and its shape |
| `reference/modal-and-overlay.md` | modality, keys and mouse under a modal, focus confinement, overlay |
| `reference/windows-raising.md` | raising, mouse capture, `render_after`, shadows |
| `reference/mounting.md` | mount/unmount order, why not an event, disposing effects |
| `reference/focus.md` | focus pointer, eligibility, bubbling, tab order |
| `reference/emitting.md` | emit, handler names, async rule, what belongs in events.py |
| `reference/double-click.md` | the double-click detector |
| `reference/timers.md` | `call_every` |
| `reference/commands.md` | commands, key tables, enabled-by-nearest-handler |
| `reference/hover.md` | hover |
| `reference/still-open.md` | navkit's open questions |
