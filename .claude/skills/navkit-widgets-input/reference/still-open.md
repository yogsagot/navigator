## Still open

- Whether the cell test should ever gain a tolerance. Two presses must land in the *same* cell today, which fails by
  missing a double-click rather than by inventing one, and that is the right way round where the consequence is
  opening something. But a cell is a large target next to the pixel slop a GUI toolkit allows, and what counts as "the
  same thing" is arguably the widget's to say — a row, a cell, a word — which navkit has no way to ask. The day
  something asks, the answer is probably a widget-supplied granularity rather than a constant, and it should not be
  guessed at before then.

- ~~What `Application.background` becomes.~~ **Answered: it is derived from the root widget's resolved style.** The
  duplication was never the second *paint* — `Manager.render` filling its own area is what lets the desktop be painted
  with no application around it, which `Manager.__init__`'s own sheet exists for. It was the second *derivation*:
  `navigator.nss` says `Manager { fg: $desktop-fg; bg: $desktop-bg }`, and `desktop_style()` read those same two
  variables by a separate route, going behind the cascade to the raw variable table because it ran "before any widget
  exists to ask". Asking the root at paint time is later, and later is when the answer exists. `background=` is now
  `None` by default and still accepted, for a root that paints only part of itself or for no root at all; `Navigator`
  stops passing it and `desktop_style()` is gone. Checked across all eleven themes: every desktop colour resolves to
  what it did before.
- ~~Which parts and properties the eventual *library* widgets declare.~~ **Answered, and the answer was read off
  DOS Navigator rather than designed.** The Colors dialog's slot table — all 144 entries of it, already transcribed
  into every theme by `tools/palconv.py` and carried inert — *names the widgets and their states*: frame and frame
  icons, scroll bar page and icons, static text, label normal/selected/shortcut, button
  normal/default/selected/disabled/shortcut/shadow, cluster normal/selected/shortcut, input normal/selected/arrow,
  list normal/focused/selected/divider. So the library's parts are a transcription, `navigator/styles/navigator.nss`
  binds them, and `navml/DESIGN.md`'s *The widget library* has the table.

  The half of this bullet that was *wrong* is now fixed too. "They are what the parser checks an unknown key
  against" was not true of parts: a `::part` selector was accepted whatever it named, so `Panel::rwo { }` matched
  nothing and said nothing. It cannot be checked at parse time — a selector matches by class *name* over the MRO, so
  the parser has no class to ask and a sheet may legally name a type it could not import. It is checked where the
  class is in hand instead: `Widget.parts` declares them, `stylesheet.parts_of()` unions them down the MRO the way
  `emitted()` does, and `part_style()` refuses a name its widget never declared. A test loads the shipped sheet with
  the widgets imported and asks the same question of every `::part` in it, which is the parse-time check spelled the
  only way it can be.
- What a full-screen child does. `run_on_terminal` hands over the real terminal and loses the output, which is the one
  thing the console exists to keep. The alternative is teaching the console an alternate buffer of its own — pyte stores
  `?1049` without obeying it — and that is worth doing only once something actually launches an editor.
- ~~Where the console's key routing belongs.~~ **Answered by focus, as predicted, and it took three methods instead
  of one.** `Navigator.on_key` keeps only what means the same thing wherever the focus is — Ctrl+O, and F10/Ctrl+Q —
  (since superseded twice: it is `Navigator.keys` now, a key table, and F10 is DOS Navigator's menu, not Quit)
  because an application hook runs before the widgets, so whatever is kept there is kept from the console, from the
  panels and from every dialog not yet written. `Console.on_key` keeps the scrollback and sends the rest to the child.
  `Manager.on_key` keeps the panel keys. **The `if manager.console_visible:` that used to arbitrate is gone
  entirely**: the console holds the focus while it is showing, so the focus path answers that question and the
  desktop's own handler never runs. Alt+X sat with the desktop rather than with the other two ways out because it has
  always been a desktop key — with the console up it is a keystroke for the child, and the child got it by
  `Manager.on_key` never running. **That stopped being true once windows could be closed**: closing the file manager
  took the key with it, and the user was left with no Alt+X at all. It is `Navigator.on_key`'s now, and the one
  application key that asks a question — it is left for the child while Ctrl+O has put windows away, and quits when
  there are none, because then the console *is* the desktop.

  One thing had to change to make it safe, and it is worth knowing before writing anything similar: **the focus
  handover has to be synchronous with the flag it follows.** It was an effect for one commit, which is correct for the
  cursor — an effect runs before the frame is composed, so the caret is never drawn in the wrong place. It is wrong
  for a keyboard: a batch of events is dispatched *before* the effects flush, so a Ctrl+O and the keystroke behind it,
  arriving together as a paste or fast typing do, would be routed by a focus that had not moved yet and the second key
  would reach the panels. `toggle_console` now moves the focus itself, and a test posts both events in one callback to
  pin it.
- ~~Which glyphs beyond a box frame the *library* widgets need.~~ **Answered: three vocabularies, and the third
  answer is the same for all of them.** `SCROLLBARS` is six characters — up, down, left, right, track, thumb, which is
  Turbo Vision's `TScrollBar.Chars` plus the thumb; `MARKS` is four — check off, check on, radio off, radio on, with
  the brackets around them fixed in the widget because they are ASCII in the original too; and `BOX_JOINS` is five
  tees keyed by *the frame's own name*, because a single rule meeting a double frame is `╤` and not `┬`, and
  `border: double` with `+` tees is a bug rather than a preference. Each has a lookup mirroring `charset()` and each
  collapses at the same lower boundary.

  **A Nerd Font improves on none of them.** Every shape is box-drawing, block-element or geometric-shape, all of
  which `GLYPHS_UNICODE` already guarantees; the Private Use Area carries icons, and an icon is a *replacement* for
  one of these rather than a better version — the one real candidate, a single-glyph check box, is refused because it
  collapses three cells into one and moves every caption in the cluster. `navigator/icons.py` remains the project's
  one deliberate departure and this is not a second.

### What the widget library needs first

**All four are now built**, and this list is kept as the record of what they were and in which order they unblocked
each other, because each one is cheaper than the last for reasons the previous one paid for. The markup language never
needed any of them — a `.nml` that declares a tree, binds geometry and carries a `style` block compiles onto what was
already here, and `Manager._place()` is the proof. A **widget library** needs all four, because a button, a dialog and
a pull-down menu are made of them.

1. **Focus — done.** `Application.focused`, `Widget.can_focus`, `Widget.focus()`, `Widget.focusable()` and
   `Application.focus_next()` are written and tested, and `dispatch_key` now walks the focus path instead of touring
   every descendant until one claimed the key; *Focus: one pointer, and eligibility decided at delivery* above is the
   reasoning. (4) did depend on this one, and cost one substitution because of it. (2) and (3) turned out not to — see
   *Emitting: a widget event walks up*, where a nested button takes a mouse press by position with no focus anywhere
   in the picture. What is left here is the application's own use of it: `Navigator.on_key` is still one central
   `if/elif` chain over a hand-rolled `Panel.active`, and `Manager.active_panel` is still what a focused widget would
   otherwise be. Converting those is `navigator`'s work, not navkit's, and nothing forces it before the panels have to
   compete with a dialog.
2. **Signals — done.** `Widget.emit()`, `Event.handler` and the `_handle` fallback are written and tested;
   *Emitting: a widget event walks up* above is the whole of the reasoning, and `navml/DESIGN.md` has the markup half
   it had to be settled with. Reactive attributes plus `effect()` stay the right answer for *state*; a signal is for
   the thing that has no state, "this button was pressed". Of the two events that still never reach a widget,
   `ResizeEvent` is answered by `layout()` already and `PasteEvent` is waiting on focus rather than on this.
3. **Mount and unmount — done.** `Widget.mounted`, `on_mount`/`on_unmount` with their empty events, the two walks and
   `reactive.dispose_effects()` are written and tested; *Mounting: joining a live tree, and leaving one* above is the
   reasoning. `add()` now lays a child out into a mounted parent, and `remove()` disposes the subtree's effects — which
   was a crash rather than a gap, since an eager effect reading `self.parent.width` raises at the flush that follows
   the detach and `Application._flush_effects` turns that into an exit. The binding half needed nothing: lazy cells are
   never evaluated while nothing paints them, and re-attaching invalidates the cached failure.
4. **Modal and overlay — done.** `Widget.modal`, `Application.modal`, `Application.overlay()` and the two rerouted
   dispatch paths are written and tested; *Modal and overlay: the input, not the painting* above is the reasoning.
   Z-order needed nothing — paint forwards, hit-test backwards already puts a dialog on top. Keyboard exclusivity cost
   one substitution, because (1) had made `dispatch_key` walk a focus path that a modal can be the end of. The mouse
   cost an actual reroute, routing by position rather than by focus. And the modal stack is maintained by (3)'s mount
   walks, so every way out of the tree gives the input back without knowing what a modal is.

A fifth, smaller — **done**: the cursor was unconditionally hidden (`Terminal.start` emits `HIDE_CURSOR` and
`render_diff` still never places one), so a text input had no caret except a reversed cell. `Widget.cursor_position()`
now says where one belongs, the application places it at the end of the frame for whichever widget the keys are going
to, and `caret` is a widget property the sheet can set to a DECSCUSR shape. *The cursor: shown where the keys go*
above is the reasoning. `navigator`'s console was converted with it: it takes the focus while it is showing and reports
the child program's cursor, so `Console.render`'s reversed cell is gone.
