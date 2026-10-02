## The widget library

Fifteen components under `navml/widgets/`, and **not one of the first thirteen was designed.** DOS Navigator's Colors dialog
exposes 144 slots, `tools/palconv.py` transcribed every one into all eleven themes, and the *Dialogs* group names the
widgets outright — frame and frame icons, scroll bar page and icons, static text, label, button, cluster, input,
history, list, information pane — with their states spelled out beside them. A colour table is a strange place to
find a specification and it is a complete one: `[41] Button normal`, `[42] Button default`, `[43] Button selected`,
`[44] Button disabled`, `[45] Button shortcut`, `[46] Button shadow` is six facts about what a button *is*, and the
project's standing rule says to take them rather than invent six of our own.

| widget | shape | parts | states | emits |
|---|---|---|---|---|
| `Control` | Python | — | `:inert`, `:focused` | — |
| `Cluster` | Python | `item`, `mark`, `shortcut` | `:inert`, `:focused` | — |
| `StaticText` | both | `shortcut` | — | — |
| `Label` | both | `shortcut` | `:selected` | — |
| `Button` | both | `shadow` | `:am_default`, `:down`, `:inert`, `:focused` | `ClickEvent` |
| `InputLine` | both | `arrow`, `selection` | `:inert`, `:focused` | — |
| `CheckBoxes` | Python | inherited | inherited | — |
| `RadioButtons` | Python | inherited | inherited | — |
| `ScrollBar` | both | `arrow`, `thumb` | — | `ScrollEvent` |
| `ListViewer` | both | `title`, `row`, `footer`, `error`, `divider` | `:inert`, `:focused` | — |
| `Modal` | both | `title`, `icon` | `:focused` | — |
| `Dialog` | both | inherited | inherited | — |
| `Window` | both | `title`, `icon` | `:active` | — |
| `Desktop` | Python | — | — | `OpenedEvent`, `EmptiedEvent` |
| `Field` | **markup only** | — | — | — |
| `ChoiceField` | **markup only** | — | — | — |
| `ChoiceLine` | Python | inherited | inherited | — |
| `DateField`, `TimeField` | **markup only** | — | — | — |
| `MaskedLine` | Python | inherited | inherited | — |
| `MaskedField` | **markup only** | — | — | — |
| `DateButton`, `TimeButton` | Python | `arrow` | — | — |
| `Calendar` | Python | `title`, `arrow`, `weekday`, `day` | `title`: `:selected`; `day`: `:selected`, `:today` | — |
| `TimePicker` | Python | `value`, `separator`, `arrow` | `value`: `:selected` | — |
| `Spacer` | Python | — | — | — |

### A button is drawn as `TButton.DrawState` draws it, and clicks on the release

The first `Button` drew `[ OK ]` and darkened whatever was to its right and below. DOS Navigator's own
(`DIALOGS.PAS`, `TButton.DrawState`, the colour path where `ShowMarkers` is off) has no brackets: the face is plain
colour, and the button Enter would press carries `►` and `◄` (CP437 16 and 17) in its first and last columns -- drawn here as `▶` and `◀`, because fonts
draw the `►◄` pointers squat and those are the full-size triangles; their width is ambiguous, as box drawing's is. The
shadow is drawn, not darkened: `▄` then `█` down the column to the right and `▀` under the face one cell in, in `[46]`
— black on the dialog's grey, so the half blocks *are* the shadow and nothing behind is read. The rectangle is
unchanged, one column and one row wider than the face. Under the ASCII tier the half blocks become whole cells.

- **Pressed moves right, into the shadow.** `DrawState(Down)` starts the face at column 2 rather than 1 and blanks
  the bottom row, so the button sinks into where its shadow was. `Button.down` is a markup property the caption's
  `x` reads.
- **The click fires on the release, and only over the button.** `HandleEvent` loops on mouse moves after the press,
  toggling `Down` as the pointer leaves and re-enters the face-plus-shadow-column rectangle, and calls `Press` on
  release if it is still down. That is `Application.capture_mouse` plus the same test. A press on the shadow is not
  a press, as `ClickRect` excluded it.
- **Space goes down and clicks on its release — a departure.** DN pressed on the Space key at once, with no pressed
  look. Taken because it is what the mouse does and the user asked for it. Where the terminal reports releases
  (`KeyEvent.releases`, kitty protocol) the click waits for `KeyReleaseEvent`. Elsewhere the button shows pressed for
  `FLASH` (0.1 s) through a one-shot `call_every`, so the up frame and the click land in one batch. A repeat while
  down is swallowed. A key-held button whose focus leaves pops up without clicking. Enter and the `Alt` shortcut
  still press at once, as in DN.
- **`:am_default` is DN's `AmDefault`, not the `default` flag.** A focused `TButton` broadcast `cmGrabDefault`, and
  the `bfDefault` button stopped looking default until `cmReleaseDefault`. `Button.am_default` is that as a computed:
  `default`, unless another `Button` under the same nearest modal ancestor holds `Application.focused`. So the
  markers, and the default colours, are on exactly one button: the one Enter presses.

### `disabled`, never `enabled` — and `inert` to ask

Forced at first, and kept now it no longer is. The selector grammar had no `:not()`, so a positively-spelled `enabled`
could never have styled the disabled case, which is the one DOS Navigator gives a slot of its own. The grammar has
`:not()` now (`navkit/DESIGN.md`, *`:not()`*), and the flag still stays `disabled`, because it is the one somebody
*sets*: a widget is enabled by saying nothing.

**The flag moved from `Control` to `Widget`, and what is asked is `inert`.** `Widget.inert` is a computed, true when
the widget or any ancestor is `disabled` (Textual's `is_disabled`; HTML's word). So disabling a container takes every
control inside it out of reach without anybody walking it, and re-enabling it gives back exactly the flags the
children had of their own. **A document writes `disabled:`, and code and sheets ask `inert`**: `can_focus` is bound to
`not inert`, every control's refusal tests `self.inert`, and `navigator.nss` greys a button with `Button:inert`, which
matches a button disabled in its own right and one inside a disabled group alike. `:disabled` still exists, and means
only the flag on that widget.

`can_focus` stays *bound*, which makes it read-only on a control. That is *A property a widget navigates cannot be
bound* arrived at from the other end: a document writes `disabled:` and never `can_focus:`.

### The shortcut is a rendering of the caption

Turbo Vision marks it inline, `~O~K`, and keeping that rather than adding a `shortcut` property means a translated
caption carries its own accelerator with nothing to hold in step. `parse_shortcut` lives in `control.py` and is
called from exactly two painters; `~~` is a literal tilde and an unpaired `~` is drawn as one, because a caption is
text first and a declaration second.

**The container dispatches it, and needs no new mechanism.** `dispatch_key` walks the focus path *upward*, so a
`Modal` is offered every key its own controls did not claim — it then walks its own subtree for a `Control` whose
letter matches. Turbo Vision broadcasts because it has no focus path; navkit has one, and the walk is the downward
half of it. **Alt and a letter only**: the original also accepts a bare letter when no input line holds the focus,
and reproducing that would mean asking the focused control whether it eats printable keys, which is an implicit
coupling between every control and every container. `KeyEvent.is_printable` is already false when `alt` is set, so
an `InputLine` never has to think about it.

`activate()` is the one virtual: a `Button` focuses and presses, an `InputLine` focuses and selects what is there so
that typing replaces it, a `Cluster` moves to the item that owns the letter and turns it on, and a `Label`
**delegates to its link** — which is what makes `~N~ame` beside a field mean the same thing as `~N~` on the field.

### A handler starts a dialog; it does not wait for one

The rule the whole library rests on, and it was found by running the obvious thing and watching it freeze.
`await dialog.execute(app)` inside `on_key` mounts the dialog, takes the modal focus, and **never paints it**:
`_main_loop` awaits `_handle` and only then renders, and it is the only consumer of the event queue, so the key that
would dismiss the dialog is read, queued and never dispatched. The measurement is in `navkit/DESIGN.md` under *What
the frame model gives up*, which has been corrected to say so.

So a handler calls `self.spawn(self._make_directory())` and returns; the batch finishes, the frame paints, and the
waiting happens in a task. `Dialog.execute` reads `Application._dispatching` and raises rather than hanging, and
`tests/test_widgets.py` asserts the dialog is *in the frame* before anything answers it.

### Rows are not widgets, and that is why markup needs no repeater

`ScrollBar`, `ListViewer`, `CheckBoxes` and `RadioButtons` all paint their own items. `navkit/DESIGN.md`'s *Parts:
listing rows do not become widgets* settled this by fidelity before there was a library to apply it to — "one view,
many items, no per-item objects; rows were never objects in the original" — and the consequence is the one that
matters here: **the thing markup cannot say turns out not to need saying.** A list's items are a *value*, and a
value is something a document can already express.

The same trick answers conditionals. `Dialog` declares all three of its buttons and binds their `visible`, because a
hidden widget is already out of the tab order, out of the shortcut walk and out of the paint. And where a *number*
varies, a conditional **expression** is still one line — which is how `Dialog` centred two buttons or three with a
ternary until *Layouts* below made the arithmetic unnecessary: a hidden child gives up its slot in a
`HorizontalLayout`, so the row centres itself.

### A dialog's geometry is bound, and that is not a style choice

`Component.layout()` does not cascade into children — but `Widget.add()` still calls
`child.layout(parent.width, parent.height)`, and `Component.layout` steps around a side only when it carries a
*binding*. So a dialog sized with a literal is resized to the whole terminal the moment `overlay()` adds it; measured
at 40x8 asked for and 100x30 got. Every modal therefore routes its size through a declared property the base binds
from:

```
Modal:
    property modal_width: 50
    width: self.modal_width
```

which is also the only way a *derived* document can change it. `width: 44` in `MkdirDialog` would be a value over a
live binding installed by `super().__init__()` a moment earlier, and would raise; `modal_width: 44` is a literal
onto an attribute nothing has bound. The binding lives on `Modal` rather than `Dialog` since the split below, and so
does the centring — which is also exactly why a modal cannot be dragged.

### A derived component's own children land after its base's

`super().__init__(**kwargs)` is the generated constructor's first line, so the base's tree is built first and
`focusable()` — which is pre-order — would open every derived dialog with the focus on OK and run Tab backwards.
`Dialog.focusable()` moves its own buttons to the end; one override fixes both, because `_claim_focus` reads the
first of that list and `focus_next` reads the same list. `MkdirDialog` opens with the keyboard in its input line
because of it.

### What the library took from `Panel`, and what it left

`ListViewer` is `navigator/widgets/manager/panel/panel.py`'s generic half, extracted: the reactive `items`/`cursor`/`scroll`,
the `rows` computed, the two invariants that keep them honest, the framed container with its centred title and
footer, the row painting, the row hit-test, and the list keys that used to sit in `Manager.on_key`. What stayed is
everything about *files*.

Two things the extraction turned up. **The invariants moved from `__init__` into `mounted()`**, because `remove()`
disposes a subtree's effects and every widget in a dialog can be removed and put back — `Panel` could get away with
the constructor only because the desktop never lets it go. And **a row is filled only when it is the cursor row**:
filling every row looks identical and is not, because `render_diff` compares cells by style and emits an SGR run for
every difference, so a fill nobody can see is real bytes on the wire. That one was caught by
`tests/fixtures/desktop-80x24.txt`, a dump of every character *and every style run* of the desktop captured before
the extraction started — which now reproduces exactly, and is the automated form of the pty `cmp` that proved
`manager.nml`.

**A list carries its own vertical scrollbar**, Turbo Vision's `vScrollBar`, as a `ScrollBar` child in
`list_viewer.nml` placed on the right frame (`x: parent.width - 1`, between the corners). So `Panel` and every
dialog list get it without doing anything. It is **visible only while the list overflows** its rows, which leaves a
short listing with its plain frame, and the desktop fixture unchanged. **Its value is the cursor, not `scroll`**,
because that is what `TListViewer` gives its bar. Working the bar raises a `ScrollEvent`; `on_bar_scroll` assigns
`cursor`, and `_follow_cursor` moves the scroll after it. Binding the bar to `scroll` instead would have put a second
writer on the value `_follow_cursor` owns, and the two would fight. Binding `value` is legal because `ScrollBar`
never assigns its own value: it emits and lets the owner decide.

**A list that lays its items out other than one per row says so through four hooks**, which `Panel`'s list mode
(Ctrl+Y) is the reason for: `capacity` (a computed, `rows` by default -- how many items are on show, which the
bar's `visible` and `page()` read), `index_at(x, y)` (the hit-test, `row_at(y)` by default), `render_items(surface)`
(the row loop, lifted out of `render()`), and `_follow_cursor`, which `mounted()` now registers as
`type(self)._follow_cursor` so a subclass's override is the effect that runs. A multi-column list keeps `scroll` a
multiple of `rows`, so a column's contents -- and a column as wide as its longest name -- do not change as the cursor
moves through it.

### Where the colours live

In `navigator/styles/navigator.nss`, not with the library. `$dialog-*` is *the file manager's* theme vocabulary,
decoded from `.PAL` files, and `CLAUDE.md` is explicit that navml may not depend on the file manager — a library
sheet naming those would not parse without a Navigator palette behind it. What navml ships is the **contract**: the
parts and states table above, declared on the classes, which is what a sheet is written against. `load_scheme()`
calls `navml.widgets.import_all()` before parsing, because a `StyleProperty` is registered by its class body running
and a list of imports is a thing to forget.

One consequence worth knowing: `Panel` is a `ListViewer` now, and a type selector matches by class *name* over the
whole MRO — so a bare `ListViewer { }` rule ties with `Panel { }` on specificity and wins on source order. The
dialog list and scrollbar rules are scoped `Modal ListViewer` for that reason — and the scope is load-bearing twice
over now that the file manager is itself a `Window`, because `Window ListViewer` would reach every panel. That is also
what the original does: DOS Navigator carries `[35-36]`/`[57-60]` under *Dialogs* and `[83-84]` under *File Manager* precisely because
the same widget is a different colour inside a dialog.

### `Timer`: the first component with nothing to show

`Timer` emits a fieldless `TimerEvent` (→ `on_timer`) every `interval` milliseconds while it is mounted, and paints
nothing. It is **Python alone** for the reason `CheckBoxes` is: it places nothing and paints nothing, so a markup half
would say only what its `class` line says. The clock underneath is navkit's `Application.call_every` — see *Timers:
through the queue* in `navkit/DESIGN.md` — so a tick reaches a markup handler inside a batch like a key does.

It arms from an **effect declared in `mounted()`** that reads `interval`: changing the interval re-arms, `interval <=
0` stops it, `remove()` disposes the effect and `unmounting()` cancels the running handle. `_repeat` is assigned
*before* `super().__init__()`, because that constructor joins the parent and a live parent calls `mounted()` from
inside it. Navigator's `Clock` is the first user: `on_timer: root.blink = not root.blink` in `clock.nml`, with
`clock.py` reading the wall clock at paint time — the time is not state, and the tick is what guarantees a paint.

