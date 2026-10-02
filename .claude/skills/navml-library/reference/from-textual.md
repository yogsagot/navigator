## What Textual has that the library takes

Textual (`github.com/Textualize/textual`, read at 8.2.8) is the nearest neighbour: a Python TUI framework with a
stylesheet, a reactive layer and a widget library. It was surveyed for what navkit and navml are missing. The point
was not to copy it or compete with it. **Fidelity decides the look and the defaults, not what the framework can
do**, so a capability DOS Navigator lacked is still taken when it is generally useful. It is then made optional where
it would change DOS Navigator's look. Where Turbo Vision has the same idea, its name and behaviour win and Textual is
only the reference. Paths below are under Textual's `src/textual/`.

**Taken, and built:**

- `:not()` — `css/match.py`. It takes one compound, as CSS 3 does. See `navkit/DESIGN.md`, *`:not()`*.
- `:focus_within` — `Widget.has_focus_within`. A computed on `Widget`, spelled as the attribute it reads.
- `:hovered` — `Widget.mouse_hover`, with mouse mode 1003. See `navkit/DESIGN.md`, *Hover: a position the
  application keeps*.
- A disabled state that cascades — `Widget.is_disabled`. It is `inert` here; see *`disabled`, never `enabled`*.
- **Commands and key tables** — `binding.py`, `actions.py`, `check_action`; Turbo Vision `cmXXX`. A command is an
  event, a key table is a class attribute or a markup `keys:` block, and the nearest handler decides whether a
  command is enabled. The key bar reads its captions off the tables and greys what cannot run. Action *strings* are
  not taken, and nor is the modifier-held key bar, which a terminal cannot see. See *Commands and key tables* in
  `navkit/DESIGN.md` and *The `keys` block* above. **Menus are the next consumer**: a menu item names a command and
  greys with it.

**Next**, in rough order:

- **A public test pilot** — `pilot.py`, `run_test()`, the snapshot plugin. It offers `press`, `click(widget or
  selector)`, `resize` and golden-frame comparison, generalising `tests/conftest.py`'s `run_app` and `desktop_dump`.
- **`Widget.query(selector)`** — `css/query.py`, reusing the selector matcher. The walk is the only new part.
- ~~**Paste reaches the focused widget**~~ — done: `Widget.dispatch_paste` walks the focus path when
  `Application.on_paste` declines, `InputLine.on_paste` takes it, and copying out is OSC 52 (*Clipboard* in
  `navkit/DESIGN.md`).
- **Input validators** — `validation.py`; Turbo Vision `TValidator`, `TPXPictureValidator`, `TRangeValidator`,
  `TFilterValidator`, `TStringLookupValidator`. Turbo Vision's names and taxonomy, with Textual's result object and
  an `:invalid` state.

**Taken when the tier that needs them arrives:**

- **A `Scroller` base** — `scroll_view.py`; Turbo Vision `TScroller`. `ListViewer`, the console scrollback, View and
  Edit would share one virtual-size and offset model, instead of each doing its own arithmetic against a
  `ScrollBar`.
- **Background work** — `worker.py`, `@work(group, exclusive, thread)`. `spawn` gains groups with exclusive
  cancellation, plus a thread variant that posts its result back through the queue. File operations and slow or
  remote filesystems need it.
- **Tree** `[104-110]` — `widgets/_tree.py`, `_directory_tree.py`; Turbo Vision `TOutline`. The node API and lazy
  expansion are taken. Rows stay painted, not widgets.
- **History** `[53-56]` — Turbo Vision `THistory`. Only the async lookup shape of `suggester.py` is taken, not inline
  ghost text.
- **The editor's document and undo model** — `widgets/_text_area.py`, `document/`. A reference architecture for View
  and Edit.
- **`min`/`max` layout hints, and track sizes and spans for `GridLayout`** — `_resolve.py`'s fr clamp loop.
- **Status-line hints** instead of tooltips — `Binding.tooltip`, `HELP`; Turbo Vision help contexts.

**New widgets DOS Navigator did not have:**

- **Toasts** — `notifications.py`, `widgets/_toast.py`. `Application.notify(text, severity, timeout)` shows a
  non-modal overlay that never takes the focus.
- **Tabs** — `widgets/_tabs.py`, `_tabbed_content.py`. A tab strip over the existing `StackLayout`.
- **Markdown** — `widgets/_markdown.py`, on **`markdown-it-py`**. That is a second run-time dependency. It is pure
  Python, so the noarch `.deb`/`.rpm` claim holds; `requirements.txt` and `pyproject.toml` gain it when it is built.
  Blocks are painted rows, not widgets, the same rule as a listing.

**Optional, and off by default:**

- **Animation** — `_animator.py`, `_easing.py`. `animate(obj, attr, to, duration, easing)` runs on `call_every`.
  DOS Navigator's modals open by growing, which is the case it exists for. Dialog geometry must stay bound, so the
  animation drives a reactive `opening` factor from 0 to 1 that the binding reads, rather than assigning the size.
  It is switched on by `--animate` or a sheet property.
- **Dimming behind a modal, experimental** — **written**, and in navkit rather than as a `ModalScreen`: it needs no
  widget's cooperation. After everything beneath the top modal is painted, those cells are rewritten faint.
  `Application(dim_modal=True)` opts in; *What is deliberately not here* in `navkit/DESIGN.md` has the rest.

**Small:** `Application.bell()`, since DOS Navigator beeps on errors. A coerce hook on `reactive()`, like Textual's
`validate_<name>`, so a `cursor` clamps itself. A `--log` sink, because the application owns the tty and `print`
cannot be used. `--watch-css`, which reloads the sheet when it changes.

**Not taken:**

- **`@on(Message, "#selector")` and `Message.control`.** Both need a sender on an event, which *Which child it was*
  rejected. `on_<id>_<event>` already answers the question.
- **`!important` and nesting.** Rejected in `navkit/DESIGN.md`.
- **Generated theme shades.** Themes are transcribed from `.PAL` files, not derived.
- **The command palette, `DataTable`, `Switch`, `Sparkline` and `Digits`.** Nothing asks for them.
- **`compose()` and `recompose`.** Markup already builds the tree declaratively.
- **`COMPONENT_CLASSES`.** `::part` already covers it, and is checked.
- **`layers`, `offset` and `position`.** Tree order, `raise_child` and `overlay()` already cover them.

